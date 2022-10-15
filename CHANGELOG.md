# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - yyyy-mm-dd

### Added

### Changed

### Fixed

## [0.7.0] - TBD

### Added

- Store task params in task log
- Store task results in task log

### Changed

- Format technical fields in task log (e.g. traceback) as code

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
