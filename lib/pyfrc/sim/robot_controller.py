
from hal_impl import mode_helpers

import threading
import time

import wpilib

from .sim_manager import SimManager

class RobotController:
    '''
        This manages the active state of the robot. At the moment, this
        isn't coded as a singleton, but because of the references to 
        wpilib.internal, it's essentially a singleton.
    '''
    
    mode_map = {
        SimManager.MODE_AUTONOMOUS: "Autonomous",
        SimManager.MODE_DISABLED: "Disabled",
        SimManager.MODE_OPERATOR_CONTROL: "OperatorControl",
        SimManager.MODE_TEST: "Test"
    }
    
    def __init__(self, robot_class, fake_time):
    
        self.mode = SimManager.MODE_DISABLED
        self.mode_callback = None
        
        self.robot_class = robot_class
        self.fake_time = fake_time
        
        #self.physics_controller = _wpilib.internal.physics_controller
        
        # any data shared with the ui must be protected by
        # this since it's running in a different thread
        self._lock = threading.RLock()
        
        self.thread = threading.Thread(target=self._robot_thread)
        self.thread.daemon = True
        
        self.ds_thread = threading.Thread(target=self._ds_thread)
        self.ds_thread.daemon = True
        
    def run(self):
        self._run_code = True
        self.thread.start()
        self.ds_thread.start()
        
    def stop(self):
        
        # Since we're using OperatorControl, there isn't a way to kill
        # the robot. Just exit and hopefully everything is ok
        return True
        
        #with self._lock:
        #    self._run_code = False
        
            # if the robot code is spinning in any of the modes, then
            # we need to change the mode so it returns back to us
        #    if self.mode == SimManager.MODE_DISABLED:
        #        self.mode = SimManager.MODE_OPERATOR_CONTROL
        #    else:
        #        self.mode = SimManager.MODE_DISABLED
        
        # resume the robot just in case it's hung somewhere
        #self.fake_time.resume()
        
        #try:
        #    self.thread.join(timeout=5.0)
        #except RuntimeError:
        #    return False
        
        #return not self.thread.is_alive()
        
    #
    # API used by the ui
    #
    
    def has_physics(self):
        return self.physics_controller._has_engine()
    
    def is_alive(self):
        return self.thread.is_alive()
    
    def on_mode_change(self, callable):
        '''When the robot mode changes, call the function with the mode'''
        with self._lock:
            self.mode_callback = callable
    
    def set_joystick(self, x, y):
        '''
            Receives joystick values from the ui
            
            TODO: needs to be more sophisticated to drive mechanum
        '''
        with self._lock:
            
            joysticks = self.physics_controller._get_robot_params()[5]
            
            if len(joysticks) == 1:
                
                # Single stick drive
                drive_stick = self.driver_station.sticks[joysticks[0]-1]
                drive_stick[0] = x
                drive_stick[1] = y
                
            elif len(joysticks) == 2:
                
                # Tank drive
                drive_stick1 = self.driver_station.sticks[joysticks[0]-1]
                drive_stick2 = self.driver_station.sticks[joysticks[1]-1]
                
                l = x - y
                r = x + y
                
                drive_stick1[1] = -l
                drive_stick2[1] = r
                
            else:
                
                raise ValueError("Invalid joystick values")
                
            
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
            
            #self.physics_controller._set_robot_enabled(mode != SimManager.MODE_DISABLED)
            
            if callback is not None:
                callback(mode)

    def get_mode(self):
        with self._lock:
            return self.mode
        
    def get_position(self):
        '''Returns x,y,angle'''
        return self.physics_controller.get_position()
        
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
        
        # setup things for the robot
        self.driver_station = wpilib.DriverStation.getInstance()
        
        try:
            wpilib.RobotBase.main(self.robot_class)
        finally:
            self.set_mode(SimManager.MODE_DISABLED)
