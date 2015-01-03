.. unit_tests:

Unit testing robot code
=======================

.. warning:: Currently unit testing is broken for pyfrc 2015, it will be fixed very soon.

pyfrc supports testing robot code using the py.test python testing tool. To
run the unit tests for your robot, just run your robot.py with the following
arguments:

.. code-block:: sh

    Windows:   py robot.py test
    
    Linux/OSX: python3 robot.py test

To find your tests, pyfrc will look for a directory called 'tests' either
next to robot.py, or in the directory above where robot.py resides. See
'samples/simple' for an example test program that starts the robot
code and runs it through autonomous mode and operator mode.

For more information on how to write py.test tests, see the documentation
at http://pytest.org , or refer to the samples directory for examples.

Builtin unit tests
------------------

pyfrc comes with testing functions that can be used to test basic
functionality of just about any robot, including running through a 
simulated practice match. To use these standardized tests, just create a file
in your tests directory called pyfrc_test.py, and put the following contents
in the file:

For an :class:`wpilib.iterativerobot.IterativeRobot` based robot::

    from pyfrc.tests.iterative_robot import *
    
For a :class:`wpilib.samplerobot.SampleRobot` based robot::

    from pyfrc.tests.sample_robot import *

Writing your own test functions
-------------------------------

When running a test, py.test will look for functions in your test modules that
start with 'test\_'. Each of these functions will be ran, and if any errors 
occur the tests will fails. A simple test function might look like this::

    def two_plus(arg):
        return 2 + arg

    def test_addition():
        assert two_plus(2) == 4

The `assert` keyword can be used to test whether something is True or False,
and if the condition is False, the test will fail.

If your test functions have any of the following arguments, then that
argument will be an object as listed below:

* `control`: An instance of :class:`pyfrc.test_support.controller.TestController`
* `fake_time`: An object that controls time for wpilib, use :meth:`get` to retrieve the
  current simulation time from the object
* `hal_data: Provides access to a dict with all the device data about the robot
* `robot`: An instance of your robot class
* `robot_file`: The absolute filename your robot code is started from
* `robot_path`: The absolute directory that your robot code is located at
* `wpilib`: the wpilib module

For more comprehensive examples of writing your own test functions, refer to
the `pyfrc samples <https://github.com/robotpy/pyfrc/tree/master/samples>`_
and the `py.test documentation <http://pytest.org/latest/example/index.html>`_.

code coverage for tests
-----------------------

pyfrc supports testing for code coverage using the `coverage.py
<http://nedbatchelder.com/code/coverage/>`_ module. This
feature can be used with any of the pyfrc commands and provide coverage
information.

For example, to run the 'test' command to run unit tests:

.. code-block:: sh

    Windows:   py robot.py coverage test
    
    Linux/OSX: python3 robot.py coverage test
    
Or to run coverage over the simulator:

.. code-block:: sh

    Windows:   py robot.py coverage sim
    
    Linux/OSX: python3 robot.py coverage sim
    
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

.. note:: There is a py.test module called pytest-cov that is supposed to allow
   you to run code coverage tests. However, I've found that it doesn't work
   particularly well for me, and doesn't appear to be maintained anymore.

.. note:: For some reason, when running the simulation under the code coverage
   tool, the output is buffered until the process exits. This does not happen
   under py.test, however. It's not clear why this occurs. 

Controlling the robot's state
-----------------------------

.. automodule:: pyfrc.test_support.pytest_plugin
   :members:

.. automodule:: pyfrc.test_support.controller
   :members: