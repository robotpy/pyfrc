'''
/*----------------------------------------------------------------------------
/* Copyright (c) FIRST 2008. All Rights Reserved.                              
/* Open Source Software - may be modified and shared by FRC teams. The code   
/* must be accompanied by the FIRST BSD license file in $(WIND_BASE)/WPILib.  
/*----------------------------------------------------------------------------
'''

import math
from ._fake_time import Notifier

class PIDOutput(object):
    pass
    
class PIDSource(object):
    pass

    
class PIDController(object):

    '''
    * Class implements a PID Control Loop.
    * 
    * Runs a specified intervals, reads the given PIDSource and takes
    * care of the integral calculations, as well as writing the given
    * PIDOutput
    '''

    def __init__(self, Kp, Ki, Kd, source, output, period=0.05):
        '''
        * Allocate a PID object with the given constants for P, I, D
        * @param Kp the proportional coefficient
        * @param Ki the integral coefficient
        * @param Kd the derivative coefficient
        * @param source The PIDSource object that is used to get values
        * @param output The PIDOutput object that is set to the output value
        * @param period the loop time for doing calculations. This particularly effects calculations of the
        * integral and differental terms. The default is 50ms.
        '''
    
        self.m_controlLoop = Notifier(self.__calculate)
    
        self.m_P = Kp
        self.m_I = Ki
        self.m_D = Kd
        self.m_maximumOutput = 1.0
        self.m_minimumOutput = -1.0

        self.m_maximumInput = 0
        self.m_minimumInput = 0

        self.m_continuous = False
        self.m_enabled = False
        self.m_setpoint = 0

        self.m_prevError = 0
        self.m_totalError = 0
        self.m_tolerance = .05

        self.m_result = 0
        self.m_error = 0

        self.m_pidInput = source
        self.m_pidOutput = output
        self.m_period = period

        self.m_controlLoop.StartPeriodic(self.m_period)


    def __calculate(self):
        '''
        * Read the input, calculate the output accordingly, and write to the output.
        * This should only be called by the Notifier indirectly through CallCalculate
        * and is created during initialization.
        '''    
        
        enabled = self.m_enabled
        pidInput = self.m_pidInput

        if enabled:
        
            input = pidInput.PIDGet()

            self.m_error = self.m_setpoint - input
            if self.m_continuous:
                
                if math.fabs(self.m_error) > (self.m_maximumInput - self.m_minimumInput) / 2:
                    if self.m_error > 0:
                        self.m_error = self.m_error - self.m_maximumInput + self.m_minimumInput
                    else:
                        self.m_error = self.m_error + self.m_maximumInput - self.m_minimumInput

            potentialIGain = (self.m_totalError + self.m_error) * self.m_I
            
            if potentialIGain < self.m_maximumOutput:
                if potentialIGain > self.m_minimumOutput:
                    self.m_totalError += self.m_error
                else:
                    self.m_totalError = self.m_minimumOutput / self.m_I
            else:
                self.m_totalError = self.m_maximumOutput / self.m_I

            self.m_result = self.m_P * self.m_error + self.m_I * self.m_totalError + self.m_D * (self.m_error - self.m_prevError)
            self.m_prevError = self.m_error

            if self.m_result > self.m_maximumOutput:
                self.m_result = self.m_maximumOutput
            elif self.m_result < self.m_minimumOutput:
                self.m_result = self.m_minimumOutput

            pidOutput = self.m_pidOutput
            result = self.m_result

            pidOutput.PIDWrite(result)
    

    def SetPID(self, p, i, d):
        '''
        * Set the PID Controller gain parameters.
        * Set the proportional, integral, and differential coefficients.
        * @param p Proportional coefficient
        * @param i Integral coefficient
        * @param d Differential coefficient
        '''
        
        self.m_P = p
        self.m_I = i
        self.m_D = d
  
    
    def GetP(self):
        '''
        * Get the Proportional coefficient
        * @return proportional coefficient
        '''
        
        return self.m_P
        

    def GetI(self):
        '''
        * Get the Integral coefficient
        * @return integral coefficient
        '''
        
        return self.m_I

        
    def GetD(self):
        '''
        * Get the Differential coefficient
        * @return differential coefficient
        '''
        
        return self.m_D

        
    def Get(self):
        '''
        * Return the current PID result
        * This is always centered on zero and constrained the the max and min outs
        * @return the latest calculated output
        '''
    
        return self.m_result
        

    def SetContinuous(self, continuous):
        '''
        *  Set the PID controller to consider the input to be continuous,
        *  Rather then using the max and min in as constraints, it considers them to
        *  be the same point and automatically calculates the shortest route to
        *  the setpoint.
        * @param continuous Set to True turns on continuous, False turns off continuous
        '''
        
        self.m_continuous = continuous
    

    def SetInputRange(self, minimumInput, maximumInput):
        '''
        * Sets the maximum and minimum values expected from the input.
        * 
        * @param minimumInput the minimum value expected from the input
        * @param maximumInput the maximum value expected from the output
        '''

        self.m_minimumInput = minimumInput
        self.m_maximumInput = maximumInput    

        self.SetSetpoint(self.m_setpoint)


    def SetOutputRange(self, minimumOutput, maximumOutput):
        '''
        * Sets the minimum and maximum values to write.
        * 
        * @param minimumOutput the minimum value to write to the output
        * @param maximumOutput the maximum value to write to the output
        '''

        self.m_minimumOutput = minimumOutput
        self.m_maximumOutput = maximumOutput

    
    def SetSetpoint(self, setpoint):
        '''
        * Set the setpoint for the PIDController
        * @param setpoint the desired setpoint
        '''

        if self.m_maximumInput > self.m_minimumInput:
        
            if setpoint > self.m_maximumInput:
                self.m_setpoint = self.m_maximumInput
            elif setpoint < self.m_minimumInput:
                self.m_setpoint = self.m_minimumInput
            else:
                self.m_setpoint = setpoint
        else:
            self.m_setpoint = setpoint

            
    def GetSetpoint(self):
        '''
        * Returns the current setpoint of the PIDController
        * @return the current setpoint
        '''

        return self.m_setpoint
        
        
    def GetError(self):
        '''
        * Retruns the current difference of the input from the setpoint
        * @return the current error
        '''

        return self.m_error

        
    def SetTolerance(self, percent):
        '''
        * Set the percentage error which is considered tolerable for use with
        * OnTarget.
        * @param percentage error which is tolerable
        '''
        
        self.m_tolerance = percent
        

    def OnTarget(self):
        '''
        * Return True if the error is within the percentage of the total input range,
        * determined by SetTolerance. This asssumes that the maximum and minimum input
        * were set using SetInput.
        '''

        return math.fabs(self.m_error) < (self.m_tolerance / 100 * (self.m_maximumInput - self.m_minimumInput))
   

    def Enable(self):
        '''
        * Begin running the PIDController
        '''
        
        self.m_enabled = True
        

    def Disable(self):
        '''
        * Stop running the PIDController, this sets the output to zero before stopping.
        '''
        self.m_pidOutput.PIDWrite(0)
        self.m_enabled = False
    

    def IsEnabled(self):
        '''
        * Return True if PIDController is enabled.
        '''
        
        return self.m_enabled
        

    def Reset(self):
        '''
        * Reset the previous error,, the integral term, and disable the controller.
        '''
        self.Disable()

        self.m_prevError = 0
        self.m_totalError = 0
        self.m_result = 0
