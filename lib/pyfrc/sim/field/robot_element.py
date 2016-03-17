
from .elements import CompositeElement, DrawableElement

import math

class RobotElement(CompositeElement):
    '''
        TODO: allow user customization
    '''
    
    def __init__(self, controller, config_obj):
        
        super().__init__()
        
        # Load params from the user's sim/config.json
        px_per_ft = config_obj['pyfrc']['field']['px_per_ft']
        
        robot_w = config_obj['pyfrc']['robot']['w']
        robot_h = config_obj['pyfrc']['robot']['h']
        center_x = config_obj['pyfrc']['robot']['starting_x']
        center_y = config_obj['pyfrc']['robot']['starting_y']
        angle = math.radians(config_obj['pyfrc']['robot']['starting_angle'])
        
        self.controller = controller
        self.controller.robot_face = 0
        self.px_per_ft = px_per_ft
        
        robot_w *= px_per_ft
        robot_h *= px_per_ft
        center_x *= px_per_ft
        center_y *= px_per_ft
        
        # drawing hack
        self._vector = (0, 0, angle)
        
        # create a bunch of drawable objects that represent the robot
        center = (center_x, center_y)
        pts = [
            (center_x - robot_w/2, center_y - robot_h/2),
            (center_x + robot_w/2, center_y - robot_h/2),
            (center_x + robot_w/2, center_y + robot_h/2),
            (center_x - robot_w/2, center_y + robot_h/2),
        ]
        
        robot = DrawableElement(pts, center, 0, 'red')
        self.elements.append(robot)
        
        pts = [
            (center_x - robot_w/2, center_y - robot_h/2),
            (center_x + robot_w/2, center_y),
            (center_x - robot_w/2, center_y + robot_h/2),
        ]
        
        robot_pt = DrawableElement(pts, center, 0, 'green')
        self.elements.append(robot_pt)
        
        if angle != 0:
            self.rotate(angle)
    
    def perform_move(self):
        
        if not self.controller.is_alive():
            self.elements[1].set_color('gray')
        
        # query the controller for move information
        self.move_robot()
        
        # finally, call the superclass to actually do the drawing
        self.update_coordinates()
        
        
    def move_robot(self):
        
        px_per_ft = self.px_per_ft
        
        x, y, a = self.controller._get_vector()    # units: ft
        ox, oy, oa = self._vector                  # units: px
        
        x *= px_per_ft
        y *= px_per_ft
        
        dx = x - ox
        dy = y - oy
        da = a - oa

        
        if da != 0:
            self.rotate(da)
        
        self.move((dx, dy))
        
        self._vector = x, y, a
        
        
        
