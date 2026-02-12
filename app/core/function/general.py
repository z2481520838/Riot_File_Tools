import sys
import struct
from typing import List
from ..objects.general import vector2, vector3, Box, Sphere, Circle, Rectangle
from pathlib import Path
import jsonpickle

def fnv1a(s, a2=0x811C9DC5):
    result = a2
    for char in s:
        result = 16777619 * (result ^ ord(char))  # ord(char) 获取字符的 ASCII 值
    return result & 0xFFFFFFFF

# submesh
def elf(to_hash):
    hash_value = 0
    high = 0
    for char in to_hash:
        hash_value = (hash_value << 4) + ord(char)  # 相当于 (hash << 4) + (byte)char

        high = hash_value & 0xF0000000
        if high != 0:
            hash_value ^= high >> 24  # 如果 high 不为0，执行高位右移并异或

        hash_value &= ~high  # 清除高位

    return hash_value & 0xFFFFFFFF  # 确保返回32位的哈希值

def elf_lower(value):
    return elf(value.lower())

def read_addr(stream):
    # 从当前流位置读取地址（偏移量）
    pos = stream.tell()
    offset = read_int32(stream)
    return pos + offset if offset != 0 else 0

def custom_lower(input_string):
    return ''.join([char.lower() if char.isalpha() else char for char in input_string])

def get_relative_path(full_path, start_str):
    # 将 full_path 转换为 Path 对象
    full_path = Path(full_path)
    
    # 查找包含 start_str 的部分
    try:
        # 获取 start_str 出现的位置
        start_index = next(i for i, part in enumerate(full_path.parts) if start_str in part)
        
        # 从该位置开始，获取相对路径
        relative_path = full_path.relative_to(Path(*full_path.parts[:start_index + 1]))
        
        return str(relative_path).replace('\\', '/')
    except (ValueError, StopIteration):
        return None

def read_uint8(stream):
    return struct.unpack('<B', stream.read(1))[0]

def read_uint16(stream):
    return struct.unpack('<H', stream.read(2))[0]

def read_uint16_pair(stream):
    return struct.unpack('<HH', stream.read(4))

def read_int32(stream):
    return struct.unpack('<i', stream.read(4))[0]

def read_int32_pair(stream):
    return struct.unpack('<ii', stream.read(8))

def read_uint32(stream):
    return struct.unpack('<I', stream.read(4))[0]

def read_uint32_pair(stream):
    return struct.unpack('<II', stream.read(8))

def read_uint64(stream):
    return struct.unpack('<Q', stream.read(8))[0]

def read_float(stream):
    return struct.unpack('<f', stream.read(4))[0]

def read_float_pair(stream):
    return struct.unpack('<ff', stream.read(8))

def read_uint32_list(count, stream):
    a = []
    for i in range(count):
        a.append(read_int32(stream))
    return a

def get_bytes_uint8(value):
    return struct.pack('<B', value)

def get_bytes_int32(value):
    return struct.pack('<i', value)

def get_bytes_uint32(value):
    return struct.pack('<I', value)

def get_bytes_uint64(value):
    return struct.pack('<Q', value)

def get_bytes_uint16(value):
    return struct.pack('<H', value)

def get_bytes_float(value):
    return struct.pack('<f', value)

def read_vector3(stream):
    x = read_float(stream)
    y = read_float(stream)
    z = read_float(stream)
    return vector3(x,y,z)

def read_str(file, length=None):
    """
    读取 C 风格的字符串，直到遇到 null 字符 '\0' 或达到最大长度限制。
    :param length: 读取的最大字符数，默认为 None 表示不限制。
    """
    ret = []
    if length is not None:
        for _ in range(length):
            byte = file.read(1)
            if not byte:  # 文件结束
                break
            ret.append(byte)
    else:
        # 如果未指定长度限制，按 4 字节一组读取
        while True:
            byte = file.read(4)  # 每次读取 4 个字节
            if not byte:  # 文件结束
                break  
            ret.append(byte)
            if b'\0' in byte:
                break
    return ''.join([b.decode('utf-8', errors='ignore') for b in ret]).replace('\0', '')

def extract_number(text):
    parts = text.split()  # 将文本按空格分隔
    for part in parts:
        if part.isdigit():  # 检查是否是数字
            return int(part)  # 转换为整数
        try:
            return float(part)  # 如果是浮动数字，转换为浮动类型
        except ValueError:
            continue  # 如果转换失败则继续检查下一个部分
    return 0

def read_box(file):
    # 读取两个 Vector3 对象，表示边界框的 min 和 max
    min_point = read_vector3(file)
    max_point = read_vector3(file)
    return Box(min_point, max_point)

def read_sphere(file):
    # 读取一个 Vector3 和一个浮动数值，表示球心和半径
    position = read_vector3(file)
    radius = read_float(file)
    return Sphere(position, radius)

# --- 封装函数 ---
def start_worker_flow(worker,on_finished,on_failed):
    worker.signals.finished.connect(on_finished)
    worker.signals.failed.connect(on_failed)
    worker.start()
    return worker

def serialize_to_pretty_json(a, b=False, c=4):
    return jsonpickle.dumps(a, b, indent=c)

def write_binary(value, file):
    file.write(value)

def write_vector3(value, file):
    write_binary(get_bytes_float(value.x), file)
    write_binary(get_bytes_float(value.y), file)
    write_binary(get_bytes_float(value.z), file)

def make_vector2(x, y):
    return vector2(x, y)

def make_circle(pos, radius):
    return Circle(pos, radius)

def make_rectangle(origin, size):
    return Rectangle(origin, size)