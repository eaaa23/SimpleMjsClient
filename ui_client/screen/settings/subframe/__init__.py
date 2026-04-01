from ...abstract import AbstractScreen


class SettingsSubframe:
    def __init__(self, parent, screen):
        self.parent = parent
        self.ui = screen.ui
        self.screen: AbstractScreen = screen

    def apply(self):
        pass

    def update_text(self):
        pass
