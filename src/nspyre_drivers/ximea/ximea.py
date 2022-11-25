"""
Ximea camera driver.

Copyright (c) 2022, Jacob Feder
All rights reserved.
"""
import ximea.xiapi
import numpy as np

class XIMEA:
    """XIMEA camera wrapper driver."""
    def __init__(self, serial_number=None):
        self.serial_number = serial_number

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    def connect(self):
        if serial_number is not None:
            self.driver = ximea.xiapi.open_device_by_SN(serial_number)
        else:
            # create instance for first connected camera
            self.driver = ximea.xiapi.Camera()

        self.driver.open_device()
        # default settings
        # exposure (us)
        self.driver.set_exposure(100000)

    def disconnect(self):
        self.driver.close_device()

    def start_acquisition(self):
        self.driver.start_acquisition()

    def stop_acquisition(self):
        self.driver.stop_acquisition()

    def get_image(self):
        img = ximea.xiapi.Image()
        self.driver.get_image(img)
        # get raw data from camera
        # for Python3.x function returns bytes
        data_raw = img.get_image_data_raw()

        # transform data to numpy array
        data = np.array(list(data_raw), dtype=np.uint8).reshape(img.width, img.height)

        return data
