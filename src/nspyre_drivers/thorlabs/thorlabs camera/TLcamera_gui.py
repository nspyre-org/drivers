import os
import sys
import ctypes
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QDoubleSpinBox
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK

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




class TLCameraGUI(QWidget):
    def __init__(self, camera):
        super().__init__()
        self.camera = camera  
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.frame_count = 0
        self.init_ui()
        
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
        self.exposure_spinbox = QDoubleSpinBox()  
        self.exposure_spinbox.setRange(0.1, 1000)  
        self.exposure_spinbox.setSingleStep(1)   
        self.exposure_spinbox.setValue(100)
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

        layout.addLayout(controls_layout)
        self.setLayout(layout)

    def toggle_acquisition(self):
        if self.timer.isActive():
            self.timer.stop()
            self.camera.stop_acquisition()
            self.start_button.setText('Start')
        else:
            try:
                self.camera.start_acquisition()
                self.timer.start(50)  # Update every 50ms
                self.start_button.setText('Stop')
            except Exception as e:
                print(f"Camera acquisition error: {str(e)}")
                self.start_button.setText('Start')

    def update_frame(self):
        try:
            frame_data = self.camera.get_frame()
            if frame_data is not None:
                # Check if we received dictionary format
                if isinstance(frame_data, dict):
                    # Reconstruct numpy array from serialized data
                    frame = np.frombuffer(frame_data['data'], 
                                        dtype=np.dtype(frame_data['dtype'])
                                       ).reshape(frame_data['shape'])
                else:
                    # Handle direct numpy array if not serialized
                    frame = np.array(frame_data, copy=True)
                
                # Ensure we have valid data before displaying
                if frame is not None and frame.size > 0:
                    self.frame_count += 1
                    # Convert to float32 to ensure compatibility
                    frame = frame.astype(np.float32)
                    self.image_view.setImage(frame.T, autoLevels=True)
        except Exception as e:
            print(f"Error updating frame: {str(e)}")

    def set_exposure(self, value_ms):
        try:
            self.camera.set_exposure(float(value_ms))
        except Exception as e:
            print(f"Error setting exposure: {str(e)}")
            # Restore previous value in ms
            current_us = self.camera.exposure_time_us
            self.exposure_spinbox.setValue(current_us / 1000.0)

    def set_gain(self, value):
        self.camera.set_gain(value)

    def closeEvent(self, event):
        if self.timer.isActive():
            self.timer.stop()
            self.camera.stop_acquisition()
        super().closeEvent(event)
