import sys
import threading
import time # 用于模拟耗时操作
import numpy as np
from typing import List, Any, Callable
from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtGui import QPixmap, QPainter, QColor, QImage, QAction
from ...objects.general import Color
from ...objects.navgrid.navgrid_cell import (NavGridCell, VisionPathingFlags, RiverRegionFlags, 
                                             JungleQuadrantFlags, MainRegionFlags, NearestLaneFlags,
                                             POIFlags, RingFlags, UnknownSRXFlags, CellMap, HeightSampleVector, HeightSampleMap)

walkableColor = Color(255, 255, 255)
brushColor = Color(0, 122, 14)
wallColor = Color(64, 64, 64)
brushWallColor = Color(0, 216, 111)
transparentWallColor = Color(0, 210, 214)
alwaysVisibleColor = Color(192, 192, 0)
blueTeamOnlyColor = Color(87, 79, 255)
redTeamOnlyColor = Color(255, 124, 124)
neutralZoneVisibilityColor = Color(255, 165, 0)
blueTeamNeutralZoneVisibilityColor = Color(12, 0, 255)
redTeamNeutralZoneVisibilityColor = Color(255, 0, 0)
heightSampleBaseColor = Color(255, 0, 0)
flag_colors = [
    Color(64, 0, 0),
    Color(140, 0, 0),
    Color(240, 0, 0),
    Color(0, 100, 0),
    Color(0, 240, 0),
    Color(0, 0, 100),
    Color(0, 0, 240),
    Color(100, 0, 100),
    Color(240, 0, 240),
    Color(140, 140, 0),
    Color(240, 240, 0),
    Color(0, 140, 140),
    Color(0, 240, 240),
    Color(64, 64, 64),
    Color(160, 160, 160),
    Color(240, 240, 240)
]

def check_river_region_flag(flags, flag):
    """检查指定的标志位是否设置"""
    return (flags | flag) == flags

def get_region_flag_color(flags):
    """根据 flags 计算并返回对应的颜色"""
    index = 0

    if check_river_region_flag(flags, RiverRegionFlags.JungleQuadrant):
        index |= 1

    if check_river_region_flag(flags, RiverRegionFlags.BaronPit):
        index |= 2

    if check_river_region_flag(flags, RiverRegionFlags.River):
        index |= 4

    if check_river_region_flag(flags, RiverRegionFlags.RiverEntrance):
        index |= 8

    if check_river_region_flag(flags, RiverRegionFlags.Unknown32):
        # 如果标志为 Unknown32，则添加第 16 位
        index |= 16

    return get_cell_flag_color(index)

def get_cell_flag_color(index):
    if index >= len(flag_colors):
        index = len(flag_colors) - 1

    return flag_colors[index]

def check_vision_pathing_flag(flags, flag):
    # 模拟检查标志是否设置
    return (flags & flag) != 0

def get_vision_pathing_color(flags):
    # 根据 flags 获取颜色
    color = walkableColor

    if check_vision_pathing_flag(flags, VisionPathingFlags.Brush):
        color = brushColor

    if check_vision_pathing_flag(flags, VisionPathingFlags.Wall):
        if color == brushColor:
            color = brushWallColor  # 作为透明墙处理
        else:
            color = wallColor

    if check_vision_pathing_flag(flags, VisionPathingFlags.TransparentWall):
        color = transparentWallColor

    if check_vision_pathing_flag(flags, VisionPathingFlags.AlwaysVisible):
        color = alwaysVisibleColor

    if check_vision_pathing_flag(flags, VisionPathingFlags.BlueTeamOnly):
        color = blueTeamOnlyColor

    if check_vision_pathing_flag(flags, VisionPathingFlags.RedTeamOnly):
        color = redTeamOnlyColor

    if check_vision_pathing_flag(flags, VisionPathingFlags.NeutralZoneVisiblity):
        if color == blueTeamOnlyColor:
            color = blueTeamNeutralZoneVisibilityColor
        elif color == redTeamOnlyColor:
            color = redTeamNeutralZoneVisibilityColor
        else:
            color = neutralZoneVisibilityColor

    return color

def render_all_map_layout(navgrid_data):
    layout_list = []
    layout_list.append(render_cell_flags(navgrid_data, "visionPathingFlags"))
    layout_list.append(render_height_samples(navgrid_data.height_samples))
    layout_list.append(render_cell_flags(navgrid_data, "riverRegionFlags"))
    layout_list.append(render_cell_flags(navgrid_data, "jungleQuadrantFlags"))
    layout_list.append(render_cell_flags(navgrid_data, "mainRegionFlags"))
    layout_list.append(render_cell_flags(navgrid_data, "nearestLaneFlags"))
    layout_list.append(render_cell_flags(navgrid_data, "poiFlags"))
    layout_list.append(render_cell_flags(navgrid_data, "ringFlags"))
    layout_list.append(render_cell_flags(navgrid_data, "srxFlags"))
    return layout_list

