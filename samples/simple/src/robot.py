
try:
    import wpilib
except ImportError:
    from pyfrc import wpilib


class MyRobot(wpilib.SimpleRobot):
    
    def __init__(self):
        super().__init__()
        
        self.lstick = wpilib.Joystick(1)
        self.motor = wpilib.CANJaguar(8)

    def Autonomous(self):
        
        self.GetWatchdog().SetEnabled(False)
        while self.IsAutonomous() and self.IsEnabled():
            wpilib.Wait(0.01)

    def OperatorControl(self):
        
        dog = self.GetWatchdog()
        dog.SetEnabled(True)
        dog.SetExpiration(0.25)

        while self.IsOperatorControl() and self.IsEnabled():
            dog.Feed()

            # Move a motor with a Joystick
            self.motor.Set(self.lstick.GetY())

            wpilib.Wait(0.04)

def run():
    
    robot = MyRobot()
    robot.StartCompetition()
    
    return robot


if __name__ == '__main__':
    wpilib.run()

