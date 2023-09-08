"""
GUI for streaming Allied Vision VimbaX camera video.

Copyright (c) 2023, Jacob Feder
All rights reserved.
"""
from functools import partial
import logging
from threading import Lock
from threading import Thread
from threading import Event
import queue
import copy

import numpy as np
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

from nspyre_drivers.allied_vision.vimbax import VimbaX
from vmbpy import FrameStatus
from vmbpy import Camera
from vmbpy import Stream
from vmbpy import Frame
from vmbpy import VmbCameraError
from vmbpy import PixelFormat

_logger = logging.getLogger(__name__)

class VimbaXFrameProducer(QtCore.QObject):
    """Adapted from VimbaX vmbpy examples/multithreading_opencv. Starts"""

    new_frame = QtCore.Signal()

    def __init__(self, cam: VimbaX, frame_queue: queue.Queue):
        super().__init__()
        self.cam = cam
        self.frame_queue = frame_queue
        self.kill = Event()

    def __call__(self, cam: Camera, stream: Stream, frame: Frame):
        # This method is executed within VmbC context. All incoming frames
        # are reused for later frame acquisition. If a frame shall be queued, the
        # frame must be copied and the copy must be sent, otherwise the acquired
        # frame will be overridden as soon as the frame is reused.
        if frame.get_status() == FrameStatus.Complete:
            # make a copy to prevent the data from being overwritten
            frame_cpy = copy.deepcopy(frame)
            # convert to a numpy array
            img_np = frame_cpy.as_opencv_image()
            try:
                self.frame_queue.put_nowait(img_np)
            except queue.Full:
                _logger.info('VimbaX camera dropped frame because the queue is full.')
            else:
                self.new_frame.emit()
        cam.queue_frame(frame)

    def stop_acquisition(self):
        self.kill.set()

    def start_acquisition(self):
        self.kill.clear()
        try:
            self.cam.set_feature('PixelFormat', PixelFormat.Mono8)
            try:
                self.cam.driver.start_streaming(self)
                self.kill.wait()
            finally:
                self.cam.driver.stop_streaming()
        except VmbCameraError as err:
            _logger.debug(f'[{self}] vmbpy error:\n{err}')

