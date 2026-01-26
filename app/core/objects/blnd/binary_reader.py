import struct
import sys
import io

class BinaryReader:
    def __init__(self, stream: io.BytesIO):
        self.stream = stream

    def read_uint32(self):
        return struct.unpack('<I', self.stream.read(4))[0]

    def read_uint64(self):
        return struct.unpack('<Q', self.stream.read(8))[0]

    def read_int32(self):
        return struct.unpack('<i', self.stream.read(4))[0]

    def read_uint16(self):
        """
        读取 2 字节的无符号整数（uint16）
        """
        return struct.unpack('<H', self.stream.read(2))[0]

    def read_float(self):
        return struct.unpack('<f', self.stream.read(4))[0]

    def read_cstring(self, length=None):
        """
        读取 C 风格的字符串，直到遇到 null 字符 '\0' 或达到最大长度限制。
        :param length: 读取的最大字符数，默认为 None 表示不限制。
        """
        ret = []
        prev_position = self.stream.tell()  # 获取当前位置
        
        # 使用 sys.maxsize 表示没有限制的长度
        max_length = length if length is not None else sys.maxsize
        
        for _ in range(max_length):
            byte = self.stream.read(1)  # 读取一个字节
            if not byte or byte == b'\0':  # 遇到 null 字符或文件结束
                break
            ret.append(byte.decode('utf-8'))  # 追加字符到结果列表
        
        # 如果指定了长度并且没有遇到 '\0'，重新设置流的位置
        if length is not None:
            self.stream.seek(prev_position + length)
        
        return ''.join(ret)  # 将字符列表连接为一个字符串

    def read_addr(self):
        # 从当前流位置读取地址（偏移量）
        pos = self.stream.tell()
        return self.read_addr_at_position(pos)

    def read_addr_at_position(self, pos):
        # 读取一个地址并计算实际位置
        addr = self.read_int32()
        return pos + addr if addr != 0 else 0

    def read(self, cls):
        return cls(self)

    def read_bytes(self, size: int):
        return self.stream.read(size)

    def tell(self):
        """获取当前文件流的位置"""
        return self.stream.tell()

    def seek(self, addr):
        """获取当前文件流的位置"""
        return self.stream.seek(addr)

    def read_arr(self, addr, num, ctr):
        """ 读取一个数组，返回由回调函数生成的对象 """
        arr = []
        self.stream.seek(addr)  # 定位到指定的地址
        for _ in range(num):
            arr.append(ctr(self))  # 使用回调函数读取数据
        return arr

    def read_arr2(self, addr, num, ctr, base_addr=None):
        """
        读取一个地址数组并使用回调函数解析数组元素。
        :param addr: 地址的起始位置
        :param num: 要读取的元素数量
        :param ctr: 回调函数，用于创建元素
        :param base_addr: 可选的基地址，默认是 `None`
        :return: 解析出来的数组
        """
        self.stream.seek(addr)  # 定位到指定地址
        
        addrs = []
        for _ in range(num):
            addrs.append(self.read_addr_at_position(base_addr or addr))  # 获取地址列表

        arr = []
        for a in addrs:
            if a == 0:  # 如果地址不为0
                arr.append(None)  # 使用回调函数读取数据
            else:
                self.stream.seek(a)  # 定位到地址
                arr.append(ctr(self))  # 使用回调函数读取数据
        return arr
    def read_resource(self, addr, resource_cls):
        """
        读取资源。如果地址为 0，则返回 None。
        
        :param br: BinaryReader 对象
        :param addr: 资源的地址
        :param resource_cls: 资源类（如 EventResource, MaskResource 等）
        :return: 资源实例或 None
        """
        self.seek(addr)
        if addr != 0:
            return self.read(resource_cls)  # 读取资源
        return None  # 如果地址为0，返回 None