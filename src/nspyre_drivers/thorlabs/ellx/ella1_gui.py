"""
Qt GUI for Thorlabs PM100D power meter.

Copyright (c) 2022, Jacob Feder, Ben Soloway
All rights reserved.
"""
import logging

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

logger = logging.getLogger(__name__)

class Ella1Widget(QtWidgets.QWidget):
    """Qt widget for controlling the Ella1 two position slider."""

    def __init__(self, ella1_driver):
        """
        Args:
            ella1_driver: Ella1 driver.
        """
        super().__init__()

        self.ella1 = ella1_driver

        # top level layout
        layout = QtWidgets.QGridLayout()
        layout_row = 0

        # position label
        self.position_label = QtWidgets.QLabel('')
        self.update_position()
        layout.addWidget(self.position_label, layout_row, 1)
        # get power button
        self.get_position_button = QtWidgets.QPushButton('Get position')
        self.get_position_button.clicked.connect(self.update_position)
        layout.addWidget(self.get_position_button, layout_row, 0)
        layout_row += 1

        # home
        self.home_button = QtWidgets.QPushButton('pos0')
        self.home_button.clicked.connect(lambda home: self.pos0_and_update_position())
        layout.addWidget(self.home_button, layout_row, 0)
        self.home_button = QtWidgets.QPushButton('pos1')
        self.home_button.clicked.connect(lambda home: self.pos1_and_update_position())
        layout.addWidget(self.home_button, layout_row, 1)
        layout_row += 1

        # take up any additional space in the final column with padding
        layout.setColumnStretch(2, 1)
        # take up any additional space in the final row with padding
        layout.setRowStretch(layout_row, 1)

        self.setLayout(layout)

    def update_position(self):
        """Query the laser for the current state then update the state text box."""
        val = str(self.ella1.write('get_position'))
        if '0' in val:
            self.position_label.setText(str(0))
        elif '31' in val:
            self.position_label.setText(str(1))
        else:
            self.position_label.setText('Unknown')

    def pos0_and_update_position(self):
        self.ella1.move_backward()
        self.update_position()

    def pos1_and_update_position(self):
        self.ella1.move_forward()
        self.update_position()