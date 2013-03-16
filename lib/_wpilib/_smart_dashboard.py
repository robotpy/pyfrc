'''
    Simple + dumb implementations of SmartDashboard related objects. If you
    want a full implementation, install pynetworktables
'''


class SmartDashboard(object):

    _table = None
    
    @staticmethod
    def init():
        if SmartDashboard._table is None:
            SmartDashboard._table = NetworkTable.GetTable("SmartDashboard")
      
    @staticmethod
    def PutData(key, data):
        SmartDashboard._table.PutData(key, data)
    
    # not implemented in RobotPy
    #@staticmethod
    #def GetData(self, key):
    #    return SmartDashboard.data[key]
    
    @staticmethod
    def PutBoolean(key, value):
        SmartDashboard._table.PutBoolean(key, value)
        
    @staticmethod
    def GetBoolean(key):
        return SmartDashboard._table.GetBoolean(key)
    
    @staticmethod
    def PutNumber(key, value):
        SmartDashboard._table.PutNumber(key, value)
    
    @staticmethod    
    def GetNumber(key):
        return SmartDashboard._table.GetNumber(key)
        
    @staticmethod
    def PutString(key, value):
        SmartDashboard._table.PutString(key, value)
    
    @staticmethod
    def GetString(key):
        return SmartDashboard._table.GetString(key)

    @staticmethod
    def PutValue(key, value):
        SmartDashboard._table.PutValue(key, value)
    
    # not implemented in RobotPy
    #def GetValue(self, key):
    #    return SmartDashboard._table.GetValue(key)
    
class SendableChooser(object):

    def __init__(self):
        self.choices = {}
        self.selected = None

    def AddObject(self, name, obj):
        self.choices[name] = obj
        
    def AddDefault(self, name, obj):
        self.selected = name
        self.choices[name] = obj
        
    def GetSelected(self):
        if self.selected is None:
            return None
        return self.choices[self.selected]

class NetworkTable(object):

    _tables = {}
    
    @staticmethod
    def GetTable(table_name):
        table = NetworkTable._tables.get(table_name)
        if table is None:
            table = NetworkTable()
            NetworkTable._tables[table_name] = NetworkTable()
        return table 
        
    def __init__(self):
        self.data = {}
    
    def AddTableListener(self, name, listener, isNew):
        pass
    
    def PutData(self, key, data):
        self.data[key] = data
    
    # not implemented in RobotPy
    #def GetData(self, key):
    #    return self.data[key]
    
    def PutBoolean(self, key, value):
        if not isinstance(value, bool):
            raise RuntimeError("%s is not a boolean (is %s instead)" % (key, type(value)))
        self.data[key] = value
        
    def GetBoolean(self, key):
        return self.data[key]
    
    def PutNumber(self, key, value):
        if not isinstance(value, (int, float)):
            raise RuntimeError("%s is not a number (is %s instead)" % (key, type(value)))
        self.data[key] = value
      
    def GetNumber(self, key):
        return self.data[key]
        
    def PutString(self, key, value):
        self.data[key] = str(value)
    
    def GetString(self, key):
        return self.data[key]

    def PutValue(self, key, value):
        self.data[key] = value
    
    # not implemented in RobotPy
    #@staticmethod
    #def GetValue(self,key):
    #    return self.data[key]
    
class ITableListener(object):
    pass
