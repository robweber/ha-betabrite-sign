# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## Version 3.0

### Added

- new variable type `dynamic`. This is a template based type used to combine other variable types into a dynamic message
- added Jinja template method `is_time()` to compare time strings in a quick way

### Changed

- refactored `render_mqtt()` to `render_template()` in `main.py`. This better reflects that this is for rendering any Jinja variable type
- JinjaVariable types only update on the sign if the rendered template has actually changed, avoids pushing to sign unless needed

## Version 2.8

### Added

- added `color_mode` and `supported_color_modes` attributes to MQTT Light registration for Home Assistant. This fulfills the new [light entity requirements](https://developers.home-assistant.io/docs/core/entity/light#color-modes).

## Version 2.7

### Added

- added instructions for running this under a virtual environment

### Changed

- updated service instructions for virtual environment
- moved files to `src/` directory

### Fixed

- `requirements-dev.txt` now also pulls in base requirements
- fixed __alphasign__ requirement url format in `requirements.txt`

## Version 2.6

### Changed

- Autodiscovery via MQTT for Home Assistant now includes the `device` attribute. This allows all entities to be categorized within a single HA device

## Version 2.5

### Added

- Added a Jinja variable type as this could more than just MQTT classes
- Added REST variable type to pull in data directly via an HTTP request
- added __device_ip__ as an attribute to easily find DHCP address in Home Assistant

### Changed

- changed `get_variables_by_filter` to filter on either a single or multiple categories
- VariableTypes can now be a part of more than one category
- MQTT now inherits from the Jinja variable type as well
- don't strip out periods (.), the sign can show these
- restructured default configuration handling so it works with multiple class inheritance

## Version 2.4

### Added

- added support for an [Home Assistant Text entity](https://www.home-assistant.io/integrations/text/) via MQTT Discovery. This exposes a variable to Home Assistant that can be updated to push text to the display. Requires HA 2022.12 or later.

### Fixed

- fixed some documentation regarding the use of the `color` filter
- fixed [Github build status badge](https://github.com/badges/shields/issues/8671)

## Version 2.3

### Added

- Added [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) with Home Assistant - will automatically create a light entity

### Changed

- flake8 tests ignore [E275 errors](https://www.flake8rules.com/rules/E275.html)

### Removed

- removed Home Assistant light template example yaml - this can now be done with MQTT Discovery

## Version 2.2

### Added

- added filter `color` to MQTT templates so the color can be changed within a string, optionally the color can be set based on a condition with a fallback color
- added `is_payload` function so comparisons can be done quickly within templates, similar to using `{{ get_payload() == 'val' }}`
- syntatic helper functions `get_payload_attr` and `is_payload_attr` to quickly get and compare attributes within JSON payloads
- some README badges to show information, including GitHub Actions pipeline status

### Changed

- time now displays in log instead of just the name of the item variable
- dependency parsing now uses regex grouping to make things easier

### Fixed

- removed some debug `print` statements that were left behind
- fixed daylight savings time issues with Time by setting it explicitly from the system time
- catch any exception thrown from Home Assistant template checking - typically this happens when HA is down

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
