
def pytest_runtest_setup():
    import wpilib
    import networktables
    
    networktables.NetworkTables.setTestMode()
    wpilib.DriverStation._reset()
