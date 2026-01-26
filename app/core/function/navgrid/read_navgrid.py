from ..general import*
import threading
import time # 用于模拟耗时操作
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
from ...objects.navgrid.navgrid_file import NavGridFile, NavGridHeader, NavGridData
from ...objects.navgrid.navgrid_cell import (NavGridCell, VisionPathingFlags, RiverRegionFlags, 
                                             JungleQuadrantFlags, MainRegionFlags, NearestLaneFlags,
                                             POIFlags, RingFlags, UnknownSRXFlags, CellMap, HeightSampleVector, HeightSampleMap)
from qfluentwidgets import InfoBarIcon
from ...objects.general import vector2
from ....components.wait_bar import WaitBar
import os

def read_navgrid(file):
    header = read_navgrid_header(file)
    data = read_navgrid_data(header.major, file)
    return NavGridFile(header, data)

def read_navgrid_header(file):
    major = read_uint8(file)
    minor = 0
    if major != 2:
        minor = read_uint16(file)
    return NavGridHeader(major, minor)

def read_cell_pos(pair):
    x, y = pair
    return vector2(x, y)

def read_navgrid_data(major, file):
    minBounds = read_vector3(file)
    maxBounds = read_vector3(file)
    cellSize = read_float(file)
    cellCountX = read_uint32(file)
    cellCountZ = read_uint32(file)
    cell_map = read_cells(major, cellCountX * cellCountZ, file)
    height_samples = read_height_samples(file)
    hint_nodes = read_hint_nodes(file)
    return NavGridData(minBounds, maxBounds, cellSize, cellCountX, cellCountZ, cell_map, height_samples, hint_nodes)

def read_cells(major, cell_count, file):
    if major == 7:
        return read_cells_version7(cell_count, file)
    elif major == 5:
        return read_cells_version5(cell_count, file)
    else:
        return read_cells_version2(cell_count, file)

def read_cells_base_data(i, cell, file):
    cell.index = i
    cell.centerHeight = read_float(file)
    cell.sessionID = read_uint32(file)
    cell.arrivalCost = read_float(file)
    cell.isOpen = read_float(file)
    cell.Heuristic = read_float(file)

def read_cells_all_data_leagcy(cell, file):
    cell.actorList = read_uint32(file)
    # x 和 z 坐标
    cell.pos = read_cell_pos(read_uint16_pair(file))
    # 其他一些数据
    cell.additional_cost = read_float(file)
    cell.hint_as_good_cell = read_float(file)
    cell.additional_cost_count = read_uint32(file)
    cell.good_cell_session_ID = read_uint32(file)
    cell.hint_weight = read_float(file)
    # 读取方向和标志
    cell.arrivalDirection = read_uint16(file)
    cell.visionPathingFlags = read_uint16(file)
    cell.hintNode1 = read_uint16(file)
    cell.hintNode2 = read_uint16(file)

def read_cells_version7(cell_count, file):
    cells = []
    for i in range(cell_count):
        cell = NavGridCell()
        read_cells_base_data(i, cell, file)

        cell.pos = read_cell_pos(read_uint16_pair(file))

        cell.actorList = read_uint32(file)
        cell.unknown1 = read_uint32(file)  # unknown 1
        cell.goodCellSessionID = read_uint32(file)
        cell.hintHeight = read_float(file)
        cell.unknown2 = read_uint16(file)  # unknown 2
        cell.arrivalDirection = read_uint16(file)
        cell.hintNode1 = read_uint16(file)
        cell.hintNode2 = read_uint16(file)

        cells.append(cell)

    for i in range(cell_count):
        cells[i].visionPathingFlags = VisionPathingFlags(read_uint16(file))

    for i in range(cell_count):
        cells[i].riverRegionFlags = RiverRegionFlags(read_uint8(file))

        jungle_quadrant_and_main_region_flags = read_uint8(file)
        cells[i].jungleQuadrantFlags = JungleQuadrantFlags(jungle_quadrant_and_main_region_flags & 0x0f)
        cells[i].mainRegionFlags = MainRegionFlags((jungle_quadrant_and_main_region_flags & ~0x0f) >> 4)

        nearest_lane_and_poi_flags = read_uint8(file)
        cells[i].nearestLaneFlags = NearestLaneFlags(nearest_lane_and_poi_flags & 0x0f)
        cells[i].poiFlags = POIFlags((nearest_lane_and_poi_flags & ~0x0f) >> 4)

        ring_and_srx_flags = read_uint8(file)
        cells[i].ringFlags = RingFlags(ring_and_srx_flags & 0x0f)
        cells[i].srxFlags = UnknownSRXFlags((ring_and_srx_flags & ~0x0f) >> 4)

    # Reading unknown block (8 blocks of 132 bytes)
    print("Reading unknown block at position:", file.tell())
    unknown_block = []
    for i in range(8):
        unknown_block_line = []
        for j in range(132):
            unknown_block_line.append(read_uint8(file))
        unknown_block.append(unknown_block_line)
    return CellMap(cells, unknown_block)

