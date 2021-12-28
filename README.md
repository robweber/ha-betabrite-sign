# Home Assistant Betabrite Sign
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg)](https://github.com/RichardLitt/standard-readme)

Integrate an LED sign that uses the [Alphasign protocol](https://www.adaptivedisplays.com/resources/documentation-and-manuals/support-documents/bid/264113/Alpha-Sign-Communications-Protocol-pn-97088061) with your [Home Assistant](https://www.home-assistant.io/) installation. This project seeks to provide a headless Python program that will communicate with the sign and allow for updates by either querying a Home Assistant instance or getting status updates via MQTT from Home Assistant.

Messages are configured for the display using a simple `.yaml` configuration file. These can be customized by using [Jinja templating](https://palletsprojects.com/p/jinja/) to provide more advanced "on the fly" formatting. Furthermore, variables can be defined that pull information from Home Assistant. These will dynamically update the sign on either a polling timer or via MQTT topics.

## Background

A long, long time ago, in an apartment far away; my college roommate and I wanted a cool LED sign to display information. I purchased a cheap [Betabrite LED display](https://www.alpha-american.com/p-betabrite.html) and a serial cable. My first crude attempts at this (circa 2006) used Java and some serial commands to write messages to the display. Over time this setup evolved to using a Raspberry Pi and [WebIOPI](http://webiopi.trouch.com/) to update the display. When I started using Home Assistant I hacked and slashed my way to integrating that with the existing setup as well.

After some time with Home Assistant I realized there had to be a better way. Projects like [ESPHome](https://esphome.io/) showed me there were better integration methods. I didn't want to write an entire custom integration for Home Assistant; but yet my existing setup was way too cumbersome and relied on a lot of code rewrites every time I wanted to add something.

What I wanted was a system that I could define with a `.yaml` file and have it dynamically generate the information needed to write messages to the LED sign. Furthermore I wanted to point to Home Assistant entities that could be polled, or MQTT topics that could be monitored, to update messaging within the sign. This project is the end result. I tried as much as possible to utilize existing Home Assistant methodologies, like Jinja templating, so that setup and configuration were somewhat intuitive.

## Install

The install procedure assumes you have a working version of the Rasperry Pi OS already installed on an Rpi or Rpi Zero. Obviously you also need an LED sign that utilizes the Alphasign Protocol and a way for the RPI to talk to it. If you notice that the time is incorrect on the sign use `raspi-config` to set the correct localization information.

```
# install os deps
sudo apt-get install git python3-pip

# clone the repo
git clone https://github.com/robweber/ha-betabrite-sign.git

# install python requirements
sudo pip3 install -r install/requirements.txt

```

## Usage

Once installed copy the existing `data/layout.yaml.example` file to `data/layout.yaml`. This file is read on startup to configure the messages sent to the display. There are two main sections to the file __variables__ and __messages__. The variables section defines strings that will be updated dynamically on the sign. The messages area defines the format of how the text will be displayed on the sign, this includes things like the display mode and color. Additionally you'll need the url to your Home Assistant instance, and a [long lived access token](https://www.home-assistant.io/docs/authentication/).

You can run the program with the following command:

```
python3 main.py -l data/layout.yaml -u https://ha.url -t access_token
```

For a more complete breakdown of the options available in the layout file, see the Variables and Messages sections below.

## Layout File

The `layout.yaml` file controls most aspects of displaying messages on the sign. This is where variables are defined and various modes and colors for display are setup.

### Variables

The variables section of the file defines dynamic variables that can be loaded for display. Depending on the type used they will be updated either via polling Home Assistant or by watching MQTT topics. The data for variables can be evaluated by using Jina templates, of which there are a few examples below. For more information on templating, see the [Jinja documentation](https://jinja.palletsprojects.com/en/3.0.x/). There are a few different variable types, some with more options than others. The different types are listed below, with examples.


__Time__

The time variable utilizes the built-in functionality of the Alphasign protocol to display the current time on the sign.

```
variables:
  # name of the variable
  current_time:
    # type of variable
    type: time
```

__Date__

Similar to the time variable, this displays the current date. Due to limitations with the display this has to be set manually once a day to be correct. This is done by polling in the background once per day.

```
variables:
  current_date:
    type: date
    # optional parameter to set the separation character between the month, day, and year. Default is a '/'
    separator: '-'
```

__Home Assistant__

The Home Assistant type is a polling variable that updates on a given interval. Data will be updated each time the polling interval is hit and the resulting string sent to the sign, wherever it is used in a message. Jinja templating can be used within the `data` field to process Home Assistant entities. Examples of this are shown below.

When using templating all entities are sent to the templating engine wrapped in a special `vars` variable. Entities are accessed by their name such as `vars['sensor.name']['state']`. For attributes you can use `vars['sensor.name']['attributes']['attribute_name']`. Using the [Developer Tools](https://www.home-assistant.io/docs/tools/dev-tools/) area of Home Assistant you can quickly see what information is available for a particular entity.

```
variables:
  # a simple example that just shows the state of an entity
  show_state:
    type: home_assistant
    # list of entities that this variable needs to load, use the HA entity name
    entities:
      - sensor.name
    # the text to be sent to the display
    text: "This entity is: {{ vars['sensor.name']['state'] }}"  # show the state of this entity
    # this is the text shown when the program first loads, before the entity is polled
    startup: "No data yet"
    # how often, in seconds, to update this variable
    poll_time: 300

  # a more complicated example, multiple entities and conditions
  show_presence:
    type: home_assistant
    entities:
      - person.person_a
      - person.person_b
    # outputs "Everyone is home" or "Everyone is not home"
    text: >-
      Everyone is
      {% if vars['person.person_a']['state'] == 'home' and vars['person.person_b']['home'] %}
        home
      {% else %}
        not home
      {% endif %}
    startup: "Loading data"
    poll_time: 60
```

## Messages

The messages area of the `.yaml` file is where the variables are setup to actually display on the sign. This is where important information such as the sign mode, color, and speed of the message are specified. Variables can also be combined here to show within the same message. The order of the messages is the order they will be sent to the sign.

### Parameters

__Mode__

The mode is how the sign will be written across the screen. Valid modes are:

* hold - display all at once and hold
* rotate - scroll right to left

__Color__

The color of the message. Valid colors are:

* green
* red
* orange
* yellow
* rainbow1
* rainbow2

__Speed__

The speed that the message will go across the screen. This is a number 1-5 with 1 being slow and 5 being fast.

### Examples

The simplest message contains no variable, and hence won't be updated after the sign is loaded.

```
messages:
  - text: "Home Assistant Sign"
    mode: "rotate"
    color: "rainbow1"
```

Using the variable examples above, variables can be defined by using the `data` tag.

```
messages:
  # show the output of one variable
  - data:
    - show_presence
    mode: "rotate"
    color: "orange"
  # show the date and time in one message
  - data:
      - current_time
      - current_date
    mode: hold
    color: "green"
    speed: 2
```

## Contributing

This is mostly a project I made for fun so not looking to really modify it too much. If you have troubles or find a bug, post it an issue. I'll review PRs as well if it fixes functionality or adds something really cool.

## License

[MIT License](https://github.com/robweber/ha-betabrite-sign/blob/main/LICENSE)
