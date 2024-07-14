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

```commandline
$ bin/debian-package-collector.py --help
usage: debian-package-collector.py [-h] [-f LOG_FILE] [-l LOG_LEVEL] [-d DOWNLOAD] [-i INTERVAL] [-p PORT] [-s SECRET] [--monitor | --no-monitor] [--webhook | --no-webhook] release_config

positional arguments:
  release_config        release config JSON file path or URL

options:
  -h, --help            show this help message and exit
  -f LOG_FILE, --log-file LOG_FILE
                        log file path (default: None)
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        logging level (default: info)
  -d DOWNLOAD, --download DOWNLOAD
                        package download location (default: /tmp/packages)
  -i INTERVAL, --interval INTERVAL
                        release monitor interval in seconds (default: 600)
  -p PORT, --port PORT  webhook server port to listen on (default: 8080)
  -s SECRET, --secret SECRET
                        webhook secret to verify requests (supports environment variable reference with $) (default: None)
  --monitor, --no-monitor
                        enable periodic monitoring (default: True)
  --webhook, --no-webhook
                        enable the webhook server (default: True)
```

### Example

```commandline
$ bin/debian-package-collector.py ~/config/release-config.json
```

Example configuration (example `release-config.json` config file content):

```json
[
  {
    "owner": "EffectiveRange",
    "repo": "wifi-manager",
    "matcher": "*.deb"
  },
  {
    "owner": "EffectiveRange",
    "repo": "pic18-q20-programmer",
    "matcher": "*.deb"
  }
]
```

Output:

```commandline
2024-07-14T20:57:42.670018Z [info     ] Starting package collector     [PackageCollectorApp] app_version=0.1.0 application=debian-package-collector arguments={'log_file': None, 'log_level': 'info', 'download': '/tmp/packages', 'interval': 600, 'port': 8080, 'secret': None, 'monitor': True, 'webhook': True, 'release_config': 'build/release-config.json'} hostname=Legion7iPro
2024-07-14T20:57:42.673127Z [info     ] Local file path provided, skipping download [FileDownloader] app_version=0.1.0 application=debian-package-collector file=/home/attilagombos/EffectiveRange/debian-package-collector/build/release-config.json hostname=Legion7iPro
2024-07-14T20:57:42.949293Z [info     ] Registered release source for repository [SourceRegistry] app_version=0.1.0 application=debian-package-collector config=ReleaseConfig(EffectiveRange/wifi-manager.git, matcher=*.deb, has_token=False) hostname=Legion7iPro repo=EffectiveRange/wifi-manager
2024-07-14T20:57:43.219239Z [info     ] Registered release source for repository [SourceRegistry] app_version=0.1.0 application=debian-package-collector config=ReleaseConfig(EffectiveRange/pic18-q20-programmer.git, matcher=*.deb, has_token=False) hostname=Legion7iPro repo=EffectiveRange/pic18-q20-programmer
2024-07-14T20:57:43.220211Z [info     ] Starting release monitor       [PackageCollector] app_version=0.1.0 application=debian-package-collector hostname=Legion7iPro
2024-07-14T20:57:43.220814Z [info     ] Starting monitoring            [ReleaseMonitor] app_version=0.1.0 application=debian-package-collector hostname=Legion7iPro
2024-07-14T20:57:43.221804Z [info     ] Starting webhook server        [PackageCollector] app_version=0.1.0 application=debian-package-collector hostname=Legion7iPro
2024-07-14T20:57:43.222532Z [info     ] Starting server                [WebhookServer] app_version=0.1.0 application=debian-package-collector hostname=Legion7iPro port=8080
2024-07-14T20:57:43.223339Z [info     ] Collecting initial packages    [PackageCollector] app_version=0.1.0 application=debian-package-collector hostname=Legion7iPro
2024-07-14T20:57:43.223805Z [info     ] Checking for new releases      [ReleaseMonitor] app_version=0.1.0 application=debian-package-collector hostname=Legion7iPro
2024-07-14T20:57:43.394138Z [info     ] New release found              [ReleaseSource] app_version=0.1.0 application=debian-package-collector hostname=Legion7iPro new_tag=v1.0.5 old_tag=None
2024-07-14T20:57:43.816178Z [info     ] Found matching asset           [AssetDownloader] app_version=0.1.0 application=debian-package-collector asset=wifi-manager_1.0.5_armhf.deb hostname=Legion7iPro release=ReleaseConfig(EffectiveRange/wifi-manager.git, matcher=*.deb, has_token=False)
2024-07-14T20:57:43.816518Z [info     ] Downloading file               [FileDownloader] app_version=0.1.0 application=debian-package-collector file_name=wifi-manager_1.0.5_armhf.deb headers=['Accept'] hostname=Legion7iPro url=https://api.github.com/repos/EffectiveRange/wifi-manager/releases/assets/175922822
2024-07-14T20:57:45.153095Z [info     ] Downloaded file                [FileDownloader] app_version=0.1.0 application=debian-package-collector file=/tmp/packages/wifi-manager_1.0.5_armhf.deb hostname=Legion7iPro
2024-07-14T20:57:45.321709Z [info     ] New release found              [ReleaseSource] app_version=0.1.0 application=debian-package-collector hostname=Legion7iPro new_tag=v0.3.0 old_tag=None
2024-07-14T20:57:45.723707Z [info     ] Found matching asset           [AssetDownloader] app_version=0.1.0 application=debian-package-collector asset=picprogrammer_0.3.0-1_amd64.deb hostname=Legion7iPro release=ReleaseConfig(EffectiveRange/pic18-q20-programmer.git, matcher=*.deb, has_token=False)
2024-07-14T20:57:45.724065Z [info     ] Downloading file               [FileDownloader] app_version=0.1.0 application=debian-package-collector file_name=picprogrammer_0.3.0-1_amd64.deb headers=['Accept'] hostname=Legion7iPro url=https://api.github.com/repos/EffectiveRange/pic18-q20-programmer/releases/assets/175069476
2024-07-14T20:57:46.893011Z [info     ] Downloaded file                [FileDownloader] app_version=0.1.0 application=debian-package-collector file=/tmp/packages/picprogrammer_0.3.0-1_amd64.deb hostname=Legion7iPro
2024-07-14T20:57:46.893530Z [info     ] Found matching asset           [AssetDownloader] app_version=0.1.0 application=debian-package-collector asset=picprogrammer_0.3.0-1_armhf.deb hostname=Legion7iPro release=ReleaseConfig(EffectiveRange/pic18-q20-programmer.git, matcher=*.deb, has_token=False)
2024-07-14T20:57:46.893794Z [info     ] Downloading file               [FileDownloader] app_version=0.1.0 application=debian-package-collector file_name=picprogrammer_0.3.0-1_armhf.deb headers=['Accept'] hostname=Legion7iPro url=https://api.github.com/repos/EffectiveRange/pic18-q20-programmer/releases/assets/175069584
2024-07-14T20:57:47.964054Z [info     ] Downloaded file                [FileDownloader] app_version=0.1.0 application=debian-package-collector file=/tmp/packages/picprogrammer_0.3.0-1_armhf.deb hostname=Legion7iPro
```