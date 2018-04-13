import pygame
from hal_impl.data import hal_data


class UsbJoysticks(object):
    def __init__(self, ui):
        pygame.init()

        self.ui = ui

        self.joysticks = self.getUsbJoystickList()
        self.initJoystickList(self.joysticks)

    def close(self):
        pygame.display.quit()
        pygame.quit()

    def getUsbJoystickList(self):
        joysticks = []

        for i in range(pygame.joystick.get_count()):
            joysticks.append(pygame.joystick.Joystick(i))
        return joysticks

    def initJoystickList(self, joystickList):
        for i, joystick in enumerate(joystickList):
            joystick.init()
            if i < len(hal_data["joysticks"]):
                hal_data["joysticks"][i]["name"] = joystick.get_name()

    def update(self):
        pygame.event.get()

        for joystick, (ui_axes, ui_buttons, _) in zip(
            self.joysticks, self.ui.joysticks
        ):

            for axis in range(min(len(ui_axes), joystick.get_numaxes())):
                ui_current_axis = ui_axes[axis]

                value = joystick.get_axis(axis)
                ui_current_axis.set_value(value)

            for button in range(min(len(ui_buttons), joystick.get_numbuttons())):
                ui_current_button = ui_buttons[button]
                ui_current_button = ui_current_button[0]

                value = joystick.get_button(button)

                if value == False:
                    ui_current_button.deselect()
                else:
                    ui_current_button.select()