def render_cell_flags(navgrid_data, flag_attribute_name: str):
    """
    使用 QPainter 渲染图像并翻转 Y 轴坐标系，直接操作 QPixmap。
    """
    width = navgrid_data.cellCountX
    height = navgrid_data.cellCountZ

    # 使用 QPainter 在 QPixmap 上绘制，并翻转 Y 轴
    image = QImage(width, height, QImage.Format_RGB32)

    # 绘制图像
    for y in range(height):
        for x in range(width):
            flags_value = getattr(navgrid_data.cellsmap.cells[y * width + x], flag_attribute_name)
            color = get_vision_pathing_color(flags_value)
            pixel_qcolor = QColor(color.r, color.g, color.b)
            image.setPixelColor(x, y, pixel_qcolor)
    return image

def render_height_samples(samples_map):
    """
    使用 QPainter 渲染图像并翻转 Y 轴坐标系，直接操作 QPixmap。
    """
    width = samples_map.vector.count.x
    height = samples_map.vector.count.y
    image = QImage(width, height, QImage.Format_RGB32)
    height_diff = samples_map.max_height_sample - samples_map.min_height_sample
    # 处理除零错误
    if height_diff == 0:
        height_diff = 1  # 避免除以零，可以设置为 1 或其他默认值
    # 对每个样本点进行渲染
    for y in range(height):
        for x in range(width):
            sample = samples_map.height_samples[y * width + x]
            # 计算 lerp 比例
            lerp = (sample - samples_map.min_height_sample) / height_diff
            # 计算颜色值（乘以比例）
            sample_color = QColor(
                int(heightSampleBaseColor.r * lerp),
                int(heightSampleBaseColor.g * lerp),
                int(heightSampleBaseColor.b * lerp)
            )
            image.setPixelColor(x, y, sample_color)
    return image

def process_height_sample_colors(samples_map):
    """处理颜色数据，返回 NumPy 数组。"""
    width = samples_map.vector.count.x
    height = samples_map.vector.count.y

    # 使用 NumPy 数组存储 RGBA 数据
    colors = np.zeros((height, width, 4), dtype=np.uint8)  # 4 是 RGBA 通道
    height_diff = samples_map.max_height_sample - samples_map.min_height_sample
    # 处理除零错误
    if height_diff == 0:
        height_diff = 1  # 避免除以零，可以设置为 1 或其他默认值
    for y in range(height):
        for x in range(width):
            sample = samples_map.height_samples[y * width + x]
            # 计算 lerp 比例
            lerp = (sample - samples_map.min_height_sample) / height_diff
            # 计算颜色值（乘以比例）
            sample_color = Color(
                int(heightSampleBaseColor.r * lerp),
                int(heightSampleBaseColor.g * lerp),
                int(heightSampleBaseColor.b * lerp)
            )
            colors[y, x] = [sample_color.r, sample_color.g, sample_color.b, 255]
    return colors

def process_colors(navgrid_data, flag_attribute_name, color_func):
    """处理颜色数据，返回 NumPy 数组。"""
    if color_func is process_height_sample_colors:
        return color_func(navgrid_data.height_samples)
    width = navgrid_data.cellCountX
    height = navgrid_data.cellCountZ

    # 使用 NumPy 数组存储 RGBA 数据
    colors = np.zeros((height, width, 4), dtype=np.uint8)  # 4 是 RGBA 通道

    for y in range(height):
        for x in range(width):
            flags_value = getattr(navgrid_data.cellsmap.cells[y * width + x], flag_attribute_name)
            if color_func is get_cell_flag_color:
                flags_value = int(flags_value)
            color = color_func(flags_value)
            colors[y, x] = [color.r, color.g, color.b, 255]  # Alpha 通道设置为 255（完全不透明）
    return colors

def convert_to_image(colors):
    """将颜色数据转换为 QImage 对象。"""
    height, width, _ = colors.shape
    image = QImage(width, height, QImage.Format_RGB32)

    for y in range(height):
        for x in range(width):
            r, g, b, a = colors[y, x]
            image.setPixelColor(x, y, QColor(r, g, b, a))

    return image

def render_all_map_layout_async(navgrid_data):
    """
    【线程安全】在工作线程中调用所有耗时渲染，返回 QImage 列表。
    """
    color_list: List[QImage] = []

    rendering_tasks = [
        ("visionPathingFlags", get_vision_pathing_color),
        ("height_sample", process_height_sample_colors),
        ("riverRegionFlags", get_region_flag_color),
        ("jungleQuadrantFlags", get_cell_flag_color),
        ("mainRegionFlags", get_cell_flag_color),
        ("nearestLaneFlags", get_cell_flag_color),
        ("poiFlags", get_cell_flag_color),
        ("ringFlags", get_cell_flag_color),
        ("srxFlags", get_cell_flag_color),
    ]

    for attr_name, color_func in rendering_tasks:
        colors = process_colors(navgrid_data, attr_name, color_func)
        color_list.append(colors)
        time.sleep(2.5)
    return color_list

class RendererSignals(QObject):
    finished = Signal(list)
    failed = Signal(str)

class RendererWorker(QThread):
    """执行耗时 QImage 渲染的工作线程。"""
    
    def __init__(self, navgrid_data, parent=None):
        super().__init__(parent)
        self.navgrid_data = navgrid_data
        self.signals = RendererSignals()
        
    def run(self):
        try:
            image_list = render_all_map_layout_async(self.navgrid_data)
            self.signals.finished.emit(image_list)
            
        except Exception as e:
            self.signals.failed.emit("e")
            self.signals.finished.emit([])