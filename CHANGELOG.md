# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## Unreleased

### Added

- added filter `color` to MQTT templates to the color can be changed within a string
- added `is_payload` macro so comparisons can be done quickly within templates, similar to using `{{ get_payload() == 'val' }}`
- some README badges to show information, including GitHub Actions pipeline status

### Changed

- time now displays in log instead of just the name of the item variable
- dependency parsing now uses regex grouping to make things easier

### Fixed

- removed some debug `print` statements that were left behind

## Version 2.1

### Added

- added some additional Jinja macros and filters

### Changed

- file labels for Strings are now lowercase letters instead of numbers. This is due to the fact that double digit numbers are not supported as file labels

## Version 2.0

### Added

- added a test utility class to send simple messages to the LED display for testing
- mqtt variables can use the `update_template` key to define a template used to evaluate if the display should be updated. MQTT is often chatty and this can cut down on unneeded updates
- `layout.yaml` file is parsed on startup for common errors, program is halted if the schema cannot validate
- added global Jinja method `get_payload()` for use in evaluating MQTT Variables. Can get the payload from any defined MQTT variable type
- MQTT messages are re-rendered whenever a variable referenced in them changes
- multiple message queues can be defined and selected by defining `active_template` conditions.
- published MQTT attributes include the current active queue (`active_queue`)

### Changed

- variables can be defined and referenced without having to be part of a given message. Useful for calling variables from within other templates.
- `layout.yaml` file now uses `display` instead of `messages` and multiple message queues can be defined. `main` is required as the default

## Version 1.0

### Added

- defaults can be set in Variable subclasses and passed up be included in the config object
- added project version to startup output

### Changed

- changed some function names to conform to PEP8 standards
- import entire constants file to `main.py` instead of every constant needed
- in `MessageManager` startup using arrays and `join` method instead of one large string with spaces
- the MQTT variable type now uses `template` instead of `text` as the YAML key to maintain consistency across variables

### Fixed

- removed @staticmethod designator from `get_category`, this was a cut/paste mistake

### Removed

- removed local `alphasign` project files, pull in as a dependency instead

## Beta

### Added

- added ability to parse MQTT payload values as JSON via `parse_json` directive
- added TOC to README

### Changed

- Home Assistant variable moved from global to within function where needed
- renamed `getVariables` to `getVariablesByFilter` to better describe what this is doing
- filter polling type variables using `getVariableByFilter` instead of filtering after getting the full list

### Fixed

- fixed issue with multiple threads accessing serial port via `connect()`
- `getVariables` filter function didn't pass argument, always returned True. Fixed now.
- TemplateSyntaxErrors now trigger on incorrect HTTP response code rather than looking for JSON in the result
- minor variable formatting issues (spacing, storage, etc)

## Alpha

## Added

- added time, date, and home_assistant variable types that post messages to the sign
- abstracted sign communications to a `yaml` file that loads message information on startup
- additional CLI argument can load actual sign communications or output to CLI for testing
- ability to render Home Assistant templates directly in HA, throws Template error if incorrect
- keep track of already allocated messages instead of re-sending them
- added fonts for variables and messages
- integrated MQTT for sign on/off events
- added Home Assistant MQTT Light yaml file to integrate with HA as a light
- added MQTT variable types
