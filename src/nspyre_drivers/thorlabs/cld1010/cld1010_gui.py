"""
Qt GUI for CLD1010 laser driver.

Copyright (c) 2022, Jacob Feder, Ben
All rights reserved.
"""
import logging

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

logger = logging.getLogger(__name__)

class CLD1010Widget(QtWidgets.QWidget):
    """Qt widget for controlling cld1010 lasers."""

    def __init__(self, laser_driver):
        """
        Args:
            laser_driver: The CLD1010 driver.
        """
        super().__init__()

        self.laser = laser_driver

        # top level layout
        layout = QtWidgets.QGridLayout()
        layout_row = 0

        # button to turn the laser off
        self.off_button = QtWidgets.QPushButton('Off')
        self.off_button.clicked.connect(self.laser_off)
        layout.addWidget(self.off_button, layout_row, 0)

        # button to turn the laser on
        self.on_button = QtWidgets.QPushButton('On')
        self.on_button.clicked.connect(self.laser_on)
        layout.addWidget(self.on_button, layout_row, 1)

        layout_row += 1

        # current setpoint label
        layout.addWidget(QtWidgets.QLabel('Current Setpoint'), layout_row, 0)

        # current setpoint spinbox
        self.current_setpoint_spinbox = SpinBox(value=1e-3, suffix='A', siPrefix=True, bounds=(0, 110), dec=True)    
        self.current_setpoint_spinbox.setMinimumWidth(100)
        layout.addWidget(self.current_setpoint_spinbox, layout_row, 2)

        # current setpoint get button
        current_setpoint_get_button = QtWidgets.QPushButton('Get')
        def get_current_setpoint(button):
            self.current_setpoint_spinbox.setValue(self.laser.get_current_setpoint())
        get_current_setpoint(None)
        current_setpoint_get_button.clicked.connect(get_current_setpoint)
        layout.addWidget(current_setpoint_get_button, layout_row, 1)

        # current setpoint set button
        current_setpoint_set_button = QtWidgets.QPushButton('Set')
        def set_current_setpoint(button):
            self.laser.set_current_setpoint(self.current_setpoint_spinbox.value())
        current_setpoint_set_button.clicked.connect(set_current_setpoint)
        layout.addWidget(current_setpoint_set_button, layout_row, 3)

        layout_row += 1

        # max current label
        layout.addWidget(QtWidgets.QLabel('Max Current'), layout_row, 0)
        # max current spinbox
        self.max_current_spinbox = SpinBox(value=1e-3, suffix='A', siPrefix=True, bounds=(0, 110), dec=True)    
        self.max_current_spinbox.setMinimumWidth(100)
        layout.addWidget(self.max_current_spinbox, layout_row, 2)

        # max current get button
        max_current_get_button = QtWidgets.QPushButton('Get')
        def get_max_current(button):
            self.max_current_spinbox.setValue(self.laser.get_max_current())
        get_max_current(None)
        max_current_get_button.clicked.connect(get_max_current)
        layout.addWidget(max_current_get_button, layout_row, 1)

        # max current set button
        max_current_set_button = QtWidgets.QPushButton('Set')
        def set_max_current(button):
            self.laser.set_max_current(self.max_current_spinbox.value())
        max_current_set_button.clicked.connect(set_max_current)
        layout.addWidget(max_current_set_button, layout_row, 3)

        layout_row += 1

        # modulation label
        layout.addWidget(QtWidgets.QLabel('Modulation'), layout_row, 0)

        # modulation combobox
        self.modulation_dropdown = QtWidgets.QComboBox()
        self.modulation_dropdown.addItem('CW') # index 0
        self.modulation_dropdown.addItem('Ext') # index 1
        def get_modulation(button):
            """Query the laser for the current modulation state then update the state combo box."""
            state = self.laser.get_modulation_state()
            if state == 'Off':
                self.modulation_dropdown.setCurrentIndex(0)
            elif state == 'On':
                self.modulation_dropdown.setCurrentIndex(1)
            else:
                raise ValueError(f'Modulation state should be "Off" or "On" but got [{state}].')
        get_modulation(None)
        layout.addWidget(self.modulation_dropdown, layout_row, 2)

        # modulation get button
        modulation_get_button = QtWidgets.QPushButton('Get')
        modulation_get_button.clicked.connect(get_modulation)
        layout.addWidget(modulation_get_button, layout_row, 1)

        # modulation set button
        modulation_set_button = QtWidgets.QPushButton('Set')
        def set_modulation(button):
            state = self.modulation_dropdown.currentIndex()
            if state == 0:
                self.laser.set_modulation_state('Off')
            elif state == 1:
                self.laser.set_modulation_state('On')
            else:
                raise ValueError(f'Modulation dropdown should be 0 or 1 but got [{state}]')
        modulation_set_button.clicked.connect(set_modulation)
        layout.addWidget(modulation_set_button, layout_row, 3)

        layout_row += 1
        # state label
        self.state_label = QtWidgets.QLabel('')
        self.update_state()
        layout.addWidget(self.state_label, layout_row, 1)
        # get state button
        self.get_state_button = QtWidgets.QPushButton('Get State')
        self.get_state_button.clicked.connect(self.update_state)
        layout.addWidget(self.get_state_button, layout_row, 0)

        layout_row += 1

        # take up any additional space in the final column with padding
        layout.setColumnStretch(2, 1)
        # take up any additional space in the final row with padding
        layout.setRowStretch(layout_row, 1)

        self.setLayout(layout)

    def laser_off(self):
        self.laser.off()
        self.update_state()

    def laser_on(self): 
        self.laser.on()
        self.update_state()

    def update_state(self):
        """Query the laser for the current state then update the state text box."""
        state = None
        if self.laser.get_ld_state():
            state="On"
        else:
            state="Off"
        self.state_label.setText(state)
