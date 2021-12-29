from . import alphasign

# variable categories
ALPHASIGN_CATEGORY = 'alphasign'
POLLING_CATEGORY = 'polling'

# dicts to transfrom yaml to alphasign variables
ALPHA_MODES = {"rotate":alphasign.modes.ROTATE, "hold":alphasign.modes.HOLD}
ALPHA_COLORS = {"green": alphasign.colors.GREEN, "orange": alphasign.colors.ORANGE, "rainbow1": alphasign.colors.RAINBOW_1,
                "rainbow2": alphasign.colors.RAINBOW_2, "red": alphasign.colors.RED, "yellow": alphasign.colors.YELLOW}
ALPHA_SPEEDS = {1: alphasign.speeds.SPEED_1, 2: alphasign.speeds.SPEED_2, 3: alphasign.speeds.SPEED_3,
                4: alphasign.speeds.SPEED_4, 5: alphasign.speeds.SPEED_5}
