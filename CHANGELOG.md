# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - yyyy-mm-dd

## [0.23.0] - TBD

### Added

- Task name can be custom and contain a different name for the "app" then the regular package name (e.g. see standings_requests vs. standingsrequests). To fix this we are adding an optional mapping feature for app names. This can be configured with the new setting `TASKMONITOR_APP_NAME_MAPPING_CONFIG`

## [0.22.0] - 2023-12-09

### Added

- Ability to search on task statistic page

## [0.21.0] - 2023-12-04

### Added

- See detailed statistics for all tasks

### Changed

- Improved test suite

## [0.20.0] - 2023-11-27

### Added

- Add support for AA4

## [0.19.1] - 2023-10-10

### Fixed

- Bug in new app failures report

## [0.19.0] - 2023-10-10

### Added

- New report: App failures over time
- Show button on reports page to navigate to logs
- Show when reports where last updated on reports page

### Changed

- Reduced frequency of house keeping and updating reports by half

## [0.18.0] - 2023-09-19

### Added

- Report showing exceptions over time

## [0.17.1] - 2023-09-04

### Changed

- Add mandatory pylint checks
- Will only delete one batch of stale task at a time to improve probability of stale tasks being deleted under high load
- Refactor to fix pylint issues

## [0.17.0] - 2023-07-04

### Update notes

We strongly recommend to run the migrations while AA is stopped in order to avoid any conflicts with potentially running tasks. Note that migrations can take a while to complete.

### Added

- New filter for exceptions
- Global setting to disable task monitor, e.g. when running local tests

### Changed

- Migrated build process to PEP 621
- Migrated to AA 3 and dropped support for AA 2
- Add support for Python 3.11
- Show exception class name instead of exception string in "exception" field

## [0.16.0] - 2023-03-25

### Added

- New report: Top tasks by total runtime
- New report: Top apps by total task runtime
- New report: Top apps by by total task runs

### Changed

- Reorganization of report list to accommodate new reports

### Fixed

- Breaks when creating TaskLog and args or kwargs is None

## [0.15.2] - 2023-03-25

### Fixed

- TypeError in task failure handler caused by missing delivery info
- Solo args not shown in params column of task logs list

## [0.15.1] - 2023-03-24

### Changed

- Reenabled "Reports" button on tasklogs admin page
- Timestamps now shown with more precision

### Fixed

- Links in reports charts are broken

## [0.15.0] - 2023-03-18

### Added

- cli tool: Can purge selected tasks from queue, by task name, task id or app name
- cli tool: "inspect queue" now also shows grouped task counts in addition to the grouped app counts
- cli too: Can now also purge task logs

### Changed

- Improved page load times for reports page

### Fixed

- Breaks on undefined args/kwargs for internal errors
- Report counts might have been slightly off

## [0.14.0] - 2023-03-14

### Added

- CLI utility to manage task log and queue

### Changed

- Added upper limit for amount of queued tasks to protect against crashed caused by too high memory consumption when trying to render 100K+ tasks. Can be configured with new setting: `TASKMONITOR_QUEUED_TASKS_ADMIN_LIMIT`
- Changed default for updating reports to 30 min

## [0.13.0] - 2023-02-22

### Added

- New chart for analyzing task impact

### Changed

- Reports are now accessible through the admin site menu only

## [0.12.0] - 2023-02-22

### Added

- New report for queue length over time
- New report for top tasks by average runtime
- Direct links to report charts

### Changed

- Faster loading of reports page with all report data now fetched async
- Faster loading of task log admin page with new index
- Selected report chart remain selected after page reload

### Fixed

- Deleting large amount of stale tasklogs fails due to transaction timeout

## [0.11.1] - 2023-02-06

### Fixed

- State filter broken for task logs

## [0.11.0] - 2023-02-03

### Added

- Show counts of apps and tasks for task log
- Add priority filter to task log

## [0.10.0] - 2023-02-02

### Added

- Show counts of apps and tasks for queued tasks

### Changed

- Reduced default cache timeout for queued tasks to 10 seconds

## [0.9.1] - 2023-02-01

### Changed

- Added caching for queued tasks to further improve performance

## [0.9.0] - 2023-01-31

### Added

- Ability to clear the task queue from the admin site

### Changed

- Significantly improved performance of the "Queued Tasks" page

## [0.8.1] - 2022-11-04

### Fixed

- TypeError('Object of type Response is not JSON serializable') (#4)

## [0.8.0] - 2022-10-18

### Added

- Ability to copy a task log to the clipboard for easy sharing

## [0.7.0] - 2022-10-16

### Added

- Store task params in task log
- Store task results in task log
- Truncate stored task params & results to safe space (can be turned off)

### Changed

- Show technical data in task log (e.g. traceback) as code

## [0.6.0] - 2022-10-02

### Added

- New Charts Task throughput over time by state
- New Charts Task throughput over time by app

## [0.5.1] - 2022-09-30

### Fixed

- Values in throughput report not showing

## [0.5.0] - 2022-09-29

### Added

- Reports are now shown as charts (when applicable)
- Has automatic dark/light mode for charts

## [0.4.1] - 2022-09-28

### Changed

- Show one report at a time and provide navigation sidebar to select report
- Reworked reports layout and style to fit better with admin site

## [0.4.0] - 2022-09-27

### Added

- Ability to see list of currently queued tasks
- Average task throughput for different time spans

### Changed

- Clicking "Recalc now" now start the tasks instead of clearing the cache

## [0.3.0] - 2022-09-25

### Added

- Show maximum and average task throughput in report

## [0.2.1] - 2022-09-12

### Fixed

- ZeroDivisionError when showing reports with no data (#3)

## [0.2.0] - 2022-09-06

### Added

- Reports can not be opened directly from the admin site main list

## [0.1.1] - 2022-09-04

### Fixed

- Error 500 when filtering for failed tasks (#1)

## [0.1.0] - 2022-09-04

### Changed

- Layout improvements

## [0.1.0a4] - 2022-09-01

### Added

- Report for top retried tasks

## [0.1.0a3] - 2022-08-29

### Fixed

- Logging of task with internal errors does not work

## [0.1.0a2] - 2022-08-27

### Added

- Initial release
