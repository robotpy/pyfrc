'''
    Implements a fake time keeping obejct
'''


class FakeTime(object):
    '''
        Internal fake_wpilib timekeeper, pretends that time is passing
        by on the robot for the test robot
    '''

    def __init__(self):
        self.Reset()
        

    def __time_test__(self):
        print('time = ' + str(self.time))
        if self.time_limit <= self.time:
            print ('test should pause')
            raise FakeTimeException
        
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
        __time_test__()
        
    def SetTimeLimit(self, time_limit):
        '''
            Sets the amount of time that a robot will run before 
        '''
        print('time limit = ' + str(time_limit))
        self.time_limit = time_limit

    class FakeTimeException(Exception):
        '''
            simple exception that allows us to go back to the test
            up to the test caller
        '''
        pass
    
# singleton object
FAKETIME = FakeTime()