
import tkinter as tk

from .elements import DrawableElement, RobotElement


class RobotField:
    
    def __init__(self, root, manager, config):
        '''
            initializes all default values and creates 
            a board, waits for run() to be called
            to start the board

            :param root: The parent tk object.
            :param manager: - An instance of SimManager
            :param config: - A dictionary with configuration parameters
        '''
        
        # TODO: support drawing a background image?

        self.manager = manager
        self.elements = []      # robots, walls, missles, etc
        
        field_size = config.get('dimensions', [27, 54])
        px_per_ft = config.get('px_per_ft', 10)
        
        # setup board characteristics -- cell size is 1ft
        self.cols, self.rows = field_size
        self.margin = 5
        self.cellSize = px_per_ft
        self.canvasWidth = 2*self.margin + self.cols*self.cellSize
        self.canvasHeight = 2*self.margin + self.rows*self.cellSize
        
        self.canvas = tk.Canvas(root, width=self.canvasWidth, height=self.canvasHeight)
        self.canvas.bind("<Key>", self.on_key_pressed)
        self.canvas.bind("<Button-1>", self.on_click)
        
        self.text_id = None
        
        # Draw the field initially
        self.draw_field()

        # Add custom field elements
        field_elements = DrawableElement(self.canvas, [0, 0, 0], scale=px_per_ft)
        for obj in config.get("objects", []):
            vertices = [(self.margin + int(pt[0]),
                        self.margin + int(pt[1])) for pt in obj['points']]
            field_elements.create_polygon(vertices, obj['color'])
        self.elements.append(field_elements)

        # Add robots
        for robot in manager.robots:
            self.elements.append(RobotElement(self.canvas, robot, px_per_ft))
    
    def grid(self, *args, **kwargs):
        self.canvas.grid(*args, **kwargs)
        
    def on_key_pressed(self, event):
        '''
            likely to take in a set of parameters to treat as up, down, left,
            right, likely to actually be based on a joystick event... not sure
            yet
        '''
        
        return
    
        # TODO
        
        if event.keysym == "Up":
            self.manager.set_joystick(0.0, -1.0, 0)
        elif event.keysym == "Down":
            self.manager.set_joystick(0.0, 1.0, 0)
        elif event.keysym == "Left":
            self.manager.set_joystick(-1.0, 0.0, 0)
        elif event.keysym == "Right":
            self.manager.set_joystick(1.0, 0.0, 0)
            
        elif event.char == " ":
            mode = self.manager.get_mode()
            if mode == self.manager.MODE_DISABLED:
                self.manager.set_mode(self.manager.MODE_OPERATOR_CONTROL)
            else:
                self.manager.set_mode(self.manager.MODE_DISABLED)
    
    def on_click(self, event):
        self.canvas.focus_set()
    
    def update_widgets(self):
        for element in self.elements:
            element.update_canvas()
            
    def draw_field(self):
        for row in range(self.rows):
            for col in range(self.cols):
                self.draw_board_cell(row, col)
            
    def draw_board_cell(self, row, col):
        left = self.margin + col * self.cellSize
        right = left + self.cellSize
        top = self.margin + row * self.cellSize
        bottom = top + self.cellSize
        self.canvas.create_rectangle(left, top, right, bottom, outline="#ccc", fill="#fff")
