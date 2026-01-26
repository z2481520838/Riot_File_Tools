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

class HexConvert(DialogWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ExtraTools_01")
        self.initmain()

    def initmain(self):
        # 输入进制选择（复选框，互斥）
        self.base_radio_buttons = {}
        self.radio_layout = QHBoxLayout()

        # 创建复选框，供选择输入的进制
        for base in [2, 8, 10, 16, 26, 32, 36, 52, 58, 62]:
            radio_button = RadioButton(f"{base}进制", self)
            if base == 10:
                radio_button.setChecked(True)  # 默认选择十进制
            radio_button.clicked.connect(self.update_output)
            self.base_radio_buttons[base] = radio_button
            self.radio_layout.addWidget(radio_button)
        # 进制选择下拉菜单（更多进制）
        self.base_selector = SplitPushButton("更多", self)
        self.menu = RoundMenu(parent=self)
        # 为下拉菜单添加多个进制选择
        self.menu.addAction(Action(self.tr("更多"), triggered=lambda  c=True, b=self.base_selector: b.setText(self.tr("更多"))))
        self.menu.addAction(Action(self.tr("60进制"), triggered=lambda  c=True, b=self.base_selector: b.setText(self.tr("60进制"))))
        self.menu.addAction(Action(self.tr("61进制"), triggered=lambda  c=True, b=self.base_selector: b.setText(self.tr("61进制"))))
        self.base_selector.setFlyout(self.menu)

        # 输入框
        self.input_layout = QHBoxLayout()
        self.inputBox = LineEdit(self)
        self.inputBox.setPlaceholderText("请输入数字（选择进制后输入）...")
        self.inputBox.textChanged.connect(self.update_output)
        self.input_layout.addWidget(self.inputBox)

        # 输出框（为每个进制单独显示一个输出框）
        self.output_layout = QVBoxLayout()
        self.output_widgets = {}

        for base in [2, 8, 10, 16, 26, 32, 36, 52, 58, 62]:
            output_box = LineEdit(self)
            output_box.setPlaceholderText(f"{base}进制转换结果...")
            output_box.setReadOnly(True)
            self.output_widgets[base] = output_box
            self.output_layout.addWidget(output_box)
            self.output_layout.addSpacing(20)  # 添加 5px 间隔

        # 按钮区（转换和清空）
        self.convert_button = PushButton("转换", self)
        self.convert_button.clicked.connect(self.convert_number)
        self.clear_button = PushButton("清空", self)
        self.clear_button.clicked.connect(self.clear_input)
        self.input_layout.addWidget(self.convert_button)
        self.input_layout.addWidget(self.clear_button)
        # 布局管理
        self.radio_layout.addWidget(self.base_selector)
        self.viewLayout.addLayout(self.radio_layout)
        self.viewLayout.addLayout(self.input_layout)
        self.viewLayout.addStretch()
        self.viewLayout.addLayout(self.output_layout)
        self.viewLayout.addStretch()

    def parse_input(self, value: str, base: int) -> int:
        """将字符串解析为十进制，支持大于36进制"""
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+/"
        
        if base > len(digits):
            raise ValueError(f"暂不支持 {base} 进制（最大支持 {len(digits)}）")
        
        value = value.strip().upper()  # 大小写统一
        result = 0
        for char in value:
            if char not in digits[:base]:
                raise ValueError(f"非法字符 {char} 对于 {base} 进制")
            result = result * base + digits.index(char)
        return result

    def convert_number(self, base=10):
        """将输入的数字转换为不同进制"""
        # 获取选择的输入进制
        input_base = self.get_input_base()
        
        # 获取输入的数值
        input_value = self.inputBox.text().strip()

        try:
            # 将输入的数值根据选择的输入进制转换为十进制
            decimal_value = self.parse_input(input_value, input_base)

            # 转换为目标进制并更新每个输出框
            for base in self.output_widgets.keys():
                converted_value = self.convert_to_base(decimal_value, base)
                # 更新对应进制的输出框
                self.output_widgets[base].setText(f"{base}进制：{converted_value}")

        except ValueError:
            self.clear_input()
    def select_base_from_menu(self, base):
        """选择下拉菜单中的进制，取消复选框的选中状态"""
        # 取消所有复选框的选中状态
        for radio_button in self.base_radio_buttons.values():
            radio_button.setChecked(False)
        
        # 根据下拉菜单选择的进制进行设置
        for radio_button in self.base_radio_buttons.values():
            if base == int(radio_button.text().split('进制')[0]):
                radio_button.setChecked(True)
        
        # 更新输出
        self.update_output()

    def convert_to_base(self, num, base):
        """将十进制数字转换为指定进制"""
        if base == 10:
            return str(num)
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        result = ""
        while num > 0:
            result = digits[num % base] + result
            num = num // base
        return result

    def get_input_base(self):
        """根据选择的复选框获取输入进制"""
        # 获取下拉菜单选择的进制
        menu_selected_base = self.base_selector.text()
        # print(menu_selected_base)
        if menu_selected_base != "更多":
            print(menu_selected_base.split('进制')[0])
            return int(menu_selected_base.split('进制')[0])  # 返回下拉菜单中选中的进制
        
        # 获取复选框选中的进制
        for base, radio_button in self.base_radio_buttons.items():
            if radio_button.isChecked():
                return base
                print(f"{base}")
        return 10  # 默认使用十进制

    def update_output(self):
        """当输入框内容改变时，更新转换结果"""
        input_value = self.inputBox.text().strip()  # 获取输入框内容并去掉前后空格
        
        if input_value:  # 只有在输入框有内容时才进行转换
            self.convert_number()
        else:
            return

    def clear_input(self):
        """清空输入框和输出框"""
        self.inputBox.clear()
        for output_box in self.output_widgets.values():
            output_box.clear()