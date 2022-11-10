"""
Simple wrapper interface for Zaber stages.

Copyright (c) 2022, Jacob Feder
All rights reserved.
"""
import logging
from pathlib import Path
from collections import OrderedDict

from zaber_motion import Library, Units
from zaber_motion.ascii import Connection
Library.enable_device_db_store()

logger = logging.getLogger(__name__)

class ZaberStages:
    """Collection of Zaber stages. Automatically connects to the stages and allows intuitive access to the underlying zaber axis objects."""
    def __init__(self, axis_mapping, serial_port=None):
        """
        Args:
            serial_port: serial COM port (see pyserial docs). Leave as None to detect automatically (linux only).
            axis_mapping: dictionary mapping an axis peripheral id (int) to the axis name (str)
        """
        self.axis_mapping = axis_mapping
        self.com_port = com_port

    def __getitem__(self, key):
        """Return the zaber axis object associated with the given key."""
        if key in self.axes:
            return self.axes[key]
        else:
            raise KeyError(f'Zaber axis key [{key}] not found')

    def __iter__(self):
        return self.axes.__iter__()

    def __next__(self):
        return self.axes.__next__()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def open(self):
        if self.com_port:
            self.conn = Connection.open_serial_port(com_port)
            logger.debug(f'Found {len(device_list)} devices')
        else:
            # detect any connected Zaber serial devices
            zaber_serial_ports = Path('/dev/serial/by-id/').glob('usb-Zaber_Technologies_Inc.*')
            self.conn = None
            for s in zaber_serial_ports:
                # connect to the first one and then exit the loop
                self.conn = Connection.open_serial_port(str(s))
                break
            if self.conn is None:
                raise IOError('No Zaber devices found')

        self.devices = self.conn.detect_devices()
        logger.debug(f'Found [{len(self.devices)}] zaber devices')

        self.axes = OrderedDict()
        for device in self.devices:
            for i in range(1, device.axis_count + 1):
                axis = device.get_axis(i)
                logger.debug(f'Found Zaber axis [{axis}] with peripheral id [{axis.peripheral_id}]')
                if axis.peripheral_id in axis_mapping:
                    axis_key = axis_mapping[axis.peripheral_id]
                    logger.debug(f'Associated zaber axis [{axis_key}] with peripheral id [{axis.peripheral_id}]')
                    self.axes[axis_key] = axis

    def close(self):
        self.conn.close()
