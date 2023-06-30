"""Driver for the Thorlabs PM100D.

Copyright (c) 2022, Jacob Feder, Ben Soloway
All rights reserved.
"""
import logging

from pyvisa import ResourceManager

logger = logging.getLogger(__name__)

class PM100D:
    def __init__(self, address):
        """
        Args:
            address: PyVISA resource path.
        """
        self.rm = ResourceManager()
        self.address = address

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def __str__(self):
        return f'{self.address} {self.idn}'

    def open(self):
        try:
            self.device = self.rm.open_resource(self.address)
        except Exception as err:
            raise ConnectionError(f'Failed connecting to PM100D @ [{self.address}]') from err
        # 1 second timeout
        self.device.timeout = 1000
        self.idn = self.device.query('*IDN?')
        logger.info(f'Connected to PM100D [{self}].')
        return self

    def close(self):
        self.device.close()

    def idn(self):
        return self.device.query('*IDN?')

    def power(self):
        return float(self.device.query('MEAS:POWER?'))

    def get_correction_wavelength(self):
        return float(self.device.query('SENS:CORR:WAV?'))

    def set_correction_wavelength(self, wavelength):
        self.device.write('SENSE:CORRECTION:WAVELENGTH {}'.format(wavelength))

    def correction_wavelength_range(self):
        cmd = 'SENSE:CORRECTION:WAVELENGTH? {}'
        cmd_vals = ['MIN', 'MAX']
        return tuple(float(self.device.query(cmd.format(cmd_val))) for cmd_val in cmd_vals)
