
import time
import threading

class FakeRealTime:
    '''
        This allows the robot to run in realtime, or we can pause and
        single-step the robot.
    
        This implementation will break anything that is trying to measure
        time while paused.. but really, that shouldn't be expected to
        work anyways.
        
        Currently, we assume all robot code runs in a single thread. This
        makes a lot of things easier. If that assumption was broken, then
        this would be a bit more complex.
    '''
    
    def __init__(self):
        self.lock = threading.Condition()
        self.reset()
        
        self.local = threading.local()
        self.ds_cond = threading.Condition()
        
    def set_physics_fn(self, fn):
        self.local.physics_fn = fn

    def get(self):
        with self.lock:         
            self._increment_tm()
            return self.tm
            
    def _increment_tm(self, secs=None):
        # internal fn, must hold lock to call this
        
        if self.paused:
            return
        
        now = time.time()
        
        # normal usage
        if secs is None or self.pause_at is None:
            self.tm += (now - self.last_tm)
            self.last_tm = now
        else:
            # used by IncrementTimeBy to determine if a further
            # pause is required.
            self.tm += secs
       
        # single step support
        if self.pause_at is not None and self.tm >= self.pause_at:
            
            self.tm = self.pause_at
            self.paused = True
            self.pause_at = None
        
        physics_fn = getattr(self.local, 'physics_fn', None)
        if physics_fn is not None:
            physics_fn(self.tm)
        
    def increment_time_by(self, secs):
        '''This is called when wpilib.Timer.delay() occurs'''
        self.slept = [True]*3
        
        was_paused = False
        
        with self.lock:
            
            self._increment_tm(secs)
                
            while self.paused and secs > 0:
                
                if self.pause_secs is not None:
                    # if pause_secs is set, this means it was a step operation,
                    # so we adjust the wait accordingly
                    if secs > self.pause_secs:
                        secs -= self.pause_secs
                    else:
                        secs = 0
                        
                    self.pause_secs = None
                
                was_paused = True
                
                self.lock.wait()
                
                # if the operator tried to do another step, this will update
                # the paused flag so we don't escape the loop
                self._increment_tm(secs)
        
        if not was_paused:
            time.sleep(secs)
                
        
    def pause(self):
        with self.lock:
            self._increment_tm()
            self.paused = True
            self.lock.notify()
    
    def reset(self):
        self.slept = [True]*3
        
        with self.lock:
            self.pause_at = None
            self.pause_secs = None
            self.paused = False
            
            self.next_ds_time = 0.020
            self.tm = 0
            self.last_tm = time.time()
            
            self.lock.notify()
        
        self.notifiers = []
        
    def resume(self, secs=None):
        with self.lock:
            
            # makes sure timers don't get messed up when we resume
            self._increment_tm()
            
            if self.paused:
                self.last_tm = time.time()
                        
            self.paused = False
            if secs is not None:
                self.pause_at = self.tm + secs
                self.pause_secs = secs
            else:
                self.pause_at = None
                self.pause_secs = None
                
            self.lock.notify()

