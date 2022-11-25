"""Arduino UNO GPIO driver (Arduino must be running pin server program).

set_dac available if an MCP4728 is connected.
https://learn.adafruit.com/adafruit-mcp4728-i2c-quad-dac/arduino

Author: Jacob Feder
Date: 10/17/2022
"""
import serial
import logging
import time

logger = logging.getLogger(__name__)

try:
    from pyqtgraph.Qt import QtCore
    QObject = QtCore.QObject
except ModuleNotFoundError:
    logger.info('Not declaring GUI because the required packages are not available')
    QObject = object
    gui = False
else:
    gui = True

class ArduinoGPIO(QObject):
    if gui:
        # for when the pin state is changed
        # args: pin id, state
        pin_state_changed = QtCore.Signal(int, bool)
        # args: dac channel, dac raw value
        dac_val_changed = QtCore.Signal(str, int)
        # args: dac channel, dac voltage
        dac_voltage_changed = QtCore.Signal(str, float)

    def __init__(self, com_port: str, pins=None, baud=115200,
                    write_timeout:float = 3.0, timeout: float = 3.0):
        """Args:
            com_port: serial COM port (see pyserial docs)
            npins: number of digital pins
            baud: baudrate
            timeout: read timeout (s)
        """
        super().__init__()

        # available pins
        if pins is not None:
            self.pins = pins
        else:
            # assume arduino UNO
            self.pins = list(range(2, 13))

        # DAC channel mapping
        self.dac_chs = {
            'VA': 0,
            'VB': 1,
            'VC': 2,
            'VD': 3,
        }

    def open(self):
        self.serial_port = serial.Serial(com_port, baudrate=baud, timeout=timeout)
        logger.info(f'connected to Arduino @ [{com_port}]')
        # this is required due to a funky issue with the arduino uno
        # (it restarts the arduino when opening the serial port, so we have to wait for it to boot)
        # https://stackoverflow.com/questions/1618141/pyserial-problem-with-arduino-works-with-the-python-shell-but-not-in-a-program/4941880#4941880
        time.sleep(2)

    def close(self):
        self.serial_port.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def _send_cmd(self, cmd, arg1=0, arg2=0, arg3=0, tries=0):
        """Format and send a command to the device.
        
        Args:
            cmd: the command to send, e.g. 'o' for digital output
            arg1: first argument for command
            arg2: second argument for command
            tries: the number of times that the communication has been attempted

        Returns:
            The device response as a string
        """
        msg = cmd.encode('ascii') + bytes([arg1, arg2, arg3])
        logger.debug(f'writing packet 0x{msg.hex()} to Arduino [{self.serial_port}]')
        self.serial_port.write(msg)
        # response the Arduino sends when it's ready for the next command
        ok_resp = b'rdy\n'
        # response from the Arduino
        resp = b''
        while ok_resp not in resp:
            resp += self.serial_port.read(1)
            logger.debug(f'Arduino responded with [{resp.decode("ascii", "ignore").encode("unicode_escape")} (ascii)] [{resp.hex()}(hex)]')
            if resp == b'':
                raise RuntimeError('Error in communication with Arduino program. No Response.')
        if b'error' in resp:
            if tries < 5:
                # shift one byte so that hopefully it reads correctly next time
                self.serial_port.write(bytes([0]))
                self._send_cmd(cmd, arg1, arg2, arg3, tries=tries + 1)
            else:
                # if it's failed too many times, give up
                raise RuntimeError(f'Error in communication with Arduino program. Arduino program error:\n{resp}')
        return resp

    def set_pin(self, pin, state, emit=True):
        """Set the output state of a GPIO pin.

        Args:
            pin: pin number
            state: True for high, False for low
            emit: True to emit a PyQt signal when the function finishes

        Raises:
            ValueError: invalid pin
        """
        if pin not in self.pins:
            raise ValueError(f'Pin is invalid. Available pins:\n{self.pins}')
        if state:
            self._send_cmd('o', pin, 1)
            logger.debug(f'Set Arduino@{self.serial_port} pin [{pin}] HIGH')
        else:
            self._send_cmd('o', pin, 0)
            logger.debug(f'Set Arduino@{self.serial_port} pin [{pin}] LOW')
        if gui and emit:
            self.pin_state_changed.emit(pin, state)

    def set_dac(self, ch, val, emit=True):
        """Set the output voltage of the connected MCP4728 quad DAC.

        Args:
            ch: DAC channel string ('VA', 'VB', 'VC', or 'VD')
            val: 12-bit DAC output raw value (0-4095) 
            emit: True to emit a PyQt signal when the function finishes

        Raises:
            ValueError: invalid pin
        """
        if ch not in self.dac_chs:
            raise ValueError(f'DAC channel is invalid. Available channels:\n{self.dac_chs.keys()}')
        if val < 0 or val > 4095 or not isinstance(val, int):
            raise ValueError('val must be an int in the range 0 < val < 4095')

        self._send_cmd('d', self.dac_chs[ch], val & 0xFF, (val & 0xFF00) >> 8)
        logger.debug(f'Set Arduino@{self.serial_port} dac ch [{ch}] to [{val}]')

        if gui and emit:
            self.dac_val_changed.emit(ch, val)

    def set_voltage(self, ch, volt, emit=True):
        """Set DAC output voltage
        
        Args:
            ch: DAC channel string ('VA', 'VB', 'VC', or 'VD')
            volt: voltage value between 0 and 4.096V
            emit: True to emit a PyQt signal when the function finishes
        """
        val = round(volt / 4.096 * 4095)
        self.set_dac(ch, val, emit=emit)
        if gui and emit:
            self.dac_voltage_changed.emit(ch, volt)

if __name__ == '__main__':
    import time
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d [%(levelname)8s] %(message)s', datefmt='%m-%d-%Y %H:%M:%S')

    with ArduinoGPIO('/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_95138323838351118221-if00') as arduino:
        arduino.set_pin(2, True)
        time.sleep(2)
        arduino.set_pin(2, False)
        for i in range(0, 4096, 10):
            arduino.set_dac('VA', i)
            time.sleep(0.01)
