# def pytest_runtest_setup():
#     import wpilib
#     import networktables

#     try:
#         networktables.NetworkTables.setTestMode()
#     except AttributeError:
#         networktables.NetworkTables.startTestMode()

#     wpilib.DriverStation._reset()
