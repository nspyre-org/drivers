"""
Qt GUI for the agiltron fiber switch driver.

Copyright (c) 2022, Jacob Feder, Ben Soloway
All rights reserved.
"""
import logging

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

logger = logging.getLogger(__name__)

class FFSWWidget(QtWidgets.QWidget):
    """Qt widget for controlling cld1010 lasers."""

    def __init__(self, ffsw, port_mapping=None):
        """
        Args:
            ffsw: The fiber-fiber switch (ffsw) driver.
            port_mapping: Dict where the keys are device port numbers and values are string name descriptors
        """
        super().__init__()

        self.ffsw = ffsw

        # top level layout
        layout = QtWidgets.QGridLayout()
        layout_row = 0

        # port dropdown
        layout.addWidget(QtWidgets.QLabel('Port'), layout_row, 0)
        self.port_dropdown = QtWidgets.QComboBox()
        if port_mapping is not None:
            # reverse keys and values
            inverse_port_mapping = {v: k for k, v in port_mapping.items()}
            self.port_dropdown.addItem(inverse_port_mapping[1]) # index 0
            self.port_dropdown.addItem(inverse_port_mapping[2]) # index 1
        else:
            self.port_dropdown.addItem('1') # index 0
            self.port_dropdown.addItem('2') # index 1
        # default to port 1
        self.port_dropdown.setCurrentIndex(0)
        self.port_dropdown.currentIndexChanged.connect(self.change_port)
        layout.addWidget(self.port_dropdown, layout_row, 1)
        layout_row += 1

        # get state button
        self.get_state_button = QtWidgets.QPushButton('Get State')
        self.get_state_button.clicked.connect(self.update_state)
        layout.addWidget(self.get_state_button, layout_row, 0)
        layout_row += 1

        # take up any additional space in the final column with padding
        layout.setColumnStretch(2, 1)
        # take up any additional space in the final row with padding
        layout.setRowStretch(layout_row, 1)

        self.setLayout(layout)

    def change_port(self, idx):
        """Change the agiltron port."""
        if idx == 0:
            self.ffsw.set_port(1)
        elif idx == 1:
            self.ffsw.set_port(2)
        else:
            raise ValueError(f'Invalid mode selection [{idx}]')

    def update_state(self):
        """Query the agiltron for the current state then update the GUI."""
        port = self.ffsw.get_port()
        self.port_dropdown.blockSignals(True)
        if port == 1:
            self.port_dropdown.setCurrentIndex(0)
        elif port == 2:
            self.port_dropdown.setCurrentIndex(1)
        else:
            raise ValueError(f'Got invalid port [{port}]')
        self.port_dropdown.blockSignals(False)
