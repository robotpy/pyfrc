
import threading
from hal_impl.mode_helpers import notify_new_ds_data


class FakeTime:
    '''
        Keeps track of time for robot code being tested, and makes sure the
        DriverStation is notified that new packets are coming in.
        
        Your testing code can use this object to control time by asking for
        the fake_time fixture.
    '''

    class FakeTimeException(BaseException):
        '''
            This is thrown when the time limit has expired
            
            This exception inherits from BaseException, so if you want to catch
            it you must explicitly specify it, as a blanket except statement
            will not catch this exception.
        '''
        pass
    
    def __init__(self):
        self.reset()
        self.lock = threading.RLock()
        
    def _setup(self):
        
        # Setup driver station hooks
        import wpilib
        ds = wpilib.DriverStation.getInstance()
        
        self._ds_cond = _DSCondition(self, ds.mutex)
        ds.dataSem = self._ds_cond
        
        self.thread_id = threading.current_thread().ident
        return self._ds_cond

    def __time_test__(self):
        if self.time_limit is not None and self.time_limit <= self.time:
            raise FakeTime.FakeTimeException()
    
    def reset(self):
        '''
            Resets the fake time to zero, and sets the time limit
        '''
        self.time = 0
        #self.time_limit = 500
        self.time_limit = None
        self.in_increment = False
        
        self.next_ds_time = 0.020

    def get(self):
        '''
            :returns: The current time for the robot
        '''
        with self.lock:
            return self.time
        
    def increment_time_by(self, time):
        '''
            Increments time by some number of seconds
            
            :param time: Number of seconds to increment time by
            :type time: float
        '''
        if time < 0:
            time = 0
        
        with self.lock:
            
            if self.in_increment:
                raise ValueError("increment_time_by is not reentrant (did you call timer.delay?)")
            
            next_ds = self.next_ds_time - self.time 
            
            # This is terrible, but it works
            while time > 0:
                
                # Short wait, just get it done and exit
                if time < next_ds:
                    self.time += time
                    self.__time_test__()
                    break
                
                self.time += next_ds
                
                if threading.current_thread().ident == self.thread_id:
                    self._ds_cond.on_step(self.time)
                
                notify_new_ds_data()
                  
                time -= next_ds
                
                next_ds = 0.020
                self.next_ds_time += next_ds
                
                self.__time_test__()
    
    def increment_new_packet(self):
        '''
            Increment time enough to where the new DriverStation packet
            comes in
        '''
        with self.lock:
            next_ds_time = self.next_ds_time
            time = self.time
        
        self.increment_time_by(next_ds_time - time)
    
    def set_time_limit(self, time_limit):
        '''
            Sets the amount of time that a robot will run. When time is
            incremented past this time, a FakeTimeException is thrown 
            
            :param time_limit: Number of seconds
            :type time_limit: float
        '''
        self.time_limit = time_limit


class _DSCondition(threading.Condition):
    '''
        Condition variable replacement to allow fake time to be used to hook
        into the DriverStation packets
    '''
    
    def __init__(self, fake_time_inst, lock):
        super().__init__(lock)
        
        self.thread_id = threading.current_thread().ident
        self.fake_time_inst = fake_time_inst
        self._on_step = lambda tm: True
    
    def on_step(self, tm):
        
        retval = self._on_step(tm)
        if not retval:
            raise FakeTime.FakeTimeException() 
    
    def wait(self, timeout=None):
        
        in_main = (threading.current_thread().ident == self.thread_id)
        
        if timeout is not None:
            raise NotImplementedError("Didn't implement timeout support yet")
        
        # If we're on the main thread, make sure a new DS packet is sent before waiting
        if in_main:
            self.fake_time_inst.increment_new_packet()
        
        print("Waiting")
        super().wait(self, timeout=timeout)
        
        print("Waiting done")
        if in_main:
            self.on_step(self.fake_time_inst.get())
        
