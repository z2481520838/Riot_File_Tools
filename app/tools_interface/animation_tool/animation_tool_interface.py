# coding:utf-8
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout, QLabel, QWidget, QHBoxLayout, QSizePolicy, QFileDialog, QListWidgetItem
from qfluentwidgets import (ScrollArea, NavigationItemPosition, MessageBox, setTheme, Theme, FluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont, InfoBadge,
                            InfoBadgePosition, FluentBackgroundTheme, TextEdit, CardWidget, PushButton, 
                            PlainTextEdit, DropDownPushButton, RoundMenu, Action, ToolButton, ToolTipFilter, 
                            InfoBar, InfoBarPosition, InfoBarIcon, SearchLineEdit, ListWidget)
from qfluentwidgets import FluentIcon as FIF
from ...common.translator import Translator
from ...common.config import cfg
from ...common.style_sheet import StyleSheet
from ...common.trie import Trie
from ..tool_interface import ToolInterface
from ...core.objects.animation.read_anm import read_anm_file
from .child_card.animation_data_card import (Invalid_Animation_Data_Card, Blnk_Animation_Data_Card, 
                                             Compressed_Animation_Data_Card, Animation_Data_Card_V3, 
                                             Animation_Data_Card_V4, Animation_Data_Card_V5)
from ...core.function.general import get_relative_path
import os

class Animation_Tool_View(QWidget):
    """ Icon card view """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.build()

    def build(self):
        self.layout = QHBoxLayout(self)
        self.build_button(self.layout)
        self.build_file_list(self.layout)
        self.build_file_list_info(self.layout)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(12)

    def build_button(self, layout):
        self.button_layout = QVBoxLayout(self)
        self.load_button = PushButton("导入文件", self)
        self.load_button.clicked.connect(self.load_folder)
        self.load_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.button_layout.addWidget(self.load_button)
        self.button_layout.addStretch()
        self.layout.addLayout(self.button_layout)

    def build_file_list(self, layout):
        self.file_list_layout = QVBoxLayout(self)
        file_list_card = CardWidget(self)
        file_list_card.setLayout(self.file_list_layout)
        layout.addWidget(file_list_card)
        self.file_list = ListWidget(self)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义右键菜单
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键菜单事件

    def append_data_card(self, card, layout, card_list, visible=True):
        layout.addWidget(card)
        card_list.append(card)
        card.setVisible(visible)
        return card

    def build_file_list_info(self, layout):
        self.card_list = []
        self.invalid_animation_data_card = self.append_data_card(Invalid_Animation_Data_Card(self), layout, self.card_list, False)
        self.blnk_animation_data_card = self.append_data_card(Blnk_Animation_Data_Card(self), layout, self.card_list)
        self.compressed_animation_data_card = self.append_data_card(Compressed_Animation_Data_Card(self), layout, self.card_list, False)
        self.animation_data_card_v3 = self.append_data_card(Animation_Data_Card_V3(self), layout, self.card_list, False)
        self.animation_data_card_v4 = self.append_data_card(Animation_Data_Card_V4(self), layout, self.card_list, False)
        self.animation_data_card_v5 = self.append_data_card(Animation_Data_Card_V5(self), layout, self.card_list, False)

    def load_folder(self):
        # 打开文件夹选择对话框
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", "", QFileDialog.Option.ShowDirsOnly)
        if not folder:
            return

        # 获取该文件夹中的所有 .anm 文件（不对子文件夹生效）
        # anm_files = [f for f in os.listdir(folder) if f.endswith('.anm') and os.path.isfile(os.path.join(folder, f))]
        anm_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.anm') and os.path.isfile(os.path.join(folder, f))]

        if not anm_files:
            InfoBar.error("错误", "文件夹中没有 .anm 文件", parent=self)
            return
        try:
            self.update_file_list(anm_files)
            InfoBar.success(
                title="已加载文件夹: ",
                content=f"{folder} 中包含 {len(anm_files)} 个 .anm 文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
        except Exception as e:
            InfoBar.error("错误", f"文件读取失败: {e}", parent=self)
            print("错误", f"文件读取失败: {e}")

    def update_file_list(self, anm_files):
        self.file_list.clear()
        for f in anm_files:
            file_name = os.path.basename(f)
            item = QListWidgetItem(file_name)
            anm_data = self.start_read_anm_file(f)
            anm_data.file_path = f
            item.setData(Qt.UserRole, anm_data)
            self.file_list.addItem(item)
        self.file_list_layout.addWidget(self.file_list)
        self.selected_layer(self.file_list.item(0))
        self.file_list.itemClicked.connect(self.show_current_file_info)

    def selected_layer(self, item):
        self.file_list.setCurrentItem(item)
        self.show_current_file_info(item)

    def show_data_card(self, index, item):
        self.card_list[index].on_set(item)
        for i, card in enumerate(self.card_list):
            card.setVisible(i == index)

    def show_current_file_info(self, item):
        item_data = item.data(Qt.UserRole)
        header = item_data.header
        data = item_data.data
        # 判断 magic 字段是否为 "r3d2canm"
        if header.magic == "r3d2canm":
            self.show_data_card(2, item_data)
        else:
            # 使用 in 检查 version 是否为 3, 4 或 5
            if header.version in [3, 4, 5]:
                self.show_data_card(header.version, item_data)
            else:
                self.show_data_card(0, item_data)

    def start_read_anm_file(self, path):
        try:
            with open(path, 'rb') as file:
                return read_anm_file(file)
        except Exception as e:
            # 捕获异常并抛出，便于在调用时处理
            raise ValueError(f"无法加载文件 {path}: {e}")

    def show_context_menu(self, pos):
        item = self.file_list.itemAt(pos)  # 获取当前点击的项目
        if item:
            menu = RoundMenu(parent=self)  # 创建菜单
            copy_path_action = Action(FIF.COPY, 'Copy Path', self)  # 创建菜单项
            copy_path_action.triggered.connect(lambda: self.copy_path(item))  # 点击时触发
            menu.addAction(copy_path_action)  # 添加菜单项
            menu.exec_(self.file_list.mapToGlobal(pos))  # 显示菜单

    def copy_path(self, item):
        path = get_relative_path(item.data(Qt.UserRole).file_path, "DATA").lower()
        QApplication.clipboard().setText(path)
        InfoBar.success(
                title="文件路径已复制到剪切板: ",
                content=path,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )

class Animation_Tool_Interface(ToolInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(parent=parent)
        self.setObjectName('animation_Tool_Interface')

        self.view = Animation_Tool_View(self)
        self.vBoxLayout.addWidget(self.view)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)