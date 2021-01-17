from hal_impl.sim_hooks import SimHooks


class PyFrcFakeHooks(SimHooks):
    """
    Defines hal hooks that use the fake time object
    """

    def __init__(self, fake_time):
        self.fake_time = fake_time
        super().__init__()

    #
    # Time related hooks
    #

    def getTime(self):
        return self.fake_time.get()

    def delayMillis(self, ms):
        self.fake_time.increment_time_by(0.001 * ms)

    def delaySeconds(self, s):
        self.fake_time.increment_time_by(s)

    #
    # DriverStation related hooks
    #

    @property
    def ds_cond(self):
        return self.fake_time.ds_cond

    @ds_cond.setter
    def ds_cond(self, value):
        pass  # ignored
