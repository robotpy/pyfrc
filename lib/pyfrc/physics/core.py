
'''
    TODO: a better way to implement this is have something track all of
    the input values, and have that in a data structure, while also
    providing the override capability.
'''

import inspect
import math
import threading

def _create_wrapper(cls, fname, new_fn, old_fn):
    setattr(cls, fname, lambda s, *args, **kwargs: new_fn(s, lambda *oargs, **okwargs: old_fn(s, *oargs, **okwargs), *args, **kwargs))

class Physics(object):
    
    def __init__(self):
        self.last_tm = None
        self._lock = threading.Lock()
        
        self.x = 0
        self.y = 0
        self.angle = 0
        
        self.robot_enabled = False
    
    def setup(self, physics):
        '''
            Pass your physics module to this function, and it will initialize
            wpilib patches and setup your callbacks.
            
            A physics module must have a class called `PhysicsEngine` which
            must have a function called update_sim. When initialized, it will
            be passed an instance of this object, which can also be found at
            wpilib.internal.physics_control
        '''
        
        # avoid circular import problems
        from .. import wpilib
        self.fake_time = wpilib._wpilib._fake_time.FAKETIME
    
        # for now, look for a class called PhysicsEngine
        self.engine = physics.PhysicsEngine(self)
        
        print("Initializing physics patching")
        
        # iterate the methods, monkeypatch them in
        for name, new_fn in inspect.getmembers(self.engine, predicate=inspect.ismethod):
            if not name.startswith('sim_'):
                continue
            
            # determine which class to override
            name_c = name.split('_')
            if len(name_c) != 3:
                raise ValueError("%s is not a valid sim method name" % name)
        
            ignore, clsname, fname = name_c
        
            cls = getattr(wpilib, clsname, None)
            if cls is None or not inspect.isclass(cls):
                raise AttributeError("%s does not specify a valid class name" % name)
        
            old_fn = getattr(cls, fname, None)
            if old_fn is None:
                raise AttributeError("%s does not specify a valid attribute of %s" % (name, clsname))
            
            # TODO: inspect function and make sure it complies with the interface
            
            _create_wrapper(cls, fname, new_fn, old_fn)
            
            print("->", name, "patches %s.%s" % (clsname, fname))
        
        #
        # setup the update_sim function
        # -> TODO: this is bad form, provide a hook somewhere or something
        #    how to chain these together without breaking existing tests?
        #
        
        self.old_wait = wpilib.Wait
        wpilib.Wait = self._wait_wrapper
        
        print("Physics initialized")
        
    def _wait_wrapper(self, tm):
        now = self.fake_time.Get()
        
        last_tm = self.last_tm
        self.last_tm = tm
        
        if last_tm is not None:
        
            # When using time, always do it based on a differential! You may
            # not always be called at a constant rate
            tm_diff = tm - last_tm
            
            self.engine.update_sim(now, tm_diff)
        
        self.old_wait(tm)
        
    def _set_robot_enabled(self, enabled):
        self.robot_enabled = enabled
            
    #######################################################
    #
    # Public API
    #
    #######################################################
    
    def drive(self, speed, yaw):
        '''Call this from your update_sim function. Will update the
           robot's position accordingly
           
           The outputs of the drivetrains.* functions should be passed
           to this function. When implementing your own versions of those,
           take care to adjust the speed/yaw values based on time.
           
           .. only allows driving in a 2D direction at the moment
           .. TODO: collisions?
        '''
        
        # if the robot is disabled, don't do anything
        if not self.robot_enabled:
            return
            
        # todo: tunable constants for weight, whatever
        angle = yaw * 100
        x = 20*speed*math.cos(angle)
        y = 20*speed*math.sin(angle)
        
        # something here
        with self._lock:
            self.x += x
            self.y += y 
            self.angle += angle
        
    def get_position(self):
        '''Returns robot's current position as x,y,angle. angle is in radians'''
        with self._lock:
            return self.x, self.y, self.angle
    
        
    