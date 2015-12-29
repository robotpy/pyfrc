import tkinter as tk


class PanelIndicator(tk.Frame):

    def __init__(self, master, width=20, height=20, clickable=False):

        super().__init__(master)

        self.updated = False
        self.value = None

        self.canvas = tk.Canvas(self, width=width, height=height)
        self.light = self.canvas.create_oval(2, 2, 18, 18, fill='#aaaaaa')

        self.canvas.pack(fill=tk.BOTH)

        if clickable:
            self.canvas.bind("<Button 1>", self._on_mouse)

    def _on_mouse(self, event):
        if self.value is None:
            return
        self.updated = True
        self.set_value(not self.value)

    def sync_value(self, value):
        if self.updated:
            self.updated = False
            return self.value

        self.set_value(value)

    def set_value(self, value):
        if value:
            self.set_on()
        else:
            self.set_off()

    def set_on(self):
        self.canvas.itemconfig(self.light, fill='#00FF00')
        self.value = True

    def set_off(self):
        self.canvas.itemconfig(self.light, fill='#008800')
        self.value = False

    def set_back(self):
        self.canvas.itemconfig(self.light, fill='#FF0000')
        self.value = -1

    def set_disabled(self):
        self.canvas.itemconfig(self.light, fill='#aaaaaa')
        self.value = None