from hal_impl.data import hal_data

class PyFrcSimHooks:
    '''
        These are useful hooks to override for tests and other pyfrc tasks
    
        To use your own hook, set hal_impl.functions.hooks
        
        TODO: figure out what needs to be changed or maybe default sim hooks are good?
        
    '''
    
    def __init__(self, fake_time):
        self.fake_time = fake_time
    #
    # Hook functions
    #
    
    def getTime(self):
        return self.fake_time.Get()
    
    def getFPGATime(self):
        return int((self.fake_time.Get() - hal_data['time']['program_start']) * 1000000)
    
    def delayMillis(self, ms):
        self.fake_time.IncrementTimeBy(.001 * ms)
    
    def delaySeconds(self, s):
        self.fake_time.IncrementTimeBy(s)