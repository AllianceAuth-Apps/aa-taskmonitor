# Task Monitor

An Alliance Auth app for monitoring celery tasks.

[![release](https://img.shields.io/pypi/v/aa-taskmonitor?label=release)](https://pypi.org/project/aa-taskmonitor/)
[![python](https://img.shields.io/pypi/pyversions/aa-taskmonitor)](https://pypi.org/project/aa-taskmonitor/)
[![django](https://img.shields.io/pypi/djversions/aa-taskmonitor?label=django)](https://pypi.org/project/aa-taskmonitor/)
[![pipeline](https://gitlab.com/ErikKalkoken/aa-taskmonitor/badges/master/pipeline.svg)](https://gitlab.com/ErikKalkoken/aa-taskmonitor/-/pipelines)
[![codecov](https://codecov.io/gl/ErikKalkoken/aa-taskmonitor/branch/master/graph/badge.svg?token=MNEUWD6X4Q)](https://codecov.io/gl/ErikKalkoken/aa-taskmonitor)
[![license](https://img.shields.io/badge/license-MIT-green)](https://gitlab.com/ErikKalkoken/aa-taskmonitor/-/blob/master/LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![chat](https://img.shields.io/discord/790364535294132234)](https://discord.gg/zmh52wnfvM)

## Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [User manual](#user-manual)
- [Settings](#settings)
- [FAQ](#faq)
- [Change Log](CHANGELOG.md)

## Features

Task Monitor enables administrators to monitor celery tasks running on their system.

- Stores full log with details of all recently executed celery tasks including failed and retried tasks.
- Keeps the storage needs in check by automatically deleting older task logs

- Admins can investigate task log with search & filters
- Admins can view details for each task incl. exceptions and trace logs
- Admins can review reports providing answers to common questions, e.g:
  - How many tasks have failed/retried?
  - How many tasks where run by each of my apps?
  - Which are the most frequent tasks?
  - Which tasks have the longest runtime?
  - Which tasks failed the most?
- Admins can export all task logs to a CSV file for further analysis with 3rd party tools (e.g. Google sheets)

## Screenshots

### Full log of all recently executed tasks

![tasklog](https://i.imgur.com/jo1McnJ.png)

### View details for each task incl. exception tracelogs

![tasklog](https://i.imgur.com/3XMc8Zi.png)

### The start of the reports page

![tasklog](https://i.imgur.com/hSX5Qsb.png)

## Installation

### Step 1 - Check prerequisites

Task Monitor is a plugin for Alliance Auth. If you don't have Alliance Auth running already, please install it first before proceeding. (see the official [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/auth/allianceauth/) for details)

### Step 2 - Install app

Make sure you are in the virtual environment (venv) of your Alliance Auth installation. Then install the newest release from PyPI:

```bash
pip install aa-taskmonitor
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

### Is it possible to store task logs longer then for just 24 hours?

Yes, there is a setting, which you can increase according to your needs. However, please keep in mind that your storage needs will increase accordingly. The current approx. usage is 0.5 KB per entry, so e.g. you need approx. 500 MB to store 1.000.000 task logs.

### How is this app different from celery analytics?

Celery Analytics seams to be designed mainly as data source for reports on Grafana. It apparently works great if you want to integrate analysis about your task executions into a Grafana dashboards. But it's usability without Grafana is limited.

Task Monitor on the other hand aims to be fully functional standalone by providing reports and many useful features for analyzing your task logs directly on the admin site. It also provides a more complete picture, since Celery Analytics ignores retried tasks.

## How is this app different from celery's flower?

Flower offers more detailed and technical information about task runs and might  therefore be more most for developers. However, it not designed to store a larger number of task logs (default is only 10K) and is appears therefore to be less suited for Alliance Auth, where you typically have 100K+ tasks per day.
