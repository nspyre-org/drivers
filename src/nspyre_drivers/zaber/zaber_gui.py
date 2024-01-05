"""Qt Widget for a Zaber stage.

Author: Jacob Feder
"""
from pyqtgraph.Qt import QtWidgets
from pyqtgraph import SpinBox
from pyqtgraph.Qt import QtCore

from zaber_motion import Units

class ZaberWidget(QtWidgets.QWidget):
    def __init__(self, stages, axis: str, min_pos: float = 0, max_pos: float = None):
        """
        Args:
            stages: ZaberStages object.
            axis: Axis name.
            min_pos: Minimum stage position (m).
            max_pos: Maximum stage position (m).
        """
        super().__init__()

        layout = QtWidgets.QGridLayout()
        layout_row = 0

        # home button
        home_button = QtWidgets.QPushButton('Home')
        def home(button):
            stages[axis].home()
        home_button.clicked.connect(home)
        layout.addWidget(home_button, layout_row, 0)

        layout_row += 1

        #################
        # position
        #################

        # position label
        layout.addWidget(QtWidgets.QLabel('Position'), layout_row, 0)

        # position spinbox
        pos_spinbox = SpinBox(
            suffix='m',
            value=stages[axis].get_position(unit=Units.LENGTH_METRES),
            bounds=(min_pos, max_pos),
            siPrefix=True,
        )
        pos_spinbox.setMinimumSize(QtCore.QSize(120, 0))
        layout.addWidget(pos_spinbox, layout_row, 2)

        # position get button
        position_get_button = QtWidgets.QPushButton('Get')
        def get_position(button):
            nonlocal pos_spinbox
            pos_spinbox.setValue(stages[axis].get_position(unit=Units.LENGTH_METRES))
        get_position(None)
        position_get_button.clicked.connect(get_position)
        layout.addWidget(position_get_button, layout_row, 1)

        # position set button
        position_set_button = QtWidgets.QPushButton('Set')
        def set_position(button):
            nonlocal pos_spinbox
            stages[axis].move_absolute(pos_spinbox.value(), unit=Units.LENGTH_METRES, wait_until_idle=False)
        position_set_button.clicked.connect(set_position)
        layout.addWidget(position_set_button, layout_row, 3)

        layout.setRowStretch(layout_row+1, 1)
        self.setLayout(layout)
