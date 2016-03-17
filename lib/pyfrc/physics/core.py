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
       currently assumes that you are only calling :func:`wpilib.Timer.delay`
       once per main loop iteration. If you do it more than that, you may get
       some rather funky results.

    By default, pyfrc doesn't modify any of your inputs/outputs without being
    told to do so by your code or the simulation GUI.
    
    See the physics sample for more details.

    Enabling physics support
    ------------------------

    You must create a python module called ``physics.py`` next to your 
    ``robot.py``. A physics module must have a class called
    :class:`PhysicsEngine` which must have a function called ``update_sim``.
    When initialized, it will be passed an instance of this object.
    
    You must also create a 'sim' directory, and place a ``config.json``
    file there, with the following JSON information::
    
        {
          "pyfrc": {
            "robot": {
              "w": 2,
              "h": 3,
              "starting_x": 2,
              "starting_y": 20,
              "starting_angle": 0
            },
            "field": {
              "w": 25,
              "h": 27,
              "px_per_ft": 10
            }
          }
        }
    
'''

import imp
import math
from os.path import exists, join
import threading

import logging
logger = logging.getLogger('pyfrc.physics')

from hal_impl.data import hal_data


class PhysicsInitException(Exception):
    pass

class PhysicsEngine:
    '''
        Your physics module must contain a class called ``PhysicsEngine``, 
        and it must implement the same functions as this class.
        
        Alternatively, you can inherit from this object. However, that is
        not required.
    '''

    def __init__(self, physics_controller):
        '''
            The constructor must take the following arguments:
            
            :param physics_controller: The physics controller interface
            :type  physics_controller: :class:`.PhysicsInterface`
        '''
        self.physics_controller = physics_controller
        
    def initialize(self, hal_data):
        '''
            Called with the hal_data dictionary before the robot has started
            running. Some values may be overwritten when devices are
            initialized... it's not consistent yet, sorry.
        '''
        pass

    def update_sim(self, hal_data, now, tm_diff):
        '''
            Called when the simulation parameters for the program need to be
            updated. This is mostly when ``wpilib.Timer.delay()`` is called.
            
            :param hal_data: A giant dictionary that has all data about the robot. See
                             ``hal-sim/hal_impl/data.py`` in robotpy-wpilib's repository
                             for more information on the contents of this dictionary.
            :param now: The current time
            :type  now: float
            :param tm_diff: The amount of time that has passed since the last
                            time that this function was called
            :type  tm_diff: float
        '''
        pass


#def _create_wrapper(cls, fname, new_fn, old_fn):
#    setattr(cls, fname, lambda s, *args, **kwargs: new_fn(s, lambda *oargs, **okwargs: old_fn(s, *oargs, **okwargs), *args, **kwargs))

class PhysicsInterface:
    '''
        An instance of this is passed to the constructor of your
        :class:`PhysicsEngine` object. This instance is used to communicate
        information to the simulation, such as moving the robot on the
        field displayed to the user.
    '''
    
    def __init__(self, robot_path, fake_time, config_obj):
        self.last_tm = None
        self._lock = threading.Lock()
        
        # These are in units of feet relative to the field
        self.x = config_obj['pyfrc']['robot']['starting_x']
        self.y = config_obj['pyfrc']['robot']['starting_y']
        self.angle = math.radians(config_obj['pyfrc']['robot']['starting_angle'])
        
        # HACK: Used for drawing
        self.vx = 0
        self.vy = 0
        
        self.fake_time = fake_time
        self.robot_enabled = False
        
        self.config_obj = config_obj
        self.engine = None
        self.analog_gyro_channels = []
        self.device_gyro_channels = []
        
        self.hal_data = hal_data
        
        physics_module_path = join(robot_path, 'physics.py')
        if exists(physics_module_path):
            
            # Load the user's physics module if it exists
            try:
                physics_module = imp.load_source('physics', physics_module_path)
            except:
                logger.exception("Error loading user physics module")
                raise PhysicsInitException()
            
            if not hasattr(physics_module, 'PhysicsEngine'):
                logger.error("User physics module does not have a PhysicsEngine object")
                raise PhysicsInitException()
            
            # for now, look for a class called PhysicsEngine
            try:
                self.engine = physics_module.PhysicsEngine(self)
                
                if hasattr(self.engine, 'initialize'):
                    self.engine.initialize(self.hal_data)
                
            except:
                logger.exception("Error creating user's PhysicsEngine object")
                raise PhysicsInitException()
            
            logger.info("Physics support successfully enabled")
            
        else:
            logger.warning("Cannot enable physics support, %s not found", physics_module_path)
            
    def setup_main_thread(self):
        if self.engine is not None:
            self.fake_time.set_physics_fn(self._on_increment_time)
            
    def __repr__(self):
        return 'Physics'
    
    def _on_increment_time(self, now):
        
        last_tm = self.last_tm
        
        if last_tm is None:
            self.last_tm = now
        else:
        
            # When using time, always do it based on a differential! You may
            # not always be called at a constant rate
            tm_diff = now - last_tm
            
            # Don't run physics calculations more than 100hz
            if tm_diff > 0.010:
                self.engine.update_sim(self.hal_data, now, tm_diff)
                self.last_tm = now
        
    def _set_robot_enabled(self, enabled):
        self.robot_enabled = enabled
        
    def _has_engine(self):
        return self.engine is not None
              
    #######################################################
    #
    # Public API
    #
    #######################################################
    
    
    def add_analog_gyro_channel(self, ch):
        '''
            If you want to enable a wpilib :class:`.AnalogGyro` object to
            be updated when the robot rotates, add the channel number via
            this function.
            
            :param ch: Analog input channel that the gyro is on
            :type  ch: int
        '''
        
        # TODO: use hal_data to detect gyros
        self.analog_gyro_channels.append(ch)
        
    # deprecated alias
    add_gyro_channel = add_analog_gyro_channel
    
    def add_device_gyro_channel(self, angle_key):
        '''
            :param angle_key: The name of the angle key in ``hal_data['robot']``
        '''
        
        # TODO: use hal_data to detect gyros
        hal_data['robot'][angle_key] = 0
        self.device_gyro_channels.append(angle_key)
    
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
        
        self._move(x, y, angle)
            
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
        
        self._move(x, y, angle)
    
    def _move(self, x, y, angle):
        # x, y, and angle are all relative to the robot
        
        with self._lock: 
            self.vx += x
            self.vy += y
            self.angle += angle
            
            c = math.cos(self.angle)
            s = math.sin(self.angle)
            
            self.x += (x*c - y*s)
            self.y += (x*s + y*c)
            
            self._update_gyros(angle)
        
    def _update_gyros(self, angle):
        
        angle = math.degrees(angle)
        
        for k in self.device_gyro_channels:
            self.hal_data['robot'][k] += angle
        
        # XXX: for now, use a constant to compute the output voltage
        #      .. however, we should do the actual calculation at some point?
        
        gyro_value =  angle / 2.7901785714285715e-12
        
        for gyro_ch in self.analog_gyro_channels:
            self.hal_data['analog_in'][gyro_ch]['accumulator_value'] += gyro_value
    
    def get_position(self):
        '''
            :returns: Robot's current position on the field as `(x,y,angle)`.
                      `x` and `y` are specified in feet, `angle` is in radians
        '''
        with self._lock:
            return self.x, self.y, self.angle
    
    def _get_vector(self):
        '''
            :returns: The sum of all movement vectors, not very useful
                      except for getting the difference of them
        '''
        return self.vx, self.vy, self.angle
        
    