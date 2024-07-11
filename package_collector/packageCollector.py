# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any

from context_logger import get_logger
from package_downloader import IJsonLoader, ReleaseConfig

from package_collector import IReleaseMonitor, IWebhookServer, ISourceRegistry

log = get_logger('PackageCollector')


@dataclass
class PackageCollectorConfig:
    config_path: str
    enable_monitor: bool
    enable_webhook: bool


class PackageCollector(object):

    def __init__(self, config: PackageCollectorConfig, json_loader: IJsonLoader, source_registry: ISourceRegistry,
                 release_monitor: IReleaseMonitor, webhook_server: IWebhookServer):
        self._config = config
        self._json_loader = json_loader
        self._source_registry = source_registry
        self._release_monitor = release_monitor
        self._webhook_server = webhook_server

    def __enter__(self) -> 'PackageCollector':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()

    def run(self) -> None:
        config_list = self._json_loader.load_list(self._config.config_path, ReleaseConfig)

        for config in config_list:
            self._source_registry.register(config)

        if self._config.enable_monitor:
            log.info('Starting release monitor')
            self._release_monitor.start()

        if self._config.enable_webhook:
            log.info('Starting webhook server')
            self._webhook_server.start()

        log.info('Collecting initial packages')
        self._release_monitor.check_all()

    def shutdown(self) -> None:
        if self._config.enable_monitor:
            log.info('Stopping release monitor')
            self._release_monitor.shutdown()

        if self._config.enable_webhook:
            log.info('Stopping webhook server')
            self._webhook_server.shutdown()
