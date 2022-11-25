"""Agiltron fiber-fiber switch serial-based driver. Compatible with any switch 
that uses their USB/serial SW-DR-5 control board.

Author: Benjamin Soloway, Jacob Feder
Date: 10/08/2022
"""
import serial
import logging

logger = logging.getLogger(__name__)

class FFSW():
    def __init__(self, com_port: str):
        self.com_port = com_port

    def _read(self):
        response = self.serial_port.read(4)
        logger.debug(f'response [{response}]')
        return response

    def _write(self, msg):
        self.serial_port.write(msg)
        logger.debug(f'sent command [{msg}]')

    def get_sn(self):
        self._write(b"\x01\x03\x00\x00")
        a = self._read()[8::] #higher bits
        self._write(b"\x01\x04\x00\x00")
        b = self._read()[8::] #lower bits
        return a+b

    def get_module_address(self):
        #TODO: don't know the meaning of this
        self._write(b"\x01\x01\x00\x00")
        return self._read()

    def set_port(self, port):
        if port == 1:
            self._write(b"\x01\x12\x00\x00")
        elif port == 2:
            self._write(b"\x01\x12\x00\x01")
        logger.info(f'set port to [{port}]')
        return self._read()

    def get_port(self):
        self._write(b"\x01\x11\x00\x00")
        response = self._read()
        if response == b"\x01\x11\x01\x00":
            port = 2
        elif response == b"\x01\x11\x00\x00":
            port = 1
        else:
            raise ValueError(f'invalid current port response {response}')
        logger.info(f'current port is [{port}]')
        return port

    def get_temp(self):
        self._write(b"\x01\x22\x00\x00")
        return self._read()

    def open(self):
        self.serial_port = serial.Serial(port=self.com_port, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)

    def close(self):
        self.serial_port.close()

    def __enter__(self):
        self.open()
        self.serial_port.flush()
        return self

    def __exit__(self, *args):
        self.serial_port.flush()
        self.close()


if __name__ == '__main__':
    with FFSW('/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AU03N2AV-if00-port0') as switch:
        print('flushing buffer')
        print(switch.serial_port.flush())
        print('setting port 1')
        print(switch.set_port(1))
        print('getting port after setting port 1')
        print(switch.get_port())
        print('setting port 2')
        print(switch.set_port(2))
        print('getting port after setting port 2')
        print(switch.get_port())
        print('getting temperature')
        print(switch.get_temp())
        print('getting module address')
        print(switch.get_module_address())