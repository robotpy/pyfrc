import tkinter as tk

class DisplaySlider(tk.Frame):

    def __init__(self, master, label, config):

        super().__init__(master)

        self.w = config.get("width", 200)
        self.h = config.get("height", 20)

        self.canvas = tk.Canvas(self, width=self.w, height=self.h)
        self.canvas.pack(fill=tk.BOTH)
        self.canvas.create_rectangle(1, 1, self.w, self.h)

        self.box = self.canvas.create_rectangle(0, 0, 0, 0, fill='#00ff00')
        self.text = self.canvas.create_text((self.w - 3, self.h/2), anchor=tk.E, text=label)

        self.minval = config.get("min", -1)
        self.maxval = config.get("max", 1)
        self.value = 0.0

    def update_widgets(self, state):
        self.set_value(state)

    def set_value(self, value):
        if value > self.maxval:
            self.maxval = value
        if value < self.minval:
            self.minval = value

        vrange = (self.maxval - self.minval)/2.0
        if value < 0:
            color = '#ff0000'
            x2 = int(self.w / 2)
            x1 = x2 - (abs(value) * x2)/vrange
        else:
            color = '#00ff00'
            x1 = int(self.w / 2)
            x2 = x1 + (abs(value)) * x1/vrange

        self.canvas.itemconfig(self.text, text='%.2f' % value)
        self.canvas.itemconfig(self.box, state=tk.NORMAL, fill=color)
        self.canvas.coords(self.box, x1, 1, x2, self.h)

        self.value = value
