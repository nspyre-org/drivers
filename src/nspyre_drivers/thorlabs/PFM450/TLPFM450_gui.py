from PyQt5.QtWidgets import (QWidget, QGridLayout, QLabel, QPushButton, QComboBox, QHBoxLayout)
from PyQt5.QtCore import QTimer, QSize
from pyqtgraph import SpinBox
from .PFM450_driver import PZ_ControlModeTypes

class PiezoWidget(QWidget):
    """GUI for controlling the PFM450E Piezo Controller"""
    
    def __init__(self, device):
        """
        Initialize the PiezoWidget.

        Args:
            device: The PFM450E device instance to control.
        """
        super().__init__()
        
        # Use the provided instrument manager to manage the instrument
        

        self.instr = device
        
        # Saved position state
        self.saved_pos = None
        
        try:
            self.instr.enable()
            self.instr.set_control_mode(PZ_ControlModeTypes.PZ_OpenLoop)
        except Exception as e:
            raise print(e)
            
        # Get device range
        self.max_range = self.instr.get_max_travel()
        
        # Initialize controls
        self.initUI()
        
        # Update range and resolution based on initial mode
        self.update_range_and_resolution()
        
        # Position update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_position)
        self.update_timer.start(100)

    def initUI(self):
        """Initialize the user interface"""
        layout = QGridLayout()
        layout_row = 0

        # Mode Selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel('Current Mode:'))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['Open Loop', 'Closed Loop'])
        self.mode_combo.currentIndexChanged.connect(self.change_control_mode)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout, layout_row, 0, 1, 4)
        layout_row += 1

        # Combined Mode Information Display
        self.mode_info = QLabel(
            "Open Loop Mode:\n"
            "• Range: ±300 μm\n"  # Updated range for open loop
            "• Resolution: 1 nm\n"
            "\n"
            "Closed Loop Mode:\n"
            "• Range: ±225 μm\n"
            "• Resolution: 3 nm\n"
        )
        layout.addWidget(self.mode_info, layout_row, 0, 1, 4)
        layout_row += 1

        # Home and save/restore buttons
        home_button = QPushButton('Home Piezo')
        home_button.clicked.connect(self.home_piezo)
        layout.addWidget(home_button, layout_row, 0, 1, 2)
        
        save_pos_button = QPushButton('Save Position')
        save_pos_button.clicked.connect(self.save_position)
        layout.addWidget(save_pos_button, layout_row, 2, 1, 1)
        
        goto_saved_button = QPushButton('Go to Saved')
        goto_saved_button.clicked.connect(self.goto_saved_position)
        layout.addWidget(goto_saved_button, layout_row, 3, 1, 1)
        
        layout_row += 1

        # Z position control
        layout.addWidget(QLabel('Z Position'), layout_row, 0)
        self.pos_spinbox = SpinBox(
            suffix='μm',
            value=self.instr.get_position_microns(),
            bounds=(-self.max_range/2, self.max_range/2),
            siPrefix=False,
            decimals=3
        )
        self.pos_spinbox.setSingleStep(1)
        layout.addWidget(self.pos_spinbox, layout_row, 2)
        
        set_button = QPushButton('Set')
        set_button.clicked.connect(self.set_position)
        layout.addWidget(set_button, layout_row, 3)
        
        layout_row += 1

        # Step size control
        layout.addWidget(QLabel('Step Size'), layout_row, 0)
        self.step_spinbox = SpinBox(
            suffix='μm',
            value=0.1,  # Default step size of 0.1 μm
            bounds=(0.001, self.max_range/2),  # Min 1nm, max half the range
            siPrefix=False,
            decimals=3
        )
        self.step_spinbox.setMinimumSize(QSize(120, 0))
        layout.addWidget(self.step_spinbox, layout_row, 2)
        
        layout_row += 1

        # Add step buttons in their own row
        step_layout = QGridLayout()
        
        button_style = """
            QPushButton {
                font-size: 60px;
                font-weight: 900;
                min-width: 80px;
                max-width: 80px;
                min-height: 80px;
                max-height: 80px;
            }
        """
        
        up_button = QPushButton('⏶')
        up_button.setStyleSheet(button_style)
        up_button.clicked.connect(lambda: self.move_relative(self.step_spinbox.value()))
        step_layout.addWidget(up_button, 0, 1)
        
        down_button = QPushButton('⏷')
        down_button.setStyleSheet(button_style)
        down_button.clicked.connect(lambda: self.move_relative(-self.step_spinbox.value()))
        step_layout.addWidget(down_button, 1, 1)

        layout.addLayout(step_layout, layout_row, 0, 2, 4)
        layout_row += 2

        self.setLayout(layout)

    def percent_to_microns(self, percent):
        """Convert percentage to microns"""
        return (percent / 100.0) * self.max_range

    def microns_to_percent(self, microns):
        """Convert microns to percentage"""
        return (microns / self.max_range) * 100.0

    def get_position(self, print_mode=False, update_spinbox=False):
        """Get current position in microns"""
        pos = self.instr.get_position_microns()
        if print_mode:
            print(f"Current Z position: {pos:.3f} μm")
        if update_spinbox:
            self.pos_spinbox.setValue(pos)
        return pos

    def set_position(self):
        """Set position from spinbox value"""
        target = self.pos_spinbox.value()
        print(f"Moving Z to position: {target:.3f} μm")
        self.instr.set_position_microns(target)

    def move_relative(self, delta_microns):
        """Move relative to current position"""
        current = self.pos_spinbox.value()
        new_pos = current + delta_microns
        self.pos_spinbox.setValue(new_pos)
        self.set_position()

    def save_position(self):
        """Save current position"""
        self.saved_pos = self.get_position()
        print(f"Position saved: {self.saved_pos:.3f} μm")

    def goto_saved_position(self):
        """Move to saved position if one exists"""
        if self.saved_pos is not None:
            print(f"Moving to saved position: {self.saved_pos:.3f} μm")
            self.pos_spinbox.setValue(self.saved_pos)
            self.set_position()
        else:
            print("No saved position available")

    def home_piezo(self):
        """Home piezo by returning to 0"""
        print("Homing piezo...")
        self.pos_spinbox.setValue(0)
        self.set_position()
        print("Piezo homed to 0 μm")

    def update_position(self):
        """Update position display"""
        try:
            self.get_position()
        except Exception as e:
            print(f"Error updating position: {e}")

    def update_range_and_resolution(self):
        """Update displayed ranges and step sizes based on control mode"""
        max_range = self.instr.get_max_travel()
        resolution = self.instr.get_resolution()
        
        # Update spinbox ranges
        self.pos_spinbox.setRange(-max_range/2, max_range/2)
        
        self.step_spinbox.setRange(resolution, max_range/2)
        self.step_spinbox.setValue(min(self.step_spinbox.value(), max_range/2))
        self.step_spinbox.setSingleStep(resolution)

    def change_control_mode(self, index):
        """Change the control mode"""
        if index == 0:  # Open Loop
            mode = PZ_ControlModeTypes.PZ_OpenLoop
            self.instr.set_control_mode(mode)
            print("Switched to Open Loop mode")
        else:  # Closed Loop
            mode = PZ_ControlModeTypes.PZ_CloseLoop
            self.instr.set_control_mode(mode)
            print("Switched to Closed Loop mode")
        
        # Update range and info display
        self.update_range_and_resolution()
    
    def cleanup(self):
        """Clean up resources and release the instrument"""
        if hasattr(self, 'update_timer') and self.update_timer is not None:
            self.update_timer.stop()
            self.update_timer.deleteLater()
            self.update_timer = None

    def closeEvent(self, event):
        """Handle widget close event"""
        self.cleanup()
        event.accept()  # Accept the close event
        
    def deleteLater(self):
        """Handle widget deletion"""
        self.cleanup()
        super().deleteLater()
        
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
