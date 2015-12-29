import tkinter as tk


class CheckButtonWrapper(tk.Checkbutton):
    '''
        Wrapper around a CheckButton object to allow synced communication
        with the robot
    '''

    def __init__(self, master, text):

        self.intval = tk.IntVar()

        super().__init__(master, text=text, variable=self.intval, command=self._on_command)

        self.updated = False

    def _on_command(self):
        self.updated = True

    def get_value(self):
        return self.intval.get() == 1

    def set_value(self, value):
        self.intval.set(1 if value else 0)

    def sync_value(self, value):
        if self.updated:
            self.updated = False
            return self.get_value()

        self.set_value(value)