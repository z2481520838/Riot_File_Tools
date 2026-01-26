from typing import List
from PySide6.QtCore import Qt, Signal, QEasingCurve, QUrl, QSize, QTimer
from PySide6.QtGui import QIcon, QDesktopServices, QColor
from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout, QLabel, QWidget, QHBoxLayout

from qfluentwidgets import (NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,
                            SplashScreen, SystemThemeListener, isDarkTheme, MaskDialogBase, FluentStyleSheet)
from ..common.style_sheet import StyleSheet

class DialogWidget(MaskDialogBase):
    """ Message box base """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setClosableOnMaskClicked(True)
        self.vBoxLayout = QVBoxLayout(self.widget)
        self.viewLayout = QVBoxLayout()
        self.__initWidget()

    def __initWidget(self):
        self.__setQss()
        self.__initLayout()
        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.setMaskColor(QColor(0, 0, 0, 76))

    def __initLayout(self):
        self._hBoxLayout.removeWidget(self.widget)
        self._hBoxLayout.addWidget(self.widget, 1, Qt.AlignCenter)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.viewLayout, 1)

        self.viewLayout.setSpacing(5)
        self.viewLayout.setContentsMargins(10, 10, 10, 10)

    def __setQss(self):
        FluentStyleSheet.DIALOG.apply(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.widget.setFixedSize(self.size()*0.9)
        if self.isVisible():  # 如果弹出窗口是可见的
            self.updateWindowPosition()

    def updateWindowPosition(self):
        """ 更新弹出窗口位置 """
        if self.parent():
            parent_pos = self.parent().pos()  # 获取父窗口的位置
            parent_size = self.parent().size()  # 获取父窗口的大小
            window_size = self.size()  # 获取弹出窗口的大小

            # 计算弹出窗口的中心位置
            center_x = parent_pos.x() + (parent_size.width() - window_size.width()) // 2
            center_y = parent_pos.y() + (parent_size.height() - window_size.height()) // 2

            # 设置弹出窗口的最终位置
            self.move(center_x, center_y)