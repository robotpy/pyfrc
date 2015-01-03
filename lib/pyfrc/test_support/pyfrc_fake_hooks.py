from hal_impl.data import hal_data

class PyFrcFakeHooks:
    '''
        Defines hal hooks that use the fake time object
    '''
    
    def __init__(self, fake_time):
        self.fake_time = fake_time
    #
    # Hook functions
    #
    
    def getTime(self):
        return self.fake_time.get()
    
    def getFPGATime(self):
        return int((self.fake_time.get() - hal_data['time']['program_start']) * 1000000)
    
    def delayMillis(self, ms):
        self.fake_time.increment_time_by(.001 * ms)
    
    def delaySeconds(self, s):
        self.fake_time.increment_time_by(s)
