"""
Allied Vision VimbaX camera driver.

https://www.alliedvision.com/en/products/software/vimba-x-sdk/

Copyright (c) 2023, Jacob Feder
All rights reserved.
"""
import logging

import numpy as np
from vmbpy import VmbSystem
from vmbpy import Camera
from vmbpy import Stream
from vmbpy import Frame
from vmbpy import VmbFeatureError
from vmbpy import VmbCameraError

_logger = logging.getLogger(__name__)

class VimbaX:
    """Allied Vision VimbaX camera wrapper driver."""
    def __init__(self, camera_id=None):
        """
        Args:
            camera_id: The camera id number to connect to. If None, the
                first available camera will be used.
        """
        self.camera_id = camera_id
        self.vmb = VmbSystem.get_instance()
        self.driver = None
        self.features = {}

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    def connect(self):
        """Connect to the camera."""

        # open the vimbax API
        self.vmb.__enter__()

        cams = self.vmb.get_all_cameras()
        if len(cams) == 0:
            raise RuntimeError('No VimbaX cameras detected')

        if self.camera_id is not None:
            # connect to a specific camera
            self.driver = self.vmb.get_camera_by_id(self.camera_id)
        else:
            # create instance for first connected camera
            self.driver = cams[0]

        # connect to the camera
        try:
            self.driver.__enter__()
        except Exception as err:
            self.driver = None
            raise err

        # collect all the features
        for feat in self.driver.get_all_features():
            self.features[feat.get_name()] = feat

        _logger.info(f'Connected to VimbaX camera with '
            f'id [{self.driver.get_id()}] '
            f'serial [{self.get_feature("DeviceSerialNumber")}].'
        )

    def disconnect(self):
        """Disconnect from the camera."""
        _logger.info(f'Disconnected from VimbaX camera with '
            f'id [{self.driver.get_id()}] '
            f'serial [{self.get_feature("DeviceSerialNumber")}].'
        )
        if self.driver is not None:
            self.driver.__exit__(None, None, None)
        self.vmb.__exit__(None, None, None)

    def get_features(self):
        """Return a list of all of the camera features."""
        return list(self.features)

    def get_feature(self, feat):
        """Return the value of an individual camera feature.

        Args:
            feat: the feature to query.
        """
        return self.features[feat].get()

    def set_feature(self, feat, val):
        """Set the value of an individual camera feature.

        Args:
            feat: the feature to set.
            val: the value to set the feature to.
        """
        self.features[feat].set(val)

    def print_features(self):
        """Print out the details of all camera features."""
        for feat in self.features.values():
            try:
                value = feat.get()
            except (AttributeError, VmbFeatureError):
                value = None
            print(f'Name [{feat.get_name()}]')
            print(f'Display name [{feat.get_display_name()}]')
            print(f'Tooltip [{feat.get_tooltip()}]')
            print(f'Description [{feat.get_description()}]')
            print(f'SFNC Namespace [{feat.get_sfnc_namespace()}]')
            print(f'Value [{value}]')
            print(f'-----------------------------')

    def get_image(self):
        """Return a single image from the camera as a numpy array."""
        frame = self.driver.get_frame()
        # get raw data from camera as numpy array
        np_frame = frame.as_opencv_image()
        return np_frame

if __name__ == '__main__':
    # vmbpy generates a lot of logging noise seemingly without a proper logger level
    # logging.basicConfig(
    #     level=logging.INFO,
    #     format='%(asctime)s.%(msecs)03d [%(levelname)8s] %(message)s',
    #     datefmt='%m-%d-%Y %H:%M:%S'
    # )

    with VimbaX() as cam:
        # cam.print_features()
        print(cam.get_features())
        # cam.set_feature('ExposureTime', 50000)
        # cam.get_feature('ExposureTime')
        # print(cam.get_image())
