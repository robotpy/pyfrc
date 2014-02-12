'''
    This manages the active state of the robot
''' 

import sys
import threading
import time

from ..wpilib import _wpilib
from .sim_manager import SimManager

class RobotController(object):
    
    mode_map = {
        SimManager.MODE_AUTONOMOUS: "Autonomous",
        SimManager.MODE_DISABLED: "Disabled",
        SimManager.MODE_OPERATOR_CONTROL: "OperatorControl"
    }
    
    def __init__(self, myrobot):
    
        self.mode = SimManager.MODE_DISABLED
        self.mode_callback = None
        
        self.myrobot = myrobot
        
        # attach to the robot
        _wpilib.internal.on_IsEnabled = self.on_IsEnabled
        _wpilib.internal.on_IsAutonomous = self.on_IsAutonomous
        _wpilib.internal.on_IsOperatorControl = self.on_IsOperatorControl
        
        # any data shared with the ui must be protected by
        # this since it's running in a different thread
        self._lock = threading.RLock()
        
        self.thread = threading.Thread(target=self._robot_thread)
        self.thread.daemon = True
        
    def run(self):
        self._run_code = True
        self.thread.start()
        
    def stop(self):
        with self._lock:
            self._run_code = False
        
            # if the robot code is spinning in any of the modes, then
            # we need to change the mode so it returns back to us
            if self.mode == SimManager.MODE_DISABLED:
                self.mode = SimManager.MODE_OPERATOR_CONTROL
            else:
                self.mode = SimManager.MODE_DISABLED
        
        # resume the robot just in case it's hung somewhere
        _wpilib._fake_time.FAKETIME.Resume()
        
        try:
            self.thread.join(timeout=5.0)
        except RuntimeError:
            return False
        
        return not self.thread.is_alive()
        
    #
    # API used by the ui
    #
    
    def is_alive(self):
        return self.thread.is_alive()
    
    def on_mode_change(self, callable):
        '''When the robot mode changes, call the function with the mode'''
        with self._lock:
            self.mode_callback = callable
    
    def set_joystick(self, x, y):
        '''
            Receives joystick values from the ui
        '''
        with self._lock:
            drive_stick = self.driver_station.sticks[0]
            drive_stick[1] = x
            drive_stick[2] = y
            
    def set_mode(self, mode):
        
        if mode not in [SimManager.MODE_DISABLED, 
                        SimManager.MODE_AUTONOMOUS, 
                        SimManager.MODE_OPERATOR_CONTROL]:
            raise ValueError("Invalid value for mode: %s" % mode)
        
        with self._lock:
            
            # TODO: need a way to notify the caller that the set failed. Perhaps an exception?
            if not self.is_alive():
                return
            
            old_mode = self.mode
            self.mode = mode
            callback = self.mode_callback
            
        # don't call from inside the lock
        if old_mode != mode and callback is not None:
            callback(mode)

    def get_mode(self):
        with self._lock:
            return self.mode

    #
    # Runs the code
    #
    
    def _check_sleep(self, idx):
        '''This ensures that the robot code called Wait() at some point'''
        
        # TODO: There are some cases where it would be ok to do this... 
        if not _wpilib._fake_time.FAKETIME.slept[idx]:
            errstr = '%s() function is not calling wpilib.Wait() in its loop!' % self.mode_map[self.mode]
            raise RuntimeError(errstr)
            
        _wpilib._fake_time.FAKETIME.slept[idx] = False
        
    
    def on_IsEnabled(self):
        with self._lock:
            self._check_sleep(0)
            return self.mode != SimManager.MODE_DISABLED
        
    def on_IsAutonomous(self, tm):
        with self._lock:
            self._check_sleep(1)
            if not self._run_code:
                return False
            return self.mode == SimManager.MODE_AUTONOMOUS
        
    def on_IsOperatorControl(self, tm):
        with self._lock:
            self._check_sleep(2)
            if not self._run_code:
                return False
            return self.mode == SimManager.MODE_OPERATOR_CONTROL
            
    def on_WatchdogError(self, last_fed, period, expiration):
        print('WATCHDOG FAILURE! Last fed %0.3f seconds ago (expiration: %0.3f seconds)' % 
                                  (period, expiration), file=sys.stderr)
        self.set_mode(SimManager.MODE_DISABLED)
    
    def _robot_thread(self):
        
        # setup things for the robot
        self.driver_station = _wpilib.DriverStation.GetInstance()
        self.myrobot.watchdog.error_handler = self.on_WatchdogError
        
        last_mode = None
        
        try:
            while True:
                with self._lock:
                
                    mode = self.mode
                
                    if not self._run_code:
                        break
                    
                # Detect if the code is implemented improperly
                # -> This error occurs if the robot returns from one of its 
                #    functions for any reason other than a mode change, as 
                #    this is the only acceptable reason for this to occur
                if last_mode is not None:
                    if last_mode == mode and mode != SimManager.MODE_DISABLED:                        
                        errstr = '%s() function returned before the mode changed' % SimManager.mode_map[last_mode]
                        raise RuntimeError(errstr)
                    
                # reset this, just in case
                _wpilib._fake_time.FAKETIME.slept = [True]*3
                
                if last_mode != mode:
                    if mode == SimManager.MODE_DISABLED:
                        self.myrobot.Disabled()
                    elif mode == SimManager.MODE_AUTONOMOUS:
                        self.myrobot.Autonomous()
                    elif mode == SimManager.MODE_OPERATOR_CONTROL:
                        self.myrobot.OperatorControl()
                    
                # make sure infinite loops don't kill the processor... 
                time.sleep(0.001)
                last_mode = mode
        
        finally:
            self.myrobot.GetWatchdog().SetEnabled(False)
            self.set_mode(SimManager.MODE_DISABLED)
