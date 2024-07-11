# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from typing import Optional, Tuple

from context_logger import get_logger
from github.GitRelease import GitRelease
from package_downloader import IRepositoryProvider, ReleaseConfig

log = get_logger('ReleaseSource')


class IReleaseSource(object):

    def get_config(self) -> ReleaseConfig:
        raise NotImplementedError()

    def get_release(self) -> Optional[GitRelease]:
        raise NotImplementedError()

    def get_config_and_release(self) -> Tuple[ReleaseConfig, Optional[GitRelease]]:
        raise NotImplementedError()

    def check_release(self) -> bool:
        raise NotImplementedError()

    def check_latest_release(self) -> bool:
        raise NotImplementedError()


class ReleaseSource(IReleaseSource):

    def __init__(self, config: ReleaseConfig, repository_provider: IRepositoryProvider) -> None:
        self._config = config
        self._release: Optional[GitRelease] = None
        self._repository = repository_provider.get_repository(self._config)

    def get_config(self) -> ReleaseConfig:
        return self._config

    def get_release(self) -> Optional[GitRelease]:
        return self._release

    def check_latest_release(self) -> bool:
        if latest_release := self._get_release():
            if not self._release or self._release.tag_name != latest_release.tag_name:
                old_tag = self._release.tag_name if self._release else None
                log.info('New release found', old_tag=old_tag, new_tag=latest_release.tag_name)
                self._release = latest_release
                return True

        return False

    def _get_release(self) -> Optional[GitRelease]:
        try:
            return self._repository.get_latest_release()
        except Exception as error:
            log.error('Error fetching release', error=error)
            return None
