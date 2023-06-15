"""
Qt GUI for Rigol DP832 power supply.

Copyright (c) 2023 Jacob Feder
All rights reserved.
"""
import logging
from functools import partial

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

class DP832Widget(QtWidgets.QWidget):
    """A Qt widget for controlling the Rigol DP832 power supply."""
    def __init__(self, driver):
        """
        Args:
            driver: The dp832 driver.
        """
        super().__init__()

        self.driver = driver

        # top level layout
        layout = QtWidgets.QGridLayout()

        channels = 3
        for ch in range(1, channels+1):
            layout_row = 0

            # label
            layout.addWidget(QtWidgets.QLabel(f'Ch {ch}'), layout_row, ch)
            layout_row += 1

            # for on/off buttons
            def toggle(checked, ch, state):
                self.driver.toggle_output(ch=ch, state=state)

            # button to turn the channel on
            self.on_button = QtWidgets.QPushButton('On')
            self.on_button.clicked.connect(partial(toggle, ch=ch, state=True))
            layout.addWidget(self.on_button, layout_row, ch)
            layout_row += 1
            
            # button to turn the channel off
            self.off_button = QtWidgets.QPushButton('Off')
            self.off_button.clicked.connect(partial(toggle, ch=ch, state=False))
            layout.addWidget(self.off_button, layout_row, ch)
            layout_row += 1

            # voltage spinbox
            volts_layout = QtWidgets.QHBoxLayout()
            volts_layout.addWidget(QtWidgets.QLabel('Volts'))
            volts_spinbox = SpinBox(value=self.driver.get_voltage(ch), bounds=(0, 30), siPrefix=False)
            def set_volts(spinbox, ch):
                self.driver.set_voltage(ch, spinbox.value(), confirm=False)
            volts_spinbox.sigValueChanged.connect(partial(set_volts, ch=ch))
            volts_layout.addWidget(volts_spinbox)
            layout.addLayout(volts_layout, layout_row, ch)
            layout_row += 1

            # current spinbox
            amps_layout = QtWidgets.QHBoxLayout()
            amps_layout.addWidget(QtWidgets.QLabel('Amps'))
            amps_spinbox = SpinBox(value=self.driver.get_current(ch), bounds=(0, 3), siPrefix=False)
            def set_amps(spinbox, ch):
                self.driver.set_current(ch, spinbox.value(), confirm=False)
            amps_spinbox.sigValueChanged.connect(partial(set_amps, ch=ch))
            amps_layout.addWidget(amps_spinbox)
            layout.addLayout(amps_layout, layout_row, ch)
            layout_row += 1

        # take up any additional space in the final row with padding
        layout.setRowStretch(layout_row, 1)

        self.setLayout(layout)
