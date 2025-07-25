import os
import numpy as np

# Load Thorlabs DLLs BEFORE importing the SDK
def _load_thorlabs_dlls():
    dll_paths = [
        r"C:\Program Files\Thorlabs\Scientific Imaging\Scientific Camera Support\Scientific Camera Interfaces\SDK\Python Toolkit\dlls\64_lib",
        r"C:\Program Files\Thorlabs\Scientific Imaging\ThorCam",
    ]
    for path in dll_paths:
        if os.path.isdir(path):
            os.add_dll_directory(path)
        else:
            raise RuntimeError(f"Required Thorlabs DLL path not found: {path}")

# Call DLL loader before SDK import
_load_thorlabs_dlls()

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK

class TLCameraDriver:
    def __init__(self):
        self.sdk = None
        self.camera = None
        self._initialize_camera()

    def _initialize_camera(self):
        """Initialize the camera SDK and connect to the first available camera."""
        try:
            self.sdk = TLCameraSDK()

            available_cameras = self.sdk.discover_available_cameras()
            if not available_cameras:
                raise RuntimeError("No Thorlabs cameras detected.")

            self.camera = self.sdk.open_camera(available_cameras[0])
            self._configure_camera()

        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Failed to initialize camera: {str(e)}")

    def _configure_camera(self):
        """Set default camera configuration."""
        self.camera.exposure_time_us = 10000
        self.camera.frames_per_trigger_zero_for_unlimited = 0
        self.camera.image_poll_timeout_ms = 1000
        self.camera.frame_rate_control_value = 10
        self.camera.is_frame_rate_control_enabled = True

    def start_acquisition(self):
        """Arm and trigger the camera to start acquisition."""
        if self.camera:
            self.camera.arm(2)
            self.camera.issue_software_trigger()

    def stop_acquisition(self):
        """Stop acquisition and disarm the camera."""
        if self.camera and self.camera.is_armed:
            self.camera.disarm()

    def get_frame(self):
        """Get a single frame from the camera."""
        if self.camera:
            frame = self.camera.get_pending_frame_or_null()
            if frame is not None:
                # Create numpy array and convert to bytes for RPyC transfer
                image_buffer = np.array(frame.image_buffer, copy=True, dtype=np.uint16)
                image = image_buffer.reshape(
                    self.camera.image_height_pixels,
                    self.camera.image_width_pixels
                )
                # Return the shape and buffer for reconstruction
                return {
                    'shape': image.shape,
                    'dtype': str(image.dtype),
                    'data': image.tobytes()
                }
        return None

    def set_exposure(self, value_ms):
        """Set exposure time in milliseconds."""
        if self.camera:
            self.camera.exposure_time_us = int(value_ms * 1000)

    def set_gain(self, value):
        """Set gain value if supported."""
        if self.camera and self.camera.gain_range.max > 0:
            gain = min(value, self.camera.gain_range.max)
            self.camera.gain = gain

    def set_frame_rate(self, value):
        """Set the camera frame rate."""
        if self.camera:
            self.camera.frame_rate_control_value = value
            self.camera.is_frame_rate_control_enabled = True

    def cleanup(self):
        """Clean up camera and SDK resources."""
        if self.camera:
            try:
                if self.camera.is_armed:
                    self.camera.disarm()
                self.camera.dispose()
            except Exception:
                pass
            self.camera = None

        if self.sdk:
            try:
                self.sdk.dispose()
            except Exception:
                pass
            self.sdk = None

    def __del__(self):
        self.cleanup()
