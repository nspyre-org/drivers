"""
Qt GUI for Thorlabs PM100D power meter.

Copyright (c) 2022, Jacob Feder, Ben Soloway
All rights reserved.
"""
import logging

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

logger = logging.getLogger(__name__)

class PM100Widget(QtWidgets.QWidget):
    """Qt widget for controlling the PM100D power meter."""

    def __init__(self, pm100d_driver):
        """
        Args:
            pm100d_driver: PM100D driver.
        """
        super().__init__()

        self.pm = pm100d_driver

        # top level layout
        layout = QtWidgets.QGridLayout()
        layout_row = 0

        # power spinbox
        layout.addWidget(QtWidgets.QLabel('Correction wavelength'), layout_row, 0)
        self.corr_wave_spinbox = SpinBox(value=488, suffix='nm', siPrefix=True, bounds=(400, 1100), dec=True, minStep=5)
        self.corr_wave_spinbox.sigValueChanged.connect(lambda spinbox: self.pm.set_correction_wavelength(spinbox.value()))
        self.corr_wave_spinbox.sigValueChanged.connect(self.update_corr_wave)
        self.corr_wave_spinbox.setValue(value=488)
        layout.addWidget(self.corr_wave_spinbox, layout_row, 1)
        layout_row += 1

        # correction wavelength label
        self.corr_wave_label = QtWidgets.QLabel('')
        self.update_corr_wave()
        layout.addWidget(self.corr_wave_label, layout_row, 1)
        # get state button
        self.get_corr_wave_button = QtWidgets.QPushButton('Get Correction Wavelength')
        self.get_corr_wave_button.clicked.connect(self.update_corr_wave)
        layout.addWidget(self.get_corr_wave_button, layout_row, 0)
        layout_row += 1

        # power label
        self.power_label = QtWidgets.QLabel('')
        self.update_power()
        layout.addWidget(self.power_label, layout_row, 1)
        # get power button
        self.get_power_button = QtWidgets.QPushButton('Get power')
        self.get_power_button.clicked.connect(self.update_power)
        layout.addWidget(self.get_power_button, layout_row, 0)
        layout_row += 1

        # take up any additional space in the final column with padding
        layout.setColumnStretch(2, 1)
        # take up any additional space in the final row with padding
        layout.setRowStretch(layout_row, 1)

        self.setLayout(layout)

    def update_power(self):
        """Query the laser for the current state then update the state text box."""
        self.power_label.setText(str(self.pm.power()))

    def update_corr_wave(self):
        self.corr_wave_label.setText(str(self.pm.get_correction_wavelength()))
