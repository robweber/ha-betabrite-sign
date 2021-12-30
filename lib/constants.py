from . import alphasign

# variable categories
ALPHASIGN_CATEGORY = 'alphasign'
POLLING_CATEGORY = 'polling'

# dicts to transfrom yaml to alphasign variables
ALPHA_MODES = {"rotate": alphasign.modes.ROTATE, "hold": alphasign.modes.HOLD, "roll_up": alphasign.modes.ROLL_UP,
               "roll_down": alphasign.modes.ROLL_DOWN, "roll_left": alphasign.modes.ROLL_LEFT, "roll_right": alphasign.modes.ROLL_RIGHT,
               "wipe_up": alphasign.modes.WIPE_UP, "wipe_down": alphasign.modes.WIPE_DOWN, "wipe_left": alphasign.modes.WIPE_LEFT,
               "wipe_right": alphasign.modes.WIPE_RIGHT, "scroll": alphasign.modes.SCROLL}
ALPHA_COLORS = {"green": alphasign.colors.GREEN, "orange": alphasign.colors.ORANGE, "rainbow1": alphasign.colors.RAINBOW_1,
                "rainbow2": alphasign.colors.RAINBOW_2, "red": alphasign.colors.RED, "yellow": alphasign.colors.YELLOW,
                "amber": alphasign.colors.AMBER, "brown": alphasign.colors.BROWN,  "color_mix": alphasign.colors.COLOR_MIX}
ALPHA_SPEEDS = {1: alphasign.speeds.SPEED_1, 2: alphasign.speeds.SPEED_2, 3: alphasign.speeds.SPEED_3,
                4: alphasign.speeds.SPEED_4, 5: alphasign.speeds.SPEED_5}
