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


# global macros
def get_date():
    """same as calling datetime.now()
    https://docs.python.org/3/library/datetime.html
    """
    return datetime.datetime.now()


def get_timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
    """same as calling timedelta()
    https://docs.python.org/3/library/datetime.html
    """
    return datetime.timedelta(days=days, seconds=seconds, microseconds=microseconds,
                              milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks)


def create_time(date_string, format):
    """same as calling strptime()
    https://docs.python.org/3/library/datetime.html
    """
    return datetime.strptime(date_string, format)


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