def read_cells_version5(cell_count, file):
    cells = []
    for i in range(cell_count):
        cell = NavGridCell()
        read_cells_base_data(i, cell, file)
        read_cells_all_data_leagcy(cell, file)
        cells.append(cell)
    for cell in cells:
        cell.riverRegionFlags = read_uint8(file)

        jungle_quadrant_and_main_region_flags = read_uint8(file)
        cell.jungleQuadrantFlags = jungle_quadrant_and_main_region_flags & 0x0f
        cell.mainRegionFlags = (jungle_quadrant_and_main_region_flags & ~0x0f) >> 4
    print("Reading unknown block at position:", file.tell())
    unknown_block = []
    for i in range(4):
        unknown_block_line = []
        for j in range(132):
            unknown_block_line.append(read_uint8(file))
        unknown_block.append(unknown_block_line)
    return CellMap(cells, unknown_block)

def read_cells_version2(cell_count, file):
    cells = []
    for i in range(cell_count):
        cell = NavGridCell()
        read_cells_base_data(i, cell, file)
        read_cells_all_data_leagcy(cell, file)
        if cell.hintNode2 == 0:
            cell.hintNode2 = cell.hintNode1
            cell.hintNode1 = cell.visionPathingFlags

            cell.visionPathingFlags = (cell.arrivalDirection & ~0xff) >> 8
            cell.arrivalDirection &= 0xff
            cells.append(cell)
    return CellMap(cells)

def read_height_samples_vector(file):
    count = read_cell_pos(read_uint32_pair(file))
    offset = read_cell_pos(read_float_pair(file))
    return HeightSampleVector(count, offset)

def read_height_samples(file):
    vector = read_height_samples_vector(file)
    # 初始化变量
    min_height_sample = 0
    max_height_sample = 0
    height_samples = []
    total_count = vector.count.x * vector.count.y

    # 读取高度样本
    for i in range(total_count):
        sample = read_float(file)
        # 更新最小值
        if i == 0 or sample < min_height_sample:
            min_height_sample = sample
        # 更新最大值
        if i == 0 or sample > max_height_sample:
            max_height_sample = sample
        height_samples.append(sample)
    return HeightSampleMap(vector, height_samples, min_height_sample, max_height_sample)

def read_hint_nodes(file):
    hint_nodes = []  # 初始化存储提示节点的列表
    for i in range(900):  # 外层循环遍历 900 行
        row_data = []  # 每行的提示节点数据
        # 读取每一行的 900 个 float 数据
        for j in range(900):
            distance = read_float(file)  # 读取距离数据
            row_data.append(distance)
        # 读取 2 个 short 数据（hint_x, hint_y）
        hint = read_cell_pos(read_uint16_pair(file))
        # 将每个行的数据加入到 hint_nodes 中
        hint_nodes.append((row_data, hint))
    return hint_nodes

class ReadSignals(QObject):
    """定义工作线程可以发射的信号。"""
    finished = Signal(NavGridFile) # 渲染完成后发射，携带 QImage 列表
    failed = Signal(str)

class ReadWorker(QThread):
    """执行耗时 QImage 渲染的工作线程。"""
    
    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.signals = ReadSignals()
        
    def run(self):
        try:
            with open(self.filepath, 'rb') as file:
                navgrid = read_navgrid(file)
                self.signals.finished.emit(navgrid)

        except Exception as e:
            self.signals.failed.emit(f"{e}")
            self.signals.finished.emit(None)
