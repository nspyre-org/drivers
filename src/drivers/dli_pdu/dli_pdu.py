"""Digital Loggers, Inc. web-controlled power strip part number 222.

https://www.digital-loggers.com/222spec.pdf

This is a thin wrapper around the dlipower module that makes the interface a little more convenient.

There is a bug in the dlipower module that causes things to fail after the session times out.
To increase the session timeout follow the instructions under "Can I set the session timeout longer?"
http://www.digital-loggers.com/lpcfaqs.html#MakeSessionLonger

Author: Jacob Feder
Date: 2/11/2022
"""
import dlipower
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
TIMEOUT = 5.0

class DLIPDU():
    def __init__(self, config=None, hostname='192.168.0.100', userid='admin', password='1234', retries=1, timeout=TIMEOUT, **kwargs):
        """
        Args:
            config: dict with integer keys mapping to the desired names of the outlets.
            setup: Write the system config. This only needs to be done once.
            hostname: See dlipower docs.
            userid: See dlipower docs.
            password: See dlipower docs.
        """
        if config:
            self.config = config
        else:
            # these outlet numbers correspond to the ones printed on the housing
            self.config = {
                            1: 'sw1',
                            2: 'sw2',
                            3: 'sw3',
                            4: 'sw4',
                            5: 'sw5',
                            6: 'sw6',
                            7: 'sw7',
                            8: 'sw8',
                        }
        self.hostname = hostname
        self.userid = userid
        self.password = password
        self.retries = retries
        self.timeout = timeout
        self.kwargs = kwargs

    def __getitem__(self, index_key):
        """Return the outlets object for a given integer index or string key (the name of the power outlets)."""
        def get_switch_index():
            if isinstance(index_key, str):
                # invert the keys and values in the config dict
                inv_config = {v: k for k, v in self.config.items()}
                return inv_config[index_key] - 1
            elif isinstance(index_key, int):
                return index_key - 1
            else:
                raise ValueError('index_key should be an integer or string')

        try:
            outlet = self.switch[get_switch_index()]
        except TypeError as err:
            # this can happen if the switch disconnects for some reason
            logger.debug(f'switch [{self}] is disconnected, attempting reconnection...')
            self.switch.login()
            outlet = self.switch[get_switch_index()]

        return outlet

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        pass

    def connect(self):
        """Connect to the switch."""
        # TODO connection timeout not working
        self.switch = dlipower.PowerSwitch(hostname=self.hostname, userid=self.userid, password=self.password, retries=self.retries, timeout=self.timeout, **self.kwargs)

        # gather the current outlet names
        current_outlets = set()
        for s in self.switch[:]:
            current_outlets.add(s.description)

        # check if the outlet names have been set, if not, set up the new outlet names
        if set(self.config.values()) != current_outlets:
            for s in self.config:
                self.switch[s - 1].name = self.config[s]

    def set(self, outlet, state, block=True, timeout=TIMEOUT):
        """Set the state of an outlet(s).
        Args:
            outlet: the name (or index) of the outlet, or an iterable of outlet names (or indices)
            state: True to turn the outlet on, otherwise off
            block: if True, wait until the outlet(s) has been toggled before returning
            timeout: time (s) to wait before giving up
        """
        # create an array of outlets to be rebooted
        if isinstance(outlet, str) or isinstance(outlet, int):
            outlets = [outlet]
        else:
            outlets = outlet

        # set the state of the outlets
        for o in outlets:
            if state:
                self.__getitem__(o).on()
                logger.debug(f'Turned outlet [{o}] on.')
            else:
                self.__getitem__(o).off()
                logger.debug(f'Turned outlet [{o}] off.')

        if block:
            # wait until all the outlets have been set, or timeout
            start_time = datetime.now()
            while True:
                # check if the states of all relevant outlets have changed
                complete = True
                for o in outlets:
                    if (state and self.__getitem__(o).state != 'ON') or \
                        (not state and self.__getitem__(o).state != 'OFF'):
                        complete = False
                if complete:
                    break

                # check for timeout
                time_delta = datetime.now() - start_time
                if time_delta.total_seconds() > timeout:
                    raise TimeoutError(f'Timed out waiting to set the state of the outlets [{outlets}]')

    def on(self, outlet, block=True, timeout=TIMEOUT):
        """Turn an outlet(s) on.
        Args:
            outlet: the name of the outlet, or an iterable of outlet names
            block: if True, wait until the outlet(s) has been toggled before returning
            timeout: time (s) to wait before giving up
        """
        self.set(outlet, True, block=block, timeout=timeout)

    def off(self, outlet, block=True, timeout=TIMEOUT):
        """Turn an outlet(s) off.
        Args:
            outlet: the name of the outlet, or an iterable of outlet names
            block: if True, wait until the outlet(s) has been toggled before returning
            timeout: time (s) to wait before giving up
        """
        self.set(outlet, False, block=block, timeout=timeout)

    def reboot(self, outlet, wait_time=1.0, timeout=TIMEOUT):
        """Power cycle an outlet.
        Args:
            outlet: the name of the outlet, or an iterable of outlet names
            wait_time: the time to wait between turning the outlet off and on
            timeout: time to wait for the individual outlets to toggle before giving up (see set())
        """
        # turn the outlet(s) off
        self.set(outlet, False)

        # wait
        time.sleep(wait_time)

        # turn the outlet(s) on
        self.set(outlet, True)

    def reboot_all(self, wait_time=1.0):
        """Power cycle all outlets.
        Args:
            wait_time: the time to wait between turning the outlet off and on
        """
        self.reboot(self.config.values(), wait_time=wait_time)
