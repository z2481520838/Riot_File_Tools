# coding: utf-8
"""NavGrid 绘制对象选项对话框(重建缺失模块 — 修复 main 分支断裂导入)。

上游 6f14ebe(Implement drawing object in navgrid view) 提交在
navgrid_tool_interface.py 引入了本模块引用, 但文件未随提交入库,
导致整个应用 MainWindow 实例化即 ImportError。本重建按
navgrid_export_options.py 同构模式实现: 逐层渲染
(visionPathing/riverRegion/jungleQuadrant/mainRegion/nearestLane/
poi/ring/srx 标志层 + 高度采样层 + 全图布局) → QImage → 导出
PNG/BMP。渲染函数直接复用 core.function.navgrid.draw_navgrid
(与 NavGrid 工具的层语义一致)。"""
import os

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFileDialog
from PySide6.QtGui import QImage

from qfluentwidgets import CardWidget, InfoBar

from ..build import (create_button, create_text_label, create_text_box,
                     create_combo_box_label, sync_window_position)
from ...components.dialog_widget import DialogWidget
from ...core.manager.logger.logger_manager import LOGGERMANAGER
from ...core.function.navgrid.draw_navgrid import (
    render_cell_flags, render_height_samples, render_all_map_layout)

# 可绘制层(标志属性名 → 展示名; 与 draw_navgrid.render_all_map_layout 序一致)
_LAYERS = [
    ('visionPathingFlags', '视野/寻路标志 visionPathing'),
    ('riverRegionFlags', '河流区域 riverRegion'),
    ('jungleQuadrantFlags', '野区象限 jungleQuadrant'),
    ('mainRegionFlags', '主区域 mainRegion'),
    ('nearestLaneFlags', '最近分路 nearestLane'),
    ('poiFlags', '兴趣点 poi'),
    ('ringFlags', '环形区域 ring'),
    ('srxFlags', 'SRX 扩展 srx'),
    ('height_samples', '高度采样 height'),
    ('all_layout', '全图布局叠加 all'),
]


class DrawObjects_Card(CardWidget):
    """绘制层选择卡(层下拉 + 导出路径/文件名)。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()

    def build(self):
        layer_row = QHBoxLayout(self)
        self.layer_box = create_combo_box_label(self, "Layer:", layer_row)
        for key, label in _LAYERS:
            self.layer_box.addItem(label, userData=key)
        self.layer_box.setCurrentIndex(0)
        self.layout.addLayout(layer_row)
        self.build_path_label(self.layout)
        name_row = QHBoxLayout(self)
        self.name_label = create_text_box(self, "Name:", name_row)
        try:
            nav = self.parent().parent().current_navgrid_data
            base = os.path.splitext(os.path.basename(
                getattr(nav, 'filename', 'navgrid') or 'navgrid'))[0]
            self.name_label.setText(base + "_draw")
        except Exception:
            self.name_label.setText('navgrid_draw')
        self.layout.addLayout(name_row)
        self.layout.addStretch()
        create_text_label(self, "Tips: 图层按 draw_navgrid 逐层栅格化, "
                              "输出 PNG(1 像素/格, 上北下南).", self.layout)

    def build_path_label(self, layout):
        self.path_label = create_text_box(self, "Path:", layout)
        select_path_button = create_button(self, "Select Path", self.select_path,
                                           layout.itemAt(0), True, 1)
        try:
            last_dir = LOGGERMANAGER.split_path('aimesh_ngrid_file')[0]
        except Exception:
            last_dir = ''
        self.path_label.setText(last_dir or os.getcwd())

    def select_path(self):
        last_dir = LOGGERMANAGER.split_path('aimesh_ngrid_file')[0]
        folder = QFileDialog.getExistingDirectory(
            self, "选择文件夹", last_dir or '', QFileDialog.Option.ShowDirsOnly)
        if not folder:
            return
        try:
            self.path_label.setText(folder)
        except Exception as e:
            InfoBar.error("错误", f"{e}", parent=self)


class NavGrid_DrawObjects_Options(DialogWidget):
    """绘制对象选项(层选择 → 渲染 QImage → 导出)。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.build()

    def build(self):
        create_text_label(self, "DrawObjectsOptions:", self.viewLayout)
        self.options_card = DrawObjects_Card(self)
        self.viewLayout.addWidget(self.options_card)
        self.build_button(self.viewLayout)

    def build_button(self, layout):
        button_layout = QHBoxLayout(self)
        export_button = create_button(self, "Draw", self.draw_action,
                                       button_layout, False, 1)
        cancel_button = create_button(self, "Cancel", self.reject,
                                       button_layout, False)
        layout.addLayout(button_layout)

    def _navgrid(self):
        try:
            return self.parent().current_navgrid_data
        except Exception:
            return None

    def draw_action(self):
        nav = self._navgrid()
        if nav is None:
            InfoBar.warning("Tips", "请先导入 aimesh_ngrid 文件", parent=self)
            return
        key = self.options_card.layer_box.currentData()
        try:
            if key == 'all_layout':
                imgs = render_all_map_layout(nav)
            elif key == 'height_samples':
                imgs = [render_height_samples(nav.height_samples)]
            else:
                imgs = [render_cell_flags(nav, key)]
        except Exception as e:
            InfoBar.error("渲染失败", f"{e}", parent=self)
            return
        file_path = self.options_card.path_label.text()
        file_name = self.options_card.name_label.text() or 'navgrid_draw'
        saved = []
        for i, img in enumerate(imgs):
            out = os.path.join(file_path,
                               '%s_%02d.png' % (file_name, i + 1)
                               if len(imgs) > 1 else file_name + '.png')
            try:
                if isinstance(img, QImage):
                    img.save(out, 'PNG')
                    saved.append(out)
            except Exception:
                pass
        if saved:
            InfoBar.success("已绘制", "导出 %d 张图层图(%s)"
                            % (len(saved), os.path.basename(saved[0])),
                            parent=self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        sync_window_position(self, 0.5)
