# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import fnmatch
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from threading import Thread
from typing import Any, Optional

from common_utility import IFileDownloader, IReusableTimer
from context_logger import get_logger
from flask import Flask, request, Response, abort
from package_downloader import IAssetDownloader
from waitress.server import create_server

from package_collector import ISourceRegistry, IReleaseSource

log = get_logger('WebhookServer')


@dataclass
class WebhookServerConfig:
    port: int
    secret: str
    delay: int


class IWebhookServer(object):

    def start(self) -> None:
        raise NotImplementedError()

    def shutdown(self) -> None:
        raise NotImplementedError()

    def is_running(self) -> bool:
        raise NotImplementedError()


class WebhookServer(IWebhookServer):

    def __init__(
        self,
        source_registry: ISourceRegistry,
        file_downloader: IFileDownloader,
        asset_downloader: IAssetDownloader,
        delay_timer: IReusableTimer,
        config: WebhookServerConfig,
    ) -> None:
        self._source_registry = source_registry
        self._file_downloader = file_downloader
        self._asset_downloader = asset_downloader
        self._delay_timer = delay_timer
        self._port = config.port
        self._secret = self._get_secret(config.secret)
        self._delay = config.delay
        self._app = Flask(__name__)
        self._server = create_server(self._app, listen=f'*:{self._port}')
        self._thread = Thread(target=self._start_server)
        self._is_running = False

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
        self._delay_timer.cancel()
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
            source = self._source_registry.get(repo_name)

            assets = release['assets']

            log.info('Available assets', assets=[asset['name'] for asset in assets])

            if assets:
                self._delay_timer.start(0, self._download_asset_from_url, args=[source, assets])
                return Response(status=200)
            else:
                log.warn(
                    'No assets found in request, retrying using the API with a delay',
                    repo=repo_name,
                    tag=tag,
                    delay=self._delay,
                )
                self._delay_timer.start(self._delay, self._download_asset_from_api, args=[source])
                return Response(status=200)
        else:
            log.warn('Repository not registered, skipping', repo=repo_name)
            return Response(status=204)

    def _download_asset_from_url(self, source: IReleaseSource, assets: list[dict[str, Any]]) -> None:
        config = source.get_config()
        any_match = False

        for asset in assets:
            if fnmatch.fnmatch(asset['name'], config.matcher):
                any_match = True
                log.info('Found matching asset', release=config, asset=asset['name'])

                self._download_asset(asset, config.raw_token)

        if not any_match:
            log.warn('No matching assets found', release=config)

    def _download_asset(self, asset: dict[str, Any], token: Optional[str] = None) -> None:
        log.debug('Downloading asset', asset=asset['name'])

        headers = {'Accept': 'application/octet-stream'}

        if token:
            headers['Authorization'] = f'token {token}'

        self._file_downloader.download(asset['url'], asset['name'], headers)

    def _download_asset_from_api(self, source: IReleaseSource) -> None:
        config = source.get_config()
        release = source.get_release()
        if release:
            self._asset_downloader.download(config, release)
