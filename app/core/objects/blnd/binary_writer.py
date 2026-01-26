import io
import struct
from typing import Optional

class BinaryWriter:
    def __init__(self, stream: Optional[io.BytesIO] = None):
        """初始化 BinaryWriter，默认使用 BytesIO 作为内存流"""
        self.stream = stream or io.BytesIO()

    def write(self, data: bytes):
        """直接写入字节数据"""
        self.stream.write(data)

    def write_uint8(self, value: int):
        """写入 uint8 数据"""
        self.stream.write(struct.pack('<B', value))

    def write_uint16(self, value: int):
        """写入 uint16 数据"""
        self.stream.write(struct.pack('<H', value))

    def write_uint32(self, value: int):
        """写入 uint32 数据"""
        self.stream.write(struct.pack('<I', value))

    def write_int8(self, value: int):
        """写入 int8 数据"""
        self.stream.write(struct.pack('<b', value))

    def write_int16(self, value: int):
        """写入 int16 数据"""
        self.stream.write(struct.pack('<h', value))

    def write_int32(self, value: int):
        """写入 int32 数据"""
        self.stream.write(struct.pack('<i', value))

    def write_float(self, value: float):
        """写入 float 数据"""
        self.stream.write(struct.pack('<f', value))

    def write_double(self, value: float):
        """写入 double 数据"""
        self.stream.write(struct.pack('<d', value))

    def write_cstring(self, value: str):
        """写入 C 风格字符串（以 null 结尾的字符串）"""
        self.stream.write(value.encode('utf-8') + b'\0')

    def get_bytes(self) -> bytes:
        """获取当前内存流中的所有字节"""
        return self.stream.getvalue()

    def seek(self, offset: int, whence: int = io.SEEK_SET):
        """设置文件指针位置"""
        self.stream.seek(offset, whence)

    def tell(self) -> int:
        """获取当前文件指针位置"""
        return self.stream.tell()

    def close(self):
        """关闭流"""
        self.stream.close()
