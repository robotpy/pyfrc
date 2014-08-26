
import tkinter as tk


class RobotField(object):
    
    def __init__(self, root, manager, field_size):
        '''
            initializes all default values and creates 
            a board, waits for run() to be called
            to start the board
            
            manager - sim manager class instance
            board_size - a tuple with values (rows, cols)
        '''
        
        # TODO: support drawing an actual field?
        
        self.manager = manager
        self.elements = []      # robots, walls, missles, etc
        
        # setup board characteristics
        self.rows, self.cols = field_size
        self.margin = 5
        self.cellSize = 30
        self.canvasWidth = 2*self.margin + self.cols*self.cellSize
        self.canvasHeight = 2*self.margin + self.rows*self.cellSize
        
        self.canvas = tk.Canvas(root, width=self.canvasWidth, height=self.canvasHeight)
        
        self.text_id = None
        
        # Draw the field initially
        self.draw_field()
        
    def add_moving_element(self, element):
        '''Add elements to the board'''
        
        element.initialize(self.canvas)
        self.elements.append(element)
    
    def grid(self, *args, **kwargs):
        self.canvas.grid(*args, **kwargs)
    
    def update_widgets(self):
        
        # TODO: process collisions and such too
        
        for element in self.elements:
            element.perform_move()
            
    def draw_field(self):
        for row in range(self.rows):
            for col in range(self.cols):
                self.draw_board_cell(row, col, "white")
            
    def draw_board_cell(self, row, col, color):
        left = self.margin + col * self.cellSize
        right = left + self.cellSize
        top = self.margin + row * self.cellSize
        bottom = top + self.cellSize
        self.canvas.create_rectangle(left, top, right, bottom, fill=color)
