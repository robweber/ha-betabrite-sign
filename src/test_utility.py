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
import argparse
import logging
import time
from termcolor import colored
from lib import constants

from datetime import datetime, timedelta

class SignTester:
    """A simple sign test utility that will display a single message to the sign"""
    __betabrite = None

    def __init__(self, device):
        if(device == 'cli'):
            self.__betabrite = alphasign.interfaces.local.DebugInterface(debug=True)
        else:
            self.__betabrite = alphasign.interfaces.local.Serial(device=device, debug=True)

    def display(self, message, color, font, mode):
        self.__betabrite.connect()
        self.__betabrite.clear_memory()

        # wait for sign to clear memory
        time.sleep(2)

        displayParams = f"{constants.ALPHA_COLORS[color]}{constants.ALPHA_FONTS[font]}"

        # create a string
        stringObj = alphasign.String(data=message,
                                     label='1', size=125)

        # create the text object - add the string
        alphaObj = alphasign.Text("%s%s" % (displayParams, stringObj.call()), mode=constants.ALPHA_MODES[mode],
                                  label="A")

        self.__betabrite.allocate((alphaObj,stringObj,))
        self.__betabrite.set_run_sequence((alphaObj,))

        # write the object to the sign
        self.__betabrite.write(stringObj)
        self.__betabrite.write(alphaObj)

        self.__betabrite.disconnect()

    def read(self):
        self.__betabrite.connect()

        resultObj = self.__betabrite.read_information()

        print(f"Model: {colored(resultObj.get_model(), 'green')}")
        print(f"Firmware: {colored(resultObj.get_firmware(), 'green')}")
        firmware_date = resultObj.get_firmware_date().strftime("%m/%Y")
        print(f"Firmware Date: {colored(firmware_date, 'green')}")
        print(f"Current Time: {colored(resultObj.get_current_time(), 'green')}")
        print(f"Time Format: {colored(resultObj.get_time_format(), 'green')}")
        print(f"Speaker Status: {colored(resultObj.get_speaker_status(), 'green')}")
        print(f"Total Memory: {colored(resultObj.get_total_memory(), 'green')}")
        print(f"Free Memory: {colored(resultObj.get_free_memory(), 'green')}")

        self.__betabrite.disconnect()


parser = argparse.ArgumentParser(description='Betabrite Sign Test Utility')
parser.add_argument('-d', '--device', default="/dev/ttyUSB0",
                    help="Path to device where Alphasign is connected, default is %(default)s, can also use 'cli' to output to screen only")
parser.add_argument('-m', '--message', required=False,
                    help="The message to display on the sign, if missing sign information is read instead")
parser.add_argument('-C', '--color', default="green",
                    help="The color of the message")
parser.add_argument('-F', '--font', default="five_stroke",
                    help="Message font")
parser.add_argument('-M', '--mode', default="hold",
                    help="The display mode, default is hold")

args = parser.parse_args()

# setup basic logger
logging.basicConfig(datefmt='%m/%d %H:%M',
                    format="%(message)s",
                    level=getattr(logging, 'DEBUG'))

# create the tester
tester = SignTester(args.device)

logging.info(colored('Sign Test Utility', 'green'))
if(args.message):
    logging.info("Writing the following message to the sign:")
    logging.info(f"Message: {colored(args.message, 'green')}")
    logging.info(f"Color: {args.color}")
    logging.info(f"Font: {args.font}")
    logging.info(f"Mode: {colored(args.mode, 'red')}")

    tester.display(args.message, args.color, args.font, args.mode)
else:
    logging.info("Reading sign information")
    tester.read()

logging.info('Complete')
