"""
Copyright 2022 Rob Weber
This file is part of ha-betabrite-sign
omni-epd is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import alphasign
import json
import re
from json.decoder import JSONDecodeError

# current version
PROJECT_VERSION = "2.1"

# variable categories
ALPHASIGN_CATEGORY = 'alphasign'
POLLING_CATEGORY = 'polling'
MQTT_CATEGORY = 'mqtt'

# MQTT topics for state and commands
MQTT_STATUS = "betabrite/sign/status"
MQTT_ATTRIBUTES = "betabrite/sign/attributes"
MQTT_SWITCH = "betabrite/sign/switch"
MQTT_AVAILABLE = "betabrite/sign/available"
MQTT_COMMAND = "betabrite/sign/command"

# variable for when the sign is in off mode
SIGN_OFF = "ALPHA_SIGN_OFF"

# dicts to transfrom yaml to alphasign variables
ALPHA_MODES = {"rotate": alphasign.modes.ROTATE, "hold": alphasign.modes.HOLD, "roll_up": alphasign.modes.ROLL_UP,
               "roll_down": alphasign.modes.ROLL_DOWN, "roll_left": alphasign.modes.ROLL_LEFT, "roll_right": alphasign.modes.ROLL_RIGHT,
               "wipe_up": alphasign.modes.WIPE_UP, "wipe_down": alphasign.modes.WIPE_DOWN, "wipe_left": alphasign.modes.WIPE_LEFT,
               "wipe_right": alphasign.modes.WIPE_RIGHT, "scroll": alphasign.modes.SCROLL, "twinkle": alphasign.modes.TWINKLE,
               "sparkle": alphasign.modes.SPARKLE, "snow": alphasign.modes.SNOW, "interlock": alphasign.modes.INTERLOCK,
               "switch": alphasign.modes.SWITCH, "spray": alphasign.modes.SPRAY, "starburst": alphasign.modes.STARBURST,
               "welcome": alphasign.modes.WELCOME, "slot_machine": alphasign.modes.SLOT_MACHINE}

ALPHA_COLORS = {"green": alphasign.colors.GREEN, "orange": alphasign.colors.ORANGE, "rainbow1": alphasign.colors.RAINBOW_1,
                "rainbow2": alphasign.colors.RAINBOW_2, "red": alphasign.colors.RED, "yellow": alphasign.colors.YELLOW,
                "amber": alphasign.colors.AMBER, "brown": alphasign.colors.BROWN,  "color_mix": alphasign.colors.COLOR_MIX}

ALPHA_SPEEDS = {1: alphasign.speeds.SPEED_1, 2: alphasign.speeds.SPEED_2, 3: alphasign.speeds.SPEED_3,
                4: alphasign.speeds.SPEED_4, 5: alphasign.speeds.SPEED_5}

ALPHA_FONTS = {"five_high_std": alphasign.charsets.FIVE_HIGH_STD, "five_stroke": alphasign.charsets.FIVE_STROKE,
               "seven_high_std": alphasign.charsets.SEVEN_HIGH_STD, "seven_stroke": alphasign.charsets.SEVEN_STROKE,
               "seven_high_fancy": alphasign.charsets.SEVEN_HIGH_FANCY, "ten_high_std": alphasign.charsets.TEN_HIGH_STD,
               "seven_shadow": alphasign.charsets.SEVEN_SHADOW, "full_height_fancy": alphasign.charsets.FULL_HEIGHT_FANCY,
               "full_height_std": alphasign.charsets.FULL_HEIGHT_STD, "seven_shadow_fancy": alphasign.charsets.SEVEN_SHADOW_FANCY,
               "five_wide": alphasign.charsets.FIVE_WIDE, "seven_wide": alphasign.charsets.SEVEN_WIDE,
               "seven_fancy_wide": alphasign.charsets.SEVEN_FANCY_WIDE, "wide_stroke_five": alphasign.charsets.WIDE_STROKE_FIVE}


def is_json(str):
    """Checks if a string can be decoded into a JSON object"""
    result = False

    try:
        json.loads(str)
        result = True
    except JSONDecodeError:
        # do nothing
        pass

    return result

def strip_control(str):
    """strips Alphasign control characters from a string so it can be logged properly
    :param str: the string to check for Alphasign control characters

    :returns: the cleaned string
    """

    return re.sub("\\x1c([1-8]|[A-C])", "", str)
