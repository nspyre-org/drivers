"""
Copied from: https://github.com/MaximilianWinter/RotatorAPI/blob/main/API/RotatorAPI.py

Part: https://www.thorlabs.com/thorproduct.cfm?partnumber=ELL14
Communication manual: https://www.thorlabs.com/Software/Elliptec/Communications_Protocol/ELLx%20modules%20protocol%20manual.pdf
Software manual: https://www.thorlabs.com/drawings/dbf356723d372c3f-2F53ED06-0E67-D3AC-CB56E3121BAA4D80/ELL14-Manual.pdf

**NOTE: WHEN DEVICE RESTARTS, IT REVERTS ADDRESS BACK TO DEFAULT ADDRESS UNLESS SAVED USER DATA
To have multiple devices with different addresses, first power ELL1B, then connect
first device and change address, saving its user data. Then connect second device and change address, saving its user data, etc.**
"""

import serial
import struct
import time
import logging
import numpy as np

class Ellx():
    
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
    
    def __init__(self, port, address=0, commands = default_commands):
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

    def _write(self, key,  val_pulses = None, read=True):
        """
        key: string, one of the available keys in the commands dict
        
        val_deg: None or string, corresponding to a 4 byte hexadecimal number
        
        read: bool, if set to True the device's reply is awaited and returned (together with the command string)
        
        returns: tuple of bytes (command string), string corresponding to a 4 byte hexadecimal number or None, 
        
        """
        if key in self.commands.keys():
            command, n_write, reply, n_read = self.commands[key]
            if isinstance(val_pulses,(int,float)): # must be 4 bytes
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
                        
                        return byte_string, val_pulses_hex
                    
                    line = self.ser.readline()

            return byte_string, None
        else:
            return None, None

    def save_user_data(self):
        byte_string = bytes(f'{self.address}us','ascii')
        self.ser.flushInput()
        self.ser.write(byte_string)

    def change_address(self, new_address):
        # address is entered in the range 0-F. The default value is 0.
        byte_string = bytes(f'{self.address}ca{new_address}','ascii')
        self.ser.flushInput()
        self.ser.write(byte_string)
        self.address = str(new_address)

    def get_information(self):
        byte_string = bytes(f'{self.address}in','ascii')
        self.ser.flushInput()
        self.ser.write(byte_string)
        line = self.ser.readline()
        header = line[0:3]
        assert(header == bytes(f'{self.address}IN','ascii'))
        model = line[3:5] # model == bytes('06', 'ascii') #Ell6 bi-positional slider
        sn = line[5:13] #serial number
        year = line[13:17] #year of manufacturing
        fw_rel = line[17:19] #firmware release
        hw_rel = line[19:21] #hardware release
        travel = line[21:25] #travel mm/deg travel == bytes('001F', 'ascii') #31mm travel
        pulses_mu = line[25:] #pulses per position
        print(sn, year, fw_rel, hw_rel, travel, pulses_mu)
        return model, sn, year, fw_rel, hw_rel, travel, pulses_mu

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

    with Ellx(port='/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DK0BJ23I-if00-port0') as ell14:
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

    with Ellx(port='/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DK0DL7OB-if00-port0') as ella1:
        print("get position: ", ella1.write('get_position'))
        print("move to home: ", ella1.write('move_to_home_cw'))
        print("get position: ", ella1.write('get_position'))
        print("move forward: ", ella1.write('move_forward'))
        print("get position: ", ella1.write('get_position'))
