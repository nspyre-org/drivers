import os
import sys
import ctypes
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QDoubleSpinBox
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import numpy as np

# Add Thorlabs DLL paths to system PATH
THORLABS_DLL_PATH = r"C:\Program Files\Thorlabs\Scientific Imaging\Scientific Camera Support\Scientific Camera Interfaces\SDK\Python Toolkit\dlls\64_lib"
THORLABS_SDK_DLL = os.path.join(THORLABS_DLL_PATH, "thorlabs_tsi_camera_sdk.dll")

# Load the DLL directly
try:
    ctypes.CDLL(THORLABS_SDK_DLL)
except Exception as e:
    print(f"Error loading DLL: {e}")
    raise

# Add to PATH as well
if THORLABS_DLL_PATH not in os.environ['PATH']:
    os.environ['PATH'] = THORLABS_DLL_PATH + os.pathsep + os.environ['PATH']

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
from thorlabs_tsi_sdk.tl_camera_enums import SENSOR_TYPE

class TLCameraGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.sdk = None
        self.camera = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.frame_count = 0
        self.init_ui()
        
        # Initialize SDK and camera using with statements
        with TLCameraSDK() as sdk:
            self.sdk = sdk
            available_cameras = sdk.discover_available_cameras()
            if len(available_cameras) < 1:
                print("No cameras detected")
                return
                
            with sdk.open_camera(available_cameras[0]) as camera:
                self.camera = camera
                self.configure_camera()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Image display
        self.image_view = pg.ImageView()
        layout.addWidget(self.image_view)

        # Controls
        controls_layout = QHBoxLayout()
        
        # Start/Stop button
        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.toggle_acquisition)
        controls_layout.addWidget(self.start_button)

        # Exposure control
        exposure_layout = QHBoxLayout()
        exposure_layout.addWidget(QLabel('Exposure (ms):'))
        self.exposure_spinbox = QSpinBox()
        self.exposure_spinbox.setRange(1, 1000)
        self.exposure_spinbox.setValue(10)
        self.exposure_spinbox.valueChanged.connect(self.set_exposure)
        exposure_layout.addWidget(self.exposure_spinbox)
        controls_layout.addLayout(exposure_layout)

        # Gain control
        gain_layout = QHBoxLayout()
        gain_layout.addWidget(QLabel('Gain:'))
        self.gain_spinbox = QSpinBox()
        self.gain_spinbox.setRange(0, 100)
        self.gain_spinbox.setValue(0)
        self.gain_spinbox.valueChanged.connect(self.set_gain)
        gain_layout.addWidget(self.gain_spinbox)
        controls_layout.addLayout(gain_layout)

        # Frame rate control
        framerate_layout = QHBoxLayout()
        framerate_layout.addWidget(QLabel('Frame Rate (fps):'))
        self.framerate_spinbox = QDoubleSpinBox()
        self.framerate_spinbox.setRange(1, 100)
        self.framerate_spinbox.setValue(10)
        self.framerate_spinbox.valueChanged.connect(self.set_frame_rate)
        framerate_layout.addWidget(self.framerate_spinbox)
        controls_layout.addLayout(framerate_layout)

        layout.addLayout(controls_layout)
        self.setLayout(layout)

    def configure_camera(self):
        """Configure initial camera settings"""
        self.camera.exposure_time_us = 10000  # set exposure to 10 ms
        self.camera.frames_per_trigger_zero_for_unlimited = 0  # continuous mode
        self.camera.image_poll_timeout_ms = 1000  # 1 second polling timeout
        self.camera.frame_rate_control_value = 10
        self.camera.is_frame_rate_control_enabled = True

    def toggle_acquisition(self):
        if self.timer.isActive():
            self.timer.stop()
            if self.camera:
                self.camera.disarm()
            self.start_button.setText('Start')
        else:
            try:
                if self.camera:
                    self.camera.arm(2)
                    self.camera.issue_software_trigger()
                    self.timer.start(50)  # Update every 50ms
                    self.start_button.setText('Stop')
            except Exception as e:
                print(f"Camera acquisition error: {str(e)}")
                self.start_button.setText('Start')

    def update_frame(self):
        if self.camera:
            frame = self.camera.get_pending_frame_or_null()
            if frame is not None:
                self.frame_count += 1
                
                # Process image
                image_buffer_copy = np.copy(frame.image_buffer)
                numpy_shaped_image = image_buffer_copy.reshape(
                    self.camera.image_height_pixels,
                    self.camera.image_width_pixels
                )
                self.image_view.setImage(numpy_shaped_image.T)

    def closeEvent(self, event):
        """Handle window close event"""
        if self.timer.isActive():
            self.timer.stop()
        if hasattr(self, 'camera') and self.camera:
            try:
                if self.camera.is_armed:
                    self.camera.disarm()
            except:
                pass
        super().closeEvent(event)

    def set_exposure(self, value_ms):
        if self.camera:
            self.camera.exposure_time_us = value_ms * 1000

    def set_gain(self, value):
        if self.camera and self.camera.gain_range.max > 0:
            gain = min(value, self.camera.gain_range.max)
            self.camera.gain = gain

    def set_frame_rate(self, value):
        if self.camera:
            self.camera.frame_rate_control_value = value
            self.camera.is_frame_rate_control_enabled = True
