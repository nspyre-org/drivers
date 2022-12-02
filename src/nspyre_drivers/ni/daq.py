"""Driver for NI-DAQ modules.

For installation on Ubunutu:
- Not all hardware is compatible, first check: https://www.ni.com/en-us/support/documentation/compatibility/21/ni-hardware-and-operating-system-compatibility.html
- Download https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html
- extract the zip file
- install the "drivers" package e.g.: sudo apt install ./ni-ubuntu2204firstlook-drivers-stream.deb
- install the ni-daqmx package: sudo apt install ni-daqmx 
- sudo dkms autoinstall
- reboot
"""

import nidaqmx

class DAQ:
    def __init__(self):
        self.system = nidaqmx.system.System.local()
        for d in self.system.devices:
            print(d)
        import pdb; pdb.set_trace()

    def set_ao_voltage(self):
        pass

    def ai_read(self, ch=None, dev=None):
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
            task.read()

if __name__ == '__main__':
    daq = DAQ()
