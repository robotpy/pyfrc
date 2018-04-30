'''
    pyfrc uses the pint library in some places for representing physical
    quantities to allow users to specify the physical parameters of their robot
    in a natural and non-ambiguous way. For example, to represent 5 feet::
    
        from pyfrc.physics.units import units
        
        five_feet = 5 * units.feet
        
    Unfortunately, actually using the quantities is a huge performance hit, so
    we don't use them to perform actual physics computations. Instead, pyfrc uses
    them to convert to known units, then performs computations using
    the magnitude of the quantity.
    
    pyfrc defines the following custom units:
    
    * ``counts_per_minute`` or ``cpm``: Counts per minute, which should be used
      instead of pint's predefined ``rpm`` (because it is rad/s). Used to
      represent motor free speed
    * ``N_m``: Shorthand for N-m or newton-meter. Used for motor torque.
    
    * ``tm_ka``: The kA value used in the tankmodel (uses imperial units)
    * ``tm_kv``: The kV value used in the tankmodel (uses imperial units)
    
    Refer to the `pint documentation <https://pint.readthedocs.io>`_ for more
    information on how to use pint.
'''


import pint

#: All units that pyfrc uses are defined in this global object
units = pint.UnitRegistry()

# Shorthand notation used to represent motor torque
units.define('N_m = newton * meter')

# Counts per minute. pint defines RPM, but it is in rad/s, which is not often
# what we want
units.define('counts_per_minute = count / minute = cpm')

# Special units used in the tankmodel
units.define('tm_kv = volt / (foot / second)')
units.define('tm_ka = volt / (foot / second ** 2)')

# Helper functions
class Helpers:
    ensure_mass = units.check('[mass]')(lambda u: u)
    ensure_length = units.check('[length]')(lambda u: u)
    
    ensure_acceleration = units.check('[length] / [time]**2')(lambda u: u)
    ensure_time = units.check('[time]')(lambda u: u)
    ensure_velocity = units.check('[length] / [time]')(lambda u: u)

# Monkeypatch in these useful functions (hopefully they'll make it to pint 0.9)
# -> https://github.com/hgrecco/pint/pull/637
if not hasattr(units.Unit, 'from_'):

    def _from_(self, value, strict=True, name='value'):
        """Converts a numerical value or quantity to this unit

        :param value: a Quantity (or numerical value if strict=False) to convert
        :param strict: boolean to indicate that only quanities are accepted
        :param name: descriptive name to use if an exception occurs
        :return: The converted value as this unit
        :raises:
            :class:`ValueError` if strict and one of the arguments is not a Quantity.
        """
        if self._check(value):
            if not isinstance(value, self._REGISTRY.Quantity):
                value = self._REGISTRY.Quantity(1, value)
            return value.to(self)
        elif strict:
            raise ValueError("%s must be a Quantity" % value)
        else:
            return value * self
    
    units.Unit.from_ = _from_

if not hasattr(units.Unit, 'm_from'):

    def _m_from(self, value, strict=True, name='value'):
        """Converts a numerical value or quantity to this unit, then returns
        the magnitude of the converted value

        :param value: a Quantity (or numerical value if strict=False) to convert
        :param strict: boolean to indicate that only quanities are accepted
        :param name: descriptive name to use if an exception occurs
        :return: The magnitude of the converted value
        :raises:
            :class:`ValueError` if strict and one of the arguments is not a Quantity.
        """
        return self.from_(value, strict=strict, name=name).magnitude

    units.Unit.m_from = _m_from
