from .NetworkTables import NetworkTable
from .Commands import Scheduler
from .core import DriverStation

class ButtonScheduler:
    def __init__(self, last, button, orders):
        self.pressedLast = last
        self.button = button
        self.command = orders

    def Execute(self):
        raise NotImplementedError

    def Start(self):
        Scheduler.GetInstance().AddButton(self)

class HeldButtonScheduler(ButtonScheduler):
    def Execute(self):
        if self.button.Grab():
            self.pressedLast = True
            self.command.Start()
        else:
            if self.pressedLast:
                self.pressedLast = False
                self.command.Cancel()

class PressedButtonScheduler(ButtonScheduler):
    def Execute(self):
        if self.button.Grab():
            if not self.pressedLast:
                self.pressedLast = True
                self.command.Start()
        else:
            self.pressedLast = False

class ReleasedButtonScheduler(ButtonScheduler):
    def Execute(self):
        if self.button.Grab():
            self.pressedLast = True
        else:
            if self.pressedLast:
                self.pressedLast = False
                self.command.Start()

class Button:
    def __init__(self):
        self.table = None

    def Get(self):
        raise NotImplementedError

    def Grab(self):
        if self.Get():
            return True
        elif self.table is not None:
            if self.table.IsConnected():
                return self.table.GetBoolean("pressed")
            else:
                return False
        else:
            return False

    def WhenPressed(self, command):
        pbs = PressedButtonScheduler(self.Grab(), self, command)
        pbs.Start()

    def WhileHeld(self, command):
        hbs = HeldButtonScheduler(self.Grab(), self, command)
        hbs.Start()

    def WhenReleased(self, command):
        rbs = ReleasedButtonScheduler(self.Grab(), self, command)
        rbs.Start()

    #
    # SmartDashboardData interface
    #
    def GetType(self):
        return "Button"

    def GetTable(self):
        if self.table is None:
            self.table = NetworkTable()
            self.table["pressed"] = self.Get()
        return self.table

class AnalogIOButton(Button):
    kThreshold = 0.5

    def __init__(self, port):
        super().__init__()
        self.port = port

    def Get(self):
        return DriverStation.GetInstance().GetEnhancedIO()\
                .GetAnalogIn(self.port) < self.kThreshold

class DigitalIOButton(Button):
    kActiveState = False

    def __init__(self, port):
        super().__init__()
        self.port = port

    def Get(self):
        return DriverStation.GetInstance().GetEnhancedIO()\
                .GetDigital(self.port) == self.kActiveState

class InternalButton(Button):
    def __init__(self, inverted=False):
        super().__init__()
        self.pressed = inverted
        self.inverted = inverted

    def SetInverted(self, inverted):
        self.inverted = inverted

    def SetPressed(self, pressed):
        self.pressed = pressed

    def Get(self):
        return self.pressed != self.inverted

class JoystickButton(Button):
    def __init__(self, joystick, buttonNumber):
        super().__init__()
        self.joystick = joystick
        self.buttonNumber = buttonNumber

    def Get(self):
        return self.joystick.GetRawButton(self.buttonNumber)

class NetworkButton(Button):
    def __init__(self, table, field):
        if not isinstance(table, NetworkTable):
            table = NetworkTable.GetTable(table)
        self.netTable = table
        self.field = field

    def Get(self):
        if self.netTable.IsConnected():
            return self.netTable.GetBoolean(self.field)
        else:
            return False

