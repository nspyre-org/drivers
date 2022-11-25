"""PI E-710 piezo controller driver. Written for controller firmware version 6.033.

Page numbers refer to the E-710 user manual.

Author: Jacob Feder
Date: August 26 2021
"""

from serial import Serial
import datetime
import logging
import time

logger = logging.getLogger(__name__)

# distance error from target position where the stage can be considered to have reached the target (um)
DEFAULT_EPSILON = 0.05
# time to wait for the stage to reach a target position
DEFAULT_POS_TIMEOUT = 2.0

class PI710:
    def __init__(self, port, axes, timeout=1.0):
        """
        Args:
            port: serial tty port e.g. 'COM4'
            axes: axis mapping from names to channel #'s
                e.g. {'x': '1', 'y': '2', 'z': '3'}
            timeout: timeout for reading (s)
        """
        self.port = port
        # pyserial port object
        self.sp = None
        self.axes = axes
        self.timeout = timeout
        # servo update period
        self.tservo = 1 / 5e3

    def connect(self, baudrate=115200):
        """Connect to the PI controller

        Args:
            baudrate: serial communication baudrate

        Raises:
            ConnectionError: Couldn't connect to the controller
        """
        # initialize at 9600 baud
        self.sp = Serial(self.port, baudrate=9600, timeout=0)
        self.flush()
        # if the controller is in 9600 baud mode, set the new baud rate
        self.send_raw('0BR' + str(baudrate))
        # disconnect then reconnect at the new baudrate
        self.disconnect()
        time.sleep(0.2)
        self.sp = Serial(self.port, baudrate=baudrate, timeout=0)
        # make sure the send buffer is empty
        self.flush()
        # query the device info to confirm connection
        self.send_raw('GI')
        # read whatever info the controller has sent after a small delay
        time.sleep(0.2)
        resp = self.read_all()
        logging.debug(f'Controller info:\n{resp}')
        if 'Digital Piezo Controller' not in resp:
            raise ConnectionError(f'Controller response "{resp}" expected to contain "Digital Piezo Controller". The controller is either not connected or not responding.')
        # disconnect and reconnect one final time, with the proper baud and timeout
        self.disconnect()
        self.sp = Serial(self.port, baudrate=baudrate, timeout=self.timeout)

    def disconnect(self):
        """Close connection to the controller."""
        if self.sp:
            self.sp.close()
            self.sp = None

    def send_raw(self, cmd):
        """Send a message to the controller (terminator is generated automatically).

        Args:
            cmd: command to send as a string
        """
        # add terminator and convert to ascii
        msg = (cmd + '\n').encode('ASCII')
        logger.debug(f'sent [{msg}]')
        # send the message
        self.sp.write(msg)

    def send(self, cmd):
        """Send a message to the controller and check whether it was received and processed (terminator is generated automatically).

        Args:
            cmd: command to send as a string
        """
        # add terminator and convert to ascii
        self.send_raw(cmd)
        # query the controller status
        self.send_raw('1GI8')
        resp = self.readline()
        # extract the status code
        status_code = -1
        for substr in resp.split():
            if substr.isdigit():
                status_code = int(substr)
        if status_code == -1:
            raise ValueError('Error checking controller status code. The command passed to send() may have had a response from the controller - use send_raw() instead.')

        # if the command was not understood, an error bit will be reported (p. 119)
        if status_code & 32768:
            raise ValueError('Command was not understood by the controller')

    def flush(self):
        """Send a terminator character to make sure any previous message has been written."""
        self.send_raw('')

    def readline(self):
        """Read a single newline terminated message from the controller.

        Returns:
            Response from the controller (with the terminator stripped)
        """
        msg = self.sp.readline().decode('ASCII')
        if msg == '':
            raise TimeoutError
        msg = msg.strip('\n')
        logger.debug(f'received [{msg}]')
        return msg

    def read_all(self):
        """Read all lines from the controller available within the timeout period.

        Returns:
            The response from the controller (with line terminators)
        """
        resp = ''
        while True:
            try:
                resp += self.readline() + '\n'
            except TimeoutError:
                return resp

    def servo_mode(self):
        """Enable closed-loop control mode."""
        for axis in self.axes.values():
            # subsequent DW (data write) commands will apply to this axis, RAM only (p. 99)
            self.send(axis + 'DP0')
            # enable servo control (p. 75)
            self.send('2DW1')
            # turn on servo control (p. 141)
            self.send(axis + 'SL1')
        logger.debug('init done')

    def home(self):
        """Go to position 0 on all axes."""
        # TODO autozero AZ?
        for axis in self.axes.values():
            self.send(axis + 'GH')

    def wait_pos(self, axis, target_pos, epsilon, timeout):
        """Poll the stage position until it is within epsilon of the target position.

        Args:
            axis: axis key e.g. 'x'
            target_pos: target position
            epsilon: function will return when the stage is within epsilon of the target
            timeout: wait timeout (s)

        Raises:
            TimeoutError: timeout occurred waiting to reach target position
        """
        start_time = datetime.datetime.now()
        current_pos = self.pos(axis)
        # wait for the stage to be in position for at least 3 subsequent readings
        for i in range(3):
            while abs(target_pos - current_pos) >= epsilon:
                if timeout and (datetime.datetime.now() - start_time).total_seconds() > timeout:
                    raise TimeoutError
                time.sleep(0.01)
                current_pos = self.pos(axis)

    def pos(self, axis):
        """Return the actual position of the given axis.

        Args:
            axis: axis key e.g. 'x'

        Returns:
            The axis position (um)
        """
        if axis in self.axes:
            self.send_raw(self.axes[axis] + 'TP')
            resp = self.readline()
            try:
                pos = float(resp)
            except ValueError as exc:
                raise ConnectionError(f'Invalid response "{resp}" from the controller when querying the position') from exc
            logger.debug(f'[{axis}] at [{pos}]')
            return pos
        else:
            raise ValueError

    def set_pos(self, axis, pos, blocking=True, epsilon=DEFAULT_EPSILON, timeout=DEFAULT_POS_TIMEOUT):
        """Set the target position of the given axis.

        Args:
            axis: axis key e.g. 'x'
            pos: the target position (um)
            blocking: if True, wait until the stage is within epsilon of the target position before returning
            epsilon: see blocking
            timeout: if blocking is True, max time to block (s)

        Raises:
            TimeoutError: timeout occurred waiting to reach target position
        """
        if axis in self.axes:
            logger.info(f'moving [{axis}] to [{pos}]')
            # TODO check input range
            self.send(self.axes[axis] + 'MA' + str(pos))
        else:
            raise ValueError('axis not found')

        if blocking:
            self.wait_pos(axis, pos, epsilon, timeout)

    def config_line_scan(self, axis, scan_len, npts, time_per_pt):
        """Configure the stage to scan in a line. Use line_scan() to initiate the actual scan.

        Args:
            axis: the axis to scan
            scan_len: the distance of the scan (um)
            npts: the number of points in the scan
            time_per_pt: the time to wait at each point (s)

        Raises:
            ValueError: Invalid arguments.
        """
        if axis not in self.axes:
            raise ValueError('axis not found')

        # TODO check input range
        # the servo loop updates with a period of self.tservo.
        # clocks_per_pt is the number of integer multiples of tservo per point
        clocks_per_pt = round(time_per_pt / self.tservo)
        if not clocks_per_pt:
            raise ValueError(f'time_per_pt [{time_per_pt}] must be greater than the controller update rate [{self.tservo}]')
        logger.debug(f'configure line scan [{clocks_per_pt}] clocks_per_pt')

        # number of points allocated for the ramp up / down portion of the motion
        npts_ramp = 50
        # number of points in controller memory
        controller_npts = npts * clocks_per_pt + 2 * npts_ramp
        if controller_npts > 63488:
            raise ValueError('maximum number of points in controller memory exceeded - reduce the npts*time_per_pt')

        if controller_npts > 16384:
            raise ValueError('maximum number of trigger points in controller memory exceeded - reduce npts')

        # correct for ramp up / down portion of the waveform (see p. 121 a2 equation)
        scan_len = scan_len * (controller_npts - npts_ramp) / (controller_npts - 2 * npts_ramp)

        # see p. 54, 119
        # segment definition mode
        self.send('0PT0')
        # set the total number of points in the segment
        self.send('1PT' + str(controller_npts))
        # set the number of points in the curve
        self.send('1CP' + str(controller_npts))
        # set the center point of the curve
        self.send('1PC' + str(round(controller_npts/2)))
        # set the ramp up / down number of points
        self.send('1PS' + str(npts_ramp))
        # set the point index in the segment definition
        # where the curve generation will begin
        self.send('1PA0')
        # set no offset
        self.send('1FO0')
        # generate the line scan curve and save it into the segment
        self.send('1GL' + str(scan_len))
        # give the controller time to generate the points

        # switch from segment definition mode to waveform definition mode
        self.send('0PT0')
        # define waveform as the entire segment
        self.send('1PT' + str(controller_npts))
        # connect waveform with wave generator (p. 58)
        self.send('1SF1')
        # connect desired axis with wave generator
        self.send(self.axes[axis] + 'CF1')

        # configure trigger settings (p. 59)
        # trigger 1 will be a "pixel" pulse that outputs a short pulse at the beginning of each point
        # trigger 2 will be active high during the entire duration of the constant-velocity portion of the line scan
        # trigger 1 is an active-high short pulse
        self.send('1KT1')
        # trigger 2 is an active-high long pulse
        self.send('2KT2')

        # clear all trigger points
        self.send('0FT0')
        # enable trigger 2 on the first point of the constant-velocity portion of the scan
        self.send(f'{npts_ramp + 1}FT2')
        # enable trigger 2 on all subsequent points until the end of the constant-velocity portion of the scan
        self.send(f'{controller_npts - npts_ramp}FT258')
        for i in range(npts):
            # for each "pixel" point, activate trigger 1 (and trigger 2 so as not to undo our work in previous FT statements)
            self.send(f'{npts_ramp + 1 + i * clocks_per_pt}FT3')

    def line_scan(self, axis, start_pos, blocking=True, epsilon=DEFAULT_EPSILON, timeout=DEFAULT_POS_TIMEOUT):
        """Run a line scan that was previously configured with config_line_scan(). The scan will start at the current position. During the scan, generate a pulse on digital output 1 for each point. After motion, return to the start position.

        Args:
            start_pos: starting position of the scan
            blocking, epsilon, timeout: see set_pos

        Raises:
            TimeoutError: timeout occurred waiting to reach target position
        """

        # move to the starting position
        self.set_pos(axis, start_pos, blocking=True, epsilon=epsilon, timeout=timeout)

        # activate the waveform generator a single time, and automatically return to the original start position
        self.send('1SC0')

        # wait until the stage returns to the starting position
        self.wait_pos(axis, start_pos, epsilon, timeout)

    def __enter__(self, *kwargs):
        self.connect()
        self.servo_mode()
        self.home()
        return self

    def __exit__(self, *kwargs):
        self.disconnect()

if __name__ == '__main__':
    # enable logging to console
    logging.basicConfig(level=logging.DEBUG)

    # initialize driver and connect to the controller
    with PI710('COM4', {'x': '1', 'y': '2', 'z': '3'}) as pi:
        # move each axis back and forth a few times
        # for axis, pos in [('x', 100), ('y', 100), ('z', 10)]:
        #     for i in range(3):
        #         pi.set_pos(axis,  0.0, blocking=False)
        #         time.sleep(0.2)
        #         pi.set_pos(axis,  pos, blocking=False)
        #         time.sleep(0.2)

        # do a few line scans
        pi.config_line_scan('x', 200.0, 100, 1e-3)
        for i in range(100):
            pi.line_scan('x', 50)
            time.sleep(1.0)
        print('done')
