
Fake WPILib for Python
----------------------

This is a library designed to emulate parts of WPILib so you can more easily
do unit testing of your robot code on any platform that supports python3,
without having to have a cRio around for testing. 

    NOTE: This is not a complete implementation of WPILib. Add more things
    as needed, and submit patches! :) 


Usage
-----

run_test.py will launch a test module, which should specify the location that
robot.py is located for that test. 

Copy test.sh.example and/or test.bat.example to your project, and modify
the paths in the file to point to run_test.py and a directory for 
test modules to reside. An example directory structure might look like this:

    src/
        robot.py
        
    tests/
        test1.py
        test2.py
        
    fake-wpilib/
        lib/
            _wpilib/
            fake_wpilib/
            
        samples/
        
        run_test.py
        
    test.sh
    test.bat
    
In this example layout, you would need to specify the TEST_MODULES as
'tests', and FAKE_WPILIB_DIR as 'fake-wpilib'

After configuring the directories properly, you should use test.sh or
test.bat to launch tests using fake-wpilib, instead of directly invoking
run_test.py


Robot Code Modifications
------------------------

Ideally, the only modifications you will need to make to your robot code
to support testing using this library is changing your WPILib import 
statement as shown below, and the run() statement in robot.py must 
return an object that derives from SimpleRobot.

robot.py:

    try:
        import wpilib
    except ImportError:
        import fake_wpilib as wpilib
        
    ...

    def run():
        robot = MyRobot()
        robot.StartCompetition()
        
        return robot


Writing test programs
---------------------

All test programs should live in the test modules directory, which is 
specified by the --test-modules argument to run_test.py

Test modules must have the following required elements:

	Variable:		robot_path
	Description:	This is the directory that robot.py is located, 
					relative to the test module's file. 
					
	Function:		run_tests
	Parameters:		robot_module, myrobot
	Description:	This function is called at the beginning of the test.
					The first argument will be a reference to the robot.py
					module, and the second argument will be the instance
					of the robot class that was returned from the robot.py
					run function.    

Test modules may have the following optional elements:

	Variable: 		import_robot
	Description:	If set to False, robot.py will not be imported, but
					the robot path details will be setup correctly. This
					allows you to run unit tests that only involve a
					single specific component. If False, run_tests will
					be called with zero arguments. Default is True.


See 'samples/import_test.py' for an example test program that starts the
robot code and runs it through autonomous mode and operator mode. 

SmartDashboard/NetworkTables support
------------------------------------

If you have pynetworktables installed, fake_wpilib can use that for
SmartDashboard/NetworkTables instead of the thin non-functional objects
that come with fake_wpilib. You need to adjust your test.bat/test.sh 
to tell fake_wpilib to use it (disabled by default), and you need to
install pynetworktables for your python interpreter.  

pynetworktables is a python module which allows the NetworkTables 
implementation in WPILib to run on a PC. Using the current version of 
SmartDashboard, you can connect to the test program running on your PC 
using the following command:

	C:\Program Files\SmartDashboard\SmartDashboard.jar ip 127.0.0.1
	
See https://github.com/robotpy/pynetworktables for more information.

Implementation Notes
--------------------

The implementation of wpilib that you can run on your computer is contained
in the 'lib' directory. If you use the 'run_test.py' script to run your
tests, it will automatically setup the python path correctly so that loading
fake_wpilib will load the correct package. 

The lib/fake_wpilib directory is the code for wpilib directly copied from 
the RobotPy implementation. This code tries to load a module called '_wpilib',
which is a binary python module on the robot. However, in lib/_wpilib there 
is a python package which emulates a lot of the functionality found in the
binary package for wpilib. 

The StartCompetition function is monkey-patched by run_test.py so that the
library and test runners can load properly. 

