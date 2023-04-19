"""
GUI for a generic camera accessible from openCV.

Copyright (c) 2022, Jacob Feder
All rights reserved.
"""
from functools import partial
import logging
from threading import Lock

import cv2
import numpy as np
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox


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
            ret, frame = self.cam.read()
            if not ret:
                raise RuntimeError('Failed reading camera frame')
            self.new_frame.emit(frame)


class CV2CameraWidget(QtWidgets.QWidget):
    """Qt widget for displaying the camera feed."""
    def __init__(self, camera_port=0):
        """
        Args:
            camera_port: the openCV port number of the camera (0 for first connected camera, 1 for second, ...)
        """
        super().__init__()

        # create camera driver
        self.cam = cv2.VideoCapture(camera_port)
        if not self.cam.isOpened():
            raise RuntimeError('Failed connecting to camera.')

        # top level layout
        layout = QtWidgets.QVBoxLayout()

        self.disply_width = 640
        self.display_height = 480
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

        # gain spinbox
        controls_layout.addWidget(QtWidgets.QLabel('Gain'))
        self.gain_spinbox = SpinBox(value=1, bounds=(0, 2e16), dec=True, minStep=1e-3)
        self.gain_spinbox.sigValueChanged.connect(lambda spinbox: self.set_gain(spinbox.value()))
        self.gain_spinbox.setValue(1000)
        controls_layout.addWidget(self.gain_spinbox)

        layout.addLayout(controls_layout)
        self.setLayout(layout)

    def stop_streamer(self):
        self.stream_worker.acquiring = False

    def exit(self):
        self.cam.release()

    def set_gain(self, gain):
        self.gain = gain

    def update_image(self, frame):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(frame)
        self.image_label.setPixmap(qt_img)
        self.stream_worker.sem.release()

    # https://gist.github.com/docPhil99/ca4da12c9d6f29b9cea137b617c7b8b1
    def convert_cv_qt(self, img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        return QtGui.QPixmap.fromImage(p)
