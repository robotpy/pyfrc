
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
        
    fake_wpilib/
        fake_wpilib/
        run_test.py
        
    test.sh
    test.bat
    
In this example layout, you would need to specify the TEST_MODULES as
'tests', and FAKE_WPILIB_DIR as 'fake_wpilib'

After configuring the directories properly, you should use test.sh or
test.bat to launch tests using fake_wpilib, instead of directly invoking
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
=====================

All test programs should live in the test modules directory, which is 
specified by the --test-modules argument to run_test.py

See 'samples/import_test.py' for an example test program that starts the
robot code and runs it through autonomous mode and operator mode. 
