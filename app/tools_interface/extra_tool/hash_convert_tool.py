import sys

from PySide6.QtCore import Qt, QUrl, QTimer, QStringListModel
from PySide6.QtGui import QIcon, QDesktopServices, QFont, QTextCursor
from PySide6.QtWidgets import QWidget, QApplication, QFrame, QHBoxLayout, QCompleter, QSizePolicy, QCheckBox, QTextEdit, QRadioButton, QPushButton, QVBoxLayout, QSplitter, QStatusBar, QLabel, QLineEdit
from qfluentwidgets import (ScrollArea, NavigationItemPosition, MessageBoxBase, MessageBox, setTheme, Theme, FluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont, InfoBadge,
                            InfoBadgePosition, FluentBackgroundTheme, TextEdit, CardWidget, PushButton, 
                            PlainTextEdit, DropDownPushButton, RoundMenu, Action, ToolButton, ToolTipFilter, 
                            InfoBar, InfoBarPosition, InfoBarIcon, SearchLineEdit, LineEdit, SplitPushButton, RadioButton)
from ...components.dialog_widget import DialogWidget

class HashConvert(DialogWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ExtraTools_02")
        self.build()

    def build(self):
        pass
