from ctypes import (
    c_short, c_char_p, c_uint32, c_int16, c_byte, c_bool, c_float, c_ushort,
    Structure, POINTER, cdll, c_int, c_uint, WinDLL, c_char, c_ulong,
)
import time
from enum import IntEnum
import os

class PZ_ControlModeTypes(IntEnum):
    """Control mode types for the piezo controller"""
    PZ_Undefined = 0
    PZ_OpenLoop = 1
    PZ_CloseLoop = 2
    PZ_OpenLoopSmooth = 3
    PZ_CloseLoopSmooth = 4

class PPC_IOSettings(Structure):
    """Settings structure for IO configuration"""
    _fields_ = [
        ("controlSrc", c_short),
        ("monitorOPSig", c_short),
        ("monitorOPBandwidth", c_short),
        ("feedbackSrc", c_short),
        ("FPBrightness", c_short),
        ("feedbackPolarity", c_uint)
    ]

class PFM450E:
    """Driver for Thorlabs PFM450E Piezo Controller"""
    
    # Device specifications for different modes
    CLOSED_LOOP_RANGE = 450.0  # Maximum travel in closed loop (microns)
    OPEN_LOOP_RANGE = 600.0    # Updated maximum travel in open loop (microns)
    CLOSED_LOOP_RESOLUTION = 0.003  # Resolution in closed loop (microns)
    OPEN_LOOP_RESOLUTION = 0.001    # Resolution in open loop (microns)
    
    # Native device units
    POSITION_SCALE = 32767  # Internal position scaling (-32767 to +32767)

    # Define possible DLL paths
    DLL_PATHS = [
        r"C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.Benchtop.PrecisionPiezo.dll",
        "Thorlabs.MotionControl.Benchtop.PrecisionPiezo.dll"
    ]
    
    # Device specifications
    STEP_SIZE = 0.1  # Each step is 100nm = 0.1 microns

    def __init__(self, serial_number):
        """Initialize the piezo controller
        
        Args:
            serial_number (str): Serial number of the device
        """
        if os.name != 'nt':
            raise OSError("This driver only supports Windows")

        # Try to load the DLL from known locations
        for dll_path in self.DLL_PATHS:
            try:
                self.lib = WinDLL(dll_path)
                break
            except OSError:
                continue
        else:
            raise OSError(
                "Could not find Thorlabs.MotionControl.Benchtop.PrecisionPiezo.dll. "
                "Please ensure Kinesis is installed."
            )

        self.serial_number = c_char_p(str(serial_number).encode())
        
        # Initialize required functions
        self._initialize_functions()
        
        # Connect to device
        if not self.connect():
            raise ConnectionError("Could not connect to piezo controller")

    def _initialize_functions(self):
        """Initialize the function signatures from the DLL"""
        # Device list functions
        self.lib.TLI_BuildDeviceList.argtypes = []
        self.lib.TLI_BuildDeviceList.restype = c_short
        
        self.lib.TLI_GetDeviceListSize.argtypes = []
        self.lib.TLI_GetDeviceListSize.restype = c_short
        
        self.lib.TLI_GetDeviceListByTypeExt.argtypes = [POINTER(c_char), c_ulong, c_int]
        self.lib.TLI_GetDeviceListByTypeExt.restype = c_short
        
        # Device identification functions
        self.lib.TLI_GetDeviceInfo.argtypes = [c_char_p, POINTER(c_char), c_ulong]
        self.lib.TLI_GetDeviceInfo.restype = c_short
        
        # Device connection functions
        self.lib.PPC_Open.argtypes = [c_char_p]
        self.lib.PPC_Open.restype = c_short
        
        self.lib.PPC_StartPolling.argtypes = [c_char_p, c_int]
        self.lib.PPC_StartPolling.restype = c_bool
        
        self.lib.PPC_Close.argtypes = [c_char_p]
        self.lib.PPC_Close.restype = None
        
        self.lib.PPC_CheckConnection.argtypes = [c_char_p]
        self.lib.PPC_CheckConnection.restype = c_bool
        
        # Device control functions
        self.lib.PPC_EnableChannel.argtypes = [c_char_p]
        self.lib.PPC_EnableChannel.restype = c_short
        
        self.lib.PPC_DisableChannel.argtypes = [c_char_p]
        self.lib.PPC_DisableChannel.restype = c_short
        
        self.lib.PPC_GetPosition.argtypes = [c_char_p]
        self.lib.PPC_GetPosition.restype = c_short
        
        self.lib.PPC_SetPosition.argtypes = [c_char_p, c_short]
        self.lib.PPC_SetPosition.restype = c_short
        
        self.lib.PPC_GetPositionControlMode.argtypes = [c_char_p]
        self.lib.PPC_GetPositionControlMode.restype = c_short
        
        self.lib.PPC_SetPositionControlMode.argtypes = [c_char_p, c_short]
        self.lib.PPC_SetPositionControlMode.restype = c_short

        # Travel and position functions
        self.lib.PPC_GetMaximumTravel.argtypes = [c_char_p]
        self.lib.PPC_GetMaximumTravel.restype = c_ushort  # WORD in Windows is unsigned short

    def connect(self):
        """Connect to the piezo controller
        
        Returns:
            bool: True if connection successful
        """
        # Build device list first
        try:
            build_result = self.lib.TLI_BuildDeviceList()
            if build_result != 0:
                print(f"Error building device list: {build_result}")
                return False
            
            # Wait for enumeration
            time.sleep(1)
            
            # Get number of devices
            size = self.lib.TLI_GetDeviceListSize()
            # print(f"Found {size} devices")
            
            if size > 0:
                # Get device list
                buffer = (c_char * 100)()
                self.lib.TLI_GetDeviceListByTypeExt(buffer, 100, 43)  # 43 is PFM450E type
                devices = buffer.value.decode().split(',')
                # print(f"Available devices: {devices}")
            
            # Try to open the device
            result = self.lib.PPC_Open(self.serial_number)
            # print(f"Open result: {result}")
            
            if result == 0:
                time.sleep(3)  # Wait for initialization
                return True
                
            # Error codes reference:
            # 0 = Success
            # 1 = Device not found
            # 2 = Device already opened
            # 3 = USB error
            # 4 = Driver error
            error_msgs = {
                1: "Device not found",
                2: "Device already opened",
                3: "USB error",
                4: "Driver error"
            }
            print(f"Connection error: {error_msgs.get(result, 'Unknown error')}")
            return False
            
        except Exception as e:
            print(f"Connection exception: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from the controller"""
        self.lib.PPC_Close(self.serial_number)

    def enable(self):
        """Enable the piezo channel"""
        return self.lib.PPC_EnableChannel(self.serial_number) == 0

    def disable(self):
        """Disable the piezo channel"""
        return self.lib.PPC_DisableChannel(self.serial_number) == 0

    def get_position(self):
        """Get the current position in internal units (-32767 to +32767)"""
        return self.lib.PPC_GetPosition(self.serial_number)

    def set_position(self, position):
        """Set position in internal units (-32767 to +32767)"""
        position = int(max(-self.POSITION_SCALE, min(self.POSITION_SCALE, position)))
        return self.lib.PPC_SetPosition(self.serial_number, position) == 0

    def get_control_mode(self):
        """Get the current control mode
        
        Returns:
            PZ_ControlModeTypes: Current control mode
        """
        mode = self.lib.PPC_GetPositionControlMode(self.serial_number)
        return PZ_ControlModeTypes(mode)

    def set_control_mode(self, mode):
        """Set the control mode
        
        Args:
            mode (PZ_ControlModeTypes): Desired control mode
            
        Returns:
            bool: True if successful
        """
        return self.lib.PPC_SetPositionControlMode(self.serial_number, mode.value) == 0

    def get_max_travel(self):
        """Get maximum travel range in microns based on current mode"""
        if self.get_control_mode() in [PZ_ControlModeTypes.PZ_OpenLoop, PZ_ControlModeTypes.PZ_OpenLoopSmooth]:
            return self.OPEN_LOOP_RANGE
        return self.CLOSED_LOOP_RANGE

    def get_resolution(self):
        """Get position resolution in microns based on current mode"""
        if self.get_control_mode() in [PZ_ControlModeTypes.PZ_OpenLoop, PZ_ControlModeTypes.PZ_OpenLoopSmooth]:
            return self.OPEN_LOOP_RESOLUTION
        return self.CLOSED_LOOP_RESOLUTION

    def get_position_microns(self):
        """Get position in microns"""
        raw_pos = self.get_position()
        max_range = self.CLOSED_LOOP_RANGE if self.get_control_mode() == PZ_ControlModeTypes.PZ_CloseLoop else self.OPEN_LOOP_RANGE
        return (raw_pos / self.POSITION_SCALE) * (max_range / 2)

    def set_position_microns(self, microns):
        """Set position in microns"""
        max_range = self.CLOSED_LOOP_RANGE if self.get_control_mode() == PZ_ControlModeTypes.PZ_CloseLoop else self.OPEN_LOOP_RANGE
        raw_pos = int((microns / (max_range / 2)) * self.POSITION_SCALE)
        return self.set_position(raw_pos)

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures device is properly closed"""
        self.disconnect()
