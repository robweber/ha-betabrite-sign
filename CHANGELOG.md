# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

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
