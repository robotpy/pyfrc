
from .pid_controller import PIDController

class SmartDashboard(object):

    instance = None
    
    @staticmethod
    def GetInstance():
        if SmartDashboard.instance is None:
            SmartDashboard.instance = SmartDashboard()
        return SmartDashboard.instance
        
    def __init__(self):
        self.data = {}
        
    def GetBoolean(self, key):
        if key in self.data:
            return self.data[key]
        return None
        
    def GetData(self, key):
        if key in self.data:
            return self.data[key]
        return None

    def GetDouble(self,key):
        if key in self.data:
            return self.data[key]
        return None
        
    def GetInt(self, key):
        if key in self.data:
            return self.data[key]
        return None
        
    def PutBoolean(self, key, value):
        self.data[key] = bool(value)
        
    def PutDouble(self, key, value):
        self.data[key] = value
        
    def PutData(self, key, value):
        self.data[key] = value
        
    def PutInt(self, key, value):
        self.data[key] = int(value)
        
    
    
    
class SendablePIDController(PIDController):
    """A {@link SendablePIDController} is a {@link PIDController} that can be
    sent over to the {@link SmartDashboard} using the
    {@link SmartDashboard#PutData()} method.

    It is useful if you want to test values of a {@link PIDController} without
    having to recompile code between tests.
    Also, consider using {@link Preferences} to save the important values
    between matches.

    @see SmartDashboard"""
    kP = "p"
    kI = "i"
    kD = "d"
    kSetpoint = "setpoint"
    kEnabled = "enabled"

    def __init__(self, p, i, d, source, output, period=0.05):
        """Allocate a PID object with the given constants for P, I, D.
        @param p the proportional coefficient
        @param i the integral coefficient
        @param d the derivative coefficient
        @param source The PIDSource object that is used to get values
        @param output The PIDOutput object that is set to the output value
        @param period the loop time for doing calculations in seconds. This
        particularly effects calculations of the integral and differential
        terms.  The default is 50ms."""
        super().__init__(p, i, d, source, output, period)
        self.table = None

    def SetSetpoint(self, setpoint):
        """Set the setpoint for the PIDController
        @param setpoint the desired setpoint"""
        super().SetSetpoint(setpoint)

        if self.table is not None:
            self.table[self.kSetpoint] = float(setpoint)

    def SetPID(self, p, i, d):
        """Set the PID Controller gain parameters.
        Set the proportional, integral, and differential coefficients.
        @param p Proportional coefficient
        @param i Integral coefficient
        @param d Differential coefficient"""
        super().SetPID(p, i, d)

        if self.table is not None:
            self.table[self.kP] = float(p)
            self.table[self.kI] = float(i)
            self.table[self.kD] = float(d)

    def Enable(self):
        """Begin running the PIDController"""
        super().Enable()

        if self.table is not None:
            self.table[self.kEnabled] = True

    def Disable(self):
        """Stop running the PIDController, this sets the output to zero before
        stopping."""
        super().Disable()

        if self.table is not None:
            self.table[self.kEnabled] = False
            
            
class SendableChooser:
    """The {@link SendableChooser} class is a useful tool for presenting a
    selection of options to the {@link SmartDashboard}.

    For instance, you may wish to be able to select between multiple
    autonomous modes.  You can do this by putting every possible
    {@link Command} you want to run as an autonomous into a
    {@link SendableChooser} and then put it into the {@link SmartDashboard}
    to have a list of options appear on the laptop.  Once autonomous starts,
    simply ask the {@link SendableChooser} what the selected value is.

    @see SmartDashboard"""
    kDefault = "default"
    kCount = "count"
    kSelected = "selected"

    def __init__(self):
        self.defaultChoice = None
        self.choices = {}   # map from names to objects
        self.ids = {}       # map from objects to ids
        #self.table = NetworkTable()
        self.table = {}
        self.count = 0

    def AddObject(self, name, obj):
        """Adds the given object to the list of options.  On the
        {@link SmartDashboard} on the desktop, the object will appear as the
        given name.
        @param name the name of the option
        @param object the option"""
        if name in self.choices:
            id = self.ids[self.choices[name]]
        else:
            id = str(self.count)
            self.count += 1
            self.ids[obj] = id
            self.table[self.kCount] = self.count
        self.choices[name] = obj
        self.table[id] = str(name)

    def AddDefault(self, name, obj):
        """Add the given object to the list of options and marks it as the
        default.  Functionally, this is very close to
        {@link SendableChooser#AddObject()} except that it will use this as
        the default option if none other is explicitly selected.
        @param name the name of the option
        @param object the option"""
        self.defaultChoice = obj
        self.AddObject(name, obj)
        self.table[self.kDefault] = str(name)

    def GetSelected(self):
        """Returns the selected option.  If there is none selected, it will
        return the default.  If there is none selected and no default, then
        it will return {@code None}.
        @return the option selected"""
        if self.kSelected in self.table:
            return self.choices[self.table[self.kSelected]]
        else:
            return self.defaultChoice

    #
    # SmartDashboardData interface
    #
    def GetType(self):
        return "String Chooser"

    def GetTable(self):
        return self.table
