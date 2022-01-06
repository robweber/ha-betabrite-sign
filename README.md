# Home Assistant Betabrite Sign
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg)](https://github.com/RichardLitt/standard-readme)

Integrate an LED sign that uses the [Alphasign protocol](https://www.adaptivedisplays.com/resources/documentation-and-manuals/support-documents/bid/264113/Alpha-Sign-Communications-Protocol-pn-97088061) with your [Home Assistant](https://www.home-assistant.io/) installation. This project seeks to provide a headless Python program that will communicate with the sign and allow for updates by either querying a Home Assistant instance or getting status updates via MQTT. It can also integrate with Home Assistant as a light entity to expose information directly to your smart home.

Messages are configured for the display using a simple `.yaml` configuration file. Variables can be defined that pull information from Home Assistant via the [templating engine](https://www.home-assistant.io/docs/configuration/templating/). These will dynamically update the sign on either a polling timer or via MQTT topics.

## Table Of Contents

- [Background](#background)
- [Install](#install)
  - [Home Assistant Setup](#home-assistant-setup)
- [Usage](#usage)
- [Layout File](#layout-file)
  - [Variables](#variables)
     - [Time](#time)
     - [Date](#date)
     - [Static](#static)
     - [Home Assistant](#home-assistant)
     - [MQTT](#mqtt)
  - [Messages](#messages)
    - [Parameters](#parameters)
    - [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## Background

A long, long time ago, in an apartment far away; my college roommate and I wanted a cool LED sign to display information. I purchased a cheap [Betabrite LED display](https://www.alpha-american.com/p-betabrite.html) and a serial cable. My first crude attempts at this (circa 2006) used Java and some serial commands to write messages to the display. Over time this setup evolved to using a Raspberry Pi and [WebIOPI](http://webiopi.trouch.com/) to update the display. When I started using Home Assistant I hacked and slashed my way to integrating that with the existing setup as well.

After some time with Home Assistant I realized there had to be a better way. Projects like [ESPHome](https://esphome.io/) showed me there were better integration methods. I didn't want to write an entire custom integration for Home Assistant; but yet my existing setup was way too cumbersome and relied on a lot of code rewrites every time I wanted to add something.

What I wanted was a system that I could define with a `.yaml` file and have it dynamically generate the information needed to write messages to the LED sign. Furthermore I wanted to point to Home Assistant entities that could be polled, or MQTT topics that could be monitored, to update messaging within the sign. This project is the end result. I tried as much as possible to utilize existing Home Assistant methodologies, like Jinja templating, so that setup and configuration were somewhat intuitive.

## Install

The install procedure assumes you have a working version of the Raspberry Pi OS already installed on an Rpi or Rpi Zero. Obviously you also need an LED sign that utilizes the Alphasign Protocol and a way for the Rpi to talk to it. If you notice that the time is incorrect on the sign use `raspi-config` to set the correct localization information.

```
# install os deps
sudo apt-get install git python3-pip

# clone the repo
git clone https://github.com/robweber/ha-betabrite-sign.git

# install python requirements
sudo pip3 install -r install/requirements.txt

```

### Home Assistant Setup

This code can run standalone, or be further integrated with Home Assistant to show up as a light entity through the use of a [MQTT Light](https://www.home-assistant.io/integrations/light.mqtt/). This allows Home Assistant to get some run-time data and control the sign as though it was a light. For this to work MQTT must be setup via the arguments below. A sample YAML file for creating the Home Assistant device is located in the `install` directory. The availability template triggers when the program exits or crashes causing the entity to show up as unavailable.

When MQTT is configured the program will watch for commands and publish to the following topics.

* betabrite/sign/status
* betabrite/sign/attributes
* betabrite/sign/switch
* betabrite/sign/available

Turning the sign off and on is done via a special Text object allocated when the program starts. This is simply a blank message that pre-empts any running message at runtime to blank the display (off) and then remove it to return the display to normal messaging (on).

## Usage

Once installed copy the existing `data/layout.yaml.example` file to `data/layout.yaml`. This file is read on startup to configure the messages sent to the display. There are two main sections to the file __variables__ and __messages__. The variables section defines strings that will be updated dynamically on the sign. The messages area defines the format of how the text will be displayed on the sign, this includes things like the display mode and color. For dynamic updates to work you'll need to poll Home Assistant or utilize MQTT. For a more complete breakdown of the options available in the layout file, see the Variables and Messages sections below.

You can run the program with the following command:

```
python3 main.py
```

You can also specify a config file location instead of passing in all arguments on the command line. This is done with the `-c` flag:

```
python3 main.py -c /path/to/config.conf
```

A full list of arguments can be found by using the `-h` flag.

```
python3 main.py -h

usage: main.py [-h] [-c CONFIG] [-l LAYOUT] [-d DEVICE] [-D] [--ha_url HA_URL]
               [--ha_token HA_TOKEN] [-m MQTT] [--mqtt_username MQTT_USERNAME]
               [--mqtt_password MQTT_PASSWORD]

Home Assistant Betabrite Sign

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to custom config file
  -l LAYOUT, --layout LAYOUT
                        Path to yaml file containing sign text layout, default
                        is data/layout.yaml
  -d DEVICE, --device DEVICE
                        Path to device where Alphasign is connected, default
                        is /dev/ttyUSB0, can also use 'cli' to output to
                        screen only
  -D, --debug           Enables logging debug mode

Home Assistant:
  Settings required for Home Assistant polling

  --ha_url HA_URL       Home Assistant full base url
  --ha_token HA_TOKEN   Home Assistant Access Token

MQTT:
  Settings required for MQTT integrations

  -m MQTT, --mqtt MQTT  MQTT Server IP
  --mqtt_username MQTT_USERNAME
                        MQTT Server username
  --mqtt_password MQTT_PASSWORD
                        MQTT Server password

```

You can also install the program as a service with the following commands. The service assumes the configuration file is located in `/home/pi/ha-betabrite-sign/config.conf`, change this if you need to.

```
sudo cp install/ha-sign.service /etc/systemd/system/ha-sign.service
sudo chown root:root /etc/systemd/system/ha-sign.service
sudo systemctl enable ha-sign

# start the service
sudo systemctl start ha-sign

# stop the Service
sudo systemctl stop ha-sign
```

## Layout File

The `layout.yaml` file controls most aspects of displaying messages on the sign. This is where variables are defined and various modes and colors for display are setup.

### Variables

The variables section of the file defines dynamic variables that can be loaded for display. Depending on the type used they will be updated either via polling Home Assistant or by watching MQTT topics. The data for dynamic variables can be evaluated by using Jina templates, of which there are a few examples below. For more information on templating, see the [Home Assistant](https://www.home-assistant.io/docs/configuration/templating/) and [Jinja documentation](https://jinja.palletsprojects.com/en/3.0.x/templates/). There are a few different variable types, some with more options than others. The different types are listed below, with examples.


#### Time

The time variable utilizes the built-in functionality of the Alphasign protocol to display the current time on the sign.

```
variables:
  # name of the variable
  current_time:
    # type of variable
    type: time
    # color of message, optional
    color: green
```

#### Date

Similar to the time variable, this displays the current date. Due to limitations with the display this has to be set manually once a day to be correct. This is done by polling in the background once per day.

```
variables:
  current_date:
    type: date
    # optional parameter to set the separation character between the month, day, and year. Default is a '/'
    separator: '-'
```

#### Static

The static type allows for displaying static text that is loaded once when the sign initalizes and then is never changed.

```
variables:
  static_text:
    type: static
    text: "Static Text Example"
```

#### Home Assistant

The Home Assistant type is a polling variable that updates on a given interval. Data will be updated each time the polling interval is hit and the resulting string sent to the sign, wherever it is used in a message. Polling intervals are specified using [cron syntax](https://en.wikipedia.org/wiki/Cron), with a default of every 5 minutes. Home Assistant templates are used to format the results directly in Home Assistant. Examples of this are shown below. Additionally you'll need to specify the url to your Home Assistant instance, and a [long lived access token](https://www.home-assistant.io/docs/authentication/).

The Home Assistant [Developer Tools](https://www.home-assistant.io/docs/tools/dev-tools/) area should be used to create the template string you need so it can be cut/pasted into the yaml configuration. This should get you the exact syntax you need to render your variable in Home Assistant and have the results displayed on the sign.

```
variables:
  # a simple example that just shows the state of an entity
  show_state:
    type: home_assistant
    # the text to be sent to the display
    template: "This entity is: {{ states('sensor.name' }}"  # show the state of this entity
    # this is the text shown when the program first loads, before the entity is polled
    startup: "No data yet"
    # how often, to update as a cron expression, if missing defaults to every 5 min
    cron: "*/30 * * * *"

  # a more complicated example, multiple entities and conditions
  show_presence:
    type: home_assistant
    # outputs "Everyone is home" or "Everyone is not home"
    text: >-
      {% if states('person.person_a') == 'home' and states('person.person_b']) %}
      Everyone is home
      {% else %}
      Everyone is gone
      {% endif %}
    startup: "Loading data"
    color: yellow
```

#### MQTT

The MQTT variable type subscribes to an MQTT topic and will update the variable text any time the topic is updated. Additionally Jinja templates can be used to evaluate the passed in data; but are limited to the data available in the MQTT payload. This is accessed via the `{{ value }}` variable in the template. JSON strings are parsed automatically and can be accessed with ```{{value['key']}}``` or ```{{value.key}}```. Topics are limited to the same MQTT host specified in the main program arguments (see above).

```
variables:
  mqtt_variable:
    type: mqtt
    # the topic to watch
    topic: homeassistant/locks/front_door/state
    # the template to render when updated
    template: >-
      The Front door is {{ value }}
    # optional mqtt quality of service (0 is default)
    qos: 1

  # more complicated example converting payload to JSON
  mqtt_variable2:
    type: mqtt
    # the topic to watch
    topic: homeassistant/media/living_room/status
    # the template to render when updated
    template: >-
      {% if value.state == 'playing' %}
      Now playing {{ value.song }}
      {% else %}
      Nothing playing
      {% endif %}
```

## Messages

The messages area of the `.yaml` file is where the variables are setup to actually display on the sign. This is where important information such as the sign mode, color, and speed of the message are specified. Variables can also be combined here to show within the same message. The order of the messages is the order they will be sent to the sign.

### Parameters

#### Mode

The mode is how the sign will be written across the screen. Valid modes are:

* hold - display all at once and hold
* rotate - scroll right to left
* roll_up, roll_down, roll_left, roll_right - rolls text in the direction indicated
* wipe_up, wipe_down, wipe_left, wipe_right - wipe text in a block in the direction indicated
* scroll - similar to roll_up
* twinkle - message has a twinkling effect
* sparkle - message is drawn with a sparkle effect
* snow
* interlock
* spray
* switch
* starburst
* welcome - puts the word welcome ahead of the text
* slot_machine - plays a slot machine animation

#### Color (optional)

The color of the message. This can also be specified per variable to have mixed colors within a single message. Valid colors are:

* green
* red
* orange
* yellow
* rainbow1
* rainbow2
* amber
* brown
* color_mix - this is similar to rainbow but each letter is 1 color only

#### Font (optional)

Different character sets (fonts) can be specified from the default. These allow some customization over the size and shape of the displayed text.

* five_high_std
* five_stroke
* seven_high_std
* seven_stroke
* seven_high_fancy
* ten_high_std
* seven_shadow
* full_height_fancy
* full_height_std
* seven_shadow_fancy
* five_wide
* seven_wide
* seven_fancy_wide
* wide_stroke_five

#### Speed (optional)

The speed that the message will go across the screen. This is a number 1-5 with 1 being slow and 5 being fast.

### Examples

The simplest message contains a static variable, and hence won't be updated after the sign is loaded. Variables are set with the `data` tag.

```
messages:
  - data:
      - static_text
    mode: "rotate"
    color: "rainbow1"
```

Below is an example with dynamic variables and multiple variables combined.

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
    speed: 2
    font: seven_high_std
```

## Contributing

This is mostly a project I made for fun so not looking to really modify it too much. If you have troubles or find a bug, post it an issue. I'll review PRs as well if it fixes functionality or adds something really cool.

## License

[GPLv3](https://github.com/robweber/ha-betabrite-sign/blob/main/LICENSE)
