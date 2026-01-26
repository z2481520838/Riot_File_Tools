import struct
from .writable import*
from .binary_reader import*

class PathRecord(Writable):
    def __init__(self, br: BinaryReader):
        self.pathHash = br.read_uint32()
        self.pathOffset = br.read_addr()

        prev_position = br.stream.tell()
        br.stream.seek(self.pathOffset)
        if self.pathOffset != 0:
            self.path = br.read_cstring()
        br.stream.seek(prev_position)

    def write(self, bw):
        # 计算路径的 FNV1a 哈希值
        path_hash = self.hash_string_fnv1a(self.path)
        # 写入路径的哈希值和路径的内存分配
        bw.write(struct.pack('<I', path_hash))  # 写入哈希值
        bw.write(self.write_cstring(self.path))  # 写入路径的 CString（带 '\0'）

    def write_cstring(self, s):
        # 将字符串转换为 CString，并返回其字节数据
        return s.encode('utf-8') + b'\0'  # 转为字节并加上 null 终止符

    def hash_string_fnv1a(self, s):
        # FNV-1a 哈希算法
        FNV_OFFSET_BASIS = 14695981039346656037
        FNV_32_PRIME = 16777619
        hash_value = FNV_OFFSET_BASIS
        for byte in s.encode('utf-8'):
            hash_value ^= byte
            hash_value *= FNV_32_PRIME
        return hash_value & 0xFFFFFFFF  # 返回 32 位哈希值
