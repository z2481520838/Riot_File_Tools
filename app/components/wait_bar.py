from enum import Enum
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout,
                             QToolButton, QGraphicsOpacityEffect, QApplication)
from qfluentwidgets import InfoBar, InfoBarIcon, InfoBarPosition, IndeterminateProgressRing
from qfluentwidgets.components.widgets.info_bar import InfoIconWidget

class ProgressRingWidget(QWidget):
    """ Icon widget """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(36, 36)
        layout = QVBoxLayout(self)
        spinner = IndeterminateProgressRing(self)
        spinner.setFixedSize(15, 15)
        spinner.setStrokeWidth(1.5)
        layout.addWidget(spinner)

class WaitBar(InfoBar):
    def __init__(self, title, content, parent=None):
        super().__init__(InfoBarIcon.SUCCESS, title, content, Qt.Horizontal, False, -1, InfoBarPosition.BOTTOM, parent)

    def _InfoBar__initLayout(self):
        self.hBoxLayout.setContentsMargins(6, 6, 6, 6)
        self.hBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.textLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)
        self.textLayout.setAlignment(Qt.AlignTop)
        self.textLayout.setContentsMargins(1, 8, 0, 8)

        self.hBoxLayout.setSpacing(0)
        self.textLayout.setSpacing(5)

        # add icon to layout
        self.hBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignTop | Qt.AlignLeft)
        self.iconWidget.setVisible(False)
        self.spinner = ProgressRingWidget(self)
        self.hBoxLayout.addWidget(self.spinner, 0, Qt.AlignTop | Qt.AlignLeft)

        # add title to layout
        self.textLayout.addWidget(self.titleLabel, 1, Qt.AlignTop)
        self.titleLabel.setVisible(bool(self.title))

        # add content label to layout
        if self.orient == Qt.Horizontal:
            self.textLayout.addSpacing(7)

        self.textLayout.addWidget(self.contentLabel, 1, Qt.AlignTop)
        self.contentLabel.setVisible(bool(self.content))
        self.hBoxLayout.addLayout(self.textLayout)

        # add widget layout
        if self.orient == Qt.Horizontal:
            self.hBoxLayout.addLayout(self.widgetLayout)
            self.widgetLayout.setSpacing(10)
        else:
            self.textLayout.addLayout(self.widgetLayout)

        # add close button to layout
        self.hBoxLayout.addSpacing(12)
        self.hBoxLayout.addWidget(self.closeButton, 0, Qt.AlignTop | Qt.AlignLeft)

        self._adjustText()

    def update_data(self, icon, title, content, duration):
        self.icon = icon
        self.title = title
        self.content = content
        self.duration = duration
        self.iconWidget.icon = icon
        self.iconWidget.setVisible(True)
        self.spinner.setVisible(False)
        self.titleLabel.setVisible(bool(self.title))
        self._adjustText()
        self._InfoBar__setQss()
        if self.duration >= 0:
            QTimer.singleShot(self.duration, self._InfoBar__fadeOut)

    def update_text(self, title, content):
        self.title = title
        self.content = content
        self._adjustText()