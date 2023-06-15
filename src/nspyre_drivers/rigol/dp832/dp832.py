"""Rigol DP832 driver.

Based on https://github.com/kearneylackas/DP832-Python

Programming manual:
https://www.batronix.com/pdf/Rigol/ProgrammingGuide/DP800_ProgrammingGuide_EN.pdf

Copyright (c) 2022, Jacob Feder
All rights reserved.
"""

import time
import logging

from pyvisa import ResourceManager

_logger = logging.getLogger(__name__)

class DP832:
    def __init__(self, address):
        """
        Args:
            address: PyVISA resource path.
        """
        # time to wait (s) after each command
        self.delay = 0.01
        self.rm = ResourceManager('@py')
        self.address = address

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def __str__(self):
        return f'DP832 {self.address} {self.idn}'

    def open(self):
        try:
            self.device = self.rm.open_resource(self.address)
        except Exception as err:
            raise ConnectionError(f'Failed connecting to DP832 @ [{self.address}]') from err
        # 1 second timeout
        self.device.timeout = 1000
        self.idn = self.device.query('*IDN?').strip()
        _logger.info(f'Connected to DP832 [{self}].')
        # see table 1-5
        self.device.write(f'*ESE {1|4|8|16|32}')
        self.device.write(f'*SRE {8|32}')
        return self

    def close(self):
        self.device.close()

    def _send_cmd(self, cmd):
        """Send a VISA command to the device and checks for errors.
        Args:
            cmd: command string to send
        """
        self.device.write(cmd)
        self.device.write('*WAI')
        standard_event_reg = int(self.device.query('*ESR?').strip())
        summary_reg = int(self.device.query('*STB?').strip())
        questionable_status_reg = int(self.device.query(':STAT:QUES?').strip())
        _logger.debug(f'[{self}] sent command [{cmd}], ESR [{standard_event_reg}],'
            f' STB [{summary_reg}], QSR [{questionable_status_reg}]')
        if standard_event_reg & 32:
            raise RuntimeError(f'DP832 [{self}] command [{cmd}] contains a syntax error.')
        if standard_event_reg & 16:
            raise RuntimeError(f'DP832 [{self}] command [{cmd}] execution error.')

    def toggle_output(self, ch, state):
        """Turn the channel output on or off.

        Args:
            ch: output channel (e.g. 1, 2, 3)
            state: True to enable the channel, False to disable
        """
        if state:
            self._send_cmd(f':OUTP CH{ch},ON')
        else:
            self._send_cmd(f':OUTP CH{ch},OFF')

    def set_voltage(self, ch, val, confirm=True, timeout=1.0, delta=0.03):
        """Set the voltage.

        Args:
            ch: output channel (e.g. 1, 2, 3)
            val: channel output (volts)
            confirm: measure the voltage continuously until it is within 
                    delta (volts) of the set voltage.
            timeout: max allowed time (s) to reach the set voltage
            delta: acceptable delta from set voltage (volts)
        """
        self._send_cmd(f':SOUR{ch}:VOLT {val}')
        if confirm:
            timeout = time.time() + timeout
            actual = self.measure_voltage(ch=ch)
            while abs(val - actual) > delta:
                time.sleep(0.1)
                if time.time() > timeout:
                    raise TimeoutError(f'Measured channel {ch} voltage [{actual}] did not reach set voltage [{val}].')
                actual = self.measure_voltage(ch=ch)

    def get_voltage(self, ch):
        """Get the voltage setpoint.
        
        Args:
            ch: output channel (e.g. 1, 2, 3)
        """
        return float(self.device.query(f':SOUR{ch}:VOLT?'))

    def set_current(self, ch, val, confirm=True, timeout=1.0, delta=0.02):
        """Set the channel current.

        Args:
            ch: output channel (e.g. 1, 2, 3)
            val: channel output (amps)
            confirm: measure the current continuously until it is within 
                    delta (amps) of the set current.
            timeout: max allowed time (s) to reach the set current
            delta: acceptable delta from set current (amps)
        """
        self._send_cmd(f':SOUR{ch}:CURR {val}')
        if confirm:
            timeout = time.time() + timeout
            actual = self.measure_current(ch=ch)
            while abs(val - actual) > delta:
                time.sleep(0.1)
                if time.time() > timeout:
                    raise TimeoutError(f'Measured channel {ch} current [{actual}] did not reach set current [{val}].')
                actual = self.measure_current(ch=ch)

    def get_current(self, ch):
        """Get the current setpoint.
        
        Args:
            ch: output channel (e.g. 1, 2, 3)
        """
        return float(self.device.query(f':SOUR{ch}:CURR?'))

    def set_ovp(self, ch, val):
        """Set the channel over-voltage protection.

        Args:
            ch: output channel (e.g. 1, 2, 3)
            val: channel ovp limit
        """
        self._send_cmd(f':OUTP:OVP:VAL CH{ch},{val}')

    def toggle_ovp(self, ch, state):
        """Enable or disable the channel over-voltage protection.

        Args:
            ch: output channel (e.g. 1, 2, 3)
            state: True to enable the OVP, False to disable
        """
        if state:
            self._send_cmd(f':OUTP:OVP CH{ch},ON')
        else:
            self._send_cmd(f':OUTP:OVP CH{ch},FF')

    def set_ocp(self, ch, val):
        """Set the channel over-current protection.

        Args:
            ch: output channel (e.g. 1, 2, 3)
            val: channel ocp limit
        """
        self._send_cmd(f':OUTP:OCP:VAL CH{ch},{val}')

    def toggle_ocp(self, ch, state):
        """Enable or disable the channel over-current protection.

        Args:
            ch: output channel (e.g. 1, 2, 3)
            state: True to enable the OCP, False to disable
        """
        if state:
            self._send_cmd(f':OUTP:OCP CH{ch},ON')
        else:
            self._send_cmd(f':OUTP:OCP CH{ch},OFF')

    def measure_voltage(self, ch):
        """Return the actual channel voltage.

        Args:
            ch: output channel (e.g. 1, 2, 3)

        Returns:
            Channel voltage as a float 
        """
        volt = float(self.device.query(f':MEAS:VOLT? CH{ch}'))
        time.sleep(self.delay)
        return volt

    def measure_current(self, ch):
        """Return the actual channel current.

        Args:
            ch: output channel (e.g. 1, 2, 3)

        Returns:
            Channel current as a float 
        """
        curr = float(self.device.query(f':MEAS:CURR? CH{ch}'))
        time.sleep(self.delay)
        return curr

    def measure_power(self, ch):
        """Return the actual channel power.

        Args:
            ch: output channel (e.g. 1, 2, 3)

        Returns:
            Channel power as a float 
        """
        power = float(self.device.query(f':MEAS:POWE? CH{ch}'))
        time.sleep(self.delay)
        return power
