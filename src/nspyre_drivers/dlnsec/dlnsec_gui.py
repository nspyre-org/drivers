"""
Qt GUI for Swabian/LABS electronics DLnsec laser.

Copyright (c) 2022, Benjamin Soloway, Jacob Feder
All rights reserved.
"""
import logging

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

logger = logging.getLogger(__name__)

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

        # button to turn the laser off
        self.off_button = QtWidgets.QPushButton('Off')
        self.off_button.clicked.connect(lambda: self.laser.off())
        layout.addWidget(self.off_button, layout_row, 0)

        # button to turn the laser on
        self.on_button = QtWidgets.QPushButton('On')
        self.on_button.clicked.connect(lambda: self.laser.on())
        layout.addWidget(self.on_button, layout_row, 1)

        # button to put the laser in CW mode
        self.on_button = QtWidgets.QPushButton('CW')
        self.on_button.clicked.connect(lambda: self.laser.cw_mode())
        layout.addWidget(self.on_button, layout_row, 2)

        # button to reboot the laser
        self.on_button = QtWidgets.QPushButton('Reboot')
        self.on_button.clicked.connect(lambda: self.laser.reboot())
        layout.addWidget(self.on_button, layout_row, 3)
        layout_row += 1

        # power spinbox
        layout.addWidget(QtWidgets.QLabel('Power (fraction from 0-1)'), layout_row, 0)
        self.power_spinbox = SpinBox(value=0, siPrefix=False, bounds=(0, 1), dec=True, minStep=0.01)
        def set_power(spinbox):
            self.laser.power(int(spinbox.value()*100))
        self.power_spinbox.sigValueChanged.connect(set_power)
        self.power_spinbox.setValue(value=0)
        layout.addWidget(self.power_spinbox, layout_row, 1)
        layout_row += 1

        # # dropdown menu to pick laser mode
        # layout.addWidget(QtWidgets.QLabel('Mode'), layout_row, 0)
        # self.mode_dropdown = QtWidgets.QComboBox()
        # #self.mode_dropdown.addItem('Digital Modulation') # index 0
        # self.mode_dropdown.addItem('Constant Power') # index 1
        # # default to modulation mode
        # self.mode_dropdown.setCurrentIndex(0)
        # self.mode_dropdown.currentIndexChanged.connect(self.change_mode)
        # layout.addWidget(self.mode_dropdown, layout_row, 1)
        # layout_row += 1

        # # state label
        # self.state_label = QtWidgets.QLabel('')
        # self.update_state()
        # layout.addWidget(self.state_label, layout_row, 1)
        # # get state button
        # self.get_state_button = QtWidgets.QPushButton('Get State')
        # self.get_state_button.clicked.connect(self.update_state)
        # layout.addWidget(self.get_state_button, layout_row, 0)
        # layout_row += 1

        # take up any additional space in the final column with padding
        layout.setColumnStretch(2, 1)
        # take up any additional space in the final row with padding
        layout.setRowStretch(layout_row, 1)

        self.setLayout(layout)

    # def update_state(self):
    #     """Query the laser for the current state then update the state text box."""
    #     self.state_label.setText(self.laser.get_state()[4:])

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
