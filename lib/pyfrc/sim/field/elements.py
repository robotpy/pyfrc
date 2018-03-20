

# TODO: Not complete yet, this is just a bunch of ideas

import math


class DrawableElement(object):
    '''
        Represents some polygon on the canvas that can move around and such
    '''

    def __init__(self, pts, center, angle, color):
        
        self.color = color
        self.pts = pts          # list of (x,y)
        self.center = center    # (x,y)
        self.angle = angle      # radians
        
    @property
    def flat_pts(self):
        '''Converts points into a flat list'''
        return [c for p in self.pts for c in p]
    
    def delete(self):
        if hasattr(self, 'id'):
            self.canvas.delete(self.id)

    def initialize(self, canvas):
        
        self.canvas = canvas
        self.id = self.canvas.create_polygon(*self.pts, fill=self.color)
                    
        
    def intersects(self):
        # TODO:
        pass
        
    def move(self, v):
        '''v is a tuple of x/y coordinates to move object'''
        
        # rotate movement vector according to the angle of the object
        vx, vy = v
        vx, vy = vx*math.cos(self.angle) - vy*math.sin(self.angle), \
                 vx*math.sin(self.angle) + vy*math.cos(self.angle)
                 
        def _move(xy):
            x, y = xy
            return x+vx, y+vy
            
        # TODO: detect other objects in the way, stop movement appropriately
            
        self.pts = [p for p in map(lambda x: _move(x), self.pts)]
        self.center = _move(self.center)
        
        
    def rotate(self, angle):
        '''
            This works. Rotates the object about its center.
            
            Angle is specified in radians
        '''
        
        self.angle = (self.angle + angle) % (math.pi*2.0)
        
        # precalculate these parameters
        c = math.cos(angle)
        s = math.sin(angle)
        px, py = self.center
    
        def _rotate_point(xy):

            x, y = xy
            
            x = x - px
            y = y - py
            
            return (x*c - y*s)+px, (x*s + y*c)+py
    
        # calculate rotation for each point
        self.pts = [p for p in map(lambda x: _rotate_point(x), self.pts)]
        
    def set_color(self, color):
        self.color = color
        self.canvas.itemconfig(self.id, fill=color)
        
    def update_coordinates(self):
    
        # flatten the list of coordinates
        if hasattr(self, 'canvas'):
            self.canvas.coords(self.id, *self.flat_pts)
        
    def perform_move(self):
        self.update_coordinates()
        
class CompositeElement(object):
    '''A composite element can contain a number of drawable elements, and
       all of them move at the same time, and deal with collisions and
       such at the same time'''
    
    
    def __init__(self):
        self.elements = []
    
    def initialize(self, canvas):
        for e in self.elements:
            e.initialize(canvas)
            
    # TODO: I feel these may not be necessary?
            
    def move(self, v):
        for e in self.elements:
            e.move(v)
            
    def rotate(self, angle):
        for e in self.elements:
            e.rotate(angle)
    
    def update_coordinates(self):
        for e in self.elements:
            e.update_coordinates()


class DrawableLine(DrawableElement):
    '''
        Represents some line drawn on the canvas
    '''
    def __init__(self, pts, color, tkargs):
        super().__init__(pts, pts[0], 0, color)
        self.tkargs = tkargs.copy()
    
    def initialize(self, canvas):
        self.canvas = canvas
        self.tkargs['fill'] = self.color
        self.id = self.canvas.create_line(self.flat_pts, **self.tkargs)


class TextElement(DrawableElement):
    '''
        An element that shows text
    '''
    
    def __init__(self, text, center, angle, color, fontSize, **kwargs):
        super().__init__([center], center, angle, color)
        self.text = text
        self.fontSize = fontSize
        self.tkargs = kwargs.copy()
        
    def initialize(self, canvas):
        self.canvas = canvas
        x, y = self.center
        self.id = self.canvas.create_text(x, y, text=self.text,
                                          font=("Helvetica", self.fontSize, "bold"),
                                          **self.tkargs)
        
        self.set_color(self.color)

    def perform_move(self):
        pass
