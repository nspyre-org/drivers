"""DLnsec laser driver.

https://labs-electronics.com/

Author: Jacob Feder, Will Burke
Date: 2/22/2022
"""
import time
import logging

import serial

logger = logging.getLogger(__name__)

class DLnsec():
    def __init__(self, com_port: str, timeout=1.0):
        """
        Args:
            com_port: serial COM port (see pyserial docs)
        """
        self.com_port = com_port
        self.timeout = timeout

    def open(self):
        """Connect to the laser."""
        self.serial_port = serial.Serial(com_port, baudrate=9600, timeout=timeout)
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()
        self.reboot()
        # query the laser serial number
        self.idn = self._query('*IDN')
        if not self.idn:
            raise RuntimeError('Failed getting laser ID number')
        logging.info(f'Connected to DLnsec [{self.idn}]')

    def close(self):
        """Disconnect from the laser."""
        self.serial_port.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.off()
        self.close()

    def _send_raw(self, msg):
        """Send a command to the laser."""
        # add a newline and encode the message into a binary string
        msg_bin = (msg + '\n').encode('ascii')
        # send the message on the serial port
        self.serial_port.write(msg_bin)
        logger.debug(f'Sent message to DLnsec: [{msg}]')
        # wait for the laser to process the message
        time.sleep(0.1)

    def _send(self, msg):
        """Send a command to the laser and check for errors."""
        # number of times to try sending the command
        attempts = 3
        while attempts:
            # send the command
            self._send_raw(msg)
            # ask if an error occurred
            response = self._query('ERR?')
            if response == '0; No error':
                break
            else:
                attempts -= 1
                err_str = f'Failed sending DLnsec command [{msg}]: response [{response}]'
                if attempts:
                    logger.warning(err_str)
                else:
                    raise RuntimeError(err_str)
                # wait a moment before trying again
                time.sleep(0.25)

    def _query(self, msg):
        """Send a query command to the laser and return the response."""
        self._send_raw(msg)
        # receive the response
        response = self.serial_port.read_until(b'\n\r')
        response = response.decode('ascii').strip('\n\r')
        logger.debug(f'Response from DLnsec: [{response}]')

        return response

    def power(self, p):
        """Set the output power (integer percentage)"""
        if not isinstance(p, int) or p > 100 or p < 0:
            raise ValueError(f'The power [{p}] must be an integer between 0-100')
        self._send(f'PWR{p}')

    def cw_mode(self):
        """Put the laser into CW output mode."""
        self._send('LASE')

    def on(self):
        """Turn the output stage on."""
        self._send('*ON')

    def off(self):
        """Turn the output stage off."""
        self._send('*OFF')

    def reboot(self):
        """Reboot the laser, applying default settings on startup."""
        self._send_raw('*RBT')
        # wait for the laser to fully restart
        time.sleep(2)
