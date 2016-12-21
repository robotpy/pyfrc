pyfrc - RobotPy development library helper
==========================================

[![Build Status](https://travis-ci.org/robotpy/pyfrc.svg)](https://travis-ci.org/robotpy/pyfrc)

pyfrc is a python 3 library designed to make developing python code using WPILib for
FIRST Robotics Competition easier.

This library contains a few primary parts:

* A built-in uploader that will upload your robot code to the robot
* Integration with the py.test testing tool to allow you to easily write unit
  tests for your robot code.
* A robot simulator tool which allows you to run your code in (vaguely) real
  time and get simple feedback via a tk-based UI
  
Documentation
=============

For usage, detailed installation information, and other notes, please see
our documentation at http://pyfrc.readthedocs.io

Quick Install + Demo
====================

If you have python3 and pip installed, then do:

    pip3 install pyfrc

Once this is done, you can run a quick demo by running:

    cd samples/physics/src/
    python3 robot.py sim


Contributing new changes
========================

pyfrc is intended to be a project that all members of the FIRST community can
quickly and easily contribute to. If you find a bug, or have an idea that you
think others can use:

1. [Fork this git repository](https://github.com/robotpy/robotpy/fork) to your github account
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push -u origin my-new-feature`)
5. Create new Pull Request on github


Authors
=======

Dustin Spicuzza (dustin@virtualroadside.com)

Contributors:

* Sam Rosenblum
* James Ward
* Christian Balcom
* Others

pyfrc is originally derived from (and supercedes) fake_wpilib, which was
developed with contributions from Sam Rosenblum and Team 2423. 
