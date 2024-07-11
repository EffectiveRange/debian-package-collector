import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging
from package_downloader import ReleaseConfig, IRepositoryProvider

from package_collector import SourceRegistry


class SourceRegistryTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('debian-package-collector', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()
        self.repository_provider = MagicMock(spec=IRepositoryProvider)
        self.source_registry = SourceRegistry(self.repository_provider)

    def test_returns_source_when_registered(self):
        # Given
        repository_provider = MagicMock(spec=IRepositoryProvider)
        source_registry = SourceRegistry(repository_provider)
        config = ReleaseConfig(owner='owner1', repo='repo1')

        # When
        result = source_registry.register(config)

        # Then
        self.assertEqual(source_registry._release_sources.get('owner1/repo1'), result)

    def test_returns_source_when_registered_again(self):
        # Given
        repository_provider = MagicMock(spec=IRepositoryProvider)
        source_registry = SourceRegistry(repository_provider)
        config = ReleaseConfig(owner='owner1', repo='repo1')

        source = source_registry.register(config)

        # When
        result = source_registry.register(config)

        # Then
        self.assertEqual(source, result)

    def test_returns_true_when_source_is_registered(self):
        # Given
        repository_provider = MagicMock(spec=IRepositoryProvider)
        source_registry = SourceRegistry(repository_provider)
        config = ReleaseConfig(owner='owner1', repo='repo1')

        source_registry.register(config)

        # When
        result = source_registry.is_registered('owner1/repo1')

        self.assertTrue(result)

    def test_returns_false_when_source_is_not_registered(self):
        # Given
        repository_provider = MagicMock(spec=IRepositoryProvider)
        source_registry = SourceRegistry(repository_provider)

        # When
        result = source_registry.is_registered('owner1/repo1')

        self.assertFalse(result)

    def test_returns_source_when_source_is_registered(self):
        # Given
        repository_provider = MagicMock(spec=IRepositoryProvider)
        source_registry = SourceRegistry(repository_provider)
        config = ReleaseConfig(owner='owner1', repo='repo1')

        source = source_registry.register(config)

        # When
        result = source_registry.get('owner1/repo1')

        # Then
        self.assertEqual(source, result)

    def test_raises_error_when_source_is_registered(self):
        # Given
        repository_provider = MagicMock(spec=IRepositoryProvider)
        source_registry = SourceRegistry(repository_provider)

        # When
        self.assertRaises(KeyError, source_registry.get, 'owner1/repo1')

        # Then
        # Exception is raised

    def test_returns_all_sources(self):
        # Given
        repository_provider = MagicMock(spec=IRepositoryProvider)
        source_registry = SourceRegistry(repository_provider)

        config1 = ReleaseConfig(owner='owner4', repo='repo4')
        config2 = ReleaseConfig(owner='owner5', repo='repo5')
        source1 = source_registry.register(config1)
        source2 = source_registry.register(config2)

        # When
        result = source_registry.get_all()

        # Then
        self.assertEqual(2, len(result))
        self.assertIn(source1, result)
        self.assertIn(source2, result)


if __name__ == '__main__':
    unittest.main()
