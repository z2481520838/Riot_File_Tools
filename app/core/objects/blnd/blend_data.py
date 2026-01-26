import struct
from .writable import*
from .binary_reader import*

class BlendData(Writable):
    def __init__(self, br=None):
        # 从 BinaryReader (br) 读取数据
        self.mFromAnimId = br.read_uint32()
        self.mToAnimId = br.read_uint32()
        self.mBlendFlags = br.read_uint32()
        self.mBlendTime = br.read_float()

    def write(self, bw):
        # 向 BinaryWriter (bw) 写入数据
        # super().write(bw)
        bw.write(struct.pack('<I', self.mFromAnimId))
        bw.write(struct.pack('<I', self.mToAnimId))
        bw.write(struct.pack('<I', self.mBlendFlags))
        bw.write(struct.pack('<f', self.mBlendTime))
