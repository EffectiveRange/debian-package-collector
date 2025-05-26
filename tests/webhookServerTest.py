import hashlib
import hmac
import json
import os
import unittest
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging
from github.GitRelease import GitRelease
from package_downloader import ReleaseConfig, IAssetDownloader
from test_utility import wait_for_assertion

from package_collector import WebhookServer, IReleaseSource, ISourceRegistry, ReleaseSource, WebhookServerConfig


class WebhookServerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('debian-package-collector', 'DEBUG', warn_on_overwrite=False)
        os.environ['TEST_TOKEN'] = 'test_token'
        os.environ['TEST_SECRET'] = 'test_secret'

    def setUp(self):
        print()

    def test_startup_and_shutdown(self):
        # Given
        source_registry, asset_downloader, config = create_components()

        # When
        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            # Then
            self.assertTrue(webhook_server.is_running())
            self.assertTrue(webhook_server._thread.is_alive())

        self.assertFalse(webhook_server.is_running())

    def test_returns_403_when_no_signature(self):
        # Given
        source_registry, asset_downloader, config = create_components()

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()

            headers = {'Content-Type': 'application/json', 'X-GitHub-Event': 'release'}

            # When
            response = client.post('/webhook', json=release, headers=headers)

        # Then
        self.assertEqual(403, response.status_code)

    def test_returns_403_when_not_supported_algorithm(self):
        # Given
        source_registry, asset_downloader, config = create_components()

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': 'sha128=abcdef',
                'X-GitHub-Event': 'release',
            }

            # When
            response = client.post('/webhook', json=release, headers=headers)

        # Then
        self.assertEqual(403, response.status_code)

    def test_returns_403_when_invalid_signature(self):
        # Given
        source_registry, asset_downloader, config = create_components()

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('wrong_secret', release),
                'X-GitHub-Event': 'release',
            }

            # When
            response = client.post('/webhook', json=release, headers=headers)

        # Then
        self.assertEqual(403, response.status_code)

    def test_returns_204_when_not_release(self):
        # Given
        source_registry, asset_downloader, config = create_components()

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('secret', release),
                'X-GitHub-Event': 'push',
            }

            # When
            response = client.post('/webhook', json=release, headers=headers)

        # Then
        self.assertEqual(204, response.status_code)

    def test_returns_204_when_action_filtered_out(self):
        # Given
        source_registry, asset_downloader, config = create_components()

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()
            release['action'] = 'created'

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('secret', release),
                'X-GitHub-Event': 'release',
            }

            # When
            response = client.post('/webhook', json=release, headers=headers)

        # Then
        self.assertEqual(204, response.status_code)

    def test_returns_200_and_downloads_asset_when_release_published(self):
        # Given
        source = create_source()
        source_registry, asset_downloader, config = create_components(source)
        config.secret = '$TEST_SECRET'

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('test_secret', release),
                'X-GitHub-Event': 'release',
            }

            # When
            response = client.post('/webhook', json=release, headers=headers)

            # Then
            wait_for_assertion(1, asset_downloader.download.assert_called_once_with, source.config, source.release)

        self.assertEqual(200, response.status_code)

    def test_returns_200_and_downloads_asset_after_delay_when_no_assets_in_release(self):
        # Given
        source = create_source()
        source_registry, asset_downloader, config = create_components(source)
        config.secret = '$TEST_SECRET'

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()
            release['release']['assets'] = []

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('test_secret', release),
                'X-GitHub-Event': 'release',
            }

            # When
            response = client.post('/webhook', json=release, headers=headers)

            # Then
            wait_for_assertion(2, asset_downloader.download.assert_called_once_with, source.config, source.release)
            source.check_latest_release.assert_called_once()

        self.assertEqual(200, response.status_code)

    def test_returns_200_and_downloads_asset_after_delay_when_no_assets_and_second_request_arrives_with_no_assets(self):
        # Given
        source = create_source()
        source_registry, asset_downloader, config = create_components(source)
        config.secret = '$TEST_SECRET'

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()
            release['release']['assets'] = []

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('test_secret', release),
                'X-GitHub-Event': 'release',
            }

            client.post('/webhook', json=release, headers=headers)

            # When
            response = client.post('/webhook', json=release, headers=headers)

            # Then
            wait_for_assertion(2, asset_downloader.download.assert_called_once_with, source.config, source.release)
            source.check_latest_release.assert_called_once()

        self.assertEqual(200, response.status_code)

    def test_returns_200_and_downloads_asset_after_delay_when_no_assets_and_second_request_arrives_with_assets(self):
        # Given
        source = create_source()
        source_registry, asset_downloader, config = create_components(source)
        config.secret = '$TEST_SECRET'

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()
            release['release']['assets'] = []

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('test_secret', release),
                'X-GitHub-Event': 'release',
            }

            client.post('/webhook', json=release, headers=headers)

            release = create_release()

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('test_secret', release),
                'X-GitHub-Event': 'release',
            }

            # When
            response = client.post('/webhook', json=release, headers=headers)

            # Then
            wait_for_assertion(2, asset_downloader.download.assert_called_once_with, source.config, source.release)
            source.check_latest_release.assert_called_once()

        self.assertEqual(200, response.status_code)

    def test_returns_200_and_downloads_asset_after_retry(self):
        # Given
        source = create_source()
        source.check_latest_release.side_effect = [False, True]
        source_registry, asset_downloader, config = create_components(source)
        config.secret = '$TEST_SECRET'

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('test_secret', release),
                'X-GitHub-Event': 'release',
            }

            # When
            response = client.post('/webhook', json=release, headers=headers)

            # Then
            wait_for_assertion(3, asset_downloader.download.assert_called_once_with, source.config, source.release)
            source.check_latest_release.assert_called()

        self.assertEqual(200, response.status_code)

    def test_returns_200_and_stops_after_retries(self):
        # Given
        source = create_source()
        source.check_latest_release.return_value = False
        source_registry, asset_downloader, config = create_components(source)
        config.secret = '$TEST_SECRET'

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('test_secret', release),
                'X-GitHub-Event': 'release',
            }

            # When
            response = client.post('/webhook', json=release, headers=headers)

            # Then
            asset_downloader.download.assert_not_called()
            source.check_latest_release.assert_called()

        self.assertEqual(200, response.status_code)

    def test_returns_200_and_stops_after_retries_when_already_retrying(self):
        # Given
        source = create_source()
        source.check_latest_release.return_value = False
        source_registry, asset_downloader, config = create_components(source)
        config.secret = '$TEST_SECRET'

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('test_secret', release),
                'X-GitHub-Event': 'release',
            }

            client.post('/webhook', json=release, headers=headers)

            # When
            response = client.post('/webhook', json=release, headers=headers)

            # Then
            asset_downloader.download.assert_not_called()
            source.check_latest_release.assert_called()

        self.assertEqual(200, response.status_code)

    def test_returns_200_when_release_released(self):
        # Given
        source = create_source()
        source_registry, asset_downloader, config = create_components(source)
        config.secret = '$TEST_SECRET'

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()
            release['action'] = 'released'

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('test_secret', release),
                'X-GitHub-Event': 'release',
            }

            # When
            response = client.post('/webhook', json=release, headers=headers)

        # Then
        self.assertEqual(200, response.status_code)

    def test_returns_200_when_release_edited(self):
        # Given
        source = create_source()
        source_registry, asset_downloader, config = create_components(source)
        config.secret = '$TEST_SECRET'

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()
            release['action'] = 'edited'

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('test_secret', release),
                'X-GitHub-Event': 'release',
            }

            # When
            response = client.post('/webhook', json=release, headers=headers)

        # Then
        self.assertEqual(200, response.status_code)

    def test_returns_204_and_skips_download_when_repo_not_registered(self):
        # Given
        source_registry, asset_downloader, config = create_components()

        with WebhookServer(source_registry, asset_downloader, config) as webhook_server:
            webhook_server.start()

            client = webhook_server._app.test_client()
            release = create_release()

            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature-256': create_signature('secret', release),
                'X-GitHub-Event': 'release',
            }

            # When
            response = client.post('/webhook', json=release, headers=headers)

        # Then
        self.assertEqual(204, response.status_code)


