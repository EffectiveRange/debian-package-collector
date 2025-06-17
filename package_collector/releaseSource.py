# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from threading import Lock
from typing import Optional

from context_logger import get_logger
from github import UnknownObjectException
from github.GitRelease import GitRelease
from github.Repository import Repository
from package_downloader import IRepositoryProvider, ReleaseConfig

log = get_logger('ReleaseSource')


class IReleaseSource(object):

    def get_config(self) -> ReleaseConfig:
        raise NotImplementedError()

    def get_release(self) -> Optional[GitRelease]:
        raise NotImplementedError()

    def check_latest_release(self) -> bool:
        raise NotImplementedError()


class ReleaseSource(IReleaseSource):

    def __init__(self, config: ReleaseConfig, repository_provider: IRepositoryProvider) -> None:
        self._config = config
        self._repository_provider = repository_provider
        self._repository: Optional[Repository] = None
        self._release: Optional[GitRelease] = None
        self._lock = Lock()

    def get_config(self) -> ReleaseConfig:
        return self._config

    def get_release(self) -> Optional[GitRelease]:
        with self._lock:
            return self._release

    def check_latest_release(self) -> bool:
        with self._lock:
            if latest_release := self._get_latest_release():
                current_tag = self._release.tag_name if self._release else None
                latest_tag = latest_release.tag_name
                repo_name = self._config.full_name

                if not current_tag:
                    log.info('Initial release', repo=repo_name, tag=latest_tag)
                    update = True
                elif current_tag != latest_tag:
                    log.info('New release found', repo=repo_name, old_tag=current_tag, new_tag=latest_tag)
                    update = True
                else:
                    update = self._check_for_new_assets(latest_release)

                if update:
                    self._release = latest_release
                    return self._check_for_any_assets(latest_release)

            return False

    def _check_for_new_assets(self, release: GitRelease) -> bool:
        current_assets = [asset.name for asset in self._release.assets] if self._release else []
        latest_assets = [asset.name for asset in release.assets]
        new_assets = list(set(latest_assets) - set(current_assets))

        if new_assets:
            log.info('New assets for release', repo=self._config.full_name, tag=release.tag_name, new_assets=new_assets)
            return True

        return False

    def _check_for_any_assets(self, release: GitRelease) -> bool:
        if not release.assets:
            log.warning('No assets for release', repo=self._config.full_name, tag=release.tag_name)
            return False

        return True

    def _get_latest_release(self) -> Optional[GitRelease]:
        try:
            repository = self._get_repository()
            return repository.get_latest_release()
        except UnknownObjectException as error:
            log.warn('No release found', status=error.status, reason=error.message, repo=self._config.full_name)
            return None
        except Exception as error:
            log.error('Unexpected error fetching latest release', error=error, repo=self._config.full_name)
            return None

    def _get_repository(self) -> Repository:
        if not self._repository:
            self._repository = self._repository_provider.get_repository(self._config)

            if self._config.private is None:
                self._config.private = self._repository.private

        return self._repository
