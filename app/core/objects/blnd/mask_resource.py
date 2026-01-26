import struct
from .resource import*
from .writable import*
from .function import*

class MaskResource(Resource):
    class JointHash(Writable):
        def __init__(self, br):
            self.mWeightID = br.read_int32()
            self.mJointHash = br.read_uint32()

        def write(self, bw):
            bw.write(struct.pack('<i', self.mWeightID))  # 写入 4 字节的带符号整数
            bw.write(struct.pack('<I', self.mJointHash))  # 写入 4 字节的无符号整数

    class JointNdx(Writable):
        def __init__(self, br):
            self.mWeightID = br.read_int32()
            self.mJointNdx = br.read_int32()

        def write(self, bw):
            bw.write(struct.pack('<i', self.mWeightID))  # 写入 4 字节的带符号整数
            bw.write(struct.pack('<i', self.mJointNdx))  # 写入 4 字节的带符号整数

    def __init__(self, br):
        super().__init__(br)
        self.mFormatToken = br.read_uint32()
        self.mVersion = br.read_uint32()
        self.mFlags = br.read_uint16()
        self.mNumElement = br.read_uint16()
        self.mUniqueID = br.read_int32()

        # 读取地址偏移
        self.mWeightOffset = br.read_addr_at_position(self.baseAddr)
        self.mJointHashOffset = br.read_addr_at_position(self.baseAddr)
        self.mJointNdxOffset = br.read_addr_at_position(self.baseAddr)
        
        self.mName = br.read_cstring(32)  # 读取字符串，最大长度 32
        
        self.mExtBuffer = [
            br.read_uint32(),
            br.read_uint32()
        ]

        # 读取偏移的数据
        prev_position = br.tell()
        if self.mWeightOffset != 0:
            br.seek(self.mWeightOffset)
            self.mWeightList = []
            for i in range(self.mNumElement):
                self.mWeightList.append(br.read_float())
        if self.mJointHashOffset != 0:
            br.seek(self.mJointHashOffset)
            self.mJointHash = br.read(self.JointHash)
        if self.mJointNdxOffset != 0:
            br.seek(self.mJointNdxOffset)
            self.mJointNdx = br.read(self.JointNdx)
        
        br.seek(prev_position)  # 恢复原来的位置

    def write(self, bw):
        # base_addr = bw.tell()  # 当前写入位置
        bw.write(struct.pack('<I', self.mResourceSize))  # 占位符，写入结构的大小
        bw.write(struct.pack('<I', self.mFormatToken))
        bw.write(struct.pack('<I', self.mVersion))
        bw.write(struct.pack('<H', self.mFlags))
        bw.write(struct.pack('<H', self.mNumElement))
        bw.write(struct.pack('<I', self.mUniqueID))
        
        bw.write(struct.pack('<i', determine(self.mWeightOffset, self.baseAddr)))
        bw.write(struct.pack('<i', determine(self.mJointHashOffset, self.baseAddr)))
        bw.write(struct.pack('<i', determine(self.mJointNdxOffset, self.baseAddr)))
        write_string(bw, self.mName, 32)
        # self.write_cstring(bw, self.mName, 32)
        for ui in self.mExtBuffer:
            bw.write(struct.pack('<I', ui))
        # 写入偏移
        """mWeightOffset = bw.tell()
        mJointHashOffset = bw.tell() + 4
        mJointNdxOffset = bw.tell() + 4
        bw.write(struct.pack('<I', 0))  # 偏移的占位符
        bw.write(struct.pack('<I', 0))  # 偏移的占位符
        bw.write(struct.pack('<I', 0))  # 偏移的占位符
        """
        # 写入数据
        if self.mWeightOffset != 0:
            bw.seek(self.mWeightOffset)
            for i in self.mWeightList:
                bw.write(struct.pack('<f', i))
        if self.mJointHashOffset != 0:
            bw.seek(self.mJointHashOffset)
            self.mJointHash.write(bw)
        if self.mJointNdxOffset != 0:
            bw.seek(self.mJointNdxOffset)
            count = self.mResourceSize - (self.mJointNdxOffset - self.baseAddr)
            # print(f"{count}")
            for i in range(int(count/8)):
                bw.write(struct.pack('<I', i))
                bw.write(struct.pack('<I', i))
            # self.mJointNdx.write(bw)

    def write_cstring(self, bw, string, length):
        # 写入 null 终止的字符串
        bw.write(string.encode('utf-8')[:length] + b'\0')

