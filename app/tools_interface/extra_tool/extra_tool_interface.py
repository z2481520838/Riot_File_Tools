# coding:utf-8
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout, QLabel, QWidget, QHBoxLayout
from qfluentwidgets import (ScrollArea, FluentIcon, IconWidget, FlowLayout, isDarkTheme,
                            Theme, applyThemeColor, SmoothScrollArea, SearchLineEdit, StrongBodyLabel,
                            BodyLabel, TitleLabel, CardWidget, TextWrap)

from ...common.translator import Translator
from ...common.config import cfg
from ...common.style_sheet import StyleSheet
from ...common.trie import Trie
from ..tool_interface import ToolInterface
from ...components.sample_card import SampleCardView
from .hex_convert_tool import HexConvert
from .hash_convert_tool import HashConvert

class ToolCard(CardWidget):
    """ Sample card """

    def __init__(self, icon, title, content, action, index, parent=None):
        super().__init__(parent=parent)
        self.index = index
        self.clicked.connect(action)

        self.iconWidget = IconWidget(icon, self)
        self.titleLabel = QLabel(title, self)
        self.contentLabel = QLabel(TextWrap.wrap(content, 45, False)[0], self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedSize(360, 90)
        self.iconWidget.setFixedSize(48, 48)

        self.hBoxLayout.setSpacing(28)
        self.hBoxLayout.setContentsMargins(20, 0, 0, 0)
        self.vBoxLayout.setSpacing(2)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        self.hBoxLayout.setAlignment(Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.contentLabel)
        self.vBoxLayout.addStretch(1)

        self.titleLabel.setObjectName('titleLabel')
        self.contentLabel.setObjectName('contentLabel')

class ToolsCardView(QWidget):
    """ Sample card view """

    def __init__(self, title: str, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.flowLayout = FlowLayout()

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)
        self.flowLayout.setContentsMargins(0, 0, 0, 0)
        self.flowLayout.setHorizontalSpacing(12)
        self.flowLayout.setVerticalSpacing(12)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addLayout(self.flowLayout, 1)

        self.titleLabel.setObjectName('viewTitleLabel')
        StyleSheet.SAMPLE_CARD.apply(self)

    def addToolCard(self, icon, title, content, action, index):
        """ add sample card """
        card = ToolCard(icon, title, content, action, index, self)
        self.flowLayout.addWidget(card)

class ToolsView(QWidget):
    """ Icon card view """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.trie = Trie()
        self.toolLibraryLabel = TitleLabel(self.tr('Extra Tools'), self)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.addWidget(self.toolLibraryLabel)
        basicInputView = ToolsCardView("", self)
        basicInputView.addToolCard(
            ":/gallery/images/hex.png", "进制转换",
            self.tr("此工具可以将所输入的内容进行进制转换"),
            lambda: self.show_tool(HexConvert(parent)), 0)
        basicInputView.addToolCard(
            ":/gallery/images/controls/BreadcrumbBar.png", "哈希转换",
            self.tr("此工具可以将所输入的内容转换为哈希值"),
            lambda: self.show_tool(HashConvert(parent)), 0)
        self.vBoxLayout.addWidget(basicInputView)

    def show_tool(self, tool):
        tool.show()

class Extra_Tool_Interface(ToolInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(parent=parent)
        self.setObjectName('extra_Tool_Interface')
        self.toolsView = ToolsView(self)
        self.vBoxLayout.addWidget(self.toolsView)