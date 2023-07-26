"""Qt Widget for a Thorlabs Kinesis stage.

Author: Jacob Feder
"""
from typing import Dict
from functools import partial

from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox
from pyqtgraph.Qt import QtCore

class KinesisWidget(QtWidgets.QWidget):
    def __init__(self, stages: Dict):
        """
        Args:
            stages: Stage name keys mapped to values of stage driver objects.
        """
        super().__init__()

        # main layout
        layout = QtWidgets.QHBoxLayout()

        def home(button, stage):
            stage.home()

        def set_pos(button, stage, ch, pos_spinbox):
            pos = pos_spinbox.value()
            stage.move_to(pos, channel=ch)

        def get_pos(button, stage, ch, pos_spinbox):
            pos = stage.get_position(channel=ch)
            pos_spinbox.setValue(pos)

        for col, stage_name in enumerate(stages):
            # extract driver object
            stage = stages[stage_name]

            stage_layout = QtWidgets.QVBoxLayout()

            ###############
            # stage label
            ###############

            # stage name label
            stage_layout.addWidget(QtWidgets.QLabel(stage_name))

            ###############
            # stage home
            ###############

            # home button
            home_button = QtWidgets.QPushButton('Home')
            home_button.clicked.connect(partial(home, stage=stage))
            stage_layout.addWidget(home_button)

            ###############

            channels_layout = QtWidgets.QVBoxLayout()

            for ch in stage.get_all_channels():
                channel_layout = QtWidgets.QGridLayout()
                layout_row = 0

                ###############
                # channel label
                ###############

                # channel name label
                channel_layout.addWidget(QtWidgets.QLabel(f'Ch {ch}'), layout_row, 0)

                layout_row += 1

                ###############
                # channel position
                ###############

                # position label
                channel_layout.addWidget(QtWidgets.QLabel('Pos'), layout_row, 0)

                # position spinbox
                pos_spinbox = SpinBox(
                    suffix='m',
                    value=stage.get_position(channel=ch),
                    siPrefix=True,
                )
                pos_spinbox.setMinimumSize(QtCore.QSize(150, 0))
                channel_layout.addWidget(pos_spinbox, layout_row, 3)

                # get button
                get_pos_button = QtWidgets.QPushButton('Get')
                get_pos_button.clicked.connect(partial(get_pos, stage=stage, ch=ch, pos_spinbox=pos_spinbox))
                channel_layout.addWidget(get_pos_button, layout_row, 1)

                # set button
                set_pos_button = QtWidgets.QPushButton('Set')
                set_pos_button.clicked.connect(partial(set_pos, stage=stage, ch=ch, pos_spinbox=pos_spinbox))
                channel_layout.addWidget(set_pos_button, layout_row, 2)

                layout_row += 1

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
