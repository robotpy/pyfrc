Anatomy of a robot
==================

.. note:: The following assumes you have some familiarity with python, and
          is meant as a primer to creating robot code using RobotPy and
          pyfrc. If you're not familar with python, you might try these
          resources:

          * `CodeAcademy <http://www.codecademy.com/tracks/python>`_
          * `Wikibooks python tutorial <https://en.wikibooks.org/wiki/Non-Programmer%27s_Tutorial_for_Python_3>`_
          * `Python 3.4 Tutorial <https://docs.python.org/3.4/tutorial/>`_
          
This tutorial will go over the things necessary for very basic robot
code that can run on an FRC robot using `RobotPy <http://firstforge.wpi.edu/sf/projects/robotpy>`_
and can also utilize the pyfrc robot simulator.

Your robot code must start within a file called `robot.py`. Your code
can do anything a normal python program can, such as importing other
python modules & packages. Here are the basic things you need to know to
get your robot code working!

Importing necessary modules
---------------------------

All of the code that actually interacts with your robot's hardware is
contained in a library called WPILib. When you're running your code 
outside of the robot, pyfrc has a partial implementation of wpilib
available so you can run simulations of your robot on your computer. To
facilitate this, you should always include the following at the top
of your python modules that require wpilib::

    try:
        import wpilib
    except ImportError:
        from pyfrc import wpilib


Robot object
------------

Every valid robot program compatible with pyfrc must define an object that
inherits from either `wpilib.SimpleRobot` or `wpilib.IterativeRobot`. These
objects define a number of functions that you need to override, which get
called at various times.

* :class:`pyfrc.wpilib.core.IterativeRobot` functions
* :class:`pyfrc.wpilib.core.SimpleRobot` functions


An incomplete version of your robot object might look like this::

    class MyRobot(wpilib.SimpleRobot):

        def __init__(self):
            super().__init__()
            self.motor = wpilib.Jaguar(1)

There are some subtle but important things to notice here:

* You must call `super().__init__()` in your `__init__` method, or the code
  will fail on the robot.

Adding motors and sensors
-------------------------

Everything that interacts with the robot hardware directly must use the wpilib
library to do so. The python version of WPILib is a wrapper over the C++ 
version of WPILib, so you can use the WPILib C++ Documentation to figure out
what objects and methods are available. A version of the WPILib documentation is `available online <http://www.virtualroadside.com/WPILib/index.html>`_.

For example, if you wanted to create an object that interacted with a Jaguar
motor controller via PWM, you could look through the documentation and read
the `documentation for the Jaguar <http://www.virtualroadside.com/WPILib/class_jaguar.html>`_. You can see that the constructor takes a single 
argument (a `uint32_t`, which is translated into an integer in python) that
indicates which PWM port to connect to. You could create the `Jaguar` object
that is using port 4 using the following python code in your `__init__` method::

    self.motor = wpilib.Jaguar(4)

Looking through the documentation some more, you would notice that to set
the PWM value of the motor, you need to call the `Set` function. The docs
say that the value needs to be between -1.0 and 1.0, so to set the motor
full speed forward you could do this::

    self.motor.Set(1)

Other motors and sensors have similar conventions.

.. note:: 
  You should *only* create instances of your motors and other WPILib hardware
  devices (Gyros, Joysticks, Sensors, etc) in the `__init__` method of your
  robot object. If you don't, the robot testing capabilities of pyfrc may not
  function correctly.


run function
------------

When the robot code is launched on the robot, RobotPy looks inside `robot.py`
for a function called `run` and calls it. This function needs to create an
instance of your robot object, call `StartCompetition()`, and return the
instance. It should look something like this::

    def run():
        robot = MyRobot()
        robot.StartCompetition()
        return robot

Main block
----------

Languages such as Java require you to define a 'static main' function. In
python, because every .py file is usable from other python programs, you
need to `define a code block which checks for __main__ <http://effbot.org/pyfaq/tutor-what-is-if-name-main-for.htm>`_. Inside your main block, you run code
that is only ran on your computer, and not on the robot. Most robot code will
have something that looks like this::
    
    if __name__ == '__main__':
        wpilib.run()


.. note:: Code inside of this block won't actually run on the robot. On the
          cRio, robot.py is imported from another module, and it looks for
          your 'run' function.

Putting it all together
-----------------------

If you combine all the pieces above, you end up with something like this
below, taken from one of the samples included with pyfrc.

.. literalinclude:: ../samples/simple/src/robot.py


There are a few different robot samples that are packaged with pyfrc, you
can find them on `pyfrc's github site <https://github.com/robotpy/pyfrc/tree/master/samples>`_.

Important robot concepts
------------------------

TODO: Explain these better

* Never use while loops in your robot code

