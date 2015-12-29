from hal_impl import mode_helpers
from hal_impl.data import hal_data

import threading
import time
import wpilib
from .sim_manager import SimManager

class RobotController:
    '''
        This manages the active state of the robot
    '''

    mode_map = {
        SimManager.MODE_AUTONOMOUS: "Autonomous",
        SimManager.MODE_DISABLED: "Disabled",
        SimManager.MODE_OPERATOR_CONTROL: "OperatorControl",
        SimManager.MODE_TEST: "Test"
    }
    
    def __init__(self, robot_class, physics_class, fake_time, config):
        self.config = config
        self.mode = SimManager.MODE_DISABLED
        self.mode_callback = None
        
        self.robot_class = robot_class
        self.fake_time = fake_time

        # Initialize physics engine if provided
        self.physics_engine = None
        if physics_class is not None:
            self.physics_engine = physics_class(hal_data)
            self.physics_engine.set_state(config.get("init_state", {}))
        
        # any data shared with the ui must be protected by
        # this since it's running in a different thread
        self._lock = threading.RLock()
        
        self.thread = threading.Thread(target=self._robot_thread, name="Robot Thread")
        self.thread.daemon = True
        
        self.ds_thread = threading.Thread(target=self._ds_thread, name="Fake DS Thread")
        self.ds_thread.daemon = True
        
    def run(self):
        self._run_code = True
        self.thread.start()
        self.ds_thread.start()
    
    def wait_for_robotinit(self):
        
        # Do this so that we don't initialize the UI until robotInit is done
        while hal_data['user_program_state'] is None:
            time.sleep(0.025)
        
    #
    # API used by the ui
    #
    
    def has_physics(self):
        return self.physics_engine is not None
    
    def is_alive(self):
        return self.thread.is_alive()
    
    def on_mode_change(self, callable):
        '''When the robot mode changes, call the function with the mode'''
        with self._lock:
            self.mode_callback = callable
    
    def set_mode(self, mode):
        
        if mode not in [SimManager.MODE_DISABLED,
                        SimManager.MODE_AUTONOMOUS,
                        SimManager.MODE_OPERATOR_CONTROL,
                        SimManager.MODE_TEST]:
            raise ValueError("Invalid value for mode: %s" % mode)
        
        with self._lock:
            
            # TODO: need a way to notify the caller that the set failed. Perhaps an exception?
            if not self.is_alive():
                return
            
            old_mode = self.mode
            self.mode = mode
            callback = self.mode_callback
            
        # don't call from inside the lock
        if old_mode != mode:
            
            if mode == SimManager.MODE_DISABLED:
                mode_helpers.set_disabled()
            elif mode == SimManager.MODE_AUTONOMOUS:
                mode_helpers.set_autonomous(True)
            elif mode == SimManager.MODE_OPERATOR_CONTROL:
                mode_helpers.set_teleop_mode(True)
            elif mode == SimManager.MODE_TEST:
                mode_helpers.set_test_mode(True)
            
            if callback is not None:
                callback(mode)

    def get_mode(self):
        with self._lock:
            return self.mode

    def get_config(self):
        return self.config
        
    def get_state(self):
        """Returns the physics state dictionary"""
        if self.physics_engine is not None:
            return self.physics_engine.get_state()
        return {}

    def get_position(self):
        position_state = self.config.get("field_position_state", "drivetrain.position")
        state = self.get_state()
        for key in position_state.split("."):
            if key in state:
                state = state.get(key, None)
            if state is None:
                break
        return state

    def update_physics(self, dt):
        if self.physics_engine is not None:
            self.physics_engine.update_physics(hal_data, self.get_mode() != SimManager.MODE_DISABLED, dt)
        
    #
    # Runs the code
    #
    def _check_sleep(self, idx):
        '''This ensures that the robot code called Wait() at some point'''
        
        # TODO: There are some cases where it would be ok to do this... 
        if not self.fake_time.slept[idx]:
            errstr = '%s() function is not calling wpilib.Timer.delay() in its loop!' % self.mode_map[self.mode]
            raise RuntimeError(errstr)
            
        self.fake_time.slept[idx] = False
    
    def _ds_thread(self):
        
        # TODO: This needs to be fixed, breaks things when paused in IterativeRobot
        while True:
            time.sleep(0.020)
            mode_helpers.notify_new_ds_data()

    def _robot_thread(self):
        
        # Initialize physics time hook -- must be done on
        # robot thread, since it uses a threadlocal variable to work
        self.fake_time.set_physics_fn(self.update_physics)
        
        # setup things for the robot
        self.driver_station = wpilib.DriverStation.getInstance()
        
        try:
            wpilib.RobotBase.main(self.robot_class)
        finally:
            self.set_mode(SimManager.MODE_DISABLED)
