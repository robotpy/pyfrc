
from .elements import CompositeElement, DrawableElement


class RobotElement(CompositeElement):
    '''
        TODO: allow user customization
    '''
    
    def __init__(self, controller):
        
        super().__init__()
        
        self.controller = controller
        self.controller.robot_face = 0
        self.position = (0, 0, 0)
        
        
        # create a bunch of drawable objects that represent the robot
        pts = [(200, 200), (230,200), (230,230), (200,230)]
        center = (215,215)
        
        robot = DrawableElement(pts, center, 0, 'red')
        self.elements.append(robot)
        
        pts = [(200, 200), (230, 215), (200, 230)]
        robot_pt = DrawableElement(pts, center, 0, 'green')
        self.elements.append(robot_pt)
    
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
        
        dx = x - ox
        dy = y - oy
        da = a - oa 
        
        if da != 0:
            self.rotate(da)
        
        self.move((dx, dy))
        
        self.position = x, y, a
        
        
        
        
