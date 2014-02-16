pyfrc - RobotPy development library helper
==========================================

pyfrc is a python 3 library designed to make developing code for RobotPy (the
Python interpreter for the FIRST Robotics Competition) easier.

This library contains a few primary parts:

* A built-in uploader that will upload your robot code to the robot
* An implementation of wpilib that will run on your computer

  This is a library designed to emulate parts of WPILib so you can more easily
  do unit testing of your robot code on any platform that supports python3,
  without having to have a cRio around for testing. 

    NOTE: This is not a complete implementation of WPILib. Add more things
    as needed, and submit patches! :) 
    
* Integration with the py.test testing tool to allow you to easily write unit
  tests for your robot code.
* A robot simulator tool which allows you to run your code in (vaguely) real
  time and get simple feedback via a tk-based UI


Installation
============

using pip to install
--------------------

The easiest installation is by using pip. On a linux/OSX system that has pip
installed, just run the following command:

	$ pip-3.2 install pyfrc
	
If you have python 3.3 installed, you may need to use 'pip-3.3' instead.

On Windows, I recommend using pip-Win to install packages. Download it from:

	https://sites.google.com/site/pydatalog/python/pip-for-windows
	
Once you've downloaded it, run it to install pip, and run the following
command in its window:

	pip install pyfrc


Non-pip installation
--------------------

You must have the following python packages installed. Make sure that you
install them for your python3 interpreter, as pyfrc only supports python 3.

* py.test (http://pytest.org/)

Once you have those installed, you can just install pyfrc the same way 
you would install most other python programs:

	$ python3 setup.py install

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
        wpilib.run(min_version='2014.4.0')


py.test unit testing integration support
========================================

pyfrc supports testing robot code using the py.test python testing tool.

See 'samples/simple' for an example test program that starts the robot
code and runs it through autonomous mode and operator mode. 

To run the unit tests, just run your robot.py with the following arguments:

	$ python3 robot.py test

For more information on how to write py.test tests, see the documentation
at http://pytest.org , or refer to the samples directory for examples.

test fixtures
-------------

If your test functions have any of the following arguments, then that
argument will be an object as listed below:

* control: the wpilib.internal module
* fake_time: the module that controls time for wpilib, use Get() to retrieve the
  current simulation time
* robot: An instance of your robot class
* robot_file: the filename your robot code is started from
* robot_path: the directory that your robot is located
* wpilib: the wpilib module


robot simulator
===============

The pyfrc robot simulator allows very simplistic simulation of your code
in real time and displays the results in a (ugly) user interface. To run
the simulator, run your robot.py with the following arguments:

    $ python3 robot.py sim
    
If you wish to run so that your simulator can connect to the SmartDashboard,
if you have pynetworktables installed you can run the following:

	$ python3 robot.py netsim

Or you can use this instead:

    $ python3 robot.py sim --enable-pynetworktables

As there is interest, I will add more features to the simulator. Please feel
free to improve it and submit pull requests!


Implementation Notes
====================

SmartDashboard/NetworkTables support
------------------------------------

The implementation of wpilib contained with pyfrc has a 'fake' implementation
of SmartDashboard/NetworkTables within it. The simulator functionality can
also use pynetworktables as the NetworkTables base when instructed.

Internals
---------

The implementation of wpilib that you can run on your computer is contained
in the 'lib' directory. If you use the 'run_test.py' script to run your
tests, it will automatically setup the python path correctly so that loading
fake_wpilib will load the correct package. 

The lib/pyfrc/wpilib directory is the code for wpilib directly copied from 
the RobotPy implementation. This code tries to load a module called '_wpilib',
which is a binary python module on the robot. However, in the directory 
lib/pyfrc/wpilib/_wpilib there is a python package which emulates a lot of
the functionality found in the binary package for wpilib. 

The StartCompetition function is monkey-patched by run_test.py so that the
library and test runners can load properly. 

Contributing new changes
========================

1. Fork this git repository
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create new Pull Request on github


Authors
=======

Dustin Spicuzza (dustin@virtualroadside.com)

pyfrc is derived from (and supercedes) fake_wpilib, which was developed with
contributions from Sam Rosenblum and Team 2423. 
