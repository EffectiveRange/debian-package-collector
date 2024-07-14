import unittest
from threading import Thread
from unittest import TestCase, mock
from unittest.mock import MagicMock

from context_logger import setup_logging
from package_downloader import IJsonLoader, ReleaseConfig

from package_collector import PackageCollector, PackageCollectorConfig, ISourceRegistry, IReleaseMonitor, IWebhookServer
from tests import wait_for_assertion


class PackageCollectorTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('debian-package-collector', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_run_and_shutdown(self):
        # Given
        release_config1 = ReleaseConfig(owner='owner1', repo='repo1')
        release_config2 = ReleaseConfig(owner='owner2', repo='repo2')
        config, json_loader, source_registry, release_monitor, webhook_server = create_components(
            [release_config1, release_config2])

        # When
        with PackageCollector(config, json_loader, source_registry, release_monitor,
                              webhook_server) as package_collector:
            Thread(target=package_collector.run).start()

            # Then
            wait_for_assertion(1, release_monitor.check_all.assert_called_once)

            source_registry.register.assert_has_calls([
                mock.call(release_config1),
                mock.call(release_config2)
            ])

            release_monitor.start.assert_called_once()
            webhook_server.start.assert_called_once()

        release_monitor.shutdown.assert_called_once()
        webhook_server.shutdown.assert_called_once()

    def test_run_and_shutdown_when_no_webhook_server(self):
        # Given
        config, json_loader, source_registry, release_monitor, webhook_server = create_components(enable_webhook=False)

        # When
        with PackageCollector(config, json_loader, source_registry, release_monitor,
                              webhook_server) as package_collector:
            Thread(target=package_collector.run).start()

            # Then
            wait_for_assertion(1, release_monitor.check_all.assert_called_once)

            release_monitor.start.assert_called_once()
            webhook_server.start.assert_not_called()

        release_monitor.shutdown.assert_called_once()
        webhook_server.shutdown.assert_not_called()

    def test_run_and_shutdown_when_no_monitoring(self):
        # Given
        config, json_loader, source_registry, release_monitor, webhook_server = create_components(enable_monitor=False)

        # When
        with PackageCollector(config, json_loader, source_registry, release_monitor,
                              webhook_server) as package_collector:
            Thread(target=package_collector.run).start()

            # Then
            wait_for_assertion(1, release_monitor.check_all.assert_called_once)

            release_monitor.start.assert_not_called()
            webhook_server.start.assert_called_once()

        release_monitor.shutdown.assert_not_called()
        webhook_server.shutdown.assert_called_once()

    def test_run_and_shutdown_when_no_webhook_server_and_no_monitoring(self):
        # Given
        config, json_loader, source_registry, release_monitor, webhook_server = create_components(enable_webhook=False,
                                                                                                  enable_monitor=False)

        # When
        with PackageCollector(config, json_loader, source_registry, release_monitor,
                              webhook_server) as package_collector:
            package_collector.run()

            # Then
            wait_for_assertion(1, release_monitor.check_all.assert_called_once)

            release_monitor.start.assert_not_called()
            webhook_server.start.assert_not_called()

        release_monitor.shutdown.assert_not_called()
        webhook_server.shutdown.assert_not_called()


def create_components(config_list=None, enable_monitor: bool = True, enable_webhook: bool = True):
    if config_list is None:
        config_list = []
    config = PackageCollectorConfig('', enable_monitor, enable_webhook)
    json_loader = MagicMock(spec=IJsonLoader)
    json_loader.load_list.return_value = config_list
    source_registry = MagicMock(spec=ISourceRegistry)
    release_monitor = MagicMock(spec=IReleaseMonitor)
    webhook_server = MagicMock(spec=IWebhookServer)

    return config, json_loader, source_registry, release_monitor, webhook_server


if __name__ == '__main__':
    unittest.main()
