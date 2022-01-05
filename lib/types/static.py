from .. variable_type import AlphaSignVariable


class StaticVariable(AlphaSignVariable):
    """Variable type that holds static text
    Once this is sent to the sign it is not updated again
    """
    def __init__(self, name, config):
        super().__init__('static', name, config)

    def get_text(self):
        return self.config['text']

    def get_startup(self):
        return self.get_text()
