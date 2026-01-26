from PySide6.QtCore import Qt, QByteArray, QRunnable, QThreadPool
from PySide6.QtWidgets import QMenu, QFrame, QVBoxLayout, QApplication, QLabel, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QInputDialog, QSizePolicy, QSpacerItem, QWidget, QListWidget, QListWidgetItem
from PySide6.QtGui import QPixmap, QPainter, QColor, QImage, QAction
from qfluentwidgets import Action, RoundMenu, ComboBox, PrimaryPushButton, CardWidget, PlainTextEdit, CheckBox, InfoBar, InfoBarPosition, MessageBoxBase, LineEdit, PushButton, ListWidget, PlainTextEdit
from io import BytesIO
from qfluentwidgets import FluentIcon as FIF
from dataclasses import is_dataclass, fields
import os

def cerate_tabel(name, info, layout):
    label = QLabel(info)
    layout.addRow(name, label)
    return label

class Invalid_Animation_Data_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.setFixedWidth(300)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.build()

    def build(self):
        info_group = QGroupBox(self)
        info_group.setTitle("属性")
        form_layout = QFormLayout(info_group)
        cerate_tabel("Tips: ", "Invalid File Version", form_layout)
        self.layout.addWidget(info_group)

    def on_set(self, item):
        pass

class Blnk_Animation_Data_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.setFixedWidth(300)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.build()

    def build(self):
        info_group = QGroupBox(self)
        info_group.setTitle("属性")
        form_layout = QFormLayout(info_group)
        cerate_tabel("文件名称", "未选择", form_layout)
        self.layout.addWidget(info_group)

    def on_set(self, item):
        pass

class Compressed_Animation_Data_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.setFixedWidth(300)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.build()

    def build(self):
        info_group = QGroupBox(self)
        info_group.setTitle("属性")
        form_layout = QFormLayout(info_group)
        self.magic_info = cerate_tabel("magic", "", form_layout)
        self.version_info = cerate_tabel("version", "", form_layout)
        self.resourceSize_info = cerate_tabel("resourceSize", "", form_layout)
        self.formatToken_info = cerate_tabel("formatToken", "", form_layout)
        self.flags_info = cerate_tabel("flags", "", form_layout)
        self.jointCount_info = cerate_tabel("jointCount", "", form_layout)
        self.frameCount_info = cerate_tabel("frameCount", "", form_layout)
        self.endframe_info = cerate_tabel("endframe", "", form_layout)
        self.jumpCacheCount_info = cerate_tabel("jumpCacheCount", "", form_layout)
        self.duration_info = cerate_tabel("duration", "", form_layout)
        self.FrameDuration_info = cerate_tabel("FrameDuration", "", form_layout)
        self.tickDuration_info = cerate_tabel("tickDuration", "", form_layout)
        self.translationMin_info = cerate_tabel("translationMin", "", form_layout)
        self.translationMax_info = cerate_tabel("translationMax", "", form_layout)
        self.scaleMin_info = cerate_tabel("scaleMin", "", form_layout)
        self.scaleMax_info = cerate_tabel("scaleMax", "", form_layout)
        self.layout.addWidget(info_group)

    def on_set(self, item):
        header = item.header
        data = item.data
        self.magic_info.setText(f"{header.magic}")
        self.version_info.setText(f"{header.version}")
        self.resourceSize_info.setText(f"{data.resourceSize}")
        self.formatToken_info.setText(f"{data.formatToken}")
        self.flags_info.setText(f"{data.flags}")
        self.jointCount_info.setText(f"{data.jointCount}")
        self.frameCount_info.setText(f"{data.frameCount}")
        self.endframe_info.setText(f"{round(data.duration/0.03333334, 1)}")
        self.jumpCacheCount_info.setText(f"{data.jumpCacheCount}")
        self.duration_info.setText(f"{round(data.duration, 7)}")
        self.FrameDuration_info.setText(f"{data.FrameDuration}")
        self.tickDuration_info.setText(f"{round(1/data.FrameDuration, 7)}")
        self.translationMin_info.setText(f"{round(data.translationMin.x, 3)}, {round(data.translationMin.y, 3)}, {round(data.translationMin.z, 3)}")
        self.translationMax_info.setText(f"{round(data.translationMax.x, 3)}, {round(data.translationMax.y, 3)}, {round(data.translationMax.z, 3)}")
        self.scaleMin_info.setText(f"{round(data.scaleMin.x, 3)}, {round(data.scaleMin.y, 3)}, {round(data.scaleMin.z, 3)}")
        self.scaleMax_info.setText(f"{round(data.scaleMax.x, 3)}, {round(data.scaleMax.y, 3)}, {round(data.scaleMax.z, 3)}")

