import tkinter as tk
from .slider import DisplaySlider

class StateDisplay:

    def __init__(self, root, label, config):
        '''
            initializes all default values and creates
            a board, waits for run() to be called
            to start the board

            manager - sim manager class instance
            board_size - a tuple with values (rows, cols)
        '''
        self.config = config
        self.frame = tk.LabelFrame(root, text=label)
        self.widgets = {}

    def update_widgets(self, state):
        if isinstance(state, int) or isinstance(state, float):
            state = [state]
        # Iterate through state components, building widgets for them as we go.
        if isinstance(state, dict):
            for component in state:
                if component not in self.widgets:
                    # Create new widget
                    self.widgets[component] = StateDisplay(self.frame, component, self.config.get(component, {}))
                    self.widgets[component].pack()
            for component in self.widgets:
                self.widgets[component].update_widgets(state[component])
        elif isinstance(state, list):
            for i in range(len(state)):
                if i not in self.widgets:
                    self.widgets[i] = DisplaySlider(self.frame, i, self.config.get(i, {}))
                    self.widgets[i].pack()
                self.widgets[i].update_widgets(state[i])

    def grid(self, *args, **kwargs):
        self.frame.grid(*args, **kwargs)

    def pack(self):
        self.frame.pack()
