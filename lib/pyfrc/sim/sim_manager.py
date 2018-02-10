
import threading


class SimManager(object):
    '''
        This holds the current mode for all robots, and holds all robot controllers
        
        We use this so that in the future we can have multiple robots.
    '''
    
    MODE_DISABLED = 0
    MODE_AUTONOMOUS = 1
    MODE_OPERATOR_CONTROL = 2
    MODE_TEST = 3
    
    mode_map = {MODE_DISABLED: 'Disabled',
                MODE_AUTONOMOUS: 'Autonomous',
                MODE_OPERATOR_CONTROL: 'OperatorControl',
                MODE_TEST: 'Test'}
    
    def __init__(self):
        
        self.mode = SimManager.MODE_DISABLED
        self.mode_callback = None
        
        self.robots = []
            
        # any data shared with ui must be protected by
        # this since it's running in a different thread
        self._lock = threading.RLock()
        
        # This only gets set on the robot when transitioning into autonomous mode
        # -> reflects the alleged behavior of the FMS
        self.game_specific_message = ''
    
    #
    # Initialization
    #
    
    def add_robot(self, controller):
        '''Add a robot controller'''
        
        # connect to the controller
        # -> this is to support module robots
        controller.on_mode_change(self._on_robot_mode_change)
        self.robots.append(controller)
    
    def _on_robot_mode_change(self, mode):
        
        # TODO: With multiple robots, this isn't actually valid
        with self._lock:
            self.mode = mode
            
        if self.mode_callback:
            self.mode_callback(mode)
    
    #
    # API used by the RobotField class
    #
    
    def is_alive(self):
        for robot in self.robots:
            if not robot.is_alive():
                return False
        return True
    
    def on_mode_change(self, callable):
        '''When the robot mode changes, call the function with the mode'''
        with self._lock:
            self.mode_callback = callable
    
    def set_joystick(self, x, y, n):
        '''
            Receives joystick values from the SnakeBoard
            
            x,y      Coordinates
            n        Robot number to give it to
        '''
        self.robots[n].set_joystick(x, y)
            
    def set_mode(self, mode):
        
        if mode not in [SimManager.MODE_DISABLED,
                        SimManager.MODE_AUTONOMOUS,
                        SimManager.MODE_OPERATOR_CONTROL,
                        SimManager.MODE_TEST]:
            raise ValueError("Invalid value for mode: %s" % mode)
        
        with self._lock:
            old_mode = self.mode
            self.mode = mode
            callback = self.mode_callback
            
            for robot in self.robots:
                robot.set_mode(mode, self.game_specific_message)
            
        # don't call from inside the lock
        if old_mode != mode and callback is not None:
            callback(mode)

    def get_mode(self):
        with self._lock:
            return self.mode
        
