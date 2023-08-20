"""
Qt GUI for Thorlabs PM100D power meter.

Copyright (c) 2022, Jacob Feder, Ben Soloway
All rights reserved.
"""
import logging

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

logger = logging.getLogger(__name__)

class Ell14Widget(QtWidgets.QWidget):
    """Qt widget for controlling the PM100D power meter."""

    def __init__(self, ell14_driver):
        """
        Args:
            pm100d_driver: PM100D driver.
        """
        super().__init__()

        self.ell14 = ell14_driver

        # top level layout
        layout = QtWidgets.QGridLayout()
        layout_row = 0

        # position spinbox
        layout.addWidget(QtWidgets.QLabel('Absolute Position (degrees)'), layout_row, 0)
        self.abs_pos_spinbox = SpinBox(value=488, siPrefix=True, bounds=(400, 1100), dec=True, minStep=5)
        self.abs_pos_spinbox.sigValueChanged.connect(lambda spinbox: self.ell14.write('move_absolute', spinbox.value()))
        self.abs_pos_spinbox.sigValueChanged.connect(self.update_position)
        self.corr_wave_spinbox.setValue(value=0)
        layout.addWidget(self.abs_pos_spinbox, layout_row, 1)
        layout_row += 1

        # get state button
        self.home_button = QtWidgets.QPushButton('Home')
        self.home_button.clicked.connect(lambda home: self.ell14.write('move_to_home_cw'))
        layout.addWidget(self.home_button, layout_row, 0)
        layout_row += 1

        # position label
        self.position_label = QtWidgets.QLabel('')
        self.update_power()
        layout.addWidget(self.position_label, layout_row, 1)
        # get power button
        self.get_position_button = QtWidgets.QPushButton('Get position (degrees)')
        self.get_position_button.clicked.connect(self.update_position)
        layout.addWidget(self.get_positon_button, layout_row, 0)
        layout_row += 1

        # take up any additional space in the final column with padding
        layout.setColumnStretch(2, 1)
        # take up any additional space in the final row with padding
        layout.setRowStretch(layout_row, 1)

        self.setLayout(layout)

    def update_position(self):
        """Query the laser for the current state then update the state text box."""
        self.power_label.setText(str(self.ell14.write('get_position'))
