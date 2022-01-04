# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## Beta

### Added

- added ability to parse MQTT payload values as JSON via `parse_json` directive

### Changed

- Home Assistant variable moved from global to within function where needed
- renamed `getVariables` to `getVariablesByFilter` to better describe what this is doing

### Fixed

- fixed issue with multiple threads accessing serial port via `connect()`
- `getVariables` filter function didn't pass argument, always returned True. Fixed now.
- TemplateSyntaxErrors now trigger on incorrect HTTP response code rather than looking for JSON in the result

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
