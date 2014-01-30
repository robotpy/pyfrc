'''
    Monkeypatches in wpilib pieces needed to make the sim work in real
    time, instead of fake time. 
'''

import sys
import time
import threading

from .. import wpilib
from ..wpilib._wpilib import _fake_time


class FakeRealTime(object):
    
    def __init__(self):
        self.Reset()

    def Get(self):
        return time.time()
        
    def IncrementTimeBy(self, secs):
        self.slept = [True]*3
        time.sleep(secs)
        
    def Reset(self):
        self.slept = [True]*3
        self.time = 0
        self.notifiers = []
    
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
            self.fed = time.time()
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
            return time.time() - self.fed
            
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
            self.fed = time.time()
            self.cv.notify()
    
    def SetExpiration(self, expiration):
        with self.lock:
            self.expiration = float(expiration)
            if self.enabled:
                self.alive = True
                self.fed = time.time()
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
                    now = time.time()
                    period = now - self.fed
                    
                    if period > self.expiration:
                        # looks like someone forgot to feed the watchdog!
                        self.alive = False
                        
                        if self.error_handler is not None:
                            self.error_handler(self.fed, period, self.expiration)
                        else:                    
                            print('WATCHDOG FAILURE! Last fed %0.3f seconds ago (expiration: %0.3f seconds)' % 
                                  (period, self.expiration), file=sys.stderr)

wpilib.Watchdog = RealFakeWatchdog


