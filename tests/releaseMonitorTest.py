import unittest
from unittest import TestCase, mock
from unittest.mock import MagicMock

from context_logger import setup_logging
from github.GitRelease import GitRelease
from package_downloader import IAssetDownloader, ReleaseConfig

from package_collector import ReleaseMonitor, ReleaseSource, IReusableTimer, ISourceRegistry, IReleaseSource


class ReleaseMonitorTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('debian-package-collector', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_starts_release_monitoring(self):
        # Given
        source_registry, asset_downloader, monitor_timer = create_components([])
        release_monitor = ReleaseMonitor(source_registry, asset_downloader, monitor_timer, 600)

        # When
        release_monitor.start()

        # Then
        monitor_timer.start.assert_called_once_with(600, release_monitor._check_all_periodic)

    def test_restarts_release_monitoring_when_timer_triggers(self):
        # Given
        source1 = create_source(is_new_release=False)
        source2 = create_source(is_new_release=True)
        source_registry, asset_downloader, monitor_timer = create_components([source1, source2])
        release_monitor = ReleaseMonitor(source_registry, asset_downloader, monitor_timer, 600)

        # When
        release_monitor._check_all_periodic()

        # Then
        monitor_timer.restart.assert_called_once()
        asset_downloader.download.assert_has_calls([
            mock.call(source2.config, source2.release)
        ])

    def test_stops_release_monitoring(self):
        # Given
        source_registry, asset_downloader, monitor_timer = create_components([])
        release_monitor = ReleaseMonitor(source_registry, asset_downloader, monitor_timer, 600)

        # When
        release_monitor.shutdown()

        # Then
        monitor_timer.cancel.assert_called_once()

    def test_downloads_all_release_assets_when_new_releases_found(self):
        # Given
        source1 = create_source(is_new_release=True)
        source2 = create_source(is_new_release=False)
        source3 = create_source(is_new_release=True)
        source_registry, asset_downloader, monitor_timer = create_components([source1, source2, source3])
        release_monitor = ReleaseMonitor(source_registry, asset_downloader, monitor_timer, 600)

        # When
        release_monitor.check_all()

        # Then
        asset_downloader.download.assert_has_calls([
            mock.call(source1.config, source1.release),
            mock.call(source3.config, source3.release)
        ])

    def test_downloads_release_asset_when_new_release_found(self):
        # Given
        source1 = create_source(is_new_release=False)
        source2 = create_source(is_new_release=True)
        source_registry, asset_downloader, monitor_timer = create_components([source1, source2], source2)
        release_monitor = ReleaseMonitor(source_registry, asset_downloader, monitor_timer, 600)

        # When
        release_monitor.check('owner1/repo1')

        # Then
        asset_downloader.download.assert_called_once_with(source2.config, source2.release)

    def test_skips_check_when_no_source_registered_for_package(self):
        # Given
        source1 = create_source(is_new_release=False)
        source2 = create_source(is_new_release=True)
        source_registry, asset_downloader, monitor_timer = create_components([source1, source2])
        release_monitor = ReleaseMonitor(source_registry, asset_downloader, monitor_timer, 600)

        # When
        release_monitor.check('owner1/repo1')

        # Then
        asset_downloader.download.assert_not_called()


def create_source(is_new_release=True):
    source = MagicMock(spec=ReleaseSource)
    source.config = MagicMock(spec=ReleaseConfig)
    source.release = MagicMock(spec=GitRelease)
    source.check_latest_release.return_value = is_new_release
    source.get_config.return_value = source.config
    source.get_release.return_value = source.release
    return source


def create_components(sources: list[IReleaseSource], source: IReleaseSource = None):
    source_registry = MagicMock(spec=ISourceRegistry)
    source_registry.get_all.return_value = sources
    source_registry.get.return_value = source
    asset_downloader = MagicMock(spec=IAssetDownloader)
    monitor_timer = MagicMock(spec=IReusableTimer)
    return source_registry, asset_downloader, monitor_timer


if __name__ == '__main__':
    unittest.main()
