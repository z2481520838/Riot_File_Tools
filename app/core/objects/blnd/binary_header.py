import struct
from .writable import*
from .binary_reader import*

class BinaryHeader(Writable):
    def __init__(self, br: BinaryReader):
        self.mEngineType = br.read_cstring(4)
        self.mBinaryBlockType = br.read_cstring(4)
        self.mBinaryBlockVersion = br.read_uint32()

    def write(self, bw):
        bw.write(self.mEngineType.encode('utf-8'))
        bw.write(self.mBinaryBlockType.encode('utf-8'))
        bw.write(struct.pack('<I', self.mBinaryBlockVersion))
