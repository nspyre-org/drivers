"""
Qt GUI for Rigol DP832 power supply.

Copyright (c) 2023 Jacob Feder
All rights reserved.
"""
import logging
from functools import partial

from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

class DP832Widget(QtWidgets.QWidget):
    """A Qt widget for controlling the Rigol DP832 power supply."""
    def __init__(self, dp832_driver):
        """
        Args:
            dp832_driver: The dp832 driver.
        """
        super().__init__()

        # top level layout
        layout = QtWidgets.QVBoxLayout()

        channels = 3
        for ch in range(1, channels+1):
            # layout for each channel
            channel_layout = QtWidgets.QGridLayout()
            layout_row = 0

            # channel label
            channel_layout.addWidget(QtWidgets.QLabel(f'Ch {ch}'), layout_row, 0)

            layout_row += 1

            #################
            # output toggle
            #################

            # output state label
            channel_layout.addWidget(QtWidgets.QLabel('Output'), layout_row, 0)

            # output state combobox
            output_state_dropdown = QtWidgets.QComboBox()
            output_state_dropdown.addItem('Off') # index 0
            output_state_dropdown.addItem('On') # index 1
            channel_layout.addWidget(output_state_dropdown, layout_row, 2)

            # output state get button
            output_state_get_button = QtWidgets.QPushButton('Get')
            def get_output_state(button, ch, dropdown):
                if dp832_driver.get_output_state(ch):
                    dropdown.setCurrentIndex(1)
                else:
                    dropdown.setCurrentIndex(0)
            get_output_state(None, ch, output_state_dropdown)
            output_state_get_button.clicked.connect(partial(get_output_state, ch=ch, dropdown=output_state_dropdown))
            channel_layout.addWidget(output_state_get_button, layout_row, 1)

            # output state set button
            output_state_set_button = QtWidgets.QPushButton('Set')
            def set_output_state(button, ch, dropdown):
                if dropdown.currentIndex():
                    dp832_driver.set_output_state(ch, True)
                else:
                    dp832_driver.set_output_state(ch, False)
            output_state_set_button.clicked.connect(partial(set_output_state, ch=ch, dropdown=output_state_dropdown))
            channel_layout.addWidget(output_state_set_button, layout_row, 3)

            layout_row += 1

            #################
            # voltage
            #################

            # voltage label
            channel_layout.addWidget(QtWidgets.QLabel('Volts'), layout_row, 0)

            # voltage spinbox
            # TODO get bounds from driver
            voltage_spinbox = SpinBox(suffix='V', bounds=(0, 30), siPrefix=True)
            voltage_spinbox.setMinimumSize(QtCore.QSize(100, 0))
            channel_layout.addWidget(voltage_spinbox, layout_row, 2)

            # voltage get button
            voltage_get_button = QtWidgets.QPushButton('Get')
            def get_voltage(button, ch, spinbox):
                spinbox.setValue(dp832_driver.get_voltage(ch))
            get_voltage(None, ch, voltage_spinbox)
            voltage_get_button.clicked.connect(partial(get_voltage, ch=ch, spinbox=voltage_spinbox))
            channel_layout.addWidget(voltage_get_button, layout_row, 1)

            # voltage set button
            voltage_set_button = QtWidgets.QPushButton('Set')
            def set_voltage(button, ch, spinbox):
                dp832_driver.set_voltage(ch, spinbox.value(), confirm=False)
            voltage_set_button.clicked.connect(partial(set_voltage, ch=ch, spinbox=voltage_spinbox))
            channel_layout.addWidget(voltage_set_button, layout_row, 3)

            layout_row += 1

            #################
            # current
            #################

            # current label
            channel_layout.addWidget(QtWidgets.QLabel('Amps'), layout_row, 0)

            # current spinbox
            current_spinbox = SpinBox(suffix='A', bounds=(0, 3), siPrefix=True)
            current_spinbox.setMinimumSize(QtCore.QSize(100, 0))
            channel_layout.addWidget(current_spinbox, layout_row, 2)

            # current get button
            current_get_button = QtWidgets.QPushButton('Get')
            def get_current(button, ch, spinbox):
                spinbox.setValue(dp832_driver.get_current(ch))
            get_current(None, ch, current_spinbox)
            current_get_button.clicked.connect(partial(get_current, ch=ch, spinbox=current_spinbox))
            channel_layout.addWidget(current_get_button, layout_row, 1)

            # current set button
            current_set_button = QtWidgets.QPushButton('Set')
            def set_current(button, ch, spinbox):
                dp832_driver.set_current(ch, spinbox.value(), confirm=False)
            current_set_button.clicked.connect(partial(set_current, ch=ch, spinbox=current_spinbox))
            channel_layout.addWidget(current_set_button, layout_row, 3)

            layout_row += 1

            #################
            # OVP state
            #################

            # OVP state label
            channel_layout.addWidget(QtWidgets.QLabel('OVP'), layout_row, 0)

            # ovp state combobox
            ovp_state_dropdown = QtWidgets.QComboBox()
            ovp_state_dropdown.addItem('Off') # index 0
            ovp_state_dropdown.addItem('On') # index 1
            channel_layout.addWidget(ovp_state_dropdown, layout_row, 2)

            # ovp state get button
            ovp_state_get_button = QtWidgets.QPushButton('Get')
            def get_ovp_state(button, ch, dropdown):
                if dp832_driver.get_ovp_state(ch):
                    dropdown.setCurrentIndex(1)
                else:
                    dropdown.setCurrentIndex(0)
            get_ovp_state(None, ch, ovp_state_dropdown)
            ovp_state_get_button.clicked.connect(partial(get_ovp_state, ch=ch, dropdown=ovp_state_dropdown))
            channel_layout.addWidget(ovp_state_get_button, layout_row, 1)

            # ovp state set button
            ovp_state_set_button = QtWidgets.QPushButton('Set')
            def set_ovp_state(button, ch, dropdown):
                if dropdown.currentIndex():
                    dp832_driver.set_ovp_state(ch, True)
                else:
                    dp832_driver.set_ovp_state(ch, False)
            ovp_state_set_button.clicked.connect(partial(set_ovp_state, ch=ch, dropdown=ovp_state_dropdown))
            channel_layout.addWidget(ovp_state_set_button, layout_row, 3)

            layout_row += 1

            #################
            # OVP value
            #################

            # ovp label
            channel_layout.addWidget(QtWidgets.QLabel('OVP'), layout_row, 0)

            # ovp spinbox
            ovp_spinbox = SpinBox(suffix='V', bounds=(0, 33), siPrefix=True)
            ovp_spinbox.setMinimumSize(QtCore.QSize(100, 0))
            channel_layout.addWidget(ovp_spinbox, layout_row, 2)

            # ovp get button
            ovp_get_button = QtWidgets.QPushButton('Get')
            def get_ovp(button, ch, spinbox):
                spinbox.setValue(dp832_driver.get_ovp(ch))
            get_ovp(None, ch, ovp_spinbox)
            ovp_get_button.clicked.connect(partial(get_ovp, ch=ch, spinbox=ovp_spinbox))
            channel_layout.addWidget(ovp_get_button, layout_row, 1)

            # ovp set button
            ovp_set_button = QtWidgets.QPushButton('Set')
            def set_ovp(button, ch, spinbox):
                dp832_driver.set_ovp(ch, spinbox.value())
            ovp_set_button.clicked.connect(partial(set_ovp, ch=ch, spinbox=ovp_spinbox))
            channel_layout.addWidget(ovp_set_button, layout_row, 3)

            layout_row += 1

            #################
            # OCP state
            #################

            # OCP state label
            channel_layout.addWidget(QtWidgets.QLabel('OCP'), layout_row, 0)

            # ocp state combobox
            ocp_state_dropdown = QtWidgets.QComboBox()
            ocp_state_dropdown.addItem('Off') # index 0
            ocp_state_dropdown.addItem('On') # index 1
            channel_layout.addWidget(ocp_state_dropdown, layout_row, 2)

            # ocp state get button
            ocp_state_get_button = QtWidgets.QPushButton('Get')
            def get_ocp_state(button, ch, dropdown):
                if dp832_driver.get_ocp_state(ch):
                    dropdown.setCurrentIndex(1)
                else:
                    dropdown.setCurrentIndex(0)
            get_ocp_state(None, ch, ocp_state_dropdown)
            ocp_state_get_button.clicked.connect(partial(get_ocp_state, ch=ch, dropdown=ocp_state_dropdown))
            channel_layout.addWidget(ocp_state_get_button, layout_row, 1)

            # ocp state set button
            ocp_state_set_button = QtWidgets.QPushButton('Set')
            def set_ocp_state(button, ch, dropdown):
                if dropdown.currentIndex():
                    dp832_driver.set_ocp_state(ch, True)
                else:
                    dp832_driver.set_ocp_state(ch, False)
            ocp_state_set_button.clicked.connect(partial(set_ocp_state, ch=ch, dropdown=ocp_state_dropdown))
            channel_layout.addWidget(ocp_state_set_button, layout_row, 3)

            layout_row += 1

            #################
            # OCP value
            #################

            # ocp label
            channel_layout.addWidget(QtWidgets.QLabel('OCP'), layout_row, 0)

            # ocp spinbox
            ocp_spinbox = SpinBox(suffix='A', bounds=(0, 3.3), siPrefix=True)
            ocp_spinbox.setMinimumSize(QtCore.QSize(100, 0))
            channel_layout.addWidget(ocp_spinbox, layout_row, 2)

            # ocp get button
            ocp_get_button = QtWidgets.QPushButton('Get')
            def get_ocp(button, ch, spinbox):
                spinbox.setValue(dp832_driver.get_ocp(ch))
            get_ocp(None, ch, ocp_spinbox)
            ocp_get_button.clicked.connect(partial(get_ocp, ch=ch, spinbox=ocp_spinbox))
            channel_layout.addWidget(ocp_get_button, layout_row, 1)

            # ocp set button
            ocp_set_button = QtWidgets.QPushButton('Set')
            def set_ocp(button, ch, spinbox):
                dp832_driver.set_ocp(ch, spinbox.value())
            ocp_set_button.clicked.connect(partial(set_ocp, ch=ch, spinbox=ocp_spinbox))
            channel_layout.addWidget(ocp_set_button, layout_row, 3)

            layout_row += 1

            #################

            layout.addLayout(channel_layout)
            # add spacer to separate channels
            spacer = QtWidgets.QSpacerItem(1, 20,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Minimum
            ) 
            layout.addItem(spacer)

        # take up any additional space in the final row with padding
        layout.addStretch()

        self.setLayout(layout)
