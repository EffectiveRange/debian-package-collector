# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/EffectiveRange/debian-package-collector/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                   |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|--------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| package\_collector/\_\_init\_\_.py     |        5 |        0 |        0 |        0 |    100% |           |
| package\_collector/packageCollector.py |       44 |        0 |       14 |        0 |    100% |           |
| package\_collector/releaseMonitor.py   |       39 |        0 |        8 |        1 |     98% |  72->exit |
| package\_collector/releaseSource.py    |       43 |        0 |       10 |        3 |     94% |41->exit, 45->exit, 47->58 |
| package\_collector/sourceRegistry.py   |       38 |        0 |        6 |        0 |    100% |           |
| package\_collector/webhookServer.py    |      125 |        3 |       34 |        5 |     95% |89-91, 101->100, 124->exit, 180->183, 186->exit, 189->exit |
|                              **TOTAL** |  **294** |    **3** |   **72** |    **9** | **97%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/EffectiveRange/debian-package-collector/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/EffectiveRange/debian-package-collector/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/EffectiveRange/debian-package-collector/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/EffectiveRange/debian-package-collector/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FEffectiveRange%2Fdebian-package-collector%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/EffectiveRange/debian-package-collector/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.