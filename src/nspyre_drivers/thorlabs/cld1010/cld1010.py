"""Driver for the Thorlabs CLD1010LP.

Programming manual: 
https://www.thorlabs.com/drawings/84b68761fa2c704c-5D5DD69C-9E91-8A48-043C41D5A362BD66/CLD1010LP-ProgrammersReferenceManual.pdf

Copyright (c) 2022, Jacob Feder, Ben Soloway
All rights reserved.
"""
import logging

from pyvisa import ResourceManager

logger = logging.getLogger(__name__)

class CLD1010:
    def __init__(self, address, max_diode_current):
        """
        Args:
            address: PyVISA resource path.
            max_diode_current: Max current of the diode installed in the CLD1010.
        """
        self.rm = ResourceManager('@py')
        self.address = address
        self.max_diode_current = max_diode_current

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.off()
        self.close()

    def __str__(self):
        return f'{self.address} {self.idn}'

    def open(self):
        try:
            self.laser = self.rm.open_resource(self.address)
        except Exception as err:
            raise ConnectionError(f'Failed connecting to CLD1010 @ [{self.address}]') from err
        # 1 second timeout
        self.laser.timeout = 1000
        self.idn = self.laser.query('*IDN?')
        logger.info(f'Connected to CLD1010 [{self}].')
        return self

    def close(self):
        self.laser.close()

    def idn(self):
        return self.laser.query('*IDN?')

    def get_ld_state(self):
        """Check if diode is lasing."""
        if int(self.laser.query('OUTP1:STAT?')):
            return True
        else:
            return False

    def set_ld_state(self, value):
        self.laser.write(f'OUTP1:STAT {value}')

    def get_max_current(self):
        return float(self.laser.query('SOUR:CURR:LIM:AMPL?'))

    def set_max_current(self, value):
        """Set the maximum laser diode current. This is the setpoint when the laser is enabled in modulation mode."""
        if value > self.max_diode_current:
            raise ValueError(f'Current setpoint: [{value}] is larger than max diode current [{self.max_diode_current}]).')

        laser_status = False
        if self.get_ld_state():
            laser_status = True
            # laser is on, so turn it off first
            self.off()

        self.laser.write(f'SOUR:CURR:LIM:AMPL {value:.5f}')

        # turn the laser back on if it was on before
        if laser_status:
            self.on()

    def meas_current(self):
        return float(self.laser.query('MEAS:CURR?'))

    def get_current_setpoint(self):
        return float(self.laser.query('SOUR:CURR?'))

    def set_current_setpoint(self, value):
        """Set the laser diode current setpoint. This is the setpoint when the laser is disabled in modulation mode."""
        max_current = self.get_max_current()
        if value <= max_current:
            self.laser.write(f'SOUR:CURR {value:.5f}')
        else:
            raise ValueError(f'Current setpoint: [{value}] is larger than max current [{max_current}]).')

    def get_tec_state(self):
        return self.laser.query('OUTP2:STAT?')

    def set_tec_state(self, value):
        self.laser.write(f'OUTP2:STAT {value}')

    def temperature(self):
        return self.laser.query('MEAS:TEMP?')

    def on(self):
        if self.get_tec_state():
            self.set_ld_state(1)
        else:
            return('Error: temperature controller disabled.')

    def get_modulation_state(self):
        value = int(self.laser.query('SOUR:AM:STAT?'))
        if value == 0:
            return 'Off'
        elif value == 1:
            return 'On'
        else:
            raise ValueError(f'invalid modulation state {value}')

    def set_modulation_state(self, value):
        if value == 'Off':
            val = 0
        elif value == 'On':
            val = 1
        else:
            raise ValueError(f'invalid modulation state {value}')
        self.laser.write(f'SOUR:AM:STAT {val}')

    def off(self):
        self.set_ld_state(0)
