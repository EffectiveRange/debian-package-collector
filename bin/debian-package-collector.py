#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, BooleanOptionalAction
from collections import OrderedDict
from pathlib import Path
from signal import signal, SIGINT, SIGTERM
from typing import Any, Optional

from common_utility import SessionProvider, FileDownloader, ReusableTimer, ConfigLoader
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

APPLICATION_NAME = 'debian-package-collector'

log = get_logger('PackageCollectorApp')


def main() -> None:
    resource_root = _get_resource_root()
    arguments = _get_arguments()

    setup_logging(APPLICATION_NAME)

    config = ConfigLoader(resource_root / f'config/{APPLICATION_NAME}.conf').load(arguments)

    _update_logging(config)

    log.info(f'Started {APPLICATION_NAME}')

    initial_collect = bool(config.get('initial_collect', True))
    github_token = config.get('github_token')
    download_dir = Path(config.get('download_dir', '/tmp/packages'))
    distro_sub_dirs = config.get('distro_sub_dirs')
    private_sub_dir = Path(config.get('private_sub_dir', 'private'))

    monitor_enable = bool(config.get('monitor_enable', True))
    monitor_interval = int(config.get('monitor_interval', 600))

    webhook_enable = bool(config.get('webhook_enable', True))
    webhook_secret = config.get('webhook_secret', '')
    webhook_port = int(config.get('webhook_port', 8080))
    webhook_retry = int(config.get('webhook_retry', 10))
    webhook_delay = int(config.get('webhook_delay', 60))

    release_config = config['release_config']

    repository_provider = RepositoryProvider()
    source_registry = SourceRegistry(repository_provider, github_token)

    session_provider = SessionProvider()
    file_downloader = FileDownloader(session_provider, download_dir)
    asset_downloader = AssetDownloader(file_downloader, _get_distro_map(distro_sub_dirs), private_sub_dir)

    reusable_timer = ReusableTimer()
    release_monitor = ReleaseMonitor(source_registry, asset_downloader, reusable_timer, monitor_interval)
    server_config = WebhookServerConfig(webhook_port, webhook_secret, webhook_retry, webhook_delay)
    webhook_server = WebhookServer(source_registry, asset_downloader, server_config)
    config_path = file_downloader.download(release_config, skip_if_exists=False)
    collector_config = PackageCollectorConfig(config_path, initial_collect, monitor_enable, webhook_enable)
    json_loader = JsonLoader()

    package_collector = PackageCollector(
        collector_config, json_loader, source_registry, release_monitor, webhook_server
    )

    def handler(signum: int, frame: Any) -> None:
        log.info(f'Shutting down {APPLICATION_NAME}', signum=signum)
        package_collector.shutdown()

    signal(SIGINT, handler)
    signal(SIGTERM, handler)

    package_collector.run()


def _get_arguments() -> dict[str, Any]:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-c',
        '--config-file',
        help='configuration file',
        default=f'/etc/effective-range/{APPLICATION_NAME}/{APPLICATION_NAME}.conf',
    )

    parser.add_argument('-f', '--log-file', help='log file path')
    parser.add_argument('-l', '--log-level', help='logging level')

    parser.add_argument('--initial-collect', help='enable initial collection', action=BooleanOptionalAction)
    parser.add_argument('--github-token', help='global token to use if not specified, supports env variables with $')
    parser.add_argument('--download-dir', help='package download location')
    parser.add_argument('--distro-sub-dirs', help='distribution subdirectories')
    parser.add_argument('--private-sub-dir', help='subdirectory for private packages')

    parser.add_argument('--monitor-interval', help='release monitor interval in seconds')
    parser.add_argument('--monitor-enable', help='enable periodic monitoring', action=BooleanOptionalAction)

    parser.add_argument('--webhook-enable', help='enable the webhook server', action=BooleanOptionalAction)
    parser.add_argument('--webhook-secret', help='secret to verify requests, supports env variables with $')
    parser.add_argument('--webhook-port', help='webhook server port to listen on')
    parser.add_argument('--webhook-retries', help='max retries to download assets', type=int)
    parser.add_argument('--webhook-delay', help='delay between retries in seconds', type=int)

    parser.add_argument('release_config', help='release config JSON file path or URL')

    return {k: v for k, v in vars(parser.parse_args()).items() if v is not None}


def _get_resource_root() -> Path:
    return Path(os.path.dirname(__file__)).parent.absolute()


def _update_logging(configuration: dict[str, Any]) -> None:
    log_level = configuration.get('log_level', 'INFO')
    log_file = configuration.get('log_file')
    setup_logging(APPLICATION_NAME, log_level, log_file, warn_on_overwrite=False)


def _get_distro_map(distro_sub_dirs: Optional[str]) -> OrderedDict[str, str]:
    distro_map = OrderedDict()

    if distro_sub_dirs:
        for distro in distro_sub_dirs.split(','):
            distro_map[distro.strip()] = distro.strip()

    return distro_map


if __name__ == '__main__':
    main()
