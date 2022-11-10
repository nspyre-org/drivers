"""Beaglebone Black GPIO driver (beaglebone must be running flask server driver).

Author: Jacob Feder
Date: 8/5/2022
"""
import requests
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

class BBGPIO(QObject):
    if gui:
        # for when the pin state is changed
        # args: pin id, state
        pin_state_changed = QtCore.Signal(str, bool)

    def __init__(self, hostname='beaglebone.local', port=5000, timeout=5):
        super().__init__()
        self.hostname = hostname
        self.port = port
        self.timeout = timeout

        # available pins
        # see https://vadl.github.io/beagleboneblack/2016/07/29/setting-up-bbb-gpio
        self.pins = []
        # pins on P8 header
        for i in range(7, 20):
            self.pins += [f'P8_{i}']
        self.pins += [f'P8_26']
        # pins on P9 header
        for i in range(11, 19):
            self.pins += [f'P9_{i}']
        for i in range(21, 25):
            self.pins += [f'P9_{i}']
        self.pins += ['P9_26', 'P9_27']

    def _request(self, msg):
        """Send a http request to the flask server.
        Args:
            msg: the https address e.g. '/gpio/output/high/<string:terminal>'

        Returns:
            http resonse text.

        Raises:
            ConnectionError: if the request failed
        """
        logger.debug(f'bbgpio request: [{msg}]')
        try:
            ret = requests.get(f'http://{self.hostname}:{self.port}{msg}', timeout=self.timeout)
            if ret.status_code != 200:
                raise ConnectionError
        except (requests.exceptions.ConnectionError, ConnectionError) as e :
            raise ConnectionError('flask request failed') from e
        logger.debug(f'bbgpio response: [{ret.text}]')
        return ret.text

    def connected(self):
        """Check if the server is accessible and running.

        Returns:
            True if so, False otherwise.
        """
        try:
            self._request(f'/')
        except ConnectionError:
            return False
        else:
            logger.info(f'Connected to Beaglebone@{self.hostname}:{self.port}')
            return True

    def restart(self):
        """Restart the flask service on the beaglebone.

        Raises:
            ConnectionError: if the beaglebone isn't responding.
        """

        # trigger the restart
        try:
            self._request('/restart')
        except ConnectionError:
            pass

        # wait until the service is back up
        timeout = time.time() + 5.0
        while True:
            if time.time() > timeout:
                raise ConnectionError('timed out waiting for beaglebone to restart')
            try:
                self._request('')
            except ConnectionError:
                pass
            else:
                break
            time.sleep(0.1)

    def set_pin(self, pin, state, emit=True):
        """Set the output state of a GPIO pin on the Beaglebone.

        Args:
            pin: pin name string like 'P8_35'
            state: True for high, False for low
            emit: True to emit a PyQt signal when the function finishes

        Raises:
            ValueError: invalid pin state
            RunTimeError: flask failure
        """
        if pin not in self.pins:
            raise ValueError(f'Pin is invalid or already allocated for another function. Available pins:\n{self.pins}')
        if state:
            self._request(f'/gpio/output/high/{pin}')
            logger.debug(f'Set Beaglebone@{self.hostname}:{self.port} pin [{pin}] HIGH')
        else:
            self._request(f'/gpio/output/low/{pin}')
            logger.debug(f'Set Beaglebone@{self.hostname}:{self.port} pin [{pin}] LOW')
        if gui and emit:
            self.pin_state_changed.emit(pin, state)

if __name__ == '__main__':
    bbgpio = BBGPIO()
    bbgpio.restart()
    bbgpio.set_pin('P8_14', False)
