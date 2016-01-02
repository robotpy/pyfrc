
import threading
import wpilib
import weakref


class TestRanTooLong(BaseException):
    '''
        This is thrown when the time limit has expired
        
        This exception inherits from BaseException, so if you want to catch
        it you must explicitly specify it, as a blanket except statement
        will not catch this exception.'
        
        Generally, only internal pyfrc code needs to catch this
    '''
    pass
    
class TestEnded(BaseException):
    '''
        This is thrown when the controller has been signaled to end the test
        
        This exception inherits from BaseException, so if you want to catch
        it you must explicitly specify it, as a blanket except statement
        will not catch this exception.'
        
        Generally, only internal pyfrc code needs to catch this
    '''
    pass

class FakeTime:
    '''
        Keeps track of time for robot code being tested, and makes sure the
        DriverStation is notified that new packets are coming in.
        
        Your testing code can use this object to control time by asking for
        the fake_time fixture.
    '''

    
    
    def __init__(self):
        self._child_threads = weakref.WeakKeyDictionary()
        self._children_free_run = False
        self._children_not_running = threading.Event()
        self.lock = threading.RLock()
        self.reset()
        
    def _setup(self):
        
        # Setup driver station hooks
        self._ds = wpilib.DriverStation.getInstance()
        
        self._ds_cond = _DSCondition(self, self._ds.mutex)
        self._ds.dataSem = self._ds_cond
        
        self.thread_id = threading.current_thread().ident
        return self._ds_cond

    def __time_test__(self):
        if self.time_limit is not None and self.time_limit <= self.time:
            raise TestRanTooLong()

    def _wake_children(self, timestep):
        # Subtract the timestep from the last requested times of the threads.
        # Wake them up if the requested time is in the past, and they haven't
        # already been stopped.
        thread_awakened = False
        for thread, thread_info in self._child_threads.items():
            thread_info['time'] -= timestep
            if thread_info['time'] <= 0 and thread.is_alive():
                self._children_not_running.clear()
                thread_info['event'].set()  # Wake it up
                thread_awakened = True
        # Wait for everything we woke up to sleep again.
        # Check that we did wake something up.
        if thread_awakened:
            self._children_not_running.wait()

    def children_stopped(self):
        # Avoid issues with keys disappearing from weakref dict
        keys = list(self._child_threads.keys())
        for thread in keys:
            if thread.is_alive():
                return False
        return True

    def teardown(self):
        self._children_free_run = True  # Stop any threads being blocked
        self._children_not_running.set()  # Main thread needs to be running
        for thread_info in self._child_threads.values():
            thread_info['event'].set()

    def reset(self):
        '''
            Resets the fake time to zero, and sets the time limit to default
        '''
        self.time = 0
        self.time_limit = 500
        self.in_increment = False

        # Drop references to any child threads
        self._child_threads = weakref.WeakKeyDictionary()
        self._children_not_running.set()
        self._children_free_run = False

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
        # If it is a thread calling us, we intercept the call and insert
        # a blocking call to a threading.Event.wait() to force it to sleep
        # in the "real world", otherwise it keeps looping indeterminately.
        # Store the requested time, and at each DS step wake up those that
        # should have fired in the previous timestep.
        current_thread = threading.current_thread()
        if current_thread.ident != self.thread_id:
            with self.lock:
                child_id = current_thread.ident
                if child_id not in self._child_threads:
                    event = threading.Event()
                    self._child_threads[current_thread] = {'event': event,
                                                           'time': time}
                child_info = self._child_threads[current_thread]
            if time > 0 and not self._children_free_run:
                # Daughter thread needs to fire in the next DS time step,
                # so make it wait
                child_info['event'].clear()
                child_info['time'] = time
                # Check to see if the other threads have finished
                running = False
                for v in self._child_threads.values():
                    if v['event'].is_set():
                        running = True
                if not running:
                    self._children_not_running.set()
                child_info['event'].wait()
            # We don't need to do anything else for children
            return

        if time < 0:
            time = 0
        
        with self.lock:
            if self.in_increment:
                raise ValueError("increment_time_by is not reentrant (did you call timer.delay?)")
            
            next_ds = self.next_ds_time - self.time 
            
        # When we wake up the TimerTasks, we can't do it while we have the lock
        # because some tasks need to get the time themselves
        # eg feeding motor watchdogs

        # This is terrible, but it works
        while time > 0:
            
            # Short wait, just get it done and exit
            if time < next_ds:
                with self.lock:
                    self.time += time
                    self.__time_test__()
                self._wake_children(time)
                break
                
            with self.lock:
                self.time += next_ds
                
                if current_thread.ident == self.thread_id:
                    self._ds_cond.on_step(self.time)
                
                # Notify the DS thread to issue a new packet, but wait for it
                # to do it.
                # TODO: This breaks on iterative robot.. 
                with self._ds_cond:
                    self._ds_cond.notify_all()
                    self._ds.getData()
                  
                time -= next_ds
                
                next_ds = 0.020
                self.next_ds_time += next_ds
                
                self.__time_test__()
            self._wake_children(next_ds)

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
            incremented past this time, a TestRanTooLong is thrown.
            
            The default time limit is 500 seconds
            
            :param time_limit: Number of seconds
            :type time_limit: float
        '''
        self.time_limit = time_limit


class _DSCondition(threading.Condition):
    '''
        Condition variable replacement to allow fake time to be used to hook
        into the DriverStation packets.
    '''
    
    def __init__(self, fake_time_inst, lock):
        super().__init__(lock)
        
        self.thread_id = threading.current_thread().ident
        self.fake_time_inst = fake_time_inst
        self._on_step = lambda tm: True
    
    def on_step(self, tm):
        
        retval = self._on_step(tm)
        if not retval:
            raise TestEnded()
    
    def wait(self, timeout=None):
        
        in_main = (threading.current_thread().ident == self.thread_id)
        
        if timeout is not None:
            raise NotImplementedError("Didn't implement timeout support yet")
        
        # If we're on the robot's main thread, when this is called we just
        # need to increment the time, no wait required. If we're not on the
        # main thread, then we need to wait for a notification.. 
        if in_main:
            self.fake_time_inst.increment_new_packet()
        else:
            super().wait(self, timeout=timeout)
