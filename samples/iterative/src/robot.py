
try:
    import wpilib
except ImportError:
    from pyfrc import wpilib


class MyRobot(wpilib.IterativeRobot):
    
    def __init__(self):
        super().__init__()
        
        self.lstick = wpilib.Joystick(1)
        self.motor = wpilib.CANJaguar(8)

    def AutonomousInit(self):
        self.GetWatchdog().SetEnabled(False)

    def AutonomousPeriodic(self):
        pass

    def DisabledInit(self):
        pass
    
    def DisabledPeriodic(self):
        pass

    def TeleopInit(self):
        dog = self.GetWatchdog()
        dog.SetEnabled(True)
        dog.SetExpiration(0.25)

    def TeleopPeriodic(self):

        self.GetWatchdog().Feed()

        # Move a motor with a Joystick
        self.motor.Set(self.lstick.GetY())


def run():
    
    robot = MyRobot()
    robot.StartCompetition()
    
    return robot


if __name__ == '__main__':
    wpilib.run()

