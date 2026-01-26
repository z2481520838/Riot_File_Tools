import struct
from .writable import*
from .binary_reader import*
class Resource(Writable):
    def __init__(self, br):
        self.br = br
        self.baseAddr = br.tell()  # 当前文件流位置
        self.mResourceSize = br.read_uint32()
    # def write(self, bw):
        # bw.write(struct.pack('<I', self.mResourceSize))