def create_release() -> dict[str, Any]:
    return {
        'action': 'published',
        'release': {'tag_name': '1.0.0', 'assets': [{'name': 'file1.deb', 'url': 'https://example.com/file1.deb'}]},
        'repository': {'full_name': 'owner1/repo1'},
    }


def create_signature(secret: str, release: dict[str, Any]) -> str:
    mac = hmac.new(secret.encode(), msg=json.dumps(release, sort_keys=True).encode(), digestmod=hashlib.sha256)
    return f'sha256={mac.hexdigest()}'


def create_source(is_new_release=True):
    source = MagicMock(spec=ReleaseSource)
    source.config = ReleaseConfig(owner='owner1', repo='repo1', matcher='*.deb', token='$TEST_TOKEN')
    source.release = MagicMock(spec=GitRelease)
    source.check_latest_release.return_value = is_new_release
    source.get_config.return_value = source.config
    source.get_release.return_value = source.release
    return source


def create_components(source: IReleaseSource = None):
    source_registry = MagicMock(spec=ISourceRegistry)
    source_registry.get.return_value = source
    source_registry.is_registered.return_value = source is not None
    asset_downloader = MagicMock(spec=IAssetDownloader)
    server_config = WebhookServerConfig(0, 'secret', 2, 0.5)
    return source_registry, asset_downloader, server_config


if __name__ == '__main__':
    unittest.main()
