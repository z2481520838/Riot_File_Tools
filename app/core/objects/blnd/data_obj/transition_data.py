from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from ..function import*

@dataclass
class TransitionToData:
    mToAnimId: int = 0
    mTransitionAnimId: int = 0

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mToAnimId))
        write_byte(new_file, get_bytes_uint32(self.mTransitionAnimId))

@dataclass
class TransitionClipData:
    FromAnimationID: int = 0
    TransitionToCount: int = 0
    TransitionToOffset: int = 0
    TransitionTo: list = field(default_factory=list)

    def get_data_size(self):
        return len(self.TransitionTo)*8
    def getsize(self):
        return 12 + len(self.TransitionTo)*8
    def aligning_offset(self, offset):
        self.TransitionToOffset = offset
    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.FromAnimationID))
        write_byte(new_file, get_bytes_uint32(self.TransitionToCount))
        write_byte(new_file, get_bytes_uint32(self.TransitionToOffset))