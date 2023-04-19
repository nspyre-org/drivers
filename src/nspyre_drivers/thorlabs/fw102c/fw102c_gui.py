"""
GUI for the thorlabs FW102C filter wheel.

https://www.thorlabs.com/thorproduct.cfm?partnumber=FW102C#ad-image-0

Copyright (c) 2022, Jacob Feder
All rights reserved.
"""

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

class FW102CWidget(QtWidgets.QWidget):
    """Qt widget for controlling the Thorlabs FW102C filter wheel."""

    def __init__(self, filter_wheel_driver, filter_wheel_channel_mapping):
        """
        Args:
            filter_wheel_driver: The FW102C driver.
            filter_wheel_channel_mapping: TODO.
        """
        super().__init__()

        self.filter_wheel = filter_wheel_driver

        # top level layout
        layout = QtWidgets.QVBoxLayout()

        wheel_position_layout = QtWidgets.QHBoxLayout()
        position_label = QtWidgets.QLabel('Position')
        position_label.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )
        )
        wheel_position_layout.addWidget(position_label)
        filter_wheel_combobox = QtWidgets.QComboBox()
        for m in filter_wheel_channel_mapping:
            filter_wheel_combobox.addItem(m)
        filter_wheel_combobox.setCurrentText(self.filter_wheel.position())
        filter_wheel_combobox.currentTextChanged.connect(lambda text: self.filter_wheel.set_position(text))
        wheel_position_layout.addWidget(filter_wheel_combobox)

        layout.addLayout(wheel_position_layout)
        layout.addStretch()

        self.setLayout(layout)
