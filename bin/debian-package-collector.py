#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, BooleanOptionalAction
from signal import signal, SIGINT, SIGTERM
from typing import Any

from common_utility import SessionProvider, FileDownloader, ReusableTimer
from common_utility.jsonLoader import JsonLoader
from context_logger import get_logger, setup_logging
from package_downloader import RepositoryProvider, AssetDownloader

from package_collector import (
    PackageCollector,
    SourceRegistry,
    ReleaseMonitor,
    WebhookServer,
    PackageCollectorConfig,
    WebhookServerConfig,
)

log = get_logger('PackageCollectorApp')


def main() -> None:
    arguments = _get_arguments()

    setup_logging('debian-package-collector', arguments.log_level, arguments.log_file)

    log.info('Starting package collector', arguments=vars(arguments))

    repository_provider = RepositoryProvider()
    source_registry = SourceRegistry(repository_provider, arguments.token)

    session_provider = SessionProvider()
    file_downloader = FileDownloader(session_provider, os.path.abspath(arguments.download))
    asset_downloader = AssetDownloader(file_downloader)

    reusable_timer = ReusableTimer()
    release_monitor = ReleaseMonitor(source_registry, asset_downloader, reusable_timer, arguments.interval)
    server_config = WebhookServerConfig(arguments.port, arguments.secret, arguments.delay)
    webhook_server = WebhookServer(source_registry, file_downloader, asset_downloader, server_config)
    config_path = file_downloader.download(arguments.release_config, skip_if_exists=False)
    config = PackageCollectorConfig(config_path, arguments.initial, arguments.monitor, arguments.webhook)
    json_loader = JsonLoader()

    package_collector = PackageCollector(config, json_loader, source_registry, release_monitor, webhook_server)

    def handler(signum: int, frame: Any) -> None:
        log.info('Shutting down package collector', signum=signum)
        package_collector.shutdown()

    signal(SIGINT, handler)
    signal(SIGTERM, handler)

    package_collector.run()


def _get_arguments() -> Namespace:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-f',
        '--log-file',
        help='log file path',
        default='/var/log/effective-range/debian-package-collector/debian-package-collector.log',
    )
    parser.add_argument('-l', '--log-level', help='logging level', default='info')
    parser.add_argument('-d', '--download', help='package download location', default='/tmp/packages')
    parser.add_argument('-i', '--interval', help='release monitor interval in seconds', type=int, default=600)
    parser.add_argument('-p', '--port', help='webhook server port to listen on', type=int, default=8080)
    parser.add_argument(
        '-s', '--secret', help='webhook secret to verify requests, supports environment variables with $'
    )
    parser.add_argument(
        '-t', '--token', help='global token to use if not specified in config, supports environment variables with $'
    )
    parser.add_argument('-D', '--delay', help='download delay in seconds after webhook request', type=int, default=10)

    parser.add_argument('--initial', help='enable initial collection', action=BooleanOptionalAction, default=True)
    parser.add_argument('--monitor', help='enable periodic monitoring', action=BooleanOptionalAction, default=True)
    parser.add_argument('--webhook', help='enable the webhook server', action=BooleanOptionalAction, default=True)

    parser.add_argument('release_config', help='release config JSON file path or URL')

    return parser.parse_args()


if __name__ == '__main__':
    main()
