# coding:utf-8
from typing import List

from PySide6.QtCore import Qt, QUrl, QTimer, QStringListModel
from PySide6.QtGui import QIcon, QDesktopServices, QFont, QTextCursor
from PySide6.QtWidgets import QWidget, QFileDialog, QApplication, QFrame, QHBoxLayout, QCompleter, QTextEdit, QPushButton, QVBoxLayout, QSplitter, QStatusBar, QLabel, QLineEdit
from qfluentwidgets import (ScrollArea, NavigationItemPosition, MessageBox, setTheme, Theme, FluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont, InfoBadge,
                            InfoBadgePosition, FluentBackgroundTheme, TextEdit, CardWidget, PushButton, 
                            PlainTextEdit, DropDownPushButton, RoundMenu, Action, ToolButton, ToolTipFilter, 
                            InfoBar, InfoBarPosition, InfoBarIcon, SearchLineEdit)
from qfluentwidgets import FluentIcon as FIF
from ...common.icon import Icon
from ...common.translator import Translator
from ...common.config import cfg
from ...common.style_sheet import StyleSheet
from ...common.trie import Trie
from ..tool_interface import ToolInterface
from ...core.function.prop_text.parser import parse_prop_text, format_obj
from ...core.function.prop_text.interaction import export_file, export_all_file, copy_output, clear_input
from .prop_data_tree_widget import PropData_TreeWidget

class Prop_Text_Tool_View(QWidget):
    """ Icon card view """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.build()

    def build(self):
        self.layout = QVBoxLayout(self)
        self.build_button(self.layout)
        self.build_text_box(self.layout)
        self.layout.setStretch(0, 0)  # 按钮区不拉伸
        self.layout.setStretch(1, 1)  # 文本区占剩余空间
        self.current_prop = None
        paste_timer = self.setup_auto_convert()

    def build_text_box(self, layout):
        text_box_layout = QVBoxLayout(self)
        text_box_layout.setContentsMargins(0, 0, 0, 0)

        self.inputBox = PlainTextEdit(self)
        self.outputBox = PlainTextEdit(self)
        self.inputBox.setPlaceholderText("在这里输入要解析的文本...")
        self.outputBox.setPlaceholderText("解析结果将在这里显示...")
        self.outputBox.setReadOnly(True)

        splitter = QSplitter(Qt.Horizontal, self)
        # splitter.setStyleSheet("background-color: transparent; border: none;")
        splitter.addWidget(self.inputBox)
        splitter.addWidget(self.outputBox)
        splitter.setSizes([500, 500])  # 默认比例，输入框小一点，输出框大一点

        text_box_layout.addWidget(splitter)
        layout.addLayout(text_box_layout)

    def build_button(self, layout):
        button_layout = QHBoxLayout(self)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.loadFilebutton = PushButton(FIF.FOLDER, '载入文件', self)

        # 带菜单栏的预览按钮
        # 1. 创建菜单
        vive_menu = RoundMenu(parent=self)
        # 2. 创建动作，并绑定槽函数
        action_preview_param = Action(FIF.DOCUMENT, '预览参数', self)
        action_preview_convert = Action(FIF.SYNC, '预览转换', self)
        action_view_obj = Action(FIF.SYNC, '展示参数', self)
        action_preview_param.triggered.connect(self.view_value)
        action_preview_convert.triggered.connect(self.convert_text)
        action_view_obj.triggered.connect(self.show_data_tree)
        # 3. 添加到菜单
        vive_menu.addAction(action_preview_param)
        vive_menu.addAction(action_preview_convert)
        vive_menu.addAction(action_view_obj)
        # 4. 创建按钮，并挂菜单
        self.vive_button_menu = DropDownPushButton(FIF.VIEW, '预览内容', self)
        self.vive_button_menu.setMenu(vive_menu)

        # 带菜单栏的导出按钮
        export_button_menu = RoundMenu(parent=self)
        action_export = Action(FIF.DICTIONARY, '混合导出', self)
        action_export_all = Action(FIF.DICTIONARY_ADD, '逐个导出', self)
        action_export.triggered.connect(lambda: export_file(self))
        action_export_all.triggered.connect(lambda: export_all_file(self))
        export_button_menu.addAction(action_export)
        export_button_menu.addAction(action_export_all)
        self.exportFilebutton = DropDownPushButton(FIF.SAVE, '导出文件', self)
        self.exportFilebutton.setMenu(export_button_menu)

        self.coptbutton = PushButton(FIF.COPY, '复制结果', self)
        self.clearbutton = PushButton(FIF.ERASE_TOOL, '清空内容', self)

        self.loadFilebutton.clicked.connect(self.load_file)
        self.coptbutton.clicked.connect(lambda: copy_output(self))
        self.clearbutton.clicked.connect(lambda: clear_input(self))

        button_layout.addWidget(self.loadFilebutton)
        button_layout.addWidget(self.vive_button_menu)
        button_layout.addWidget(self.exportFilebutton)
        button_layout.addStretch()
        button_layout.addWidget(self.coptbutton)
        button_layout.addWidget(self.clearbutton)
        layout.addLayout(button_layout)

    def show_data_tree(self):
        if not self.current_prop:
            InfoBar.info("提示:", "输入为空，无法预览", parent=self)
            return
        try:
            tree = PropData_TreeWidget(self)  # 创建PropViewer窗口
            tree.show()  # 显示窗口
            tree.showPropAsTree(self.current_prop)  # 展示数据
            InfoBar.success("完成:", "参数已展示", parent=self)
        except Exception as e:
            InfoBar.error("错误:", f"{e}", parent=self)

    def view_value(self):
        self.outputBox.clear()
        if not self.current_prop:
            InfoBar.info("提示:", "输入为空，无法预览", parent=self)
            return
        try:
            serialize = format_obj(self.current_prop)
            self.outputBox.setPlainText(serialize)
            InfoBar.success("完成:", "参数已展示", parent=self)
        except Exception as e:
            InfoBar.error("错误:", "{e}", parent=self)

    def load_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "选择 PROP 文件", "", "All Files (*.*)")
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            self.inputBox.setPlainText(text)
            InfoBar.success("已载入文件:", f"{filepath}", parent=self)
        except Exception as e:
            InfoBar.error("文件读取失败:", f"{e}", parent=self)

    def convert_text(self):
        if not self.current_prop:
            InfoBar.info("提示:", "输入为空，无法转换", parent=self)
            return
        try:
            out_text = self.current_prop.to_custom_format(False)
            self.outputBox.setPlainText(out_text)
            InfoBar.success("成功", "文本已转换", parent=self)
        except Exception as e:
            self.outputBox.clear()
            InfoBar.error("错误:", f"{e}", parent=self)

    def setup_auto_convert(self, timer_interval=100):
        """设置输入框自动触发转换"""
        paste_timer = QTimer()
        paste_timer.setSingleShot(True)

        def convert_wrapper():
            text = self.inputBox.toPlainText().strip()
            if not text:
                self.outputBox.clear()
                self.current_prop = None
                return
            self.current_prop = parse_prop_text(text)
            self.convert_text()

        paste_timer.timeout.connect(convert_wrapper)
        self.inputBox.textChanged.connect(lambda: paste_timer.start(timer_interval))
        return paste_timer

class Prop_Text_Tool_Interface(ToolInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(parent=parent)
        self.setObjectName('prop_Text_Tool_Interface')

        self.view = Prop_Text_Tool_View(self)
        self.vBoxLayout.addWidget(self.view)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
