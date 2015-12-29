import tkinter as tk


class ValueWidget(tk.Frame):

    def __init__(self, master, width=80, height=20, clickable=False, default=None, minval=-1.0, maxval=1.0, step=0.05):

        super().__init__(master)

        self.w = width
        self.h = height

        self.canvas = tk.Canvas(self, width=width, height=height)
        self.canvas.pack(fill=tk.BOTH)
        self.canvas.create_rectangle(1, 1, self.w, self.h)

        self.box = self.canvas.create_rectangle(0, 0, 0, 0, fill='#00ff00')
        self.text = self.canvas.create_text((self.w - 3, self.h/2), anchor=tk.E, text='--')

        if clickable:
            self.canvas.bind("<Button 1>", self._on_mouse)
            self.canvas.bind("<Key>", self._on_key)

        self.updated = False
        self.disabled = False

        self.minval = minval
        self.maxval = maxval
        self.step = step
        self.value = 0.0

        if default is None:
            self.set_disabled()
        else:
            self.set_value(default)

    def _on_key(self, event):
        if self.disabled:
            return

        self.updated = True

        if event.keysym in ['Left', 'Down']:
            self.set_value(self.value - self.step)

        elif event.keysym in ['Right', 'Up']:
            self.set_value(self.value + self.step)

        elif event.keysym in [str(i) for i in range(0, 10)]:
            self.set_value(int(event.keysym))

    def _on_mouse(self, event):

        has_focus = False
        if self.canvas.focus_get() == self.canvas:
            has_focus = True

        self.canvas.focus_set()

        if self.disabled or not has_focus:
            return

        # TODO: this needs to be better..
        self.updated = True

        # pad the value
        if event.x < 5:
            value = 0
        elif event.x > self.w - 5:
            value = self.w - 5
        else:
            value = event.x - 5

        value = ((value / (self.w - 10.0)) * float(self.maxval - self.minval)) + self.minval
        self.set_value(value)


    #
    # Public interface
    #

    def set_disabled(self, disabled=True):

        if self.disabled == disabled:
            return

        self.disabled = disabled

        if disabled:
            self.canvas.itemconfig(self.text, text='--')
            self.canvas.itemconfig(self.box, state=tk.HIDDEN)
        else:
            self.set_value(self.value)

    def set_range(self, minval, maxval, step):
        self.minval = minval
        self.maxval = maxval
        self.step = step

        self.set_value(self.value)

    def sync_value(self, value):
        if self.updated:
            self.updated = False
            return self.value

        self.set_value(value)

    def set_value(self, value):

        value = float(min(max(value, self.minval), self.maxval))

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


    def get_value(self):
        return self.value