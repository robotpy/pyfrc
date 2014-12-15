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

    def Reset(self):
        self.time = 0
        self.notifiers = []

    def Get(self):
        return self.time
        
    def IncrementTimeBy(self, time):
    
        if time < 0:
            time = 0
        
        final_time = self.time + time
        

# singleton object
FAKETIME = FakeTime()