import struct
import io
from typing import Callable, List, TypeVar, Any, Optional

T = TypeVar('T')

# Read address - 读取地址并返回实际位置
def read_addr(br: io.BytesIO, pos: int = None) -> int:
    if pos is None:
        pos = br.tell()  # 获取当前文件指针位置
    addr = struct.unpack('<I', br.read(4))[0]  # 读取 4 字节无符号整数
    return pos + addr if addr != 0 else 0

# 读取数组 - 读取指定地址的多个元素
def read_arr(br: io.BytesIO, addr: int, num: int, ctr: Callable[[io.BytesIO], T]) -> List[T]:
    br.seek(addr)  # 定位到指定地址
    return [ctr(br) for _ in range(num)]

# 读取指向对象数组的地址 - 处理指针偏移
def read_arr2(br: io.BytesIO, addr: int, num: int, ctr: Callable[[io.BytesIO], T], base_addr: Optional[int] = None) -> List[T]:
    br.seek(addr)  # 定位到指定地址
    addrs = [read_addr(br, base_addr or addr) for _ in range(num)]
    arr = []
    for a in addrs:
        if a != 0:
            br.seek(a)
            arr.append(ctr(br))
    return arr

# 读取 C 字符串 - 读取 null 终止的字符串
def read_cstring(br: io.BytesIO, length: int = 1024) -> str:
    result = []
    for _ in range(length):
        char = br.read(1)
        if char == b'\0':
            break
        result.append(char.decode('utf-8'))
    return ''.join(result)

# 缓存读取对象，防止重复读取相同位置的数据
read_cache = {}

def read(br: io.BytesIO, cls: T) -> T:
    pos = br.tell()
    if pos in read_cache:
        return read_cache[pos]
    
    # 创建对象并缓存
    instance = cls(br)
    read_cache[pos] = instance
    return instance

# 写入函数 - 将对象写入 BinaryWriter
def write(bw: io.BytesIO, wobj: Any) -> None:
    wobj.write(bw)

# 写入 C 字符串 - 写入 null 终止的字符串
def write_cstring(bw: io.BytesIO, sobj: str) -> None:
    bw.write(sobj.encode('utf-8') + b'\0')

def write_cstring_with_length(bw: io.BytesIO, sobj: str, length: int) -> None:
    sobj = sobj[:length].ljust(length, '\0')
    bw.write(sobj.encode('utf-8') + b'\0')

