
import inspect

from hal_impl import mode_helpers
from hal_impl.data import hal_data

from .fake_time import _DSCondition

class _PracticeMatch:
      
    autonomous_period = 10
    operator_period = 120
    
    def __init__(self, on_step):
        self._on_step = on_step
    
    def on_step(self, tm):
        '''
            Called when a driver station packet would be delivered
        '''
        
        if tm < 5:
            mode_helpers.set_mode('auto', False)
        
        elif tm < 5 + self.autonomous_period:
            mode_helpers.set_mode('auto', True)
            
        elif tm < 5 + self.autonomous_period + 1:
            mode_helpers.set_mode('teleop', False)
        
        elif tm < 5 + self.autonomous_period + 1 + self.operator_period:
            mode_helpers.set_mode('teleop', True)
            
        else:
            return False
        
        return self._on_step(tm)
    

class TestController:
    '''
        An object that you can use to control tests. You control the tests
        via the on_step function.
    '''
    
    def __init__(self, fake_time_inst):
        self._ds_cond = fake_time_inst._setup()
    
    def _on_step(self, value):
        
        if inspect.isclass(value):
            obj = value()
            self._ds_cond._on_step = obj.on_step
        
        elif callable(value):
            self._ds_cond._on_step = value
          
        else:
            raise ValueError("Invalid object passed to on_step")
    
    #: Set this to a function that takes a single argument, and it
    #: will be called when a new driver station packet would be received
    #: If this is an object, then it will be constructed and it's on_step
    #: function will be called
    on_step = property(fset=_on_step)
    
    def setup_practice_match(self, on_step=lambda tm: True):
        '''Call this function to enable a practice match. Just call
        startCompetition() on your robot object
        
        :param on_step: If set, is called on each simulation step
        '''
        pm = _PracticeMatch(on_step)
        self._ds_cond._on_step = pm.on_step
   
    def set_autonomous(self, enabled=True):
        '''Puts the robot in autonomous mode'''
        mode_helpers.set_mode('auto', enabled)
    
    def set_operator_control(self, enabled=True):
        '''Puts the robot in operator control mode'''
        mode_helpers.set_mode('teleop', enabled)
        
    def set_test_mode(self, enabled=True):
        '''Puts the robot in test mode'''
        mode_helpers.set_mode('test', enabled)
    

