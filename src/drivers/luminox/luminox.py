"""LuminOX LOX-02 oxygen sensor driver.
https://gaslab.com/products/oxygen-sensor-luminox-lox-o2

Author: Jacob Feder, Kimberly Carrillo Rivera
Date: 8/12/2021
"""

import serial
import logging
import time

logger = logging.getLogger(__name__)

class LOX_02:
    def __init__(self, com_port: str):
        """Args:
            com_port: serial COM port (see pyserial docs)
        """
        self.com_port = com_port

    def open(self):
        self.serial_port = serial.Serial(self.com_port)
        self.mode_poll()
        self.serial_port.reset_input_buffer()

    def close(self):
        self.serial_port.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def _format_msg(self, command, arg=None):
        msg = command
        if arg:
            msg = msg + ' ' + arg
        msg += '\r\n'
        logger.debug(f'sent message [{msg}]')
        self.serial_port.write(msg.encode('ascii'))

    def mode_poll(self):
        self._format_msg('M', arg='1')
        response = self.serial_port.readline() # 'M 01\r\n'

    def read_all(self):
        self.mode_poll() # 'M 1\r\n'
        self._format_msg('A') # 'A\r\n'
        response = self.serial_port.readline() # 'O xxxx.x T yxx.x P xxxx % xxx.xx e xxxx\r\n'
        logger.debug(f'response [{response}]')
        ppo2 = float(response[2:8])
        temp = float(response[11:16])
        pressure = float(response[19:23])
        percento2 = float(response[26:32])
        status = int(response[35:39])
        return (ppo2, temp, pressure, percento2, status)

    def ppo2(self):
        """Return the partial pressure of oxygen (mbar)"""
        ppo2, temp, pressure, percento2, status = self.read_all()
        return ppo2
    
    def temp(self):
        """Return the temperature (deg C)"""
        ppo2, temp, pressure, percento2, status = self.read_all()
        return temp

    def o2(self):
        """Return the O2 concentration as a percentage"""
        ppo2, temp, pressure, percento2, status = self.read_all()
        return percento2

    def pressure(self):
        """Return the total pressure in mbar"""
        ppo2, temp, pressure, percento2, status = self.read_all()
        return pressure
