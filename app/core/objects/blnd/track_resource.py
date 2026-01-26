import sys
import struct
from .resource import*
from .function import*

class TrackResource(Resource):
    def __init__(self, br):
        super().__init__(br)
        self.mBlendWeight = br.read_float()
        self.mBlendMode = br.read_uint32()
        self.mIndex = br.read_uint32()
        self.mName = br.read_cstring(32)

    def write(self, bw):
        blendWeight_bytes = get_bytes_float(self.mBlendWeight)
        blendMode_bytes = get_bytes_uint32(self.mBlendMode)
        index_bytes = get_bytes_uint32(self.mIndex)
        name_bytes = get_bytes_str(self.mName, 32)
        resource_size_bytes = get_bytes_uint32(4 + len(blendWeight_bytes) + len(blendMode_bytes) + len(index_bytes) + len(name_bytes))
        bw.write(resource_size_bytes)
        bw.write(blendWeight_bytes)
        bw.write(blendMode_bytes)
        bw.write(index_bytes)
        bw.write(name_bytes)