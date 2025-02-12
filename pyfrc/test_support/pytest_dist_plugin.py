import multiprocessing
import os
import pathlib
import sys
import time

from typing import Type

import pytest

import robotpy.main
import robotpy.logconfig
import wpilib


from .pytest_plugin import PyFrcPlugin


def _enable_faulthandler():
    #
    # In the event of a segfault, faulthandler will dump the currently
    # active stack so you can figure out what went wrong.
    #
    # Additionally, on non-Windows platforms we register a SIGUSR2
    # handler -- if you send the robot process a SIGUSR2, then
    # faulthandler will dump all of your current stacks. This can
    # be really useful for figuring out things like deadlocks.
    #

    import logging

    logger = logging.getLogger("faulthandler")

    try:
        # These should work on all platforms
        import faulthandler

        faulthandler.enable()
    except Exception as e:
        logger.warning("Could not enable faulthandler: %s", e)
        return

    try:
        import signal

        faulthandler.register(signal.SIGUSR2)
        logger.info("registered SIGUSR2 for PID %s", os.getpid())
    except Exception:
        return


def _run_test(item_nodeid, config_args, robot_class, robot_file, verbose, pipe):
    """This function runs in a subprocess"""
    robotpy.logconfig.configure_logging(verbose)
    _enable_faulthandler()

    # This is used by getDeployDirectory, so make sure it gets fixed
    robotpy.main.robot_py_path = robot_file

    # keep the plugin around because it has a reference to the robot
    # and we don't want it to die and deadlock
    plugin = PyFrcPlugin(robot_class, robot_file, True)

    ec = pytest.main(
        [item_nodeid, "--no-header", *config_args],
        plugins=[plugin],
    )

    # ensure output is printed out
    # .. TODO could implement pytest_runtestloop and send the
    #    test result back to the parent and print it there?
    sys.stdout.flush()

    # Don't let the process die, let the parent kill us to avoid
    # python interpreter badness
    pipe.send(ec)

    # ensure that the gc doesn't collect the plugin..
    while plugin:
        time.sleep(100)


def _run_test_in_new_process(
    test_function, config, robot_class, robot_file, builtin_tests, verbose
):
    """Run a test function in a new process."""

    config_args = config.invocation_params.args
    if builtin_tests:
        item_nodeid = f"{config_args[0]}::{test_function.name}"
        config_args = config_args[1:]
    else:
        item_nodeid = test_function.nodeid

    parent, child = multiprocessing.Pipe()

    process = multiprocessing.Process(
        target=_run_test,
        args=(item_nodeid, config_args, robot_class, robot_file, verbose, child),
    )
    process.start()
    try:
        ec = parent.recv()
    finally:
        process.kill()

    if ec != 0:
        pytest.fail(
            f"Test failed in subprocess: {item_nodeid} (exit code {ec})",
            pytrace=False,
        )


def _make_runtest(item, config, robot_class, robot_file, builtin_tests, verbose):
    def isolated_runtest():
        _run_test_in_new_process(
            item, config, robot_class, robot_file, builtin_tests, verbose
        )

    return isolated_runtest


class DistPlugin:

    def __init__(
        self,
        robot_class: Type[wpilib.RobotBase],
        robot_file: pathlib.Path,
        builtin_tests: bool,
        verbose: bool,
    ) -> None:
        self._robot_class = robot_class
        self._robot_file = robot_file
        self._builtin_tests = builtin_tests
        self._verbose = verbose

    @pytest.hookimpl(tryfirst=True)
    def pytest_collection_modifyitems(
        self,
        session: pytest.Session,
        config: pytest.Config,
        items: list[pytest.Function],
    ):
        """Modify collected test items to run each in a new process."""

        multiprocessing.set_start_method("spawn")

        for item in items:
            # Overwrite the runtest protocol for each item
            item.runtest = _make_runtest(
                item,
                config,
                self._robot_class,
                self._robot_file,
                self._builtin_tests,
                self._verbose,
            )

    #
    # These fixtures match the ones in PyFrcPlugin but these have no effect
    #

    @pytest.fixture(scope="function", autouse=True)
    def robot(self):
        pass

    @pytest.fixture(scope="function")
    def control(self, reraise, robot):
        pass

    @pytest.fixture()
    def robot_file(self):
        pass

    @pytest.fixture()
    def robot_path(self):
        pass
