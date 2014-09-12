Usage
=====

Once you modify your robot code, you can directly run your robot.py file
and the pyfrc features will be enabled. You must modify your code slightly
to make this work correctly.


Robot Code Modifications
------------------------

There are a few modifications that you need to make to your robot.py
to take advantage of the features provided by pyfrc. 

* Your import statement must catch the wpilib :exc:`ImportError` and import
  wpilib from pyfrc instead.
* Your run() function must return the Robot object you create
* You must add a block that calls wpilib.run() at the bottom of your
  program
* You must define all of your motors and sensors inside of your robot
  class, and they cannot be global variables. This allows them to be
  reset each time a new test is created, as a new instance of your 
  robot is created each time a test is run.

An example robot.py with the modifications looks like this::

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
of SmartDashboard/NetworkTables within it. If you have 
`pynetworktables <https://github.com/robotpy/pynetworktables>`_ installed, the
simulator can be used to communicate with the SmartDashboard or other
NetworkTables clients.

For more details, see :ref:`smartdashboard`

Uploading code to the robot
---------------------------

This command will first run any unit tests on your robot code, and if they
pass then it will upload the robot code to the cRio. Running the tests is
really important, so you can catch errors in your code before you run it 
on the robot.

.. code-block:: sh

    python3 robot.py upload

Of course, maybe you really need to upload the code, and don't care about the
tests. That's OK, you can still upload code to the robot:

.. code-block:: sh

    python3 robot.py upload --skip-tests

Running an interactive robot simulation
---------------------------------------

The simple robot simulation available in pyfrc will let you interact with your
robot via a simple UI that shows the status of all your motors and sensors,
and lets you give it input too. There is also a field simulator that will show
the position of your robot on a simulated field.

.. code-block:: sh

    python3 robot.py sim

Or if you want to be able to connect to the SmartDashboard, use:

.. code-block:: sh

    python3 robot.py netsim

For more details, see :doc:`simulator`

Running unit tests
------------------

.. code-block:: sh

    python3 robot.py test

For more details, see :doc:`testing`
