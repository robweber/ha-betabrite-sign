# Home Assistant Betabrite Sign
[![Build Status](https://img.shields.io/github/actions/workflow/status/robweber/ha-betabrite-sign/flake8.yml?branch=main)](https://github.com/robweber/ha-betabrite-sign/actions)
[![License](https://img.shields.io/github/license/robweber/ha-betabrite-sign)](https://github.com/robweber/ha-betabrite-sign/blob/main/LICENSE)
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg)](https://github.com/RichardLitt/standard-readme)

Integrate an LED sign that uses the [Alphasign protocol](https://www.adaptivedisplays.com/resources/documentation-and-manuals/support-documents/bid/264113/Alpha-Sign-Communications-Protocol-pn-97088061) with your [Home Assistant](https://www.home-assistant.io/) installation. This project seeks to provide a headless Python program that will communicate with the sign and allow for updates by either querying a Home Assistant instance or getting status updates via MQTT. It can also integrate with Home Assistant as a light entity to expose information directly to your smart home.

Messages are configured for the display using a simple `.yaml` configuration file. Variables can be defined that pull information from Home Assistant via the [templating engine](https://www.home-assistant.io/docs/configuration/templating/). These will dynamically update the sign on either a polling timer or via MQTT topics.

## Table Of Contents

- [Background](#background)
- [Install](#install)
  - [Home Assistant Entity Setup](#home-assistant-setup)
  - [Home Assistant MQTT Setup](#home-assistant-mqtt-setup)
- [Usage](#usage)
  - [Testing](#testing)
- [Layout File](#layout-file)
  - [Variables](#variables)
     - [Time](#time)
     - [Date](#date)
     - [Static](#static)
     - [Dynamic](#dynamic)
     - [Home Assistant](#home-assistant)
     - [Home Assistant Test Variable](#home-assistant-text-variable)
     - [MQTT](#mqtt)
     - [REST Request](#rest-request)
  - [Display](#display)
    - [Parameters](#parameters)
    - [Examples](#examples)
 - [Templating](#templating)
    - [Functions](#functions)
    - [Filters](#filters)
- [Contributing](#contributing)
- [License](#license)

## Background

A long, long time ago, in an apartment far away; my college roommate and I wanted a cool LED sign to display information. I purchased a cheap [Betabrite LED display](https://www.alpha-american.com/p-betabrite.html) and a serial cable. My [first crude attempts](https://sourceforge.net/projects/betasigncontrol/) at this (circa 2007) used Java and some serial commands to write messages to the display. Over time this setup evolved to using a Raspberry Pi and [WebIOPI](http://webiopi.trouch.com/) to update the display. When I started using Home Assistant I hacked and slashed my way to integrating that with the existing setup as well.

After some time with Home Assistant I realized there had to be a better way. Projects like [ESPHome](https://esphome.io/) showed me there were better integration methods. I didn't want to write an entire custom integration for Home Assistant; but yet my existing setup was way too cumbersome and relied on a lot of code rewrites every time I wanted to add something.

What I wanted was a system that I could define with a `.yaml` file and have it dynamically generate the information needed to write messages to the LED sign. Furthermore I wanted to point to Home Assistant entities that could be polled, or MQTT topics that could be monitored, to update messaging within the sign. This project is the end result. I tried as much as possible to utilize existing Home Assistant methodologies, like Jinja templating, so that setup and configuration were somewhat intuitive.

## Install

The install procedure assumes you have a working version of the Raspberry Pi OS already installed on an Rpi or Rpi Zero. Obviously you also need an LED sign that utilizes the Alphasign Protocol and a way for the Rpi to talk to it. If you notice that the time is incorrect on the sign use `raspi-config` to set the correct localization information.

```
# install os deps
sudo apt-get install git python3-pip python3-venv

# clone the repo
git clone https://github.com/robweber/ha-betabrite-sign.git

# create the virtual environment
cd ha-betabrite-sign
python3 -m venv .venv
source .venv/bin/activate

# install python requirements
pip3 install -r install/requirements.txt

# if installing for development/testing
pip3 install -r install/requirements-dev.txt

# deactivate virtual environment when done
deactivate

```

### Home Assistant Entity Discovery

This code can run standalone, or be further integrated with Home Assistant to expose some entities via [MQTT Light](https://www.home-assistant.io/integrations/light.mqtt/) and [MQTT Text](https://www.home-assistant.io/integrations/text.mqtt/) integrations. This allows Home Assistant to get some run-time data, control the sign as though it was a light, and push text to the sign. For this to work MQTT must be setup as [described below](#mqtt). In Home Assistant [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) is used to automatically configure the device when `--ha_discovery` is passed in at startup. Other options, like the device name, can be configured as well.

When MQTT is configured the program will watch for commands and publish to the following topics.

* betabrite/sign/status - sign off/on status
* betabrite/sign/attributes - attributes for the Light entity
* betabrite/sign/switch - command topic to toggle the light entity
* betabrite/sign/available - availability topic (ie, is the program running)
* betabrite/sign/current_text - current text entity value
* betabrite/sign/new_text - command topic to update text entity from Home Assistant

Turning the sign off and on is done via a special Text object allocated when the program starts. This is simply a blank message that pre-empts any running message at runtime to blank the display (off) and then remove it to return the display to normal messaging (on). The text entity can be set in Home Assistant and used in any message through a special MQTT variable.

### Home Assistant MQTT Statestream

Topics from any MQTT device can be monitored, but a common use case is to get entity information from Home Assistant. Utilizing the [MQTT broker](https://github.com/home-assistant/addons/tree/master/mosquitto) add-on for Home Assistant and the built in [state stream integration](https://www.home-assistant.io/integrations/mqtt_statestream/) it is very easy to get up to date entity information pushed to the LED sign. See the pages for each of these on their setup within Home Assistant. Once configured you can monitor the state topics required to get the information needed to display on the sign.

## Usage

Once installed copy the existing `data/layout.yaml.example` file to `data/layout.yaml`. This file is read on startup to configure the messages sent to the display. There are two main sections to the file __variables__ and __display__. The variables section defines strings that will be updated dynamically on the sign. The display area defines which text will be displayed on the sign, and in what order. This includes things like the display mode and color. For dynamic updates to work you'll need to poll Home Assistant or utilize MQTT. For a more complete breakdown of the options available in the layout file, see the [Variables](#variables) and [Display](#display) sections below.

You can run the program with the following command:

```
python3 src/main.py
```

You can also specify a config file location instead of passing in all arguments on the command line. This is done with the `-c` flag:

```
python3 src/main.py -c /path/to/config.conf
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
  --ha_discovery        Enable Home Assistant MQTT Discovery, default is False
  --ha_device_name HA_DEVICE_NAME
                        The Home Assistant entity name, default is 'Betabrite
                        Sign'
  --mqtt_discovery_prefix MQTT_DISCOVERY_PREFIX
                        The Home Assistant MQTT Discovery Prefix, default is
                        'homeassistant'


```

You can also install the program as a service with the following commands. The service assumes the working directory is ``/home/pi/ha-betabrite-sign/`` and the configuration file is located at `/etc/default/ha-sign`, change this if you need to.

```
sudo cp install/ha-sign.service /etc/systemd/system/ha-sign.service
sudo chown root:root /etc/systemd/system/ha-sign.service
sudo systemctl enable ha-sign

# start the service
sudo systemctl start ha-sign

# stop the Service
sudo systemctl stop ha-sign
```

### Testing

There is a basic test utility also included to test if communication to your sign is working or just test different message configurations. It can be accessed via the `test_utility.py` script. As with the main program using a device of __cli__ will output everything to the display and simply simulate the commands. Parameters for the color, font, and mode are shown below in the [messages](#messages) area.

```
usage: test_utility.py [-h] [-d DEVICE] -m MESSAGE [-C COLOR] [-F FONT]
                       [-M MODE]

Betabrite Sign Test Utility

optional arguments:
  -h, --help            show this help message and exit
  -d DEVICE, --device DEVICE
                        Path to device where Alphasign is connected, default
                        is /dev/ttyUSB0, can also use 'cli' to output to
                        screen only
  -m MESSAGE, --message MESSAGE
                        The message to display on the sign
  -C COLOR, --color COLOR
                        The color of the message
  -F FONT, --font FONT  Message font
  -M MODE, --mode MODE  The display mode, default is hold

```

## Layout File

The `layout.yaml` file controls most aspects of displaying messages on the sign. This is where variables are defined and various modes and colors for display are setup. If the contents of the file do not validate against constraints (ie incorrect variable types, colors, etc) the program will exit with an error on startup.

### Variables

The variables section of the file defines variables that can store information or format text for display. Depending on the type used they will be updated either via polling or by watching MQTT topics. The data for dynamic variables is evaluated by using Jijna templates, of which there are a few examples below. For more information on templating, see the [Home Assistant](https://www.home-assistant.io/docs/configuration/templating/) and [Jinja documentation](https://jinja.palletsprojects.com/en/3.0.x/templates/). There are a few different variable types, some with more options than others. The different types are listed below, with examples.


#### Time

The time variable utilizes the built-in functionality of the Alphasign protocol to display the current time on the sign.

```
variables:
  # name of the variable
  current_time:
    # type of variable
    type: time
    # optional, 12 or 24 depending on the type of clock you wish to see
    format: 12
    # color of message, optional
    color: green
```

#### Date

Similar to the time variable, this displays the current date. Due to limitations with the display this has to be set manually once a day to be correct. This is done by polling in the background once per day. When formatting the date you can use any format codes accepted by [strftime()](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior). Keep in mind you can use time codes however this will only update once per day - use the time variable if you want to keep real time.

```
variables:
  current_date:
    type: date
    # optional parameter to format the date differently
    format: "%A, %B %m, %Y"
```

#### Static

The static type allows for displaying static text that is loaded once when the sign initializes and then is never changed.

```
variables:
  static_text:
    type: static
    text: "Static Text Example"
```

#### Dynamic

Dynamic text can utilize Jinja template syntax to update the message contents dynamically. Dynamic text is re-evaluated once every minute for changes, or whenever a referenced variable is updated. These are found at runtime and displayed when debug logging is enabled.

A common use case for this variable type is combining data from other variables through the `get_payload()` or `is_payload()` template methods. Similar to the [states()](https://www.home-assistant.io/docs/configuration/templating/#states) methods in Home Assistant; this allows templates to get payloads from MQTT or REST variable types. The example below subscribes to 2 MQTT topics and combines them using a dynamic variable to display which lights are currently on.

```
variables:
  dynamic_text:
    type: dynamic
    # the template to render when updated
    template: >-
      {% set result = [] %}
      {% if is_payload('office_lights', 'on') %}
        {% set result = result + ['Office Lights are on'] %}
      {% endif %}
      {% if is_payload('living_room_lights', 'on') %}
        {% set result = result + ['Living Room Lights are on'] %}
      {% endif %}
      {{ result | join(' and ') }}
    # optional, display before content is rendered
    startup: "Loading"
  office_lights:
    type: mqtt
    topic: ha_states/light/office_lights/state
  living_room_lights:
    type: mqtt
    topic: ha_states/light/living_room_lights/state
```

#### Home Assistant

The Home Assistant type is a polling variable that updates on a given interval. Data will be updated each time the polling interval is hit and the resulting value stored for use. Polling intervals are specified using [cron syntax](https://en.wikipedia.org/wiki/Cron), with a default of every 5 minutes. Home Assistant templates are used to format the results directly in Home Assistant. Examples of this are shown below. Additionally you'll need to specify the URL to your Home Assistant instance, and a [long lived access token](https://www.home-assistant.io/docs/authentication/).

The Home Assistant [Developer Tools](https://www.home-assistant.io/docs/tools/dev-tools/) area should be used to create the template string you need so it can be cut/pasted into the yaml configuration. This should get you the exact syntax you need to render your variable in Home Assistant and have the results displayed on the sign.

```
variables:
  # a simple example that just shows the state of an entity
  show_state:
    type: home_assistant
    # the text to be sent to the display - just show the state of this entity
    template: "This entity is: {{ states('sensor.name' }}"
    # this is the text shown when the program first loads, before the entity is polled
    startup: "No data yet"
    # how often, to update as a cron expression, if missing defaults to every 5 min
    cron: "*/30 * * * *"

  # a more complicated example, multiple entities and conditions
  show_presence:
    type: home_assistant
    # outputs "Everyone is home" or "Everyone is not home"
    template: >-
      {% if states('person.person_a') == 'home' and states('person.person_b']) == 'home' %}
      Everyone is home
      {% else %}
      Everyone is gone
      {% endif %}
    startup: "Loading data"
    color: yellow
```

#### Home Assistant Text Variable

The Home Assistant Text Entity (setup via [Entity Discovery described above](#home-assistant-entity-discovery) is a special variable available to pull the value from the Home Assistant Text Entity. The way this works is that the entity is available to be set in Home Assistant. This can be done through a Lovelace card or through a service call. This text entry will be published via MQTT and available for use in the sign as a standard variable. It is available via the `HA_TEXT_ENTITY` variable name. Below are a few examples.

```
# add the HA Text Entity to a message
display:
  main:
    - message:
        - mqtt_location
        - HA_TEXT_ENTITY
      color: green
      mode: hold
```

#### MQTT

The MQTT variable type subscribes to an MQTT topic and will update the variable text any time the topic is updated. Topics are limited to the same MQTT host specified in the main program arguments (see above). Additionally Jinja templates can be used to evaluate the passed in data. This is accessed via the `{{ value }}` variable in the template. JSON strings are parsed automatically and can be accessed with `{{value['key']}}` or `{{value.key}}`.

MQTT can sometimes be very chatty so an additional `update_template` key is available. Using this allows you to define a True/False statement to determine if the data in the payload should actually trigger an update to the sign. The current ```value```  is available just like in the text template.

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

  # an example where the payload contains JSON
  mqtt_json:
    type: mqtt
    # the topic to watch
    topic: homeassistant/media_player/living_room/status
    # the template to render when updated
    template: >-
      {% if value.state == 'playing' %}
      Now playing {{ value.song }}
      {% else %}
      Nothing playing
      {% endif %}

  mqtt_conditional:
    type: mqtt
    topic: homeassistant/locks/front_door/state
    template: >-
      The Front door is {{ value.state }}
    # example of a conditional
    # returns true if the state is not unknown
    update_template: >-
      {{ value.state != 'unknown' }}
```

A more advanced use caes utilizes `get_payload` and `is_payload` to reference between variables.  The example below subscribes to 2 topics, one for geolocation and one for general home/away presence. The `mqtt_location` variable references the presence information to decide if the person is home or not before displaying the full geo location.  Anytime a variable is updated that is used within other templates the downstream template will also be updated. These are found at runtime and displayed when debug logging is enabled.

```
variables:
  mqtt_presence:
    type:mqtt
    # published home/away status
    topic: homeassistant/person/person_a/state
  mqtt_location:
    type: mqtt
    # geolocation published from Home Assistant Companion App
    topic: homeassistant/mobile_app/person_a/geo_location
    template: >-
      {% if is_payload('mqtt_presence', 'home') %}
      Person A is Home
      {% else %}
      Person A is {{ value }}
      {% endif %}
# only display one message on the sign
display:
  main:
    - message:
        - mqtt_location
      color: green
      mode: hold
```

#### REST Request

The REST Request variable will perform an HTTP request and pull in the response to display. This is most useful for REST APIs that return JSON formatted results, but can be used for any type of HTTP request. This is a polling variable that will be updated on a schedule. The default schedule is every 5 minutes but can be adjusted using [cron syntax](https://en.wikipedia.org/wiki/Cron). Additionally Jinja templates can be used to evaluate the passed in data. This is accessed via the `{{ value }}` variable in the template. JSON strings are parsed automatically and can be accessed with `{{value['key']}}` or `{{value.key}}`.

During configuration the `update_template` key is also available. Using this allows you to define a True/False statement to determine if the data in the payload should actually trigger an update to the sign. The current `value`  is available just like in the text template.

```
variables:
  example_rest_request:
    type: rest
    url: https://url/to/payload
    # update every hour, 5 min by default
    cron: "*/60 * * * *"
    template: >-
      The value is: {{ value }}
  anoter_example_rest_request:
    type: rest
    url: https://url/tojson/payload
    # method can be 'get' or 'post' - 'get' requests used by default
    method: post
    template: >-
      JSON Value: {{ value.key }}

```

## Display

The display area of the `.yaml` file is where messages are setup to actually display on the sign. Each message queue has a name and a list of messages. Within each message is where important information such as the sign mode, color, and speed of the message are specified. Variables can also be combined here to show within the same message. The order of the messages is the order they will be sent to the sign.

The `main` queue must be present, as this is the default and loaded on startup. Additional queues can be defined as well. The currently active queue is determined by evaluating the `active_template` function. This template should return True/False to determine if the queue should be set to active. These are evaluated top-down, so the first queue that returns True is set as active. If no statement returns True, then the `main` queue is set to active automatically. Examples of this are below. __Note:__ the active queue is re-evaluated every minute, not on the fly, so there may be some delay between variables updating and the queue changing.

### Parameters

These parameters are used within the `message` tag.

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

The simplest message contains a static variable, within the main queue. This won't be updated after the sign is loaded.

```
display:
  main:
    queue:
      - message:
          - static_text
        mode: "rotate"
        color: "rainbow1"
```

Below is an example with dynamic variables and multiple variables combined.

```
display:
  main:
    queue:
      # show the output of one variable
      - message:
        - show_presence
        mode: "rotate"
        color: "orange"
      # show the date and time in one message
      - message:
          - current_time
          - current_date
        mode: hold
        speed: 2
        font: seven_high_std
```

Finally, this example has multiple message queues defined. The variable `lights` contains a payload of either on or off from Home Assistant. This is used to trigger the correct queue.

```
variables:
  current_time:
    type: time
  static_text:
    type: static
    text: "The lights are on"
  lights:
    type: mqtt
    topic: homeassistant/light/living_room/state
display:
  # show only the time when the lights are off
  main:
    queue:
      - message:
        - current_time
        mode: hold
        color: red
  # show this queue when the lights are on
  lights_on:
    queue:
      - message:
        - current_time
        - static_text
        mode: rotate
        color: green
    active_template: >-
      {{ is_payload('lights', 'on') }}  
```

## Templating

There are a handful of custom functions and filters available to use in local Jinja templates, outside of the built in ones. These can be used with variables that support templates, update templates or active queue templates.

### Functions

Jinja offers a variety of [built in functions](https://jinja.palletsprojects.com/en/3.0.x/templates/#list-of-global-functions) that can be used when rendering templates. Below are some custom ones for this project specifically.

#### get_payload(var_name)

Return the payload of another variable, or a blank string if there isn't one. This also works on JSON values.

Example:
```
# normal variable with a string payload
{{ get_payload('custom_var_name') }}

# variable with a JSON payload
{% set some_json = get_payload('custom_var_name') %}
{{ some_json.key_name }}

```

#### get_payload_attr(var_name, attribute_name)

Returns the attribute value of a given payload variable. This is helper method to quickly get attribute values where you know the payload is JSON. This will return `None` if the attribute does not exist.

```
{{ get_payload_attr('custom_var_name', 'attribute_name') }}
```

#### is_payload(var_name, expected_value)

Similar to `get_payload` but this will evaluate against an expected value and return True/False.

```
{% is_payload('var_name', 'on') %}
Value is on
{% endif %}

# is the same as
{% if get_payload('var_name') == 'on' %}
Value is on
{% endif %}
```

#### is_payload_attr(var_name, attribute_name, expected_value)

Combination of `is_payload` and `get_payload_attr` to compare the attribute value to an expected value.

```
{% if is_payload_attr('var_name', 'attribute_name', 'on') %}
Value is On
{% endif %}
```

#### now()

Returns a Python [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) object that represents the current time.

```
# check if current time greater than 11 AM
{% if now().strftime("%H") | int >= 11 %}
 It's after 11:00 AM
{% endif %}
```

#### timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)

Returns a Python [timedelta](https://docs.python.org/3/library/datetime.html#datetime-objects) object. This can be used to add or subtract a given amount from a current datetime value.

```
# add 30 min to the current time
{{ now() + timedelta(minutes=30) }}
```

#### strptime(date_string, format)

Uses the Python [strptime](https://docs.python.org/3/library/datetime.html#datetime.datetime.strptime) function to parse a string into a [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) object

```
{{ strptime("January 12, 2022", "%B %d, %Y") }}
```

#### is_time(time_expression, format, datetime_obj=now())

Tests if a given time expression matches the current time, or a given datetime object. Useful as part of a [Dynamic Variable](#dynamic) to check if the current date is a specific day of the week, a holiday, birthday, or other important date. Parameters are the expression to compare and the [strftime format code](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes) to format the current date to.

```
# is today Christmas
{% is_time("12/25", "%m/%d") %}
Merry Christmas!
{% endif %}

# is tomorrow Friday
{% is_time("Friday", "%A", now() + timedelta(days=1)) %}
Tomorrow is Friday
{% endif %}

```

### Filters

Filters are a quick way of modifying data within a template. Jinja offers several [built in filters](https://jinja.palletsprojects.com/en/3.0.x/templates/#list-of-builtin-filters) but below are a few custom ones to help with templating.

#### color(color, conditional, alt_color)

The color filter can be used with a template to change the color of a string within the template. Due to how the Alphasign protocol handles colors, everything after this filter will use this color until a new color code is used. Optional parameters allow a conditional and alternative color selection should the condition be False. Examples of this are shown below.

```
# simplest version of using the filter, apply a new color to a string
{{ 'this is red' | color('red') }}

# only apply the color if the condition is True
{{ 'this might be red' | color('red', is_payload('other_var', 'on')) }}

# apply a different color should the condition fail, this will fail if value is less or equal to 0
{{ 'this will be red or green' | color('red', value > 0, 'green') }}
```

_Note_: due to some technical limitations with the Alphasign protocol the `rainbow1', 'rainbow2`, and `color_mix` colors can't be set inline and will be set to `green` when using this filter. To get around this set the color on a variable and combine variables in a message.

#### shorten_urls

This filter finds all urls in a given string and shortens them, useful when URLs are part of text but you don't want the full string on the display. The shortened form is just the domain of the link.

```
# the following would return "text with url www.google.com"
{{ "text with a url https://www.google.com/search?q=Python" | shorten_urls }}
```

## Contributing

This is mostly a project I made for fun so not looking to really modify it too much. If you have troubles or find a bug, post an issue. I'll review PRs as well if it fixes functionality or adds something really cool.

## License

[GPLv3](https://github.com/robweber/ha-betabrite-sign/blob/main/LICENSE)
