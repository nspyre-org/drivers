"""
GUI for Arduino GPIO.

Copyright (c) 2022, Jacob Feder
All rights reserved.
"""
from functools import partial

from pyqtgraph.Qt import QtWidgets

class ArduinoGPIOWidget(QtWidgets.QWidget):
    """Qt widget for controlling the Arduino GPIO."""
    def __init__(self, arduino):
        """
        Args:
            arduino: The Arduino driver.
        """
        super().__init__()

        self.arduino = arduino

        # top level layout
        layout = QtWidgets.QGridLayout()
        layout_row = 0

        # DO state dropdowns
        self.digital_out_dropdowns = {}
        # run pin_changed_external() when the pin state is changed from another source
        self.arduino.pin_state_changed.connect(self.pin_changed_external)
        for i, pin in enumerate(self.arduino.pins):
            layout.addWidget(QtWidgets.QLabel(f'Digital Out {pin}'), layout_row, 0)
            self.digital_out_dropdowns[pin] = QtWidgets.QComboBox()
            self.digital_out_dropdowns[pin].addItem('Low') # index 0
            self.digital_out_dropdowns[pin].addItem('High') # index 1
            # default to low
            self.digital_out_dropdowns[pin].setCurrentIndex(0)
            # update the driver state when the combobox is changed
            self.digital_out_dropdowns[pin].currentIndexChanged.connect(partial(self.combobox_changed, pin))
            layout.addWidget(self.digital_out_dropdowns[pin], layout_row, 1)
            layout_row += 1

        # take up any additional space in the final column with padding
        layout.setColumnStretch(2, 1)
        # take up any additional space in the final row with padding
        layout.setRowStretch(layout_row, 1)

        self.setLayout(layout)

    def pin_changed_external(self, pin, state):
        """The underlying driver changed the pin state"""
        self.digital_out_dropdowns[pin].blockSignals(True)
        if state:
            self.digital_out_dropdowns[pin].setCurrentIndex(1)
        else:
            self.digital_out_dropdowns[pin].setCurrentIndex(0)
        self.digital_out_dropdowns[pin].blockSignals(False)

    def combobox_changed(self, pin, index):
        """User changed the combobox selection"""
        self.arduino.set_pin(pin, index, emit=False)
