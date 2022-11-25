"""Rohde and Schwarz HMP4040 driver.

Programming manual:
https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/dl_common_library/dl_manuals/gb_1/h/hmp_serie/HMPSeries_UserManual_en_02.pdf

Copyright (c) 2022, Jacob Feder
All rights reserved.
"""

import time
import logging

from pyvisa import ResourceManager

logger = logging.getLogger(__name__)

class HMP4040:
    def __init__(self, address):
        """
        Args:
            address: PyVISA resource path.
        """
        self.address = address
        self.rm = ResourceManager('@py')

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
            raise ConnectionError(f'Failed connecting to HMP4040 @ [{self.address}]') from err
        self.device.read_termination = '\n'
        self.device.write_termination = '\n'
        # 1 second timeout
        self.device.timeout = 1000
        self.idn = self.device.query('*IDN?')
        if int(self.device.query('*TST?')):
            raise RuntimeError(f'HMP4040 [{self}] self-test failed.')
        logger.info(f'Connected to HMP4040 [{self}].')
        return self

    def close(self):
        self.device.close()

    def _write(self, cmd):
        """Send a VISA command to the device.
        Args:
            cmd: command string to send
        """
        self.device.write(cmd)
        # wait until the command was processed
        self.device.write('*WAI')
        # check for errors
        # query('SYST:ERR?') returns a string like '-100, "Command error"'
        err = self.device.query('SYST:ERR?').replace('"', '').split(', ')
        err_num = int(err[0])
        if err_num:
            # empty error queue
            other_errs = err_num
            while other_errs:
                other_errs = int(self.device.query('SYST:ERR?').split(', ')[0])
            raise RuntimeError(f'HMP4040 communication error: {err}')

    def _select_output(self, ch):
        """Select the channel that will receive subsequent commands.

        Args:
            ch: output channel (e.g. 1, 2, 3)
        """
        self._write(f'INST:NSEL {ch}')

    def set_output(self, ch, state):
        """Turn the channel output on or off.

        Args:
            ch: output channel (e.g. 1, 2, 3)
            state: True to enable the channel, False to disable
        """
        self._select_output(ch)
        if state:
            self._write(f'OUTP:STAT ON')
        else:
            self._write(f'OUTP:STAT OFF')

    def set_voltage(self, ch, val, confirm=True, timeout=1.0, delta=0.05):
        """Set the channel voltage.

        Args:
            ch: output channel (e.g. 1, 2, 3)
            val: channel output (volts)
            confirm: measure the voltage continuously until it is within 
                    delta (volts) of the set voltage.
            timeout: max allowed time (s) to reach the set voltage
            delta: acceptable delta from set voltage (volts)
        """
        self._select_output(ch)
        self._write(f'VOLT {val}')
        if confirm:
            timeout = time.time() + timeout
            actual = self.measure_voltage(ch=ch)
            while abs(val - actual) > delta:
                time.sleep(0.1)
                if time.time() > timeout:
                    raise TimeoutError(f'Measured channel {ch} voltage [{actual}] did not reach set voltage [{val}].')
                actual = self.measure_voltage(ch=ch)

    def set_current(self, ch, val, confirm=True, timeout=1.0, delta=0.05):
        """Set the channel current.

        Args:
            ch: output channel (e.g. 1, 2, 3)
            val: channel output (amps)
            confirm: measure the current continuously until it is within 
                    delta (amps) of the set current.
            timeout: max allowed time (s) to reach the set current
            delta: acceptable delta from set current (amps)
        """
        self._select_output(ch)
        self._write(f'CURR {val}')
        if confirm:
            timeout = time.time() + timeout
            actual = self.measure_current(ch=ch)
            while abs(val - actual) > delta:
                time.sleep(0.1)
                if time.time() > timeout:
                    raise TimeoutError(f'Measured channel {ch} current [{actual}] did not reach set current [{val}].')
                actual = self.measure_current(ch=ch)

    def set_ovp(self, ch, val):
        """Set the channel over-voltage protection trip threshold.

        Args:
            ch: output channel (e.g. 1, 2, 3)
            val: channel ovp limit
        """
        self._select_output(ch)
        self._write(f':VOLT:PROT:MODE MEAS')
        self._write(f'VOLT:PROT {val}')

    def clear_ovp(self, ch):
        """Clear and disable the channel over-voltage protection.

        Args:
            ch: output channel (e.g. 1, 2, 3)
        """
        self._select_output(ch)
        self._write(f':VOLT:PROT:CLE')

    def measure_voltage(self, ch):
        """Return the actual channel voltage.

        Args:
            ch: output channel (e.g. 1, 2, 3)

        Returns:
            Channel voltage as a float 
        """
        self._select_output(ch)
        volt = float(self.device.query(f'MEAS:VOLT?'))
        return volt

    def measure_current(self, ch):
        """Return the actual channel current.

        Args:
            ch: output channel (e.g. 1, 2, 3)

        Returns:
            Channel current as a float 
        """
        self._select_output(ch)
        curr = float(self.device.query(f'MEAS:CURR?'))
        return curr
