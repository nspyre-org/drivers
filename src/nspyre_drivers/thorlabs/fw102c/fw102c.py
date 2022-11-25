"""
Serial driver for Thorlabs FW102C filter wheel.

https://www.thorlabs.com/thorproduct.cfm?partnumber=FW102C#ad-image-0

Copyright (c) 2022, Jacob Feder
All rights reserved.
"""
import serial
import logging

logger = logging.getLogger(__name__)

class FW102C:
    def __init__(self, com_port: str, channel_mapping=None, baud=115200, timeout: float = 10.0):
        """Args:
            com_port: serial COM port (see pyserial docs)
            channel_mapping: dictionary mapping an identifier to a channel, which can be used instead of the channel number e.g.
            {'filter1': 1, 'filter2': 2}
            baud: 9600 or 115200
            timeout: read timeout
        """
        self.channel_mapping = channel_mapping
        self.com_port = com_port
        self.baud = baud
        self.timeout = timeout

    def __str__(self):
        return f'{self.address} {self.idn}'

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.serial_port.close()

    def open(self):
        self.serial_port = serial.Serial(self.com_port, baudrate=self.baud, timeout=self.timeout)
        # send a dummy command to clear any previous messages
        self.idn = self._query('*idn')
        logger.info(f'Connected to [{self}].')

    def _send_cmd(self, cmd):
        """Format and send a command to the device.
        
        Args:
            cmd: the command to send, e.g. '*idn?'
        
        Returns:
            The device response as a string (with the '>' stripped)
        """
        logger.debug(f'sending message [{cmd}]')
        cmd += '\r'
        self.serial_port.write(cmd.encode('ascii'))
        response = self.serial_port.read_until('> '.encode('ascii')).decode('ascii')
        if '> ' not in response: 
            raise RuntimeError('Timed out waiting for response')
        # strip preceding message and trailing '\r> '
        trimmed_response = response[len(cmd):-3]
        logger.debug(f'received response [{trimmed_response}]')
        return trimmed_response

    def _set(self, param, val):
        """Set a parameter value.
        
        Args:
            param: the parameter, e.g. 'pos' for the wheel position
            val: the value to set the parameter to
        """
        self._send_cmd(f'{param}={val}')

    def _query(self, param):
        """Get a parameter value.
        
        Args:
            param: the parameter, e.g. 'pos' for the wheel position
        """
        return self._send_cmd(f'{param}?')

    def version(self):
        """Return the version information"""
        return self._query('*idn')

    def position(self):
        """Return the wheel position."""
        pos_num = int(self._query('pos'))
        if self.channel_mapping is None:
            return pos_num
        else:
            inverse_channel_mapping = {v: k for k, v in self.channel_mapping.items()}
            return inverse_channel_mapping[pos_num]

    def set_position(self, pos):
        """Set the wheel position.

        Args:
            pos: new wheel position

        Raises:
            ValueError: invalid position
        """
        if self.channel_mapping is not None:
            pos = self.channel_mapping[pos]
        pcount = self.position_count()
        if pos in range(1, pcount+1):
            logger.info(f'setting position to [{pos}]')
            return self._set('pos', pos)
        else:
            raise ValueError(f'[{pos}] not in range [1, {pcount}]')

    def position_count(self):
        """Return the number of wheel positions."""
        return int(self._query('pcount'))

    def set_position_count(self, count):
        """Set the number of wheel positions.

        Args:
            count: number of wheel positions

        Raises:
            ValueError: invalid position count
        """
        if count != 6 and count != 12:
            raise ValueError(f'invalid position count [{count}]')
        logger.info(f'setting position count to [{count}]')
        return self._set('pcount', count)

    def trigger_mode(self):
        """Return the trigger mode."""
        return int(self._query('trig'))

    def set_trigger_mode(self, mode):
        """Set the trigger mode.

        Args:
            mode: 0 for input, 1 for output

        Raises:
            ValueError: invalid mode
        """
        if mode != 0 and mode != 1:
            raise ValueError(f'invalid trigger mode [{mode}]')
        logger.info(f'setting trigger mode to [{mode}]')
        return self._set('trig', mode)

    def speed_mode(self):
        """Return the speed mode."""
        return int(self._query('speed'))

    def set_speed_mode(self, mode):
        """Set the speed mode.

        Args:
            mode: 0 for slow, 1 for fast

        Raises:
            ValueError: invalid mode
        """
        if mode != 0 and mode != 1:
            raise ValueError(f'invalid speed mode [{mode}]')
        logger.info(f'setting speed mode to [{mode}]')
        return self._set('speed', mode)

    def sensor_mode(self):
        """Return the sensor mode."""
        return int(self._query('sensors'))

    def set_sensor_mode(self, mode):
        """Set the sensor mode.

        Args:
            mode: 0 to turn off sensors when wheel is idle to eliminate stray light, 1 to keep sensors active 

        Raises:
            ValueError: invalid mode
        """
        if mode != 0 and mode != 1:
            raise ValueError(f'invalid speed mode [{mode}]')
        logger.info(f'setting sensor mode to [{mode}]')
        return self._set('sensors', mode)

    def baud(self):
        """Return the baud rate."""
        return int(self._query('baud'))

    def set_baud(self, baud):
        """Set the baud rate.

        Args:
            baud: 0 for 9600, 1 for 115200

        Raises:
            ValueError: invalid baud
        """
        if baud != 0 and baud != 1:
            raise ValueError(f'invalid baud [{baud}]')
        logger.info(f'setting baud to [{baud}]')
        return self._set('baud', baud)

    def save(self):
        """Save the current settings as default"""
        self._send_cmd('save')
