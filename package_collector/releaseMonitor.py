# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from common_utility import IReusableTimer
from context_logger import get_logger
from package_downloader import IAssetDownloader

from package_collector import ISourceRegistry, IReleaseSource

log = get_logger('ReleaseMonitor')


class IReleaseMonitor(object):

    def start(self) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()

    def check_all(self) -> None:
        raise NotImplementedError()

    def check(self, package: str) -> None:
        raise NotImplementedError()


class ReleaseMonitor(IReleaseMonitor):

    def __init__(self, source_registry: ISourceRegistry, asset_downloader: IAssetDownloader,
                 monitor_timer: IReusableTimer, monitor_interval: int = 600) -> None:
        self._source_registry = source_registry
        self._asset_downloader = asset_downloader
        self._monitor_timer = monitor_timer
        self._monitor_interval = monitor_interval
        self._is_running = False

    def start(self) -> None:
        log.info('Starting monitoring')
        self._monitor_timer.start(self._monitor_interval, self._check_all_periodic)
        self._is_running = True

    def stop(self) -> None:
        log.info('Stopping monitoring')
        self._monitor_timer.cancel()
        self._is_running = False

    def check_all(self) -> None:
        log.info('Checking for new releases')

        for source in self._source_registry.get_all():
            if not self._is_running:
                log.info('Checking interrupted')
                return

            self._check_source(source)

        log.info('Checking completed')

    def check(self, repo_name: str) -> None:
        if source := self._source_registry.get(repo_name):
            self._check_source(source)
        else:
            log.warn('No source registered for repository', repo=repo_name)

    def _check_all_periodic(self) -> None:
        self._monitor_timer.restart()

        self.check_all()

    def _check_source(self, source: IReleaseSource) -> None:
        if source.check_latest_release():
            if release := source.get_release():
                try:
                    self._asset_downloader.download(source.get_config(), release)
                except Exception as exception:
                    log.error('Failed to download release',
                              repo=source.get_config().full_name, release=release.tag_name, error=str(exception))
