'''
    Implements all useful time-related classes and functions needed to
    simulate a running robot.
'''


class FakeTime(object):
    '''
        Internal fake_wpilib timekeeper, pretends that time is passing
        by on the robot
    '''

    def __init__(self):
        self.time = 0
        self.notifiers = []

    def Get(self):
        return self.time
        
    def IncrementTimeBy(self, time):
    
        final_time = self.time + time
        
        if len(self.notifiers) > 0:
            qitem = min(self.notifiers)
        
            while qitem.run_time <= final_time:
            
                self.time = qitem.run_time
                if not qitem._run():
                    self.notifiers.remove(qitem)
                    
                qitem = min(self.notifiers)
    
        self.time = final_time
    
    def AddNotifier(self, notifier):
        if notifier not in self.notifiers:
            notifier.run_time = self.time + notifier.m_period
            self.notifiers.append( notifier )
    
    def RemoveNotifier(self, notifier):
        if notifier in self.notifiers:
            self.notifiers.remove( notifier )
        

# singleton object
FAKETIME = FakeTime()


class Notifier(object):

    def __init__(self, handler):
        '''
        * Create a Notifier for timer event notification.
        * @param handler The handler is called at the notification time which is set
        * using StartSingle or StartPeriodic.
        '''
    
        self.handler = handler

        
    def StartSingle(self, delay):
        '''
        * Register for single event notification.
        * A timer event is queued for a single event after the specified delay.
        * @param delay Seconds to wait before the handler is called.
        '''
        
        self.m_periodic = False
        self.m_period = delay
        
        FAKETIME.RemoveNotifier(self)
        FAKETIME.AddNotifier(self)
 
 
    def StartPeriodic(self, period):
        '''
        * Register for periodic event notification.
        * A timer event is queued for periodic event notification. Each time the interrupt
        * occurs, the event will be immedeatly requeued for the same time interval.
        * @param period Period in seconds to call the handler starting one period after the call to this method.
        '''
        
        self.m_periodic = True
        self.m_period = period
        
        FAKETIME.RemoveNotifier(self)
        FAKETIME.AddNotifier(self)
        
    def Stop(self):
        '''
        * Stop timer events from occuring.
        * Stop any repeating timer events from occuring. This will also remove any single
        * notification events from the queue.
        * If a timer-based call to the registered handler is in progress, this function will
        * block until the handler call is complete.
        '''
        
        FAKETIME.RemoveNotifier(self)

    #
    # functions required to implement a queue of notifiers for FakeTime
    #
    
    def __lt__(self, other):
        return self.run_time < other.run_time
        
    def _run(self):
        '''Returns True if this should be run again'''
        self.handler()
        if self.m_periodic is True:
            self.run_time += self.m_period
            
        return self.m_periodic
        
        
class Timer(object):

    '''
    * Timer objects measure accumulated time in seconds.
    * The timer object functions like a stopwatch. It can be started, stopped, and cleared. When the
    * timer is running its value counts up in seconds. When stopped, the timer holds the current
    * value. The implementation simply records the time when started and subtracts the current time
    * whenever the value is requested.
    *
    * Note that this implementation does not use actual time, but 'fake' time as computed
    * by the simulation. 
    '''
    
    def __init__(self):
        '''
        * Create a new timer object.
        * 
        * Create a new timer object and reset the time to zero. The timer is initially not running and
        * must be started.
        '''   

        self.start_time = 0
        self.accumulated_time = 0
        self.running = False
        self.Reset()
    
    
    def Get(self):
        '''
        * Get the current time from the timer. If the clock is running it is derived from
        * the current system clock the start time stored in the timer class. If the clock
        * is not running, then return the time when it was last stopped.
        * 
        * @return unsigned Current time value for this timer in seconds
        '''
    
        if self.running:
            return (FAKETIME.Get() - self.start_time) + self.accumulated_time
        else:
            return self.accumulated_time
    
    
    def Reset(self):
        '''
        * Reset the timer by setting the time to 0.
        * 
        * Make the timer startTime the current time so new requests will be relative to now
        '''
        
        self.accumulated_time = 0
        self.start_time = FAKETIME.Get()
    
    
    def Start(self):
        '''
        * Start the timer running.
        * Just set the running flag to true indicating that all time requests should be
        * relative to the system clock.
        '''
    
        if not self.running:
            self.start_time = FAKETIME.Get()
            self.running = True
    
    
    def Stop(self):
        '''
        * Stop the timer.
        * This computes the time as of now and clears the running flag, causing all
        * subsequent time requests to be read from the accumulated time rather than
        * looking at the system clock.
        '''
    
        if self.running:
            self.accumulated_time += self.Get()
            self.running = False
    
    
    def HasPeriodPassed(self, period):
        '''
        * Check if the period specified has passed and if it has, advance the start
        * time by that period. This is useful to decide if it's time to do periodic
        * work without drifting later by the time it took to get around to checking.
        *
        * @param period The period to check for (in seconds).
        * @return If the period has passed.
        '''
        
        if self.Get() > period:
            self.start_time += period
            return True
        return False
        
    
    @staticmethod
    def GetPPCTimestamp():
        return FAKETIME.Get()
    
        
def Wait(time):
    '''
    * Pause the task for a specified time.
    * 
    * Pause the execution of the program for a specified period of time given in seconds.
    * Motors will continue to run at their last assigned values, and sensors will continue to
    * update. Only the task containing the wait will pause until the wait time is expired.
    * 
    * @param seconds Length of time to pause, in seconds.
    '''

    FAKETIME.IncrementTimeBy(time)
    
    
def GetClock():
    return FAKETIME.Get()
    