class VimbaXCameraWidget(QtWidgets.QWidget):
    """Qt widget for displaying the camera feed."""
    def __init__(
        self,
        camera_serial: str = None,
        rot: bool = False,
        mirror_h: bool = False,
        mirror_v: bool = False,
        exposure: float = 0.05,
        gain: float = 1.0,
    ):
        """
        Args:
            camera_serial: the serial number of the camera, or None to pick the
                first available.
            rot: Rotate the image by 90.
            mirror_h: Mirror the image horizontally.
            mirror_v: Mirror the image vertically.
            exposure: Default exposure time (s).
            gain: Default gain.
        """
        super().__init__()

        # create camera driver
        self.cam = VimbaX(camera_serial)
        self.cam.__enter__()

        # frame queue
        self.frame_queue = queue.Queue(maxsize=10)

        # top level layout
        layout = QtWidgets.QHBoxLayout()

        # worker object to queue the camera data
        self.producer_worker = VimbaXFrameProducer(self.cam, self.frame_queue)
        # thread to run frame producer routine
        self.thread = QtCore.QThread()
        self.producer_worker.moveToThread(self.thread)
        # stop the streamer when this object is destroyed
        self.destroyed.connect(partial(self._stop))
        self.destroyed.connect(partial(self._exit))
        # run update_image to update the QLabel whenever a new image is available from the camera
        self.producer_worker.new_frame.connect(self.update_image)
        # start the thread
        self.thread.start()

        # acuisition controls
        controls_layout = QtWidgets.QVBoxLayout()

        # button to turn the acquisition on
        self.start_button = QtWidgets.QPushButton('Start')
        self.start_button.clicked.connect(self.producer_worker.start_acquisition)
        controls_layout.addWidget(self.start_button)

        # button to turn the acquisition off
        self.stop_button = QtWidgets.QPushButton('Stop')
        def stop_producer(button):
            self.producer_worker.stop_acquisition()
        self.stop_button.clicked.connect(stop_producer)
        controls_layout.addWidget(self.stop_button)

        # button to rotate the image 90 deg
        self.rot = rot
        self.rot_button = QtWidgets.QPushButton('Rot')
        def rot_image(button):
            self.rot = not self.rot
        self.rot_button.clicked.connect(rot_image)
        controls_layout.addWidget(self.rot_button)

        # button to mirror the image about the horizontal axis
        self.mirror_h = mirror_h
        self.mirror_h_button = QtWidgets.QPushButton('Mirror H')
        def mirror_h_image(button):
            self.mirror_h = not self.mirror_h
        self.mirror_h_button.clicked.connect(mirror_h_image)
        controls_layout.addWidget(self.mirror_h_button)

        # button to mirror the image about the vertical axis
        self.mirror_v = mirror_v
        self.mirror_v_button = QtWidgets.QPushButton('Mirror V')
        def mirror_v_image(button):
            self.mirror_v = not self.mirror_v
        self.mirror_v_button.clicked.connect(mirror_v_image)
        controls_layout.addWidget(self.mirror_v_button)

        # exposure time spinbox
        controls_layout.addWidget(QtWidgets.QLabel('Exposure'))
        self.exposure_spinbox = SpinBox(suffix='s', siPrefix=True, bounds=(0, 1000), dec=True, minStep=1e-6)
        self.exposure_spinbox.setMinimumSize(QtCore.QSize(100, 0))
        def set_exposure(spinbox):
            self.cam.set_feature('ExposureTime', spinbox.value()*1e6)
        self.exposure_spinbox.sigValueChanged.connect(set_exposure)
        self.exposure_spinbox.setValue(exposure)
        controls_layout.addWidget(self.exposure_spinbox)

        # gain spinbox
        controls_layout.addWidget(QtWidgets.QLabel('Gain'))
        self.gain_spinbox = SpinBox(bounds=(0, 2e16), dec=True, minStep=1e-3)
        self.gain_spinbox.setMinimumSize(QtCore.QSize(50, 0))
        def set_gain(spinbox):
            self.cam.set_feature('Gain', spinbox.value())
        self.gain_spinbox.sigValueChanged.connect(set_gain)
        self.gain_spinbox.setValue(gain)
        controls_layout.addWidget(self.gain_spinbox)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        layout.setStretchFactor(controls_layout, 0)

        # create the label that holds the image
        self.image_label = QtWidgets.QLabel()
        # make an initial fake image to display
        img = np.zeros((1280, 720, 1))
        self.frame_queue.put(img)
        self.update_image()
        layout.addWidget(self.image_label)
        layout.setStretchFactor(self.image_label, 100)

        self.setLayout(layout)

    def _exit(self):
        self.cam.__exit__()

    def _stop(self):
        self.producer_worker.stop_acquisition()
        self.thread.quit()
        self.thread.wait()

    def update_image(self):
        """Updates the image_label with a new image."""

        try:
            img_np = self.frame_queue.get_nowait()
        except queue.Empty:
            return

        if self.rot:
            # rotate image
            img_np = np.rot90(img_np)

        if self.mirror_v:
            # mirror image horizontally
            img_np = np.fliplr(img_np)

        if self.mirror_h:
            # mirror image vertically
            img_np = np.flipud(img_np)

        # transpose x,y pixel axes
        img_np = np.transpose(img_np, (1, 0, 2))
        img_np = np.ascontiguousarray(img_np)

        width = img_np.shape[1]
        height = img_np.shape[0]
        # convert from a greyscale numpy array image to QPixmap
        qt_img = QtGui.QImage(img_np.data, width, height, QtGui.QImage.Format.Format_Grayscale8)
        # scale to the window size
        scaled_qt_img = qt_img.scaled(
            self.image_label.frameGeometry().width(),
            self.image_label.frameGeometry().height(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio
        )
        self.image_label.setPixmap(QtGui.QPixmap.fromImage(scaled_qt_img))
