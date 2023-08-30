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

        # button to turn the laser off
        off_button = QtWidgets.QPushButton('Off')
        off_button.clicked.connect(lambda: self.laser.off())
        layout.addWidget(off_button, layout_row, 0)

        # button to turn the laser on
        on_button = QtWidgets.QPushButton('On')
        on_button.clicked.connect(lambda: self.laser.on())
        layout.addWidget(on_button, layout_row, 1)

        layout_row += 1

        # power spinbox
        layout.addWidget(QtWidgets.QLabel('Power %'), layout_row, 0)
        self.power_spinbox = SpinBox(value=0, siPrefix=False, bounds=(0, 100), int=True)
        self.power_spinbox.setValue(value=0)
        layout.addWidget(self.power_spinbox, layout_row, 2)

        # power get button
        power_get_button = QtWidgets.QPushButton('Get')
        def get_power(button):
            self.power_spinbox.setValue(self.laser.get_power())
        get_power(None)
        power_get_button.clicked.connect(get_power)
        layout.addWidget(power_get_button, layout_row, 1)

        # power set button
        power_set_button = QtWidgets.QPushButton('Set')
        def set_power(button):
            self.laser.set_power(self.power_spinbox.value())
        power_set_button.clicked.connect(set_power)
        layout.addWidget(power_set_button, layout_row, 3)

        layout_row += 1

        # modulation label
        layout.addWidget(QtWidgets.QLabel('Modulation'), layout_row, 0)

        # modulation combobox
        self.modulation_dropdown = QtWidgets.QComboBox()
        unknown_modulation_state_text = '?'
        cw_modulation_state_text = 'CW'
        external_trigger_modulation_state_text = 'Ext'
        self.modulation_dropdown.addItem(unknown_modulation_state_text) # index 0
        self.modulation_dropdown.addItem(cw_modulation_state_text) # index 1
        self.modulation_dropdown.addItem(external_trigger_modulation_state_text) # index 2
        layout.addWidget(self.modulation_dropdown, layout_row, 2)

        # modulation set button
        modulation_set_button = QtWidgets.QPushButton('Set')
        def set_modulation(button):
            mode = self.modulation_dropdown.currentText()
            if mode == cw_modulation_state_text:
                self.laser.cw_mode()
            elif mode == external_trigger_modulation_state_text:
                self.laser.trig_mode()
            else:
                raise RuntimeError('Modulation mode error.')

            if self.modulation_dropdown.itemText(0) == unknown_modulation_state_text:
                self.modulation_dropdown.removeItem(0)
        modulation_set_button.clicked.connect(set_modulation)
        layout.addWidget(modulation_set_button, layout_row, 3)

        layout_row += 1

        # take up any additional space in the final column with padding
        layout.setColumnStretch(2, 1)
        # take up any additional space in the final row with padding
        layout.setRowStretch(layout_row, 1)

        self.setLayout(layout)
