"""
Qt GUI for Cobolt lasers utilizing the python driver:
https://github.com/cobolt-lasers/pycobolt

Copyright (c) 2022, Jacob Feder
All rights reserved.
"""
import logging

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

logger = logging.getLogger(__name__)

class CoboltWidget(QtWidgets.QWidget):
    """Qt widget for controlling Cobolt lasers."""
    def __init__(self, laser_driver):
        """
        Args:
            laser_driver: The pycobolt.CoboltLaser driver.
        """
        super().__init__()

        self.laser = laser_driver

        # top level layout
        layout = QtWidgets.QGridLayout()
        layout_row = 0

        # button to turn the laser off
        self.off_button = QtWidgets.QPushButton('Off')
        self.off_button.clicked.connect(lambda: self.laser.turn_off())
        self.off_button.clicked.connect(self.update_state)
        layout.addWidget(self.off_button, layout_row, 0)

        # button to turn the laser on
        self.on_button = QtWidgets.QPushButton('On')
        self.on_button.clicked.connect(lambda: self.laser.turn_on())
        self.on_button.clicked.connect(self.update_state)
        layout.addWidget(self.on_button, layout_row, 1)
        layout_row += 1

        # power spinbox
        layout.addWidget(QtWidgets.QLabel('Power'), layout_row, 0)
        self.power_spinbox = SpinBox(value=1e-3, suffix='W', siPrefix=True, bounds=(0, 100e-3), dec=True, minStep=0.1e-6)
        def set_power(spinbox):
            self.laser.set_power(spinbox.value()*1000)
            self.laser.set_modulation_power(spinbox.value()*1000)
        self.power_spinbox.setValue(value=0)
        self.power_spinbox.sigValueChanged.connect(set_power)
        layout.addWidget(self.power_spinbox, layout_row, 1)
        layout_row += 1

        # dropdown menu to pick laser mode
        layout.addWidget(QtWidgets.QLabel('Mode'), layout_row, 0)
        self.mode_dropdown = QtWidgets.QComboBox()
        self.mode_dropdown.addItem('Digital Modulation') # index 0
        self.mode_dropdown.addItem('Constant Power') # index 1
        # default to modulation mode
        self.mode_dropdown.setCurrentIndex(0)
        self.mode_dropdown.currentIndexChanged.connect(self.change_mode)
        layout.addWidget(self.mode_dropdown, layout_row, 1)
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

    def update_state(self):
        """Query the laser for the current state then update the state text box."""
        self.state_label.setText(self.laser.get_state()[4:])

    def change_mode(self, idx):
        """Change the laser output mode."""
        # constant power
        # digital modulation
        if idx == 0:
            self.laser.modulation_mode()
        elif idx == 1:
            self.laser.constant_power()
        else:
            raise ValueError('Invalid mode selection')
        self.update_state()
