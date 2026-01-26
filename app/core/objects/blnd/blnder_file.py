import struct
from .binary_header import*
from .path_record import*
from .pool_data import*
from .binary_reader import*
import io

class BlendFile:
    def __init__(self, file):
        br = BinaryReader(file)  # Use BufferedReader to read binary data
        self.Header = br.read(BinaryHeader)
        self.Pool = br.read(PoolData)

    def write(self, bw):
        # 写入 BinaryHeader 和 PoolData
        self.Header.write(bw)
        self.Pool.write(bw)