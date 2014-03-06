
try:
    import wpilib
except ImportError:
    from pyfrc import wpilib


class MyRobot(wpilib.SimpleRobot):
    '''Main robot class'''
    
    def __init__(self):
        '''Constructor'''
        super().__init__()
        
        self.lstick = wpilib.Joystick(1)
        self.motor = wpilib.CANJaguar(8)
        self.ds = wpilib.DriverStation.GetInstance()
        
        print(wpilib.SmartDashboard)
        
    def Disabled(self):
        '''Called when the robot is disabled'''
        while self.IsDisabled():
            wpilib.Wait(0.01)

    def Autonomous(self):
        '''Called when autonomous mode is enabled'''
        
        self.GetWatchdog().SetEnabled(False)
        while self.IsAutonomous() and self.IsEnabled():
            wpilib.Wait(0.01)

    def OperatorControl(self):
        '''Called when operation control mode is enabled'''
        
        dog = self.GetWatchdog()
        dog.SetEnabled(True)
        dog.SetExpiration(0.25)

        timer = wpilib.Timer()
        timer.Start()

        while self.IsOperatorControl() and self.IsEnabled():
            dog.Feed()

            # Move a motor with a Joystick
            self.motor.Set(self.lstick.GetY())

            if timer.HasPeriodPassed(1.0):
                print("Analog 8: %s" % self.ds.battery.GetVoltage())

            wpilib.Wait(0.04)

def run():
    '''Called by RobotPy when the robot initializes'''
    
    robot = MyRobot()
    robot.StartCompetition()
    
    return robot


if __name__ == '__main__':
    wpilib.run()

