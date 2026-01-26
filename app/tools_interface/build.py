import sys
import os
from PySide6.QtCore import Qt, QUrl, QTimer, QStringListModel, QPoint, QEvent, Slot
from PySide6.QtGui import QIcon, QDesktopServices, QFont, QTextCursor, QColor, QPixmap, QPainter, QImage, QAction
from PySide6.QtWidgets import (QWidget, QApplication, QFrame, QFileDialog, QStackedWidget, QHBoxLayout, 
                               QDialog, QSizePolicy, QCompleter, QTextEdit, QPushButton, QListWidget, 
                               QListWidgetItem, QVBoxLayout, QSplitter, QStatusBar, QHeaderView, QLabel, 
                               QLineEdit, QTreeWidget, QTreeWidgetItem, QFormLayout, QGroupBox)
from qfluentwidgets import (ScrollArea, NavigationItemPosition, MessageBox, MessageBoxBase, setTheme, Theme, FluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont, InfoBadge,
                            InfoBadgePosition, FluentBackgroundTheme, TextEdit, CardWidget, PushButton, 
                            PlainTextEdit, DropDownPushButton, RoundMenu, Action, ToolButton, ToolTipFilter, 
                            InfoBar, InfoBarPosition, InfoBarIcon, SearchLineEdit, TreeView, TreeWidget, MaskDialogBase,
                            FluentStyleSheet, PrimaryPushButton, MaskDialogBase, LineEdit, ComboBox, ListWidget, SwitchButton,
                            CheckBox, SegmentedWidget, SegmentedToggleToolWidget, SettingCard, EditableComboBox)
from qfluentwidgets import FluentIcon as FIF
from .tool_interface import ToolInterface
from ..common.translator import Translator
from ..components.wait_bar import WaitBar

def create_text_box(owner, label, layout, text=None):
    a = QHBoxLayout()
    b = QLabel(label, owner)
    b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    c = LineEdit(owner)
    if text is not None:
        c.setText(text)
    a.addWidget(b)
    a.addWidget(c)
    layout.addLayout(a)
    return c

def create_text_label(owner, text, layout):
    label = QLabel(text, owner)
    label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    layout.addWidget(label)

def create_child_card(child_card, layout, card_list = None, visible = True):
    layout.addWidget(child_card)
    if card_list is not None:
        card_list.append(child_card)
    child_card.setVisible(visible)
    return child_card

def create_combo_box_label(self, label, layout):
    combo_layout = QHBoxLayout()
    lable = QLabel(label, self)
    lable.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    combo_box = ComboBox(self)
    combo_layout.addWidget(lable)
    combo_layout.addWidget(combo_box)
    layout.addLayout(combo_layout)
    return combo_box

def create_combo_box(self, label, tip, items, layout, action):
    combo_layout = QHBoxLayout()
    lable = QLabel(label, self)
    lable.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    combo_box = ComboBox(self)
    combo_box.setPlaceholderText(tip)
    combo_box.addItems(items)
    combo_box.setCurrentIndex(-1)
    combo_box.currentTextChanged.connect(action)
    combo_layout.addWidget(lable)
    combo_layout.addWidget(combo_box)
    layout.addLayout(combo_layout)
    return combo_box

def create_button(self, label, action, layout, fixed=True, type_=0):
    button = None
    if type_ == 0:
        button = PushButton(label, self)
    else:
        button = PrimaryPushButton(label, self)
    button.clicked.connect(action)
    if fixed == True:
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    layout.addWidget(button)
    return button

def sync_window_position(window, v=1):
    window.widget.setFixedSize(window.size()*v)
    if window.isVisible() and window.parent():
        parent_pos = window.parent().pos()  # 获取父窗口的位置
        parent_size = window.parent().size()  # 获取父窗口的大小
        window_size = window.size()  # 获取弹出窗口的大小

        # 计算弹出窗口的中心位置
        center_x = parent_pos.x() + (parent_size.width() - window_size.width()) // 2
        center_y = parent_pos.y() + (parent_size.height() - window_size.height()) // 2

        # 设置弹出窗口的最终位置
        window.move(center_x, center_y)

def load_objects_to_combobox(combobox, objects, get_text=lambda o: str(o)):
    """
    向 ComboBox 加载对象列表
    combobox: 目标 ComboBox
    objects: 可迭代对象
    get_text: 从对象提取显示名称的方法（默认 str）
    """
    combobox.clear()
    for obj in objects:
        combobox.addItem(get_text(obj), userData=obj)