"""
Copied from: https://github.com/MaximilianWinter/RotatorAPI/blob/main/API/RotatorAPI.py

Part: https://www.thorlabs.com/thorproduct.cfm?partnumber=ELL14
Communication manual: https://www.thorlabs.com/Software/Elliptec/Communications_Protocol/ELLx%20modules%20protocol%20manual.pdf
Software manual: https://www.thorlabs.com/drawings/dbf356723d372c3f-2F53ED06-0E67-D3AC-CB56E3121BAA4D80/ELL14-Manual.pdf
"""

import serial
import struct
import time
import logging
import numpy as np
from nspyre_drivers.thorlabs.ellx.ellx import Ellx

class Ell14(Ellx):
    
    # dict, of all available commands, structured as {key: ('command', n_write, 'reply', n_read)},
    # where n_write is the number of bytes to be written, and n_read the number of bytes to be read
    # with the respective command
    # all possible commands are listed in https://www.thorlabs.com/Software/Elliptec/Communications_Protocol/ELLx%20modules%20protocol%20manual.pdf
    
    def __init__(self, port, address=0, rev_in_pulses = 143360):
        """
        serial: running serial instance
        
        address: int (0-8), internal address of device
        
        commands: dict, of all available commands, structured as {key: ('command', n_write, 'reply', n_read)},
                    where n_write is the number of bytes to be written, and n_read the number of bytes to be read
                    with the respective command
                    
        rev_in_pulses: one full revolution (2pi = 360 degrees) in pulses
        """
        Ellx.__init__(self, port, address)
        self.rev_in_pulses = rev_in_pulses
        
    def write(self, key,  val_deg = None, read=True):
        """
        key: string, one of the available keys in the commands dict
        
        val_deg: float, int or None, value in degrees
        
        read: bool, if set to True the device's reply is awaited and returned (together with the command string)
        
        returns: tuple of bytes (command string), int (reply in pulses), float (reply in deg) or None
        
        """
        byte_string, val_pulses_hex = self._write(key, self.degree_to_pulses(val_deg), read)
        return byte_string, self.pulses_to_degrees(val_pulses_hex)
        
    def degree_to_pulses(self, val_deg):
        """
        val_degree: float or int (4 bytes)
        
        returns: bytes, converted value to pulses in hexadecimal and byte format
        """
        if val_deg is not None:
            return struct.pack('>l', int(val_deg*self.rev_in_pulses/360)).hex().upper()
        else:
            return None

    def pulses_to_degrees(self, val_pulses):
        """
        val_pulses: string, corresponding to a 4 byte hexadecimal number
        
        returns: float (4 byte), converted value to degrees 
        """
        if val_pulses is not None:
            return 360*struct.unpack('>l', bytes.fromhex(val_pulses))[0]/self.rev_in_pulses
        else:
            return None
        
if __name__ == '__main__':
    # enable logging to console
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d [%(levelname)8s] %(message)s', datefmt='%m-%d-%Y %H:%M:%S')

    with Ell14(port='/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DK0DL7OB-if00-port0') as ell14:
        print("possible commands are: ")
        print(ell14.commands.keys())
        print("returns tuple of (commandbytestring, reply in degrees)")
        print("move to 45 deg (absolute): ", ell14.write('move_absolute', 45))
        print("get position: ", ell14.write('get_position'))
        time.sleep(2)
        print("move to home: ", ell14.write('move_to_home_cw'))
        degs = np.linspace(0,355,72)
        moved_degs = []
        time.sleep(5)
        for deg in degs:
            print(deg)
            a, b = ell14.write('move_absolute', deg)
            moved_degs.append(b)
            time.sleep(0.25)
        print(moved_degs)
        import pdb; pdb.set_trace()

        pass