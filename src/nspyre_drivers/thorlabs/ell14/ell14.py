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

class Ell14():
    
    # dict, of all available commands, structured as {key: ('command', n_write, 'reply', n_read)},
    # where n_write is the number of bytes to be written, and n_read the number of bytes to be read
    # with the respective command
    # all possible commands are listed in https://www.thorlabs.com/Software/Elliptec/Communications_Protocol/ELLx%20modules%20protocol%20manual.pdf
    
    default_commands = {'get_position'      : ('gp', 0, 'PO', 8),
                        'get_home_offset'   : ('go', 0, 'HO', 8),
                        'get_jogstep_size'  : ('gj', 0, 'GJ', 8),
                        
                        'move_to_home_cw'   : ('ho0', 0, 'PO', 8), # clockwise
                        'move_to_home_ccw'  : ('ho1', 0, 'PO', 8), # counter clockwise
                        'move_absolute'     : ('ma', 8, 'PO', 8),
                        'move_relative'     : ('mr', 8, 'PO', 8),
                        'move_forward'      : ('fw', 0, 'PO', 8),
                        'move_backward'     : ('bw', 0, 'PO', 8),
                        'set_jogstep_size'  : ('sj', 8, 'GJ', 8)}
    
    def __init__(self, port, address=0, commands = default_commands, rev_in_pulses = 143360):
        """
        serial: running serial instance
        
        address: int (0-8), internal address of device
        
        commands: dict, of all available commands, structured as {key: ('command', n_write, 'reply', n_read)},
                    where n_write is the number of bytes to be written, and n_read the number of bytes to be read
                    with the respective command
                    
        rev_in_pulses: one full revolution (2pi = 360 degrees) in pulses
        """
        self.ser = serial.Serial(port, baudrate=9600, timeout=2)
        self.address = str(address)
        
        self.commands = commands
        
        self.rev_in_pulses = rev_in_pulses
        
    def write(self, key,  val_deg = None, read=True):
        """
        key: string, one of the available keys in the commands dict
        
        val_deg: float, int or None, value in degrees
        
        read: bool, if set to True the device's reply is awaited and returned (together with the command string)
        
        returns: tuple of bytes (command string), int (reply in pulses), float (reply in deg) or None
        
        """
        # value must be in degrees
        if key in self.commands.keys():
            command, n_write, reply, n_read = self.commands[key]
            
            if isinstance(val_deg,(int,float)): # must be 4 bytes
                val_pulses = self.degree_to_pulses(val_deg)
                
                byte_string = bytes(self.address + command + val_pulses, 'ascii') 
            else:
                byte_string = bytes(self.address + command, 'ascii')
                
            if read == True:
                self.ser.flushInput()
            self.ser.write(byte_string)
            
            if read == True:            
                line = self.ser.readline()

                while (line[0:3] == bytes(self.address + 'GS', 'ascii')) or (line[0:3] == bytes(self.address + reply, 'ascii')):
                    
                    if line[0:3] == bytes(self.address + reply, 'ascii'):
                        val_pulses_hex = (8-n_read)*'0' + line[3:n_read+3].decode()
                        
                        return byte_string, self.hex_to_decimal(val_pulses_hex), self.pulses_to_degrees(val_pulses_hex)
                    
                    line = self.ser.readline()

            return byte_string, None, None
        else:
            return None, None, None
        
    def degree_to_pulses(self, val_degree):
        """
        val_degree: float or int (4 bytes)
        
        returns: bytes, converted value to pulses in hexadecimal and byte format
        """
        return struct.pack('>l', int(val_degree*self.rev_in_pulses/360)).hex().upper()
        
        
        
    def pulses_to_degrees(self, val_pulses):
        """
        val_pulses: string, corresponding to a 4 byte hexadecimal number
        
        returns: float (4 byte), converted value to degrees 
        """
        return 360*struct.unpack('>l', bytes.fromhex(val_pulses))[0]/self.rev_in_pulses
    
    def hex_to_decimal(self, val_hex):
        """
        val_hex: string, corresponding to a 4 byte hexadecimal number
        
        returns: long int (4 bytes) 
        """
        return struct.unpack('>l', bytes.fromhex(val_hex))[0]
          
    def __del__(self):
        self.ser.close()
        
    def close(self):
        self.ser.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        
if __name__ == '__main__':
    # enable logging to console
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d [%(levelname)8s] %(message)s', datefmt='%m-%d-%Y %H:%M:%S')

    with Ell14(port='/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DK0BJ23I-if00-port0') as ell14:
        print("possible commands are: ")
        print(ell14.commands.keys())
        print("returns tuple of (commandbytestring, reply in pulses (steps), reply in degrees)")
        print("move to 45 deg (absolute): ", ell14.write('move_absolute', 45))
        print("get position: ", ell14.write('get_position'))
        print("move to home: ", ell14.write('move_to_home_cw'))
        degs = np.linspace(0,355,72)
        moved_degs = []
        time.sleep(5)
        for deg in degs:
            print(deg)
            a, b, c = ell14.write('move_absolute', deg)
            moved_degs.append(c)
            time.sleep(0.25)
        print(moved_degs)
        import pdb; pdb.set_trace()

        pass