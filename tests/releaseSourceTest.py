import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging
from github.GitRelease import GitRelease
from github.GitReleaseAsset import GitReleaseAsset
from github.Repository import Repository
from package_downloader import IRepositoryProvider, ReleaseConfig

from package_collector import ReleaseSource


class ReleaseSourceTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('debian-package-collector', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_returns_false_when_failed_to_get_repository(self):
        # Given
        config, repository_provider, repository = create_components()
        release_source = ReleaseSource(config, repository_provider)
        repository_provider.get_repository.side_effect = Exception('Failed to get repository')

        # When
        result = release_source.check_latest_release()

        # Then
        self.assertFalse(result)
        repository_provider.get_repository.assert_called_once_with(config)

    def test_returns_false_when_no_release_found(self):
        # Given
        config, repository_provider, repository = create_components()
        release_source = ReleaseSource(config, repository_provider)

        # When
        result = release_source.check_latest_release()

        # Then
        self.assertFalse(result)
        repository_provider.get_repository.assert_called_once_with(config)

    def test_returns_true_when_first_release_found(self):
        # Given
        release = create_release('1.0.0')
        config, repository_provider, repository = create_components(release)
        release_source = ReleaseSource(config, repository_provider)

        # When
        result = release_source.check_latest_release()

        # Then
        self.assertTrue(result)
        repository_provider.get_repository.assert_called_once_with(config)

    def test_returns_true_when_new_release_found(self):
        # Given
        release1 = create_release('1.0.0')
        release2 = create_release('1.1.0')
        config, repository_provider, repository = create_components(release1)
        release_source = ReleaseSource(config, repository_provider)

        release_source.check_latest_release()

        repository.get_latest_release.return_value = release2

        # When
        result = release_source.check_latest_release()

        # Then
        self.assertTrue(result)

    def test_returns_false_when_new_release_found_and_no_assets(self):
        # Given
        release1 = create_release('1.0.0')
        release2 = create_release('1.1.0')
        release2.assets = []
        config, repository_provider, repository = create_components(release1)
        release_source = ReleaseSource(config, repository_provider)

        release_source.check_latest_release()

        repository.get_latest_release.return_value = release2

        # When
        result = release_source.check_latest_release()

        # Then
        self.assertFalse(result)

    def test_returns_false_when_same_release(self):
        # Given
        release1 = create_release('1.1.0')
        release2 = create_release('1.1.0')
        config, repository_provider, repository = create_components(release1)
        release_source = ReleaseSource(config, repository_provider)

        release_source.check_latest_release()

        repository.get_latest_release.return_value = release2

        # When
        result = release_source.check_latest_release()

        # Then
        self.assertFalse(result)

    def test_returns_true_when_same_release_and_new_assets_found(self):
        # Given
        release1 = create_release('1.1.0')
        release2 = create_release('1.1.0')

        new_asset = MagicMock(spec=GitReleaseAsset)
        new_asset.name = 'asset3'
        release2.assets.append(new_asset)

        config, repository_provider, repository = create_components(release1)
        release_source = ReleaseSource(config, repository_provider)

        release_source.check_latest_release()

        repository.get_latest_release.return_value = release2

        # When
        result = release_source.check_latest_release()

        # Then
        self.assertTrue(result)

    def test_returns_config(self):
        # Given
        release = create_release('1.0.0')
        config, repository_provider, repository = create_components(release)
        release_source = ReleaseSource(config, repository_provider)

        # When
        result = release_source.get_config()

        # Then
        self.assertEqual(config, result)

    def test_returns_release(self):
        # Given
        release = create_release('1.0.0')
        config, repository_provider, repository = create_components(release)
        release_source = ReleaseSource(config, repository_provider)

        release_source.check_latest_release()

        # When
        result = release_source.get_release()

        # Then
        self.assertEqual(release, result)


def create_release(tag_name):
    release = MagicMock(spec=GitRelease)
    release.tag_name = tag_name
    asset1 = MagicMock(spec=GitReleaseAsset)
    asset1.name = 'asset1'
    asset2 = MagicMock(spec=GitReleaseAsset)
    asset2.name = 'asset2'
    release.assets = [asset1, asset2]
    return release


def create_components(latest_release=None):
    config = ReleaseConfig(owner='owner1', repo='repo1')
    repository = MagicMock(spec=Repository)
    if latest_release:
        repository.get_latest_release.return_value = latest_release
    else:
        repository.get_latest_release.side_effect = Exception('No release found')
    repository_provider = MagicMock(spec=IRepositoryProvider)
    repository_provider.get_repository.return_value = repository

    return config, repository_provider, repository


if __name__ == '__main__':
    unittest.main()
