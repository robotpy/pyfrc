from collections import namedtuple

MotorModelConfig = namedtuple(
    "MotorModelConfig",
    [
        "name",
        "nominalVoltage",
        "freeSpeed",
        "freeCurrent",
        "stallTorque",
        "stallCurrent",
    ],
)
MotorModelConfig.__doc__ = """
    Configuration parameters useful for simulating a motor. Typically these
    parameters can be obtained from the manufacturer via a data sheet or other
    specification.
    
    RobotPy contains MotorModelConfig objects for many motors that are commonly
    used in FRC. If you find that we're missing a motor you care about, please
    file a bug report and let us know!
    
    .. note:: The motor configurations that come with pyfrc are defined using the
              pint units library. See :ref:`units`
    
"""
MotorModelConfig.name.__doc__ = "Descriptive name of motor"
MotorModelConfig.nominalVoltage.__doc__ = "Nominal voltage for the motor"
MotorModelConfig.freeSpeed.__doc__ = "No-load motor speed (``1 / [time]``)"
MotorModelConfig.freeCurrent.__doc__ = "No-load motor current"
MotorModelConfig.stallTorque.__doc__ = (
    "Stall torque (``[length]**2 * [mass] / [time]**2``)"
)
MotorModelConfig.stallCurrent.__doc__ = "Stall current"

from .units import units

NOMINAL_VOLTAGE = 12 * units.volts

#: Motor configuration for CIM
MOTOR_CFG_CIM = MotorModelConfig(
    "CIM",
    NOMINAL_VOLTAGE,
    5310 * units.cpm,
    2.7 * units.amp,
    2.42 * units.N_m,
    133 * units.amp,
)

#: Motor configuration for Mini CIM
MOTOR_CFG_MINI_CIM = MotorModelConfig(
    "MiniCIM",
    NOMINAL_VOLTAGE,
    5840 * units.cpm,
    3.0 * units.amp,
    1.41 * units.N_m,
    89.0 * units.amp,
)

#: Motor configuration for Bag Motor
MOTOR_CFG_BAG = MotorModelConfig(
    "Bag",
    NOMINAL_VOLTAGE,
    13180 * units.cpm,
    1.8 * units.amp,
    0.43 * units.N_m,
    53.0 * units.amp,
)

#: Motor configuration for 775 Pro
MOTOR_CFG_775PRO = MotorModelConfig(
    "775Pro",
    NOMINAL_VOLTAGE,
    18730 * units.cpm,
    0.7 * units.amp,
    0.71 * units.N_m,
    134 * units.amp,
)

#: Motor configuration for Andymark RS 775-125
MOTOR_CFG_775_125 = MotorModelConfig(
    "RS775-125",
    NOMINAL_VOLTAGE,
    5800 * units.cpm,
    1.6 * units.amp,
    0.28 * units.N_m,
    18.0 * units.amp,
)

#: Motor configuration for Banebots RS 775
MOTOR_CFG_BB_RS775 = MotorModelConfig(
    "RS775",
    NOMINAL_VOLTAGE,
    13050 * units.cpm,
    2.7 * units.amp,
    0.72 * units.N_m,
    97.0 * units.amp,
)

#: Motor configuration for Andymark 9015
MOTOR_CFG_AM_9015 = MotorModelConfig(
    "AM-9015",
    NOMINAL_VOLTAGE,
    14270 * units.cpm,
    3.7 * units.amp,
    0.36 * units.N_m,
    71.0 * units.amp,
)

#: Motor configuration for Banebots RS 550
MOTOR_CFG_BB_RS550 = MotorModelConfig(
    "RS550",
    NOMINAL_VOLTAGE,
    19000 * units.cpm,
    0.4 * units.amp,
    0.38 * units.N_m,
    84.0 * units.amp,
)

#: Motor configuration for NEO 550 Brushless Motor
MOTOR_CFG_NEO_550 = MotorModelConfig(
    "NEO 550",
    NOMINAL_VOLTAGE,
    11000 * units.cpm,
    1.4 * units.amp,
    0.97 * units.N_m,
    100 * units.amp,
)

#: Motor configuration for Falcon 500 Brushless Motor
MOTOR_CFG_FALCON_500 = MotorModelConfig(
    "Falcon 500",
    NOMINAL_VOLTAGE,
    6380 * units.cpm,
    1.5 * units.amp,
    4.69 * units.N_m,
    257 * units.amp,
)

del units
