'''
    pyfrc supports simplistic custom physics model implementations for
    simulation and testing support. It can be as simple or complex as you want
    to make it. We will continue to add helper functions (such as the 
    :mod:`pyfrc.physics.drivetrains` module) to make this a lot easier
    to do. General purpose physics implementations are welcome also!

    The idea is you provide a :class:`PhysicsEngine` object that overrides specific
    pieces of WPILib, and modifies motors/sensors accordingly depending on the
    state of the simulation. An example of this would be measuring a motor
    moving for a set period of time, and then changing a limit switch to turn 
    on after that period of time. This can help you do more complex simulations
    of your robot code without too much extra effort.

    .. note::

       One limitation to be aware of is that the physics implementation
       currently assumes that you are only calling :func:`wpilib.Wait` once
       per main loop iteration. If you do it more than that, you may get some
       rather funky results.

    By default, pyfrc doesn't modify any of your inputs/outputs without being
    told to do so by your code or the simulation GUI, except for :class:`wpilib.Gyroscope`.
    When you update the robot's position using :func:`Physics.drive` or
    :func:`Physics.vector_drive`, the simulation will automatically update
    the robot angle in any :class:`wpilib.Gyroscope` objects that have been
    created.

    See the physics sample for more details. The API has changed a bit as of 
    pyfrc 2014.7.0

    Enabling physics support
    ------------------------

    You must create a python module (for example, physics.py), and import
    it in your __main__ block in robot.py. The imported module must be passed
    to :func:`wpilib.internal.physics_controller.setup`. Your __main__ block
    should end up looking something like this::

        if __name__ == '__main__':
            
            wpilib.require_version('2014.7.2')
            
            import physics
            wpilib.internal.physics_controller.setup(physics)
            
            wpilib.run()

    A physics module must have a class called :class:`PhysicsEngine` which
    must have a function called update_sim. When initialized, it will
    be passed an instance of this object, which can also be found at
    :obj:`wpilib.internal.physics_control`
'''

# TODO: a better way to implement this is have something track all of
# the input values, and have that in a data structure, while also
# providing the override capability.

import inspect
import math
import threading


class PhysicsEngine(object):
    '''
        Your physics module must contain a class called PhysicsEngine, 
        and it must implement the same functions as this class.

        The constructor must take the following parameters:

        :param physics_controller: An instance of :class:`Physics`
    '''

    #: Width/height of robot in feet
    ROBOT_WIDTH = 2

    #: Height of the robot specified in feet
    ROBOT_HEIGHT = 3
    
    #: Starting X position of robot on the field, in feet
    ROBOT_STARTING_X = 18.5

    #: Starting Y position of robot on the field, in feet
    ROBOT_STARTING_Y = 12
    
    #: Starting angle of robot in degrees; 0 is east, 90 is south
    STARTING_ANGLE = 180

    def __init__(self, physics_controller):
        self.physics_controller = physics_controller

    def update_sim(self, now, tm_diff):
        '''
            Called when the simulation parameters for the program need to be
            updated. This is mostly when wpilib.Wait is called.
            
            :param now: The current time as a float
            :param tm_diff: The amount of time that has passed since the last
                            time that this function was called
        '''
        pass


def _create_wrapper(cls, fname, new_fn, old_fn):
    setattr(cls, fname, lambda s, *args, **kwargs: new_fn(s, lambda *oargs, **okwargs: old_fn(s, *oargs, **okwargs), *args, **kwargs))

