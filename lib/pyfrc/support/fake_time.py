'''
    Implements a fake time keeping obejct
'''


class FakeTime(object):
    '''
        Internal fake_wpilib timekeeper, pretends that time is passing
        by on the robot for the test robot
    '''

    class FakeTimeException(Exception):
        '''
            simple exception that allows us to go back to the test
            up to the test caller
        '''
        pass
    
    def __init__(self):
        self.Reset()
        

    def __time_test__(self):
        if self.time_limit <= self.time:
            raise FakeTime.FakeTimeException
        
    def Reset(self):
        self.time = 0
        self.time_val = None
        self.notifiers = []
        self.time_limit = None

    def Get(self):
        return self.time
        
    def IncrementTimeBy(self, time):
    
        if time < 0:
            time = 0
        
        self.time = self.time + time
        self.__time_test__()
        
    def SetTimeLimit(self, time_limit):
        '''
            Sets the amount of time that a robot will run before 
        '''
        self.time_limit = time_limit


    
# singleton object
FAKETIME = FakeTime()