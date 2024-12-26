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
import datetime
import re
from urllib.parse import urlparse
from . import constants


# global functions
def get_date():
    """same as calling datetime.now()
    https://docs.python.org/3/library/datetime.html#datetime.datetime.now
    """
    return datetime.datetime.now()


def get_timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
    """same as calling timedelta()
    https://docs.python.org/3/library/datetime.html#timedelta-objects
    """
    return datetime.timedelta(days=days, seconds=seconds, microseconds=microseconds,
                              milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks)


def create_time(date_string, format):
    """same as calling strptime()
    https://docs.python.org/3/library/datetime.html#datetime.datetime.strptime
    """
    return datetime.datetime.strptime(date_string, format)


def is_time(test_expr, format, current_time=datetime.datetime.now()):
    """ tests if a given time expression matches the datetime given (now() by default)
    example to check if current month is Oct: is_time("10", "%m")
    https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

    :param text_expr: the expression to test, should match the format of format parameter (ex 12/24)
    :param format: the format of the expression to test, using strftime format codes (ex %m/%d)
    :param current_time: the time to compare against, datetime.now() by default

    :returns: True/False on if test expression matches
    """
    # format date according to expression
    check_date = current_time.strftime(format)

    return test_expr == check_date


# filters
def shorten_urls(value):
    """replace urls in the given string with a shorterned version, just the domain piece
    https://www.google.com becomes www.google.com as an example
    """
    # find the urls in the string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"  # noqa: E501
    matches = re.findall(regex, value)

    for m in matches:
        # replace each url with it's shortened version
        url = urlparse(m[0])
        value = value.replace(m[0], url.netloc)

    return value


def set_color(text, color, conditional=True, alt_color=None):
    """returns the string along with the valid Alphasign color code so that strings
    can have different colors within message templates. Optionally a conditional can be set so that the color is only
    applied if the condition evaulates to True. If the condition is False the text can be returned unchanged, or set to a different
    color depending on if alt_color is set.

    :params text: the text to color, first argument of a filter
    :params color: a valid color text value, rainbow values cannot be used within Strings (per Alphasign protocol)
    :params conditional: a True/False conditional statement that controls if the color is applied or not
    :params alt_color: an alternative color to set if the condition is False, optional

    :returns: the text plus the valid Alphasign color code value or just the text if conditional evaluates to False and no alt_color exists
    """
    applied_color = ''
    invalid_colors = ['rainbow1', 'rainbow2']

    if(color in invalid_colors):
        # convert this to green as this won't work
        color = 'green'

    if(alt_color in invalid_colors):
        alt_color = 'green'

    # apply the color if conditional is True
    if(conditional):
        applied_color = constants.ALPHA_COLORS[color]
    else:
        # if not true, set the alt color if one is given
        applied_color = constants.ALPHA_COLORS[alt_color] if alt_color is not None else ''

    return f"{applied_color}{text}"
