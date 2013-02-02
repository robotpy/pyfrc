
class SmartDashboard(object):

    data = None
    
    @staticmethod
    def init():
        if SmartDashboard.instance is not None:
            raise RuntimeError("Only initialize this once")
        SmartDashboard.instance = SmartDashboard()    
      
    @staticmethod
    def PutData(self, key, data):
        if key in SmartDashboard.data:
            return SmartDashboard.data[key]
        return None
    
    # not implemented in RobotPy
    #@staticmethod
    #def GetData(self, key):
    #    return SmartDashboard.data[key]
    
    @staticmethod
    def PutBoolean(key, value):
        if not isinstance(value, bool):
            raise RuntimeError("%s is not a boolean (is %s instead)" % (key, type(value)))
        SmartDashboard.data[key] = value
        
    @staticmethod
    def GetBoolean(key):
        return SmartDashboard.data[key]
    
    @staticmethod
    def PutNumber(key, value):
        if not isinstance(value, (int, float)):
            raise RuntimeError("%s is not a number (is %s instead)" % (key, type(value)))
        SmartDashboard.data[key] = value
    
    @staticmethod    
    def GetNumber(key):
        return SmartDashboard.data[key]
        
    @staticmethod
    def PutString(key, value):
        SmartDashboard.data[key] = str(value)
    
    @staticmethod
    def GetString(key):
        return SmartDashboard.data[key]

    @staticmethod
    def PutValue(key, value):
        SmartDashboard.data[key] = value
    
    # not implemented in RobotPy
    #@staticmethod
    #def GetValue(self,key):
    #    return self.data[key]
    
