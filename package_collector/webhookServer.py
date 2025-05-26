# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import hashlib
import hmac
import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Thread, Event
from typing import Any, Optional

from context_logger import get_logger
from flask import Flask, request, Response, abort
from package_downloader import IAssetDownloader
from tenacity import Retrying, stop_after_attempt, wait_fixed, stop_any, stop_when_event_set
from waitress.server import create_server

from package_collector import ISourceRegistry

log = get_logger('WebhookServer')


@dataclass
class WebhookServerConfig:
    port: int
    secret: str
    retry: int
    delay: float


class AssetsNotAvailableError(Exception):

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class IWebhookServer(object):

    def start(self) -> None:
        raise NotImplementedError()

    def shutdown(self) -> None:
        raise NotImplementedError()

    def is_running(self) -> bool:
        raise NotImplementedError()


class WebhookServer(IWebhookServer):

    def __init__(self, source_registry: ISourceRegistry, asset_downloader: IAssetDownloader,
                 config: WebhookServerConfig) -> None:
        self._source_registry = source_registry
        self._asset_downloader = asset_downloader
        self._port = config.port
        self._secret = self._get_secret(config.secret)
        self._retry = config.retry
        self._delay = config.delay
        self._app = Flask(__name__)
        self._server = create_server(self._app, listen=f'*:{self._port}')
        self._thread = Thread(target=self._start_server)
        self._is_running = False
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._events: dict[str, Event] = {}

        self._set_up_webhook_endpoint()

    def __enter__(self) -> 'WebhookServer':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()

    def start(self) -> None:
        log.info('Starting server', port=self._port)
        self._thread.start()

    def shutdown(self) -> None:
        log.info('Shutting down')
        for event in self._events.values():
            event.set()
        self._executor.shutdown()
        self._server.close()
        self._thread.join()
        self._is_running = False

    def is_running(self) -> bool:
        return self._is_running

    def _start_server(self) -> None:
        try:
            self._is_running = True
            self._server.run()
        except Exception as error:
            self._is_running = False
            log.info('Shutdown', reason=error)

    def _get_secret(self, secret: str) -> Optional[str]:
        if secret and secret.startswith('$'):
            return os.getenv(secret[1:])
        return secret

    def _set_up_webhook_endpoint(self) -> None:

        @self._app.route('/webhook', methods=['POST'])
        def webhook() -> Response:
            self._verify_signature()

            if request.headers.get('X-GitHub-Event') == 'release':
                payload = json.loads(request.data)

                log.debug('Received release event', payload=payload)

                if payload['action'] in ['released', 'published', 'edited']:
                    return self._process_release(payload)

            return Response(status=204)

    def _verify_signature(self) -> None:
        if not (signature_header := request.headers.get('X-Hub-Signature-256')):
            log.error('No signature provided')
            abort(403, 'No signature provided')

        sha_name, signature = signature_header.split('=')
        if sha_name != 'sha256':
            log.error('Only sha256 signature is supported')
            abort(403, 'Only sha256 signature is supported')

        if self._secret:
            mac = hmac.new(self._secret.encode(), msg=request.data, digestmod=hashlib.sha256)
            if not hmac.compare_digest(mac.hexdigest(), signature):
                log.error('Invalid signature')
                abort(403, 'Invalid signature')

    def _process_release(self, payload: dict[str, Any]) -> Response:
        repo_name = payload['repository']['full_name']
        release = payload['release']
        action = payload['action']
        tag = release['tag_name']

        log.info('Processing release', repo=repo_name, action=action, tag=tag)

        if self._source_registry.is_registered(repo_name):
            event = self._get_event(repo_name)

            retryer = Retrying(stop=stop_any(stop_after_attempt(self._retry), stop_when_event_set(event)),
                               wait=wait_fixed(self._delay), reraise=True)

            self._executor.submit(retryer, self._download_asset_from_api, repo_name)

            return Response(status=200)
        else:
            log.warn('Repository not registered, skipping', repo=repo_name)
            return Response(status=204)

    def _download_asset_from_api(self, repo_name: str) -> None:
        source = self._source_registry.get(repo_name)

        if source.check_latest_release():
            if release := source.get_release():
                self._asset_downloader.download(source.get_config(), release)
        else:
            log.warn('Assets not available yet', repo=repo_name)
            raise AssetsNotAvailableError('Assets not available yet')

    def _get_event(self, repo_name: str) -> Event:
        if repo_name in self._events:
            self._events[repo_name].set()

        event = Event()
        self._events[repo_name] = event

        return event
