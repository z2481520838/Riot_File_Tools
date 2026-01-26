# coding:utf-8
from typing import List
from ..build import*
import jsonpickle
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
from ...core.manager.logger.logger_manager import LOGGERMANAGER
from ...core.function.blnd.read_blnd import read_blnd
from .start_create import Start_Create
from .adjunction_data import Adjunction_Data

class Blnd_Tool_Interface(ToolInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(parent=parent)
        self.setObjectName('blnd_Tool_Interface')
        self.build()

    def build(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(12)
        self.build_button(self.layout)
        self.build_text_box(self.layout)
        self.layout.setStretch(0, 0)
        self.layout.setStretch(1, 1)

    def build_button(self, layout):
        button_layout = QVBoxLayout(self)
        self.load_btn = create_button(self, "导入文件", self.load_file_from_dialog, button_layout, True, 0)
        self.show_obj_btn = create_button(self, "展示参数", self.show_obj, button_layout, True, 0)
        self.export_t_btn = create_button(self, "导出文本", self.export_text, button_layout, True, 0)
        self.export_f_btn = create_button(self, "导出文件", self.export_file, button_layout, True, 0)
        self.create_btn = create_button(self, "创建文件", self.create_blnd, button_layout, True, 1)
        self.export_c_btn = create_button(self, "保存项目", self.export_create, button_layout, True, 1)
        self.export_p_btn = create_button(self, "打开路径", self.open_path, button_layout, True, 1)
        self.new_project_btn = create_button(self, "新建项目", self.new_project, button_layout, True, 1)
        self.add_data_btn = create_button(self, "添加数据", self.add_data, button_layout, True, 1)
        self.examine_file_btn = create_button(self, "检查文件", self.examine_file, button_layout, True, 1)
        self.add_data_btn2 = create_button(self, "添加条目", self.adjunction_data, button_layout, True, 1)
        self.load_data_btn = create_button(self, "导入数据", self.load_data, button_layout, True, 1)
        self.save_data_btn = create_button(self, "保存数据", self.save_data, button_layout, True, 1)

        button_layout.addStretch()
        layout.addLayout(button_layout)
        # self.layout.addStretch()

    def build_text_box(self, layout):
        text_box_layout = QVBoxLayout(self)
        text_box_layout.setContentsMargins(0, 0, 0, 0)
        self.outputBox = PlainTextEdit(self)
        self.outputBox.setPlaceholderText("解析结果将在这里显示...")
        self.outputBox.setReadOnly(True)
        text_box_layout.addWidget(self.outputBox)
        layout.addLayout(text_box_layout)

    def load_file_from_dialog(self):
        last_blnd_file = LOGGERMANAGER.get("blnd_file")
        default_directory = "" if last_blnd_file is None else last_blnd_file
        file, _ = QFileDialog.getOpenFileName(self, "选择文件", default_directory, "Blnd Files (*.blnd)")
        self.load_file(file)

    def load_file(self, file):
        if not file:
            return
        try:
            LOGGERMANAGER.save("blnd_file", file)
            self.load_blnd_file(file)
            InfoBar.success("成功", f"已加载文件: {file}", parent=self)
        except Exception as e:
            InfoBar.error("错误", f"文件读取失败: {e}", parent=self)
            print("错误", f"文件读取失败: {e}")

    def load_blnd_file(self, path):
        with open(path, 'rb') as file:
            self.current_blnder_data = read_blnd(file)
            self.current_blnder_data.file_name = path
            self.current_blnder_data.pool.sync_data()
            self.show_blnd_data(self.current_blnder_data)

    def show_blnd_data(self, blnder_data):
        self.outputBox.setPlainText(jsonpickle.dumps(blnder_data, False, indent=4))

    def show_obj(self):
        pass

    def export_text(self):
        pass

    def export_file(self):
        pass

    def create_blnd(self):
        pass

    def export_create(self):
        # 这里选择导出的路径
        current_skin_path = LOGGERMANAGER.get("current_skin_path")
        default_directory = "" if not os.path.exists(current_skin_path) else current_skin_path
        filepath, _ = QFileDialog.getSaveFileName(self, "保存 Blnd 文件", default_directory, "Blnd Files (*.blnd)")
        if not filepath:
            return
        try:
            with open(filepath, 'wb') as file:
                self.current_blnder_data.write(file)
            InfoBar.success("导出文件成功", f"{filepath}", parent=self)
        except Exception as e:
            InfoBar.error("错误", f"文件导出失败: {e}", parent=self)
            print("错误", f"文件导出失败: {e}")

    def open_path(self):
        pass

    def new_project(self):
        self.start_create = Start_Create(self)
        self.start_create.show()

    def add_data(self):
        pass

    def examine_file(self):
        pass

    def adjunction_data(self):
        if hasattr(self, 'current_blnder_data'):
            self.adjunction_data_window = Adjunction_Data(self)
            self.adjunction_data_window.show()
        else:
            InfoBar.warning("提示", "请先创建项目", parent=self)

    def load_data(self):
        default_directory = LOGGERMANAGER.get_pkl_path()
        filepath, _ = QFileDialog.getOpenFileName(self, "导入序列化数据", default_directory, "JSON 文件 (*.json)")
        if not filepath:
            return
        try:
            with open(filepath, "r") as f:
                json_data = LOGGERMANAGER.load_json(f.read())
                self.current_blnder_data = json_data.data
            self.current_blnder_data.pool.sync_data()
            self.show_blnd_data(self.current_blnder_data)
            self.load_anm_path(json_data.path)
            InfoBar.success("已加载序列化数据:", f"{filepath}", parent=self)
        except Exception as e:
            InfoBar.error("错误", f"序列化数据载入失败: {e}", parent=self)
            print("错误", f"序列化数据载入失败: {e}")

    def load_anm_path(self, folder):
        if not folder:
            return

        # 获取该文件夹中的所有 .anm 文件（不对子文件夹生效）
        # anm_files = [f for f in os.listdir(folder) if f.endswith('.anm') and os.path.isfile(os.path.join(folder, f))]
        anm_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.anm') and os.path.isfile(os.path.join(folder, f))]

        if not anm_files:
            InfoBar.warning("警告", "文件夹中没有 .anm 文件", parent=self)
            return
        try:
            LOGGERMANAGER.save("animations_path", folder)
            self.anm_files = anm_files
            InfoBar.success("已加载文件夹: ", f"{folder} 中包含 {len(anm_files)} 个 .anm 文件", parent=self)
        except Exception as e:
            InfoBar.error("错误", f"文件读取失败: {e}", parent=self)

    def save_data(self):
        skl_path = self.current_blnder_data.pool.mSkeleton.Path
        skl_name = os.path.basename(skl_path)
        default_directory = LOGGERMANAGER.get_pkl_path()
        pkl_name = os.path.splitext(os.path.join(default_directory, skl_name))[0]
        filepath, _ = QFileDialog.getSaveFileName(self, "保存序列化数据", pkl_name, "JSON 文件 (*.json)")
        if not filepath:
            return
        with open(filepath, "w") as f:
            LOGGERMANAGER.save_json(self.current_blnder_data, f)
