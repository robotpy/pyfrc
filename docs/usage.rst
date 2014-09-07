Usage
=====

Once you modify your robot code, you can directly run your robot.py file
and the pyfrc features will be enabled. You must modify your code slightly
to make this work correctly.


Robot Code Modifications
------------------------

There are a few modifications that you need to make to your robot.py
to take advantage of the features provided by pyfrc. 

* Your import statement must catch the wpilib import error and import
  wpilib from pyfrc instead.
* Your run() function must return the Robot object you create
* You must add a block that calls wpilib.run() at the bottom of your
  program
* You must define all of your motors and sensors inside of your robot
  class, and they cannot be global variables. This allows them to be
  reset each time a new test is created, as a new instance of your 
  robot is created each time a test is run.

robot.py:

    try:
        import wpilib
    except ImportError:
        from pyfrc import wpilib
        
    ...

    def run():
        robot = MyRobot()
        robot.StartCompetition()
        
        return robot
        
    if __name__ == '__main__':
        wpilib.run(min_version='2014.7.3')


SmartDashboard/NetworkTables support
------------------------------------

The implementation of wpilib contained with pyfrc has a 'fake' implementation
of SmartDashboard/NetworkTables within it. The simulator functionality can
also use `pynetworktables <https://github.com/robotpy/pynetworktables>`_ 
as the NetworkTables base when instructed.

