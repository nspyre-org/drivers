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
        self.off_button.clicked.connect(lambda: self.laser.off())
        self.off_button.clicked.connect(self.update_state)
        layout.addWidget(self.off_button, layout_row, 0)

        # button to turn the laser on
        self.on_button = QtWidgets.QPushButton('On')
        self.on_button.clicked.connect(lambda: self.laser.on())
        self.on_button.clicked.connect(self.update_state)
        layout.addWidget(self.on_button, layout_row, 1)
        layout_row += 1

        # power spinbox
        layout.addWidget(QtWidgets.QLabel('Current'), layout_row, 0)
        self.current_spinbox = SpinBox(value=100, suffix='mA', siPrefix=True, bounds=(0, 110), dec=True, minStep=1)
        self.current_spinbox.sigValueChanged.connect(lambda spinbox: self.laser.set_current_setpoint(spinbox.value()/1000))
        self.current_spinbox.setValue(value=0)
        layout.addWidget(self.current_spinbox, layout_row, 1)
        layout_row += 1

        # # dropdown menu to pick laser mode
        # layout.addWidget(QtWidgets.QLabel('Mode'), layout_row, 0)
        # self.mode_dropdown = QComboBox()
        # self.mode_dropdown.addItem('Digital Modulation') # index 0
        # self.mode_dropdown.addItem('Constant Power') # index 1
        # # default to modulation mode
        # self.mode_dropdown.setCurrentIndex(0)
        # self.mode_dropdown.currentIndexChanged.connect(self.change_mode)
        # layout.addWidget(self.mode_dropdown, layout_row, 1)
        # layout_row += 1

        # state label
        self.state_label = QtWidgets.QLabel('')
        self.update_state()
        layout.addWidget(self.state_label, layout_row, 1)
        # get state button
        self.get_state_button = QtWidgets.QPushButton('Get State')
        self.get_state_button.clicked.connect(self.update_state)
        layout.addWidget(self.get_state_button, layout_row, 0)
        layout_row += 1

        # modulation dropdown
        layout.addWidget(QtWidgets.QLabel('Modulation'), layout_row, 0)
        self.modulation_dropdown = QtWidgets.QComboBox()
        self.modulation_dropdown.addItem('Off') # index 0
        self.modulation_dropdown.addItem('On') # index 1
        # default to Modulation Off
        if self.laser.get_modulation_state() == 'Off':
            self.modulation_dropdown.setCurrentIndex(0)
        if self.laser.get_modulation_state() == 'On':
            self.modulation_dropdown.setCurrentIndex(1)
        self.modulation_dropdown.currentIndexChanged.connect(self.set_mod)
        layout.addWidget(self.modulation_dropdown, layout_row, 1)
        layout_row += 1

        # modulation label
        self.mod_label = QtWidgets.QLabel('')
        self.update_mod()
        layout.addWidget(self.mod_label, layout_row, 1)
        # get state button
        self.get_mod_button = QtWidgets.QPushButton('Get Modulation State')
        self.get_mod_button.clicked.connect(self.update_mod)
        layout.addWidget(self.get_mod_button, layout_row, 0)
        layout_row += 1

        # take up any additional space in the final column with padding
        layout.setColumnStretch(2, 1)
        # take up any additional space in the final row with padding
        layout.setRowStretch(layout_row, 1)

        self.setLayout(layout)

    def update_state(self):
        """Query the laser for the current state then update the state text box."""
        self.state_label.setText(str(self.laser.get_ld_state()))

    def update_mod(self):
        """Query the laser for the current state then update the state text box."""
        self.mod_label.setText(str(self.laser.get_modulation_state()))

    def set_mod(self, idx):
        """Change the agiltron port."""
        if idx == 0:
            self.laser.set_modulation_state('Off')
        elif idx == 1:
            self.laser.set_modulation_state('On')
        else:
            raise ValueError(f'Invalid mode selection [{idx}]')
        self.update_mod()


    # TODO modulation mode
    # def change_mode(self, idx):
    #     """Change the laser output mode."""
    #     # constant power
    #     # digital modulation
    #     if idx == 0:
    #         self.laser.modulation_mode()
    #     elif idx == 1:
    #         self.laser.constant_power()
    #     else:
    #         raise ValueError('Invalid mode selection')
    #     self.update_state()
