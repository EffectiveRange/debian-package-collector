# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from typing import Optional

from context_logger import get_logger
from package_downloader import IRepositoryProvider, ReleaseConfig

from package_collector import IReleaseSource, ReleaseSource

log = get_logger('SourceRegistry')


class ISourceRegistry(object):

    def register(self, config: ReleaseConfig) -> IReleaseSource:
        raise NotImplementedError()

    def is_registered(self, repo_name: str) -> bool:
        raise NotImplementedError()

    def get(self, repo_name: str) -> IReleaseSource:
        raise NotImplementedError()

    def get_all(self) -> list[IReleaseSource]:
        raise NotImplementedError()


class SourceRegistry(ISourceRegistry):

    def __init__(self, repository_provider: IRepositoryProvider, github_token: Optional[str] = None) -> None:
        self._repository_provider = repository_provider
        self._github_token = github_token
        self._release_sources: dict[str, IReleaseSource] = {}

    def register(self, config: ReleaseConfig) -> IReleaseSource:
        repo_name = config.full_name

        source = self._release_sources.get(repo_name)

        if source:
            log.warn('Release source already registered', repo=repo_name)
            return source

        if not config.token and self._github_token:
            log.info('Using global GitHub token for release source', repo=repo_name)
            config.token = self._github_token

        source = ReleaseSource(config, self._repository_provider)
        self._release_sources[repo_name] = source
        log.info('Registered release source for repository', repo=repo_name, config=config)

        return source

    def is_registered(self, repo_name: str) -> bool:
        return self._release_sources.get(repo_name) is not None

    def get(self, repo_name: str) -> IReleaseSource:
        source = self._release_sources.get(repo_name)

        if not source:
            log.error('Release source not registered', repo=repo_name)
            raise KeyError('Release source not registered')

        return source

    def get_all(self) -> list[IReleaseSource]:
        return list(self._release_sources.values())
