"""
Qt GUI for acton monochromator driver.

Copyright (c) 2022, Jacob Feder, Benjamin Soloway
All rights reserved.
"""
import logging

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

logger = logging.getLogger(__name__)

class ActonWidget(QtWidgets.QWidget):
    """Qt widget for controlling cobolt lasers."""
    def __init__(self, mono):
        """
        Args:
            mono: The monochromator driver.
        """
        super().__init__()

        self.mono = mono

        # top level layout
        layout = QtWidgets.QGridLayout()
        layout_row = 0

        # wavelength spinbox
        layout.addWidget(QtWidgets.QLabel('Wavelength'), layout_row, 0)
        self.wl_spinbox = SpinBox(value=self.mono.get_wavelength(), suffix='nm', siPrefix=True, bounds=(0, 1000), dec=True, minStep=0.1e-6)
        def set_wl(spinbox):
            self.mono.set_wavelength(spinbox.value())
        self.wl_spinbox.sigValueChanged.connect(set_wl)
        self.wl_spinbox.setValue(value=0)
        layout.addWidget(self.wl_spinbox, layout_row, 1)
        layout_row += 1

        # dropdown menu to pick laser mode
        layout.addWidget(QtWidgets.QLabel('Grating'), layout_row, 0)
        self.mode_dropdown = QtWidgets.QComboBox()
        self.mode_dropdown.addItem(self.mono.get_all_gratings().split('\n')[1]) # index 0
        self.mode_dropdown.addItem(self.mono.get_all_gratings().split('\n')[2]) # index 1
        # default to modulation mode
        self.mode_dropdown.setCurrentIndex(0)
        self.mode_dropdown.currentIndexChanged.connect(self.change_grating)
        layout.addWidget(self.mode_dropdown, layout_row, 1)
        layout_row += 1

        # take up any additional space in the final column with padding
        layout.setColumnStretch(2, 1)
        # take up any additional space in the final row with padding
        layout.setRowStretch(layout_row, 1)

        self.setLayout(layout)

    def update_wavelength(self):
        """Query the laser for the current state then update the state text box."""
        self.state_label.setText(self.mono.get_wavelength())

    def change_grating(self, idx):
        """Change the laser output mode."""
        # constant power
        # digital modulation
        if idx == 0:
            self.mono.set_grating(1)
        elif idx == 1:
            self.mono.set_grating(2)
        else:
            raise ValueError('Invalid mode selection')
