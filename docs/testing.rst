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

