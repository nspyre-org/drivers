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
        return f'DP832 [{self.address}]'

    def open(self):
        try:
            self.device = self.rm.open_resource(self.address)
        except Exception as err:
            raise ConnectionError(f'Failed connecting to DP832 @ [{self.address}]') from err
        # 1 second timeout
        self.device.timeout = 1000
        self.idn = self.device.query('*IDN?').strip()
        _logger.info(f'Connected to DP832 {self}.')
        # see table 1-5
        self.device.write(f'*ESE {1|4|8|16|32}')
        self.device.write(f'*SRE {8|32}')
        return self

    def close(self):
        self.device.close()

    def _send_cmd(self, cmd: str):
        """Send a VISA command to the device and checks for errors.

        Args:
            cmd: Command string to send.

        Raises:
            RuntimeError: Error with the command syntax or execution.
        """
        self.device.write(cmd)
        self.device.write('*WAI')
        standard_event_reg = int(self.device.query('*ESR?').strip())
        summary_reg = int(self.device.query('*STB?').strip())
        questionable_status_reg = int(self.device.query(':STAT:QUES?').strip())
        _logger.debug(f'{self} sent command [{cmd}], ESR [{standard_event_reg}],'
            f' STB [{summary_reg}], QSR [{questionable_status_reg}]')
        if standard_event_reg & 32:
            raise RuntimeError(f'{self} command [{cmd}] contains a syntax error.')
        if standard_event_reg & 16:
            raise RuntimeError(f'{self} command [{cmd}] execution error.')

    def toggle_output(self, ch: int, state: bool):
        """Turn the channel output on or off.

        Args:
            ch: Output channel (e.g. 1, 2, 3).
            state: True to enable the channel, False to disable.
        """
        if state:
            self._send_cmd(f':OUTP CH{ch},ON')
        else:
            self._send_cmd(f':OUTP CH{ch},OFF')

    def set_voltage(self, ch: int, val: float, confirm: bool = True, timeout: float = 2.0, delta: float = 0.03):
        """Set the voltage.

        Args:
            ch: Output channel (e.g. 1, 2, 3).
            val: Channel output (volts).
            confirm: Measure the voltage continuously until it is within 
                    delta (volts) of the set voltage.
            timeout: Max allowed time (s) to reach the set voltage.
            delta: Acceptable delta from set voltage (volts).
        """
        self._send_cmd(f':SOUR{ch}:VOLT {val}')
        _logger.info(f'Setting {self} ch [{ch}] to [{val} V].')
        if confirm:
            timeout = time.time() + timeout
            actual = self.measure_voltage(ch=ch)
            while abs(val - actual) > delta:
                time.sleep(0.1)
                if time.time() > timeout:
                    raise TimeoutError(f'Measured channel {ch} voltage [{actual}] did not reach set voltage [{val}].')
                actual = self.measure_voltage(ch=ch)
            _logger.info(f'{self} ch [{ch}] reached setpoint [{val} V].')

    def get_voltage(self, ch: int) -> float:
        """Get the voltage setpoint.
        
        Args:
            ch: output channel (e.g. 1, 2, 3)
        """
        return float(self.device.query(f':SOUR{ch}:VOLT?'))

    def set_current(self, ch: int, val: float, confirm: bool = True, timeout: float = 1.0, delta: float = 0.02):
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
        _logger.info(f'Setting {self} ch [{ch}] to [{val} A].')

        if confirm:
            timeout = time.time() + timeout
            actual = self.measure_current(ch=ch)
            while abs(val - actual) > delta:
                time.sleep(0.1)
                if time.time() > timeout:
                    raise TimeoutError(f'Measured channel {ch} current [{actual}] did not reach set current [{val}].')
                actual = self.measure_current(ch=ch)
            _logger.info(f'{self} ch [{ch}] reached setpoint [{val} A].')

    def get_current(self, ch: int):
        """Get the current setpoint.
        
        Args:
            ch: output channel (e.g. 1, 2, 3)
        """
        return float(self.device.query(f':SOUR{ch}:CURR?'))

    def get_ovp_alarm(self, ch: int) -> True:
        """Return whether there was an over-voltage protection event.

        Args:
            ch: Output channel (e.g. 1, 2, 3).
        """
        alarm = self.device.query(f':OUTP:OVP:ALAR? CH{ch}').strip()
        _logger.debug(f'{self} ch [{ch}] OVP alarm status [{alarm}].')
        if alarm == 'YES':
            return True
        elif alarm == 'NO':
            return False
        else:
            raise RuntimeError(f'Unrecognized response to OVP alarm status query [{alarm}].')

    def clear_ovp_alarm(self, ch: int) -> True:
        """Clear the over-voltage protection event.

        Args:
            ch: Output channel (e.g. 1, 2, 3).
        """
        self._send_cmd(f':OUTP:OVP:CLEAR CH{ch}')
        _logger.info(f'{self} ch [{ch}] cleared OVP alarm.')

    def set_ovp(self, ch: int, val: float):
        """Set the channel over-voltage protection.

        Args:
            ch: Output channel (e.g. 1, 2, 3).
            val: Channel OVP limit.
        """
        self._send_cmd(f':OUTP:OVP:VAL CH{ch},{val}')
        _logger.info(f'{self} ch [{ch}] set OVP [{val} V].')

    def toggle_ovp(self, ch: int, state: bool):
        """Enable or disable the channel over-voltage protection.

        Args:
            ch: Output channel (e.g. 1, 2, 3).
            state: True to enable the OVP, False to disable.
        """
        if state:
            self._send_cmd(f':OUTP:OVP CH{ch},ON')
            _logger.info(f'{self} ch [{ch}] set OVP ON.')
        else:
            self._send_cmd(f':OUTP:OVP CH{ch},FF')
            _logger.info(f'{self} ch [{ch}] set OVP OFF.')

    def get_ocp_alarm(self, ch: int) -> True:
        """Return whether there was an over-current protection event.

        Args:
            ch: Output channel (e.g. 1, 2, 3).
        """
        alarm = self.device.query(f':OUTP:OCP:ALAR? CH{ch}').strip()
        _logger.debug(f'{self} ch [{ch}] OCP alarm status [{alarm}].')
        if alarm == 'YES':
            return True
        elif alarm == 'NO':
            return False
        else:
            raise RuntimeError(f'Unrecognized response to OCP alarm status query [{alarm}].')

    def clear_ocp_alarm(self, ch: int) -> True:
        """Clear the over-current protection event.

        Args:
            ch: Output channel (e.g. 1, 2, 3).
        """
        self._send_cmd(f':OUTP:OCP:CLEAR CH{ch}')
        _logger.info(f'{self} ch [{ch}] cleared OCP alarm.')

    def set_ocp(self, ch: int, val: float):
        """Set the channel over-current protection.

        Args:
            ch: Output channel (e.g. 1, 2, 3).
            val: Channel OCP limit.
        """
        self._send_cmd(f':OUTP:OCP:VAL CH{ch},{val}')
        _logger.info(f'{self} ch [{ch}] set OCP [{val} A].')

    def toggle_ocp(self, ch: int, state: bool):
        """Enable or disable the channel over-current protection.

        Args:
            ch: Output channel (e.g. 1, 2, 3).
            state: True to enable the OCP, False to disable.
        """
        if state:
            self._send_cmd(f':OUTP:OCP CH{ch},ON')
            _logger.info(f'{self} ch [{ch}] set OCP ON.')
        else:
            self._send_cmd(f':OUTP:OCP CH{ch},OFF')
            _logger.info(f'{self} ch [{ch}] set OCP OFF.')

    def measure_voltage(self, ch: int) -> float:
        """Return the actual channel voltage.

        Args:
            ch: Output channel (e.g. 1, 2, 3).

        Returns:
            Channel voltage.
        """
        volt = float(self.device.query(f':MEAS:VOLT? CH{ch}'))
        _logger.debug(f'{self} ch [{ch}] measured voltage [{volt}].')
        time.sleep(self.delay)
        return volt

    def measure_current(self, ch: int) -> float:
        """Return the actual channel current.

        Args:
            ch: Output channel (e.g. 1, 2, 3).

        Returns:
            Channel current. 
        """
        curr = float(self.device.query(f':MEAS:CURR? CH{ch}'))
        time.sleep(self.delay)
        return curr

    def measure_power(self, ch: int) -> float:
        """Return the actual channel power.

        Args:
            ch: Output channel (e.g. 1, 2, 3).

        Returns:
            Channel power.
        """
        power = float(self.device.query(f':MEAS:POWE? CH{ch}'))
        time.sleep(self.delay)
        return power
