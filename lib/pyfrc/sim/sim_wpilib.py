'''
    Monkeypatches in wpilib pieces needed to make the sim work in real
    time, instead of fake time. 
'''

import sys
import time
import threading

from .. import wpilib
from ..wpilib._wpilib import _core, _fake_time


class FakeRealTime(object):
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
        self.Reset()

    def Get(self):
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
        
    def IncrementTimeBy(self, secs):
        '''This is called when wpilib.Wait() occurs'''
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
                
        
    def Pause(self):
        with self.lock:
            self._increment_tm()
            self.paused = True
            self.lock.notify()
    
    def Reset(self):
        self.slept = [True]*3
        
        with self.lock:
            self.pause_at = None
            self.pause_secs = None
            self.paused = False
            
            self.tm = 0
            self.last_tm = time.time()
            
            self.lock.notify()
        
        self.notifiers = []
        
    def Resume(self, secs=None):
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
    
    def AddNotifier(self, notifier):
        # todo: use threads to implement these
        raise RuntimeError("TODO: Implement this")
        
        if notifier not in self.notifiers:
            notifier.run_time = self.time + notifier.m_period
            self.notifiers.append( notifier )
    
    def RemoveNotifier(self, notifier):
        # todo: use threads to implement these
        raise RuntimeError("TODO: Implement this")
    
        if notifier in self.notifiers:
            self.notifiers.remove( notifier )

_fake_time.FAKETIME = FakeRealTime()


class RealFakeWatchdog(object):
    '''
        This is a watchdog implementation for the sim. If you
        spend too much time not executing Robot code, then this will
        kill your robot. 
        
        When the watchdog detects a problem, it will call the function
        stored in RealFakeWatchdog.watchdog_handler. The default handler
        prints out an error message. 
        
        This class should be fully threadsafe.
    '''
    
    kDefaultWatchdogExpiration = wpilib.Watchdog.kDefaultWatchdogExpiration
    
    @staticmethod
    def _reset():
        if hasattr(RealFakeWatchdog, '_instance'):
            delattr(RealFakeWatchdog, '_instance')
    
    @staticmethod
    def GetInstance():
        try:
            return RealFakeWatchdog._instance
        except AttributeError:
            RealFakeWatchdog._instance = RealFakeWatchdog._inner()
            return RealFakeWatchdog._instance
    
    class _inner:

        def __init__(self):
        
            # a callable object that takes a single parameter, which is the 
            # time that the watchdog was last fed
            # -> Note that this handler may be called multiple times, and
            #    it will be called from the watchdog thread.
            self.error_handler = None
        
            self.enabled = False
            self.fed = None
            self.alive = True
            self.expiration = RealFakeWatchdog.kDefaultWatchdogExpiration
            
            self.lock = threading.RLock()
            self.cv = threading.Condition(self.lock)
            
            self.thread = threading.Thread(target=self._watcher_fn)
            self.thread.daemon = True
            self.thread.start()
            
        def Feed(self):
            with self.lock:
                if not self.enabled:
                    return False
                    
                was_alive = self.alive
                self.alive = True
                self.fed = _fake_time.FAKETIME.Get()
                self.cv.notify()
            
            return was_alive
                
        def GetEnabled(self):
            with self.lock:
                return self.enabled
        
        def GetExpiration(self):
            with self.lock:
                raise self.expiration
            
        def GetTimer(self):
            with self.lock:
                return _fake_time.FAKETIME.Get() - self.fed
                
        def IsAlive(self):
            with self.lock:
                return self.alive
            
        def IsSystemActive(self):
            return self.IsAlive()
            
        def Kill(self):
            raise NotImplementedError()
        
        def SetEnabled(self, enabled):
            with self.lock:
                self.enabled = bool(enabled)
                self.alive = True
                self.fed = _fake_time.FAKETIME.Get()
                self.cv.notify()
        
        def SetExpiration(self, expiration):
            with self.lock:
                self.expiration = float(expiration)
                if self.enabled:
                    self.alive = True
                    self.fed = _fake_time.FAKETIME.Get()
                self.cv.notify()
        
        def _watcher_fn(self):
            '''
                This function runs in a separate thread, and checks the
                watchdog and determines whether it has starved or not
            '''
            
            with self.lock:
                while True:
                
                    # use the condition variable to wait for the dog to be enabled
                    # -> note that condition variables release the lock while 
                    #    they are waiting to be notified of a change
                    self.cv.wait_for(lambda: self.enabled)
                    
                    # once enabled, ensure that the dog is being fed on time
                    while True:
                        
                        self.cv.wait(timeout=self.expiration)
                        
                        # did someone disable us?
                        if not self.enabled:
                            break
                        
                        # check for hunger
                        now = _fake_time.FAKETIME.Get()
                        period = now - self.fed
                        
                        if period > self.expiration:
                            # looks like someone forgot to feed the watchdog!
                            self.alive = False
                            
                            if self.error_handler is not None:
                                self.error_handler(self.fed, period, self.expiration)
                            else:                    
                                print('WATCHDOG FAILURE! Last fed %0.3f seconds ago (expiration: %0.3f seconds)' % 
                                      (period, self.expiration), file=sys.stderr)

_core.Watchdog = RealFakeWatchdog


