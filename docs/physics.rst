Simulation Physics
==================

.. _physics_model:

.. automodule:: pyfrc.physics.core
   :members:

Drivetrain support
------------------

.. automodule:: pyfrc.physics.drivetrains
   :members:

Motor configurations
--------------------

.. automodule:: pyfrc.physics.motor_cfgs
  :members:

Motion support
--------------

.. automodule:: pyfrc.physics.motion
   :members:

Tank drive model support
------------------------

.. automodule:: pyfrc.physics.tankmodel
   :members:

.. _units:

Unit conversions
----------------

.. automodule:: pyfrc.physics.units
   :members:

Custom labels
-------------

If you write data to the 'custom' key of the ``hal_data`` dictionary, the
data will be shown on the pyfrc simulation UI. The key will be the label for
the data, and the value will be rendered as text inside the box::

    # first time you set the data
    hal_data.setdefault('custom', {})['My Label'] = '---'
    
    # All other times
    hal_data['custom']['My Label'] = 1


.. versionadded:: 2018.3.0

Custom drawing
--------------

.. autofunction:: pyfrc.sim.get_user_renderer

.. autoclass:: pyfrc.sim.field.user_renderer.UserRenderer
   :members:

Camera 'simulator'
------------------

.. automodule:: pyfrc.physics.visionsim
   :members:
