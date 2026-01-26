from .resource import*
from .writable import*
from .binary_reader import*

class AnimResourceBase(Resource):
    def __init__(self, br: BinaryReader):
        super().__init__(br)
        self.formatToken = br.read_uint32()

    @staticmethod
    def read(br: BinaryReader):
        prev_position = br.tell()
        formatToken = br.read_uint32()
        br.seek(prev_position)  # 恢复位置
        return br.read(AnimResourceBase)

    def write(self, bw):
        bw.write(struct.pack('<I', self.formatToken))

class AnimationResource(AnimResourceBase):
    def __init__(self, br: BinaryReader):
        super().__init__(br)
        self.mVersion = br.read_uint32()
        self.mFlags = br.read_uint32()
        self.mNumChannels = br.read_uint32()
        self.mNumTicks = br.read_uint32()
        self.mTickDuration = br.read_uint32()

        self.mJointNameHashesOffset = br.read_addr_at_position(self.baseAddr)
        self.mAssetNameOffset = br.read_addr_at_position(self.baseAddr)
        self.mTimeOffset = br.read_addr_at_position(self.baseAddr)
        self.mVectorPaletteOffset = br.read_addr_at_position(self.baseAddr)
        self.mQuatPaletteOffset = br.read_addr_at_position(self.baseAddr)
        self.mTickDataOffset = br.read_addr_at_position(self.baseAddr)

        self.mExtBuffer = [
            br.read_uint32(),
            br.read_uint32(),
            br.read_uint32()
        ]

        prev_position = br.tell()
        br.seek(self.mAssetNameOffset)
        self.mAssetName = br.read_cstring()
        br.seek(prev_position)

    def write(self, bw):
        # 这个例子没有 Memory.Allocate 等相关细节，因此这里假设你会处理内存分配逻辑
        bw.write(struct.pack('<I', self.mVersion))
        bw.write(struct.pack('<I', self.mFlags))
        bw.write(struct.pack('<I', self.mNumChannels))
        bw.write(struct.pack('<I', self.mNumTicks))
        bw.write(struct.pack('<f', self.mTickDuration))

        bw.write(struct.pack('<I', self.mJointNameHashesOffset))
        bw.write(struct.pack('<I', self.mAssetNameOffset))
        bw.write(struct.pack('<I', self.mTimeOffset))
        bw.write(struct.pack('<I', self.mVectorPaletteOffset))
        bw.write(struct.pack('<I', self.mQuatPaletteOffset))
        bw.write(struct.pack('<I', self.mTickDataOffset))

        for ext in self.mExtBuffer:
            bw.write(struct.pack('<I', ext))

        # 写入字符串
        if self.mAssetName:
            bw.write(self.mAssetName.encode('utf-8') + b'\0')