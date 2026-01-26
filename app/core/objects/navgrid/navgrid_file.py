from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from ..general import vector3, vector2
from .navgrid_cell import CellMap, HeightSampleMap
import os

@dataclass
class NavGridHeader:
    major: int = 0
    minor: int = 0

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint8(self.major))
        write_byte(new_file, get_bytes_uint8(self.minor))

@dataclass
class NavGridData:
    minBounds: vector3 = None
    maxBounds: vector3 = None
    cellSize: float = 0
    cellCountX: int = 0
    cellCountZ: int = 0
    cellsmap: CellMap = None
    height_samples: HeightSampleMap = None
    hint_nodes: list = field(default_factory=list)

    def write(self, new_file):
        pass

@dataclass
class NavGridFile:
    header: NavGridHeader = None
    data: NavGridData = None

    def write(self, new_file):
        pass
