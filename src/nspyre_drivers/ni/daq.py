"""Wrapper driver for NI-DAQ modules. Implements some basic functionality to make the DAQ easier to use.

nidaqmx low-level driver needs to be installed first: https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html

For installation on Ubunutu:
- Not all hardware is compatible, first check: https://www.ni.com/en-us/support/documentation/compatibility/21/ni-hardware-and-operating-system-compatibility.html
- Download https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html
- extract the zip file
- install the "drivers" package e.g.: sudo apt install ./ni-ubuntu2204firstlook-drivers-stream.deb
- install the ni-daqmx package: sudo apt install ni-daqmx (may need to run sudo apt update)
- sudo dkms autoinstall
- (BEN: I needed to run python -m pip install nidaqmx)
- reboot
"""

import logging
import nidaqmx

logger = logging.getLogger(__name__)

class DAQ:
    def __init__(self, serial_num=None):
        """
        Args:
            serial_num: device serial number as a hex string e.g. '20BA17A' - leave as None to connect to any available nidaqmx device
        """
        self.system = nidaqmx.system.System.local()
        self.dev = None
        # iterate over the nidaqmx devices
        for d in self.system.devices:
            logger.debug(f'Found nidaqmx device [{d.name}] with serial number [{self.dec_sn_to_hex(d.dev_serial_num)}]')
            if serial_num is None or d.dev_serial_num == self.hex_sn_to_dec(serial_num):
                self.dev = d
        # check whether the device was found
        if self.dev is not None:
            logger.info(f'Bound to nidaqmx device [{self.dev.name}] with serial number [{self.dec_sn_to_hex(self.dev.dev_serial_num)}]')
        else:
            if serial_num is None:
                raise ValueError('No nidaqmx devices found.')
            else:
                raise ValueError(f'No nidaqmx device with the serial number {serial_num} was found.')
        self.task = None

    def __repr__(self):
        if self.dev is not None:
            return f'DAQ(name={self.dev.name}, serial_num={self.dec_sn_to_hex(self.dev.dev_serial_num)})'
        else:
            return 'DAQ(Not connected)'

    def serial_number(self):
        """Return the device serial number as a hex string"""
        return self.dec_sn_to_hex(self.dev.dev_serial_num)

    def dec_sn_to_hex(self, dec):
        """Convert the device serial number from decimal to hex form."""
        return hex(dec)[2:].upper()

    def hex_sn_to_dec(self, hex):
        """Convert the device serial number from hex to decimal form."""
        return int(hex, base=16)

    def reset(self):
        self.dev.reset_device()

    def _remove_dev_prefix(self, l):
        """remove device name e.g. 'Dev1/' prefix from all elements in list l."""
        trimmed_l = []
        for c in l:
            trimmed_l.append(c.split('/', 1)[1])
        return trimmed_l

    def ao_chans(self):
        """Return all of the analog output channel names e.g. ['ao0', 'ao1', ...]"""
        return self._remove_dev_prefix(self.dev.ao_physical_chans.channel_names)

    def ai_chans(self):
        """Return all of the analog input channel names e.g. ['ai0', 'ai1', ...]"""
        return self._remove_dev_prefix(self.dev.ai_physical_chans.channel_names)

    def do_lines(self):
        """Return all of the digital output line names e.g. ['port0/line0', 'port0/line1', ...]"""
        return self._remove_dev_prefix(self.dev.do_lines.channel_names)

    def set_ao(self, ch, val):
        """Set the analog output voltage for a given channel.

        Args:
            ch: analog output channel string e.g. 'ao0', 'ao1', ...
            val: analog output value (V)
        """
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(f'{self.dev.name}/{ch}')
            task.write(val, auto_start=True)

    def get_ai_se(self, ch):
        """Get the single-ended analog input voltage on a given channel.

        Args:
            ch: analog input channel string e.g. 'ai0', 'ai1', ...
        """
        ret = None
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(f'{self.dev.name}/{ch}', terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
            ret = task.read()
        return ret

    def set_do(self, port, line, state):
        """Set a digital output voltage.

        Args:
            port: device port string e.g. 'port0', 'port1', ...
            line: port line string e.g. 'line0', 'line1', ...
            state: output state boolean
        """
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(f'{self.dev.name}/{port}/{line}')
            task.write(state)

if __name__ == '__main__':
    import time
    # enable logging to console
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d [%(levelname)8s] %(message)s', datefmt='%m-%d-%Y %H:%M:%S')
    daq = DAQ(serial_num='20BA17A')
    import pdb; pdb.set_trace()
    for i in range(3):
        daq.set_ao('ao1', 1.2)
        daq.set_do('port0', 'line1', True)
        time.sleep(1)
        print(f'ai voltage (on): {daq.get_ai_se("ai0")}')
        daq.set_ao('ao1', 0.0)
        daq.set_do('port0', 'line1', False)
        time.sleep(1)
        print(f'ai voltage (off): {daq.get_ai_se("ai0")}')
