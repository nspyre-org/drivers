"""
GUI for streaming XIMEA camera video.

Copyright (c) 2022, Jacob Feder
All rights reserved.
"""
from functools import partial
import logging
from threading import Lock

import numpy as np
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

from nspyre_drivers.ximea.ximea import XIMEA

logger = logging.getLogger(__name__)

class VideoStreamer(QtCore.QObject):
    """Worker object to stream data from the camera in a thread."""
    new_frame = QtCore.Signal(np.ndarray)

    def __init__(self, cam):
        super().__init__()
        self.cam = cam
        self.acquiring = False
        self.lock = Lock()
        self.sem = QtCore.QSemaphore(n=1)

    def acquire(self):
        """Continuously acquire images."""
        with self.lock:
            if self.acquiring:
                logger.warning('Cannot start acquisition because camera is already acquiring.')
                return
            self.acquiring = True
        while self.acquiring:
            # don't get the next frame until the previous frame has been displayed
            # in order to prevent overwhelming the GUI
            self.sem.acquire()
            frame = self.cam.get_image()
            self.new_frame.emit(frame)


class XimeaCameraWidget(QtWidgets.QWidget):
    """Qt widget for displaying the camera feed."""
    def __init__(self, camera_port=None):
        """
        Args:
            camera_port: the serial number of the camera, or None to pick the first available
        """
        super().__init__()

        # create camera driver
        self.cam = XIMEA(camera_port)
        self.cam.__enter__()
        self.cam.start_acquisition()

        # top level layout
        layout = QtWidgets.QVBoxLayout()

        # get an image to figure out the dimension
        img = self.cam.get_image()
        self.disply_width = img.shape[0]
        self.display_height = img.shape[1]

        # create the label that holds the image
        self.image_label = QtWidgets.QLabel()
        self.image_label.resize(self.disply_width, self.display_height)
        layout.addWidget(self.image_label)

        # worker object to read the camera data
        self.stream_worker = VideoStreamer(self.cam)
        # proper Qt thread handling
        # https://mayaposch.wordpress.com/2011/11/01/how-to-really-truly-use-qthreads-the-full-explanation/
        self.thread = QtCore.QThread()
        self.stream_worker.moveToThread(self.thread)
        # stop the streamer when this object is destroyed
        self.destroyed.connect(partial(self.stop_streamer))
        self.destroyed.connect(self.thread.quit)
        self.thread.finished.connect(partial(self.exit))
        # run update_image to update the QLabel whenever a new image is available from the camera
        self.stream_worker.new_frame.connect(self.update_image)
        # start the thread
        self.thread.start()

        # acuisition controls
        controls_layout = QtWidgets.QHBoxLayout()

        # button to turn the acquisition on
        self.start_button = QtWidgets.QPushButton('Start')
        self.start_button.clicked.connect(self.stream_worker.acquire)
        controls_layout.addWidget(self.start_button)

        # button to turn the acquisition off
        self.stop_button = QtWidgets.QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_streamer)
        controls_layout.addWidget(self.stop_button)

        # exposure time spinbox
        controls_layout.addWidget(QtWidgets.QLabel('Exposure time'))
        self.exposure_spinbox = SpinBox(value=100e-3, suffix='s', siPrefix=True, bounds=(0, 1000), dec=True, minStep=1e-6)
        self.exposure_spinbox.sigValueChanged.connect(lambda spinbox: self.cam.driver.set_exposure(spinbox.value()*1e6))
        self.exposure_spinbox.setValue(100e-3)
        controls_layout.addWidget(self.exposure_spinbox)

        # gain spinbox
        controls_layout.addWidget(QtWidgets.QLabel('Gain'))
        self.gain_spinbox = SpinBox(value=1, bounds=(0, 2e16), dec=True, minStep=1e-3)
        self.gain_spinbox.sigValueChanged.connect(lambda spinbox: self.cam.driver.set_gain(spinbox.value()))
        self.gain_spinbox.setValue(1)
        controls_layout.addWidget(self.gain_spinbox)

        layout.addLayout(controls_layout)
        self.setLayout(layout)

    def stop_streamer(self):
        self.stream_worker.acquiring = False

    def exit(self):
        self.cam.stop_acquisition()
        self.cam.__exit__()

    def update_image(self, frame):
        """Updates the image_label with a new opencv image"""
        # convert from numpy array to qt pixmap
        qt_img = self.convert_np_qt(frame)
        self.image_label.setPixmap(qt_img)
        self.stream_worker.sem.release()

    def convert_np_qt(self, img):
        """Convert from an greyscale numpy array image to QPixmap"""
        # make a copy to prevent the data from being overwritten
        self.img = img.copy()
        width = img.shape[0]
        height = img.shape[1]
        qt_image = QtGui.QImage(img, width, height, QtGui.QImage.Format.Format_Grayscale8)
        # scale to the window size
        scaled_qt_image = qt_image.scaled(self.image_label.frameGeometry().width(),
                                        self.image_label.frameGeometry().height(),
                                        QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        return QtGui.QPixmap.fromImage(scaled_qt_image)
