"""
Qt GUI for Swabian/LABS electronics DLnsec laser.

Copyright (c) 2022, Benjamin Soloway, Jacob Feder
All rights reserved.
"""
import logging

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

class DLnsecWidget(QtWidgets.QWidget):
    """Qt widget for controlling DLnsec lasers."""
    def __init__(self, laser_driver):
        """
        Args:
            laser_driver: The dlnsec driver.
        """
        super().__init__()

        self.laser = laser_driver

        # top level layout
        layout = QtWidgets.QGridLayout()
        layout_row = 0

        # button to turn the laser on
        self.on_button = QtWidgets.QPushButton('On')
        self.on_button.clicked.connect(lambda: self.laser.on())
        layout.addWidget(self.on_button, layout_row, 0)

        # button to turn the laser off
        self.off_button = QtWidgets.QPushButton('Off')
        self.off_button.clicked.connect(lambda: self.laser.off())
        layout.addWidget(self.off_button, layout_row, 1)
        layout_row += 1

        # button to put the laser in CW mode
        self.on_button = QtWidgets.QPushButton('CW')
        self.on_button.clicked.connect(lambda: self.laser.cw_mode())
        layout.addWidget(self.on_button, layout_row, 0)

        # button to put the laser in external trigger mode
        self.on_button = QtWidgets.QPushButton('Trig')
        self.on_button.clicked.connect(lambda: self.laser.trig_mode())
        layout.addWidget(self.on_button, layout_row, 1)
        layout_row += 1

        # power spinbox
        layout.addWidget(QtWidgets.QLabel('Power (0-100)%'), layout_row, 0)
        self.power_spinbox = SpinBox(value=0, siPrefix=False, bounds=(0, 100), int=True)
        def set_power(spinbox):
            self.laser.power(int(spinbox.value()))
        self.power_spinbox.sigValueChanged.connect(set_power)
        self.power_spinbox.setValue(value=0)
        layout.addWidget(self.power_spinbox, layout_row, 1)
        layout_row += 1

        # button to reboot the laser
        self.on_button = QtWidgets.QPushButton('Reboot')
        self.on_button.clicked.connect(lambda: self.laser.reboot())
        layout.addWidget(self.on_button, layout_row, 1)
        layout_row += 1

        # take up any additional space in the final column with padding
        layout.setColumnStretch(2, 1)
        # take up any additional space in the final row with padding
        layout.setRowStretch(layout_row, 1)

        self.setLayout(layout)
