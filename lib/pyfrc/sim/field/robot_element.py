
from .elements import CompositeElement, DrawableElement

import math

class RobotElement(CompositeElement):
    '''
        TODO: allow user customization
    '''
    
    def __init__(self, controller, px_per_ft):
        
        super().__init__()
        
        self.controller = controller
        self.controller.robot_face = 0
        self.position = (0, 0, 0)
        self.px_per_ft = px_per_ft
        
        # get robot starting position, size from physics engine
        robot_params = self.controller.physics_controller._get_robot_params()
        robot_w, robot_h, center_x, center_y, angle = robot_params[:5]
        
        robot_w *= px_per_ft
        robot_h *= px_per_ft
        center_x *= px_per_ft
        center_y *= px_per_ft
        
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
            self.rotate(math.radians(angle))
    
    def perform_move(self):
        
        if not self.controller.is_alive():
            self.elements[1].set_color('gray')
        
        # query the controller for move information
        self.move_robot()
        
        # finally, call the superclass to actually do the drawing
        self.update_coordinates()
        
        
    def move_robot(self):
        
        x, y, a = self.controller.get_position()
        ox, oy, oa = self.position
        
        x *= self.px_per_ft
        y *= self.px_per_ft
        
        dx = x - ox
        dy = y - oy
        da = a - oa
        
        if da != 0:
            self.rotate(da)
        
        self.move((dx, dy))
        
        self.position = x, y, a
        
        
        
        
