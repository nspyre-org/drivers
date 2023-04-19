"""
Qt GUI for Ocean Optics spectrometer HR2000+ES.

Copyright (c) 2022, Benjamin Soloway
All rights reserved.
"""
import logging

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox
from nspyre import LinePlotWidget
from rpyc.utils.classic import obtain

logger = logging.getLogger(__name__)

class OceanWidget(QtWidgets.QWidget):
    """Qt widget for controlling Ocean Optics HR2000ES spectrometers."""

    def __init__(self, spectrometer_driver):
        """
        Args:
            spectrometer_driver: The HR2000ES driver.
        """
        super().__init__()

        self.spec = spectrometer_driver

        # top level layout
        layout = QtWidgets.QGridLayout()
        layout_row = 0

        # button to acquire data
        self.plot = HR2000ES_LinePlotWidget()
        layout.addWidget(self.plot, layout_row, 0)
        layout_row+=1

        self.acquire_button = QtWidgets.QPushButton('Acquire')
        self.acquire_button.clicked.connect(self.acquire_and_plot)
        layout.addWidget(self.acquire_button, layout_row, 0)
        layout_row += 1

        # integration time spinbox
        layout.addWidget(QtWidgets.QLabel('Integration time'), layout_row, 0)
        layout_row += 1
        self.int_time_spinbox = SpinBox(value=0.1, suffix='s', siPrefix=True, bounds=(0, 4.147e6), dec=True, minStep=0.1e-3)
        self.int_time_spinbox.sigValueChanged.connect(lambda spinbox: self.spec.set_int_time_sec(spinbox.value()))
        self.int_time_spinbox.setValue(value=0.1)
        layout.addWidget(self.int_time_spinbox, layout_row, 0)
        layout_row += 1

        # time acquiring label
        self.time_acq_label = QtWidgets.QLabel('')
        layout.addWidget(self.time_acq_label, layout_row, 1)
        layout_row += 1
        # get time acquiring
        self.get_time_acq_button = QtWidgets.QPushButton('Get elapsed acquisition duration')
        self.get_time_acq_button.clicked.connect(self.update_acquisition_duration)
        layout.addWidget(self.get_time_acq_button, layout_row, 0)
        layout_row += 1

        # trigger mode spinbox
        layout.addWidget(QtWidgets.QLabel('Trigger Mode'), layout_row, 0)
        self.port_dropdown = QtWidgets.QComboBox()
        self.port_dropdown.addItem('Normal ("Free Running")') # index 0
        self.port_dropdown.addItem('Software Trigger (not tested)') # index 1
        self.port_dropdown.addItem('External Hardware Level (not tested)')  # index 2
        self.port_dropdown.addItem('External Hardware Edge')  # index 3
        layout_row += 1
        # default to modulation mode
        self.port_dropdown.setCurrentIndex(0)
        self.port_dropdown.currentIndexChanged.connect(self.set_trigger_mode)
        layout.addWidget(self.port_dropdown, layout_row, 0)
        layout_row += 1

        # #trigger mode label
        # self.trigger_label = QLabel('')
        # layout.addWidget(self.trigger_label, layout_row, 1)
        # layout_row += 1
        # # get time acquiring
        # self.get_trig_mode_button = QPushButton('Get trigger mode')
        # self.get_trig_mode_button.clicked.connect(self.update_trig_mode)
        # layout.addWidget(self.get_trig_mode_button, layout_row, 0)
        # layout_row += 1

        ## button to turn the laser on
        #self.on_button = QPushButton('On')
        #self.on_button.clicked.connect(lambda: self.laser.turn_on())
        #self.on_button.clicked.connect(self.update_state)
        #layout.addWidget(self.on_button, layout_row, 1)
        #layout_row += 1
        self.setLayout(layout)

    def acquire_and_plot(self):
        ws, ints = obtain(self.spec.acquire())
        self.plot.set_data('Spectrum', ws, ints)

    def update_time_acquiring(self):
        """Query the spectrometer for the current state then update the state text box."""
        self.time_acq_label.setText(self.spec.get_state()[4:])

    def update_acquisition_duration(self):
        self.time_acq_label.setText(str(self.spec.get_elapsed_time_sec()))

    def set_trigger_mode(self, idx):
        self.spec.set_trigger_mode(idx)

    # def update_trig_mode(self):
    #     """Query the laser for the current state then update the state text box."""
    #     self.trigger_label.setText(self.spec.get_state()[4:])