class Physics(object):
    '''
        An instance of this is passed to the constructor of your
        :class:`PhysicsEngine` object. This instance is used to communicate
        information to the simulation, such as moving the robot on the
        field displayed to the user.
    '''
    
    def __init__(self):
        self.last_tm = None
        self._lock = threading.Lock()
        
        self.x = 0
        self.y = 0
        self.angle = 0
        
        self.robot_enabled = False
        
        self.engine = None

    def __repr__(self):
        return 'Physics'
    
    def setup(self, physics):
        '''
            Pass your physics module to this function, and it will initialize
            the :class:`PhysicsEngine` instance, setup wpilib patches and 
            your simulation callbacks.
        '''
        
        # avoid circular import problems
        from .. import wpilib
        self.gyro_class = wpilib.Gyro
    
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
        
    def _wait_wrapper(self, wait_tm):
        
        if not hasattr(self, 'fake_time'):
            from .. import wpilib
            self.fake_time = wpilib._wpilib._fake_time.FAKETIME
                
        now = self.fake_time.Get()
        
        last_tm = self.last_tm
        self.last_tm = now
        
        
        if last_tm is not None:
        
            # When using time, always do it based on a differential! You may
            # not always be called at a constant rate
            tm_diff = now - last_tm
            
            self.engine.update_sim(now, tm_diff)
        
        self.old_wait(wait_tm)
        
    def _set_robot_enabled(self, enabled):
        self.robot_enabled = enabled
        
    def _has_engine(self):
        return self.engine is not None
        
    def _get_robot_params(self):
        '''
            :returns: a tuple of 
                (robot_width,      # in feet
                robot_height,      # in feet
                starting_x,        # center of robot
                starting_y,        # center of robot
                starting_angle,    # in degrees (0 is east, 90 is south)
                joysticks)         # joystick numbers that driving uses
        '''
        
        engine = self.engine
        if engine is None:
            engine = object()
        
        return (getattr(engine, 'ROBOT_WIDTH', 2),
                getattr(engine, 'ROBOT_HEIGHT', 3),
                getattr(engine, 'ROBOT_STARTING_X', 18.5),
                getattr(engine, 'ROBOT_STARTING_Y', 12),
                getattr(engine, 'STARTING_ANGLE', 180),
                getattr(engine, 'JOYSTICKS', [1]))
        
            
    #######################################################
    #
    # Public API
    #
    #######################################################
    
    def drive(self, speed, rotation_speed, tm_diff):
        '''Call this from your :func:`PhysicsEngine.update_sim` function.
           Will update the robot's position on the simulation field.

           You can either calculate the speed & rotation manually, or you
           can use the predefined functions in :mod:`pyfrc.physics.drivetrains`.
           
           The outputs of the `drivetrains.*` functions should be passed
           to this function.

           .. note:: The simulator currently only allows 2D motion
           
           :param speed:           Speed of robot in ft/s
           :param rotation_speed:  Clockwise rotational speed in radians/s
           :param tm_diff:         Amount of time speed was traveled (this is the 
                                   same value that was passed to update_sim)
        '''
        
        # if the robot is disabled, don't do anything
        if not self.robot_enabled:
            return
        
        distance = speed * tm_diff 
        angle = rotation_speed * tm_diff
        
        x = distance*math.cos(angle)
        y = distance*math.sin(angle)
        
        # something here
        with self._lock:
            self.x += x
            self.y += y 
            self.angle += angle
            
            self._update_gyros(angle)
            
    def vector_drive(self, vx, vy, vw, tm_diff):
        '''Call this from your :func:`PhysicsEngine.update_sim` function.
           Will update the robot's position on the simulation field.
           
           This moves the robot using a vector relative to the robot
           instead of by speed/rotation speed.
           
           :param vx: Speed in x direction relative to robot in ft/s
           :param vy: Speed in y direction relative to robot in ft/s
           :param vw: Clockwise rotational speed in rad/s
           :param tm_diff:         Amount of time speed was traveled
        '''
        
        # if the robot is disabled, don't do anything
        if not self.robot_enabled:
            return
        
        angle = vw * tm_diff
        vx = (vx * tm_diff)
        vy = (vy * tm_diff)

        x = vx*math.sin(angle) + vy*math.cos(angle)
        y = vx*math.cos(angle) + vy*math.sin(angle)
        
        with self._lock:
            self.x += x
            self.y += y
            self.angle += angle
                 
            self._update_gyros(angle)
            
    def _update_gyros(self, angle):
        # must be called while holding the lock
        
        gyro_value = math.degrees(angle)
        for gyro in self.gyro_class._all_gyros:
            gyro.value += gyro_value
    
    def get_position(self):
        '''
            :returns: Robot's current position on the field as `(x,y,angle)`.
                      `x` and `y` are specified in feet, `angle` is in radians
        '''
        with self._lock:
            return self.x, self.y, self.angle
    
        
    