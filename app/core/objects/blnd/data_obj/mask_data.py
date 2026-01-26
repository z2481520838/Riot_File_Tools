from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from ..function import*

@dataclass
class MaskResource:
    mResourceSize: int = 0
    mFormatToken: int = 0
    mVersion: int = 0
    mFlags: int = 0
    mNumElement: int = 0
    mUniqueID: int = 0
    mWeightOffset: int = 0
    mJointHashOffset: int = 0
    mJointNdxOffset: int = 0
    mName: str = None
    mExtBuffer: list = field(default_factory=lambda: [4294967295, 4294967295])
    mWeightList: list = field(default_factory=list)

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mResourceSize))
        write_byte(new_file, get_bytes_uint32(self.mFormatToken))
        write_byte(new_file, get_bytes_uint32(self.mVersion))
        write_byte(new_file, get_bytes_uint16(self.mFlags))
        write_byte(new_file, get_bytes_uint16(len(self.mWeightList)))
        write_byte(new_file, get_bytes_uint32(self.mUniqueID))
        write_byte(new_file, get_bytes_int32(self.mWeightOffset))
        write_byte(new_file, get_bytes_int32(self.mJointHashOffset))
        write_byte(new_file, get_bytes_int32(self.mJointNdxOffset))
        write_byte(new_file, get_bytes_str(self.mName, 32))
        write_uint32_list(self.mExtBuffer, new_file)
        write_float_list(self.mWeightList, new_file)
        for x in range(len(self.mWeightList)):
            write_byte(new_file, get_bytes_uint64(0))
        for y in range(len(self.mWeightList)):
            write_byte(new_file, get_bytes_uint32(y))
            write_byte(new_file, get_bytes_uint32(y))

    def get_start_pos(self, tell):
        self.start_pos = tell

    def get_resource_size(self):
        return 72 + len(self.mWeightList) * 20

    def aligning_data(self):
        self.mNumElement = len(self.mWeightList)
        self.mWeightOffset = 72
        self.mJointHashOffset = 72 + len(self.mWeightList) * 4
        self.mJointNdxOffset = 72 + len(self.mWeightList) * 12