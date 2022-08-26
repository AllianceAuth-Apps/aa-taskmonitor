# Task Monitor

An Alliance Auth app for monitoring celery tasks.

[![release](https://img.shields.io/pypi/v/aa-analytics?label=release)](https://pypi.org/project/aa-analytics/)
[![python](https://img.shields.io/pypi/pyversions/aa-analytics)](https://pypi.org/project/aa-analytics/)
[![django](https://img.shields.io/pypi/djversions/aa-analytics?label=django)](https://pypi.org/project/aa-analytics/)
[![pipeline](https://gitlab.com/ErikKalkoken/aa-analytics/badges/master/pipeline.svg)](https://gitlab.com/ErikKalkoken/aa-analytics/-/pipelines)
[![codecov](https://codecov.io/gl/ErikKalkoken/aa-analytics/branch/master/graph/badge.svg?token=3tY1AOIp4B)](https://codecov.io/gl/ErikKalkoken/aa-analytics)
[![license](https://img.shields.io/badge/license-MIT-green)](https://gitlab.com/ErikKalkoken/aa-analytics/-/blob/master/LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![chat](https://img.shields.io/discord/790364535294132234)](https://discord.gg/zmh52wnfvM)

## Contents

- [Features](#features)
- [Installation](#installation)
- [User manual](#user-manual)
- [Settings](#settings)
- [FAQ](#faq)
- [Change Log](CHANGELOG.md)

## Features

Task Monitor gives administrators additional insights into the celery tasks that run on their system.

- Full log with details of all recently executed tasks including failed and retried tasks.
- Reports highlighting common aspects, e.g. Top most failed tasks
- Export task logs to CSV for further analysis with 3rd party tools (e.g. Google sheets)

Note that all information incl. the reports is available exclusively through the admin site.

## Installation

### Step 1 - Check prerequisites

Task Monitor is a plugin for Alliance Auth. If you don't have Alliance Auth running already, please install it first before proceeding. (see the official [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/auth/allianceauth/) for details)

### Step 2 - Install app

Make sure you are in the virtual environment (venv) of your Alliance Auth installation. Then install the newest release from PyPI:

```bash
pip install git+https://gitlab.com/ErikKalkoken/task-analytics.git
```

### Step 3 - Configure Auth settings

Configure your Auth settings (`local.py`) as follows:

- Add `'taskmonitor'` to `INSTALLED_APPS`
- Optional: Add additional settings if you want to change any defaults. See [Settings](#settings) for the full list.

### Step 4 - Finalize App installation

Run migrations & copy static files

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

Restart your supervisor services for Auth.

## Settings

Here is a list of available settings for this app. They can be configured by adding them to your AA settings file (`local.py`).

Note that all settings are optional and the app will use the documented default settings if they are not used.

Name | Description | Default
-- | -- | --
`TASKMONITOR_DATA_MAX_AGE`| Max age of logged tasks in hours. Older logs be deleted automatically. | `24`
`TASKMONITOR_HOUSEKEEPING_FREQUENCY`| Frequency of house keeping runs in minutes. | `15`
`TASKMONITOR_REPORTS_MAX_AGE`| Max age of cached reports in minutes. | `15`
`TASKMONITOR_REPORTS_MAX_TOP`| Max items to show in the top reports. e.g. 10 will shop the top ten items. | `15`

## FAQ

- Q: How is this app different from celery analytics?
- A: Celery Analytics appears to be mainly designed as data source for reports on Grafana. So you also need to install and setup Grafana to make use of it. Task Monitor on the other hand aims to be fully functional standalone, e.g. it provides reports and many useful features for analyzing the raw data directly on the admin site.

- Q: How is this app different from flower?
- A: Flower offers more detailed and technical information about task runs and might be therefore more suitable for developers. However, it not designed to store a larger number of task logs (default is 10K) and is therefore less suited to monitor tasks with Alliance Auth, where you typically have many 100K tasks per day.

- Q: Is it possible to store tasks longer then for 24 hours?
- A: Yes, there is a setting, which you can increase according to your needs. However, please keep in mind that your storage needs will increase accordingly. The current approx. usage is 0.5 KB per entry, so e.g. you need 200MB for 400.000 entries. At some point you also might run into performance issues, e.g. long page load times. Nevertheless, we want this app to work with very large data sets. So if you run into any issues, please let us know.
