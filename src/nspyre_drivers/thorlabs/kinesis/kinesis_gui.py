"""Qt Widget for a Thorlabs Kinesis stage. The stage driver objects are assumed
to be pylablib KinesisMotor objects.

Author: Jacob Feder
"""
from typing import Dict
from functools import partial

from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox

class KinesisWidget(QtWidgets.QWidget):
    def __init__(self, stages: Dict):
        """
        Args:
            stages: Stage name keys mapped to values of KinesisMotor objects.
        """
        super().__init__()

        # main layout
        layout = QtWidgets.QHBoxLayout()

        # store all of the GUI elements
        self.gui_elements = {}

        for col, stage_name in enumerate(stages):
            self.gui_elements[stage_name] = {}
            self.gui_elements[stage_name]['general'] = {}

            # extract driver object
            stage = stages[stage_name]

            stage_layout = QtWidgets.QVBoxLayout()

            ###############
            # status
            ###############

            status_layout = QtWidgets.QGridLayout()
            layout_row = 0

            # stage name label
            status_layout.addWidget(QtWidgets.QLabel(stage_name), layout_row, 0)

            # get status button
            get_status_button = QtWidgets.QPushButton('Get Status')
            get_status_button.clicked.connect(partial(self.get_status, stage_name=stage_name, stage=stage))
            status_layout.addWidget(get_status_button, layout_row, 1)

            layout_row += 1

            # connection status
            status_layout.addWidget(QtWidgets.QLabel('Connected:'), layout_row, 0)
            connection_status_label = QtWidgets.QLabel('')
            status_layout.addWidget(connection_status_label, layout_row, 1)
            self.gui_elements[stage_name]['general']['connection_status_label'] = connection_status_label

            layout_row += 1

            # homed status
            status_layout.addWidget(QtWidgets.QLabel('Homed:'), layout_row, 0)
            homed_status_label = QtWidgets.QLabel('')
            status_layout.addWidget(homed_status_label, layout_row, 1)
            self.gui_elements[stage_name]['general']['homed_status_label'] = homed_status_label

            layout_row += 1

            # power status
            status_layout.addWidget(QtWidgets.QLabel('Power:'), layout_row, 0)
            power_status_label = QtWidgets.QLabel('')
            status_layout.addWidget(power_status_label, layout_row, 1)
            self.gui_elements[stage_name]['general']['power_status_label'] = power_status_label

            layout_row += 1

            # enabled status
            status_layout.addWidget(QtWidgets.QLabel('Enabled:'), layout_row, 0)
            enabled_status_label = QtWidgets.QLabel('')
            status_layout.addWidget(enabled_status_label, layout_row, 1)
            self.gui_elements[stage_name]['general']['enabled_status_label'] = enabled_status_label

            layout_row += 1

            self.get_status(None, stage_name, stage)

            stage_layout.addLayout(status_layout)

            ###############

            channels_layout = QtWidgets.QVBoxLayout()

            for ch in stage.get_all_channels():
                self.gui_elements[stage_name][ch] = {}

                channel_layout = QtWidgets.QGridLayout()
                layout_row = 0

                ###############
                # channel label
                ###############

                # channel name label
                channel_layout.addWidget(QtWidgets.QLabel(f'Ch {ch}'), layout_row, 0)

                ###############
                # stop
                ###############

                # stop button
                stop_button = QtWidgets.QPushButton('Stop')
                stop_button.clicked.connect(partial(self.stop, stage_name=stage_name, stage=stage, ch=ch))
                channel_layout.addWidget(stop_button, layout_row, 2)
                self.gui_elements[stage_name][ch]['stop_button'] = stop_button

                ###############
                # home
                ###############

                # home button
                home_button = QtWidgets.QPushButton('Home')
                home_button.clicked.connect(partial(self.home, stage_name=stage_name, stage=stage, ch=ch))
                channel_layout.addWidget(home_button, layout_row, 3)
                self.gui_elements[stage_name][ch]['home_button'] = home_button

                layout_row += 1

                ###############
                # position
                ###############

                # position label
                channel_layout.addWidget(QtWidgets.QLabel('Pos'), layout_row, 0)

                # position spinbox
                pos_spinbox = SpinBox(
                    suffix='m',
                    value=stage.get_position(channel=ch),
                    siPrefix=True,
                    dec=True,
                )
                pos_spinbox.setMinimumSize(QtCore.QSize(150, 0))
                channel_layout.addWidget(pos_spinbox, layout_row, 2)
                self.gui_elements[stage_name][ch]['pos_spinbox'] = pos_spinbox

                # get button
                get_pos_button = QtWidgets.QPushButton('Get')
                get_pos_button.clicked.connect(partial(self.get_pos, stage=stage, ch=ch, pos_spinbox=pos_spinbox))
                channel_layout.addWidget(get_pos_button, layout_row, 1)
                self.gui_elements[stage_name][ch]['get_pos_button'] = get_pos_button

                # set button
                set_pos_button = QtWidgets.QPushButton('Set')
                set_pos_button.clicked.connect(partial(self.set_pos, stage=stage, ch=ch, pos_spinbox=pos_spinbox))
                if not stage.is_homed(channel=ch):
                    # disable the move button if the stage isn't homed
                    self.disable_button(set_pos_button)
                    self.disable_button(get_pos_button)
                channel_layout.addWidget(set_pos_button, layout_row, 3)
                self.gui_elements[stage_name][ch]['set_pos_button'] = set_pos_button

                layout_row += 1

                ###############
                # step
                ###############

                # step label
                channel_layout.addWidget(QtWidgets.QLabel('Step'), layout_row, 0)

                # step spinbox
                step_spinbox = SpinBox(
                    suffix='m',
                    value=1e-3,
                    siPrefix=True,
                    dec=True,
                )
                step_spinbox.setMinimumSize(QtCore.QSize(150, 0))
                channel_layout.addWidget(step_spinbox, layout_row, 1)
                self.gui_elements[stage_name][ch]['step_spinbox'] = step_spinbox

                # step- button
                step_minus_button = QtWidgets.QPushButton('-')
                step_minus_button.clicked.connect(partial(
                    self.step,
                    stage=stage,
                    ch=ch,
                    direction=False,
                    step_spinbox=step_spinbox
                ))
                channel_layout.addWidget(step_minus_button, layout_row, 2)
                self.gui_elements[stage_name][ch]['step_minus_button'] = step_minus_button

                # step+ button
                step_plus_button = QtWidgets.QPushButton('+')
                step_plus_button.clicked.connect(partial(
                    self.step,
                    stage=stage,
                    ch=ch,
                    direction=True,
                    step_spinbox=step_spinbox
                ))
                channel_layout.addWidget(step_plus_button, layout_row, 3)
                self.gui_elements[stage_name][ch]['step_plus_button'] = step_plus_button

                ###############

                # add this channel layout to the channels layout
                channels_layout.addLayout(channel_layout)

            # add the channels layout to the stage
            stage_layout.addLayout(channels_layout)
            # add stretch to the end
            stage_layout.addStretch()
            # add this stage layout to the main layout
            layout.addLayout(stage_layout)

        self.setLayout(layout)

    def disable_button(self, button):
        # change the color to "disabled" color
        col_bg = QtGui.QColor(
            self.palette().color(QtGui.QPalette.ColorRole.AlternateBase)
        ).name()
        col_txt = QtGui.QColor(QtCore.Qt.GlobalColor.gray).name()
        button.setStyleSheet(
            f'QPushButton {{background-color: {col_bg}; color: {col_txt};}}'
        )
        # disable the button until the save finished
        button.setEnabled(False)

    def enable_button(self, button):
        # reset the color
        col_bg = QtGui.QColor(
            self.palette().color(QtGui.QPalette.ColorRole.Button)
        ).name()
        col_txt = QtGui.QColor(
            self.palette().color(QtGui.QPalette.ColorRole.ButtonText)
        ).name()
        button.setStyleSheet(
            f'QPushButton {{background-color: {col_bg}; color: {col_txt};}}'
        )
        # re-enable the button
        button.setEnabled(True)

    def get_status(self, button, stage_name, stage):
        # TODO continuously update?
        status = stage.get_status()

        if 'connected' in status:
            self.gui_elements[stage_name]['general']['connection_status_label'].setText('Yes')
        else:
            self.gui_elements[stage_name]['general']['connection_status_label'].setText('No')

        if 'homed' in status:
            self.gui_elements[stage_name]['general']['homed_status_label'].setText('Yes')
        else:
            self.gui_elements[stage_name]['general']['homed_status_label'].setText('No')

        if 'power_ok' in status:
            self.gui_elements[stage_name]['general']['power_status_label'].setText('Yes')
        else:
            self.gui_elements[stage_name]['general']['power_status_label'].setText('No')

        if 'enabled' in status:
            self.gui_elements[stage_name]['general']['enabled_status_label'].setText('Yes')
        else:
            self.gui_elements[stage_name]['general']['enabled_status_label'].setText('No')

    def stop(self, button, stage_name, stage, ch):
        stage.stop(immediate=True, sync=True, channel=ch, timeout=None)

    def home(self, button, stage_name, stage, ch):
        stage.home(sync=True, force=True, channel=ch)
        self.enable_button(self.gui_elements[stage_name][ch]['get_pos_button'])
        self.enable_button(self.gui_elements[stage_name][ch]['set_pos_button'])

    def set_pos(self, button, stage, ch, pos_spinbox):
        pos = pos_spinbox.value()
        stage.move_to(pos, channel=ch)

    def get_pos(self, button, stage, ch, pos_spinbox):
        pos = stage.get_position(channel=ch)
        pos_spinbox.setValue(pos)

    def step(self, button, stage, ch, direction, step_spinbox):
        step_size = step_spinbox.value()
        if not direction:
            step_size = -step_size
        stage.move_by(distance=step_size, channel=ch)
