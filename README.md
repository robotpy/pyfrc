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
	
code coverage support
---------------------

If you wish to run code coverage testing, then you must install the following
package:

* coverage (https://pypi.python.org/pypi/coverage)

It requires a compiler to install from source, so if you're on Windows you
probably just want to download the binary from pypi and install that, instead
of trying to install from pip.

Quick Demo
==========

Once you get this installed, then you can run a quick demo with the following:

	cd samples/physics/src/
	python3 robot.py sim

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

Robot 'physics model'
---------------------

pyfrc now supports a simplistic custom physics model implementations for
simulation and testing support. It can be as simple or complex as you want
to make it. Hopefully in the future we will be adding helper functions to
make this a lot easier to do.

The idea here is you provide a simulation object that overrides specific
pieces of WPILib, and modifies motors/sensors accordingly depending on the
state of the simulation. An example of this would be measuring a motor
moving for a set period of time, and then changing a limit switch to turn 
on after that period of time. This can help you do more complex simulations
of your robot code without too much extra effort.

By default, pyfrc doesn't modify any of your inputs/outputs without being
told to do so by your code or the simulation GUI. 

See samples/physics for more details. The API has changed a bit as of 
pyfrc 2014.7.0

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

code coverage for tests
-----------------------

pyfrc supports testing for code coverage using the coverage.py module. This
feature can be used with any of the pyfrc commands and provide coverage
information.

For example, to run the 'test' command to run unit tests:

    $ python3 robot.py coverage test
    
Or to run coverage over the simulator:

    $ python3 robot.py coverage sim
	
Running code coverage while the simulator is running is nice, because you
don't have to write unit tests to make sure that you've completely covered
your code. Of course, you *should* write unit tests anyways... but this is
good for developing code that needs to be run on the robot quickly and you
need to make sure that you tested everything first.

When using the code coverage feature, what actually happens is robot.py gets
executed *again*, except this time it is executed using the coverage module.
This allows coverage.py to completely track code coverage, otherwise any
modules that are imported by robot.py (and much of robot.py itself) would not
be reported as covered. 

Note: There is a py.test module called pytest-cov that is supposed to allow
you to run code coverage tests. However, I've found that it doesn't work
particularly well for me, and doesn't appear to be maintained anymore.

Note II: For some reason, when running the simulation under the code coverage
tool, the output is buffered until the process exits. This does not happen
under py.test, however. It's not clear why this occurs.  

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

Adding custom tooltips to motors/sensors
----------------------------------------

If you move the mouse over the motors/sensors in the simulator user interface,
you will notice that tooltips are shown which show which type of object is
using the slot. pyfrc will now read the 'label' attribute from each object,
and if present it will display that as the tooltip instead. For example:

    motor = wpilib.Jaguar(1)
    motor.label = 'whatzit motor'

I haven't tested it on the cRio yet, but I believe that this should not affect
operation on the robot, as RobotPy will just ignore the extra attribute.


Implementation Notes
====================

SmartDashboard/NetworkTables support
------------------------------------

The implementation of wpilib contained with pyfrc has a 'fake' implementation
of SmartDashboard/NetworkTables within it. The simulator functionality can
also use pynetworktables as the NetworkTables base when instructed.

Internals
---------

The lib/pyfrc/wpilib directory is the code for wpilib directly copied from 
the RobotPy implementation. This code tries to load a module called '_wpilib',
which is a binary python module on the robot. However, in the directory 
lib/pyfrc/wpilib/_wpilib there is a python package which emulates a lot of
the functionality found in the binary package for wpilib. 


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
