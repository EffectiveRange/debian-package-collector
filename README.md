
[![Test and Release](https://github.com/EffectiveRange/debian-package-collector/actions/workflows/test_and_release.yml/badge.svg)](https://github.com/EffectiveRange/debian-package-collector/actions/workflows/test_and_release.yml)
[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/EffectiveRange/debian-package-collector/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/EffectiveRange/debian-package-collector/blob/python-coverage-comment-action-data/htmlcov/index.html)

# debian-package-collector

Debian package collector to download .deb packages from new releases

## Features

- [x] Downloads .deb packages from releases
- [x] Supports periodic monitoring of new releases
- [x] Supports webhooks to get notified of new releases

## Requirements

- [Python3](https://www.python.org/downloads/)
- [flask](https://flask.palletsprojects.com/en/3.0.x/)
- [waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/)

## Installation

### Install from source root directory

```bash
pip install .
```

### Install from source distribution

1. Create source distribution
    ```bash
    python setup.py sdist
    ```

2. Install from distribution file
    ```bash
    pip install dist/debian-package-collector-1.0.0.tar.gz
    ```

3. Install from GitHub repository
    ```bash
    pip install git+https://github.com/EffectiveRange/debian-package-collector.git@latest
    ```

## Usage

### Command line reference

```bash
$ bin/debian-package-collector.py --help
usage: debian-package-collector.py [-h] [-c CONFIG_FILE] [-f LOG_FILE] [-l LOG_LEVEL] [--initial-collect | --no-initial-collect] [--github-token GITHUB_TOKEN] [--download-dir DOWNLOAD_DIR] [--distro_sub_dirs DISTRO_SUB_DIRS] [--monitor-interval MONITOR_INTERVAL] [--monitor-enable | --no-monitor-enable]
                                   [--webhook-enable | --no-webhook-enable] [--webhook-secret WEBHOOK_SECRET] [--webhook-port WEBHOOK_PORT] [--webhook-delay WEBHOOK_DELAY]
                                   release_config

positional arguments:
  release_config        release config JSON file path or URL

options:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        configuration file (default: /etc/effective-range/debian-package-collector/debian-package-collector.conf)
  -f LOG_FILE, --log-file LOG_FILE
                        log file path (default: None)
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        logging level (default: None)
  --initial-collect, --no-initial-collect
                        enable initial collection (default: None)
  --github-token GITHUB_TOKEN
                        global token to use if not specified, supports env variables with $ (default: None)
  --download-dir DOWNLOAD_DIR
                        package download location (default: None)
  --distro_sub_dirs DISTRO_SUB_DIRS
                        distribution subdirectories (default: None)
  --monitor-interval MONITOR_INTERVAL
                        release monitor interval in seconds (default: None)
  --monitor-enable, --no-monitor-enable
                        enable periodic monitoring (default: None)
  --webhook-enable, --no-webhook-enable
                        enable the webhook server (default: None)
  --webhook-secret WEBHOOK_SECRET
                        secret to verify requests, supports env variables with $ (default: None)
  --webhook-port WEBHOOK_PORT
                        webhook server port to listen on (default: None)
  --webhook-delay WEBHOOK_DELAY
                        download delay in seconds after webhook request (default: None)
```

## Configuration

Default configuration (config/debian-package-collector.conf):

```ini
[logging]
log_level = info
log_file = /var/log/effective-range/debian-package-collector/debian-package-collector.log

[collector]
initial_collect = true
github_token = ${GITHUB_TOKEN}
download_dir = /opt/debs
distro_sub_dirs = bullseye, bookworm

[monitor]
monitor_enable = true
monitor_interval = 3600

[webhook]
webhook_enable = true
webhook_secret = ${WEBHOOK_SECRET}
webhook_port = 8080
webhook_delay = 600
```

### Example

```bash
$ bin/debian-package-collector.py ~/config/release-config.json
```

Example configuration (example `release-config.json` config file content):

```json
[
  {
    "owner": "EffectiveRange",
    "repo": "wifi-manager"
  },
  {
    "owner": "EffectiveRange",
    "repo": "pic18-q20-programmer"
  }
]
```

Output:

```bash
2025-03-15T16:23:31.787518Z [info     ] Using configuration file       [ConfigLoader] app_version=1.1.4 application=debian-package-collector config_file=/etc/effective-range/debian-package-collector/debian-package-collector.conf hostname=Legion7iPro
2025-03-15T16:23:31.788483Z [info     ] Started debian-package-collector [PackageCollectorApp] app_version=1.1.4 application=debian-package-collector arguments={'log_level': 'info', 'log_file': '/var/log/effective-range/debian-package-collector/debian-package-collector.log', 'initial_collect': 'true', 'github_token': '${GITHUB_TOKEN}', 'download_dir': '/tmp/packages', 'distro_sub_dirs': 'bullseye, bookworm', 'monitor_enable': 'true', 'monitor_interval': '3600', 'webhook_enable': 'true', 'webhook_secret': '${WEBHOOK_SECRET}', 'webhook_port': '8080', 'webhook_delay': '600', 'config_file': '/etc/effective-range/debian-package-collector/debian-package-collector.conf', 'release_config': 'build/release-config.json'} hostname=Legion7iPro
2025-03-15T16:23:31.811759Z [info     ] Local file path provided, skipping download [FileDownloader] app_version=1.1.4 application=debian-package-collector file=/home/attilagombos/EffectiveRange2/debian-package-collector/build/release-config.json hostname=Legion7iPro
2025-03-15T16:23:31.812479Z [info     ] Using global GitHub token for release source [SourceRegistry] app_version=1.1.4 application=debian-package-collector hostname=Legion7iPro repo=EffectiveRange/wifi-manager
2025-03-15T16:23:31.812878Z [info     ] Registered release source for repository [SourceRegistry] app_version=1.1.4 application=debian-package-collector config=ReleaseConfig(EffectiveRange/wifi-manager.git, matcher=*.deb, has_token=False) hostname=Legion7iPro repo=EffectiveRange/wifi-manager
2025-03-15T16:23:31.813326Z [info     ] Using global GitHub token for release source [SourceRegistry] app_version=1.1.4 application=debian-package-collector hostname=Legion7iPro repo=EffectiveRange/pic18-q20-programmer
2025-03-15T16:23:31.813654Z [info     ] Registered release source for repository [SourceRegistry] app_version=1.1.4 application=debian-package-collector config=ReleaseConfig(EffectiveRange/pic18-q20-programmer.git, matcher=*.deb, has_token=False) hostname=Legion7iPro repo=EffectiveRange/pic18-q20-programmer
2025-03-15T16:23:31.814030Z [info     ] Starting release monitor       [PackageCollector] app_version=1.1.4 application=debian-package-collector hostname=Legion7iPro
2025-03-15T16:23:31.814357Z [info     ] Starting monitoring            [ReleaseMonitor] app_version=1.1.4 application=debian-package-collector hostname=Legion7iPro
2025-03-15T16:23:31.814861Z [info     ] Starting webhook server        [PackageCollector] app_version=1.1.4 application=debian-package-collector hostname=Legion7iPro
2025-03-15T16:23:31.815223Z [info     ] Starting server                [WebhookServer] app_version=1.1.4 application=debian-package-collector hostname=Legion7iPro port=8080
2025-03-15T16:23:31.815755Z [info     ] Initial package collection     [PackageCollector] app_version=1.1.4 application=debian-package-collector hostname=Legion7iPro
2025-03-15T16:23:31.816496Z [info     ] Checking for new releases      [ReleaseMonitor] app_version=1.1.4 application=debian-package-collector hostname=Legion7iPro
2025-03-15T16:23:32.523592Z [info     ] Initial release                [ReleaseSource] app_version=1.1.4 application=debian-package-collector hostname=Legion7iPro repo=EffectiveRange/wifi-manager tag=v1.3.0
2025-03-15T16:23:32.931951Z [info     ] Found matching asset           [AssetDownloader] app_version=1.1.4 application=debian-package-collector asset=wifi-manager_1.3.0-1_all.deb hostname=Legion7iPro release=ReleaseConfig(EffectiveRange/wifi-manager.git, matcher=*.deb, has_token=False)
2025-03-15T16:23:32.933222Z [warning  ] No matching distro found in file name, using default [AssetDownloader] app_version=1.1.4 application=debian-package-collector asset=wifi-manager_1.3.0-1_all.deb distro=bullseye hostname=Legion7iPro
2025-03-15T16:23:32.934114Z [info     ] Downloading file               [FileDownloader] app_version=1.1.4 application=debian-package-collector file_name=wifi-manager_1.3.0-1_all.deb headers=['Accept'] hostname=Legion7iPro url=https://api.github.com/repos/EffectiveRange/wifi-manager/releases/assets/228471102
2025-03-15T16:23:34.729972Z [info     ] Downloaded file                [FileDownloader] app_version=1.1.4 application=debian-package-collector file=/tmp/packages/bullseye/wifi-manager_1.3.0-1_all.deb hostname=Legion7iPro
2025-03-15T16:23:35.463651Z [info     ] Initial release                [ReleaseSource] app_version=1.1.4 application=debian-package-collector hostname=Legion7iPro repo=EffectiveRange/pic18-q20-programmer tag=v0.3.1
2025-03-15T16:23:35.881742Z [info     ] Found matching asset           [AssetDownloader] app_version=1.1.4 application=debian-package-collector asset=picprogrammer_0.3.0-1_amd64.deb hostname=Legion7iPro release=ReleaseConfig(EffectiveRange/pic18-q20-programmer.git, matcher=*.deb, has_token=False)
2025-03-15T16:23:35.882322Z [warning  ] No matching distro found in file name, using default [AssetDownloader] app_version=1.1.4 application=debian-package-collector asset=picprogrammer_0.3.0-1_amd64.deb distro=bullseye hostname=Legion7iPro
2025-03-15T16:23:35.882675Z [info     ] Downloading file               [FileDownloader] app_version=1.1.4 application=debian-package-collector file_name=picprogrammer_0.3.0-1_amd64.deb headers=['Accept'] hostname=Legion7iPro url=https://api.github.com/repos/EffectiveRange/pic18-q20-programmer/releases/assets/208544277
2025-03-15T16:23:39.741440Z [info     ] Downloaded file                [FileDownloader] app_version=1.1.4 application=debian-package-collector file=/tmp/packages/bullseye/picprogrammer_0.3.0-1_amd64.deb hostname=Legion7iPro
2025-03-15T16:23:39.743407Z [info     ] Found matching asset           [AssetDownloader] app_version=1.1.4 application=debian-package-collector asset=picprogrammer_0.3.0-1_arm64.deb hostname=Legion7iPro release=ReleaseConfig(EffectiveRange/pic18-q20-programmer.git, matcher=*.deb, has_token=False)
2025-03-15T16:23:39.743980Z [warning  ] No matching distro found in file name, using default [AssetDownloader] app_version=1.1.4 application=debian-package-collector asset=picprogrammer_0.3.0-1_arm64.deb distro=bullseye hostname=Legion7iPro
2025-03-15T16:23:39.744370Z [info     ] Downloading file               [FileDownloader] app_version=1.1.4 application=debian-package-collector file_name=picprogrammer_0.3.0-1_arm64.deb headers=['Accept'] hostname=Legion7iPro url=https://api.github.com/repos/EffectiveRange/pic18-q20-programmer/releases/assets/208544395
2025-03-15T16:23:42.539513Z [info     ] Downloaded file                [FileDownloader] app_version=1.1.4 application=debian-package-collector file=/tmp/packages/bullseye/picprogrammer_0.3.0-1_arm64.deb hostname=Legion7iPro
2025-03-15T16:23:42.541539Z [info     ] Found matching asset           [AssetDownloader] app_version=1.1.4 application=debian-package-collector asset=picprogrammer_0.3.0-1_armhf.deb hostname=Legion7iPro release=ReleaseConfig(EffectiveRange/pic18-q20-programmer.git, matcher=*.deb, has_token=False)
2025-03-15T16:23:42.542852Z [warning  ] No matching distro found in file name, using default [AssetDownloader] app_version=1.1.4 application=debian-package-collector asset=picprogrammer_0.3.0-1_armhf.deb distro=bullseye hostname=Legion7iPro
2025-03-15T16:23:42.544005Z [info     ] Downloading file               [FileDownloader] app_version=1.1.4 application=debian-package-collector file_name=picprogrammer_0.3.0-1_armhf.deb headers=['Accept'] hostname=Legion7iPro url=https://api.github.com/repos/EffectiveRange/pic18-q20-programmer/releases/assets/208544421
2025-03-15T16:23:50.137828Z [info     ] Downloaded file                [FileDownloader] app_version=1.1.4 application=debian-package-collector file=/tmp/packages/bullseye/picprogrammer_0.3.0-1_armhf.deb hostname=Legion7iPro
```