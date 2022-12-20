"""Spectrometer/Monochromator from Acton/Princeton Instruments
Using SP2150i but I think this should work for any of their spectrometers

Author: Benjamin Soloway, Jacob Feder
Date: 12/19/2022
"""
import serial
import logging

logger = logging.getLogger(__name__)

class SP2150i():
    def __init__(self, serial_port: str):
        self.serial_port = serial_port

    def _read(self):
        flagStop = 0
        commStr = ''
        while flagStop == 0:
            commStr += self.conn.read(1).decode()
            if 'ok' in commStr:
                flagStop = 1
        logger.debug(f'received [{commStr}]')
        self.clearSer()
        return commStr

    def _write(self, msg):
        enc_msg = msg.encode() + b'\x0d'
        self.conn.write(enc_msg)
        logger.debug(f'sent command [{enc_msg}]')

    def get_all_gratings(self):
        msg = '?GRATINGS'
        self._write(msg)
        return self._read()

    def set_wavelength(self, wavelength):
        """
        wavelength: wavelength in nm as integer or float

        Goes to destination wavelength to nearest 0.1nm at selected scan rate
        """
        self._write(str(wavelength) + ' goto')
        self._read()

    def set_target_wavelength(self, wavelength):
        """
        wavelength: wavelength in nm as integer or float

        Scans to destination wavelength to nearest 0.1nm at sleected scan rate
        """
        self._write(str(wavelength) + ' nm')
        self._read()

    def set_scan_speed(self, speed):
        """
        wavelength: wavelength in nm as integer or float

        Scans to destination wavelength to nearest 0.1nm at sleected scan rate
        """
        self._write(str(speed) + ' nm/min')
        self._read()

    def get_wavelength(self):
        msg = '?NM'
        self._write(msg)
        ans = self._read() #example:  999.989 nm  ok
        return float(self._clean_up_string(ans[1:8])) #example: 999.989

    def get_scanspeed(self):
        msg = '?NM/MIN'
        self._write(msg)
        ans = self._read()  #example: 100.000 nm/min  ok
        return float(self._clean_up_string(ans[1:8])) #example: 100.000

    def get_turret(self):
        """
        Sends the selected turret number (1, 2, 3, or 4) to the computer or terminal.
        """
        msg = '?TURRET'
        self._write(msg)
        ans = self._read()  #example:  1  ok
        return int(ans[1]) #example: 1

    def get_turret_gratings(self):
        """
        Sends the groove spacing of each grating for each turret to the computer or terminal.
        """
        msg = '?TURRETS'
        self._write(msg)
        return self._read()

    def set_grating(self, grating):
        if grating != 1 and grating != 2:
            raise ValueError(f'Grating {grating} is not available.')
        msg = f'{grating} GRATING'
        self._write(msg)
        return self._read()

    def set_turret(self, turret):
        if turret != 1:
            raise ValueError(f'Turret {turret} is not available.')
        msg = f'{turret} TURRET'
        self._write(msg)
        return self._read()

    def open(self):
        self.conn = serial.Serial(port=self.serial_port, baudrate=9600, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, timeout=10)

    def close(self):
        self.conn.close()

    def clearSer(self):
        self.conn.reset_input_buffer()
        self.conn.reset_output_buffer()

    def __enter__(self):
        self.open()
        self.clearSer()
        return self

    def __exit__(self, *args):
        self.clearSer()
        self.close()

    def _clean_up_string(self, str):
        return str.replace(' ', '').replace('n', '').replace('m', '')

if __name__ == '__main__':
    with Spec('/dev/serial/by-id/usb-Acton_Research_ACTON_RESEARCH_CONTROLLER-if00-port0') as spec:
        print("getting turret")
        print(spec.get_turret())
        print("setting grating 2 - please give this operation at least 20 seconds")
        spec.set_grating(2)
        print("getting all gratings")
        print(spec.get_all_gratings())
        print("setting grating 1  - please give this operation at least 20 seconds")
        spec.set_grating(1)
        print("getting all gratings")
        print(spec.get_all_gratings())
        #spec.get_turret_gratings()
        print("getting scan speed in nm/min")
        print(spec.get_scanspeed())
        print("setting wavelength to 1000nm")
        spec.set_wavelength(1000)
        print("getting wavelength")
        print(spec.get_wavelength())
        print("setting wavelength to 500nm")
        spec.set_wavelength(500)
        print("getting wavelength")
        print(spec.get_wavelength())