class Animation_Data_Card_V3(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.setFixedWidth(300)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.build()

    def build(self):
        info_group = QGroupBox(self)
        info_group.setTitle("属性")
        form_layout = QFormLayout(info_group)
        self.magic_info = cerate_tabel("magic", "", form_layout)
        self.version_info = cerate_tabel("version", "", form_layout)
        self.skeletonId_info = cerate_tabel("skeletonId", "", form_layout)
        self.trackCount_info = cerate_tabel("trackCount", "", form_layout)
        self.frameCount_info = cerate_tabel("frameCount", "", form_layout)
        self.endframe_info = cerate_tabel("endframe", "", form_layout)
        self.frameduration_info = cerate_tabel("FrameDuration", "", form_layout)
        self.layout.addWidget(info_group)

    def on_set(self, item):
        header = item.header
        data = item.data
        self.magic_info.setText(f"{header.magic}")
        self.version_info.setText(f"{header.version}")
        self.skeletonId_info.setText(f"{data.skeletonId}")
        self.trackCount_info.setText(f"{data.trackCount}")
        self.frameCount_info.setText(f"{data.frameCount}")
        self.endframe_info.setText(f"{data.frameCount - 1}")
        self.frameduration_info.setText(f"{data.FrameDuration}")

class Animation_Data_Card_V4(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.setFixedWidth(300)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.build()

    def build(self):
        info_group = QGroupBox(self)
        info_group.setTitle("属性")
        form_layout = QFormLayout(info_group)
        self.magic_info = cerate_tabel("magic", "", form_layout)
        self.version_info = cerate_tabel("version", "", form_layout)
        self.resourceSize_info = cerate_tabel("resourceSize", "", form_layout)
        self.formatToken_info = cerate_tabel("formatToken", "", form_layout)
        self.version_s_info = cerate_tabel("version_s", "", form_layout)
        self.flags_info = cerate_tabel("flags", "", form_layout)
        self.trackCount_info = cerate_tabel("trackCount", "", form_layout)
        self.frameCount_info = cerate_tabel("frameCount", "", form_layout)
        self.endframe_info = cerate_tabel("endframe", "", form_layout)
        self.FrameDuration_info = cerate_tabel("FrameDuration", "", form_layout)
        self.layout.addWidget(info_group)

    def on_set(self, item):
        header = item.header
        data = item.data
        self.magic_info.setText(f"{header.magic}")
        self.version_info.setText(f"{header.version}")
        self.resourceSize_info.setText(f"{data.resourceSize}")
        self.formatToken_info.setText(f"{data.formatToken}")
        self.version_s_info.setText(f"{data.version_s}")
        self.flags_info.setText(f"{data.flags}")
        self.trackCount_info.setText(f"{data.trackCount}")
        self.frameCount_info.setText(f"{data.frameCount}")
        self.endframe_info.setText(f"{data.frameCount - 1}")
        self.FrameDuration_info.setText(f"{data.FrameDuration}")

class Animation_Data_Card_V5(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.setFixedWidth(300)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.build()

    def build(self):
        info_group = QGroupBox(self)
        info_group.setTitle("属性")
        form_layout = QFormLayout(info_group)
        self.magic_info = cerate_tabel("magic", "", form_layout)
        self.version_info = cerate_tabel("version", "", form_layout)
        self.resourceSize_info = cerate_tabel("resourceSize", "", form_layout)
        self.formatToken_info = cerate_tabel("formatToken", "", form_layout)
        self.version_s_info = cerate_tabel("version_s", "", form_layout)
        self.flags_info = cerate_tabel("flags", "", form_layout)
        self.trackCount_info = cerate_tabel("trackCount", "", form_layout)
        self.framesPerTrack_info = cerate_tabel("framesPerTrack", "", form_layout)
        self.endframe_info = cerate_tabel("endframe", "", form_layout)
        self.FrameDuration_info = cerate_tabel("FrameDuration", "", form_layout)
        self.layout.addWidget(info_group)

    def on_set(self, item):
        header = item.header
        data = item.data
        self.magic_info.setText(f"{header.magic}")
        self.version_info.setText(f"{header.version}")
        self.resourceSize_info.setText(f"{data.resourceSize}")
        self.formatToken_info.setText(f"{data.formatToken}")
        self.version_s_info.setText(f"{data.version_s}")
        self.flags_info.setText(f"{data.flags}")
        self.trackCount_info.setText(f"{data.trackCount}")
        self.framesPerTrack_info.setText(f"{data.framesPerTrack}")
        self.endframe_info.setText(f"{data.framesPerTrack - 1}")
        self.FrameDuration_info.setText(f"{data.FrameDuration}")
