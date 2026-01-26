import os
import io
import struct
from ..prop_tools.PROP_obj_Functions import*
from ..prop_tools.PROP_value import vec3
from .navgridcell import*
from dataclasses import dataclass

# 尝试改用QColor
@dataclass
class Color:
    r: int = 0
    g: int = 0
    b: int = 0

    def __mul__(self, value: float) -> 'Color':
        """Multiply the color by a float value."""
        r = int(self.r * value)
        g = int(self.g * value)
        b = int(self.b * value)
        return Color(r, g, b)

    def __eq__(self, other: 'Color') -> bool:
        """Compare two colors for equality."""
        return self.r == other.r and self.g == other.g and self.b == other.b

    def __ne__(self, other: 'Color') -> bool:
        """Check if two colors are not equal."""
        return not self.__eq__(other)

# 颜色常量
walkableColor = Color(255, 255, 255)
brushColor = Color(0, 122, 14)
wallColor = Color(64, 64, 64)
brushWallColor = Color(0, 216, 111)
transparentWallColor = Color(0, 210, 214)
alwaysVisibleColor = Color(192, 192, 0)
blueTeamOnlyColor = Color(87, 79, 255)
redTeamOnlyColor = Color(255, 124, 124)
neutralZoneVisibilityColor = Color(255, 165, 0)
blueTeamNeutralZoneVisibilityColor = Color(12, 0, 255)
redTeamNeutralZoneVisibilityColor = Color(255, 0, 0)
heightSampleBaseColor = Color(255, 0, 0)
flag_colors = [
    Color(64, 0, 0),    # Color 1: (64, 0, 0)
    Color(140, 0, 0),   # Color 2: (140, 0, 0)
    Color(240, 0, 0),   # Color 3: (240, 0, 0)
    Color(0, 100, 0),   # Color 4: (0, 100, 0)
    Color(0, 240, 0),   # Color 5: (0, 240, 0)
    Color(0, 0, 100),   # Color 6: (0, 0, 100)
    Color(0, 0, 240),   # Color 7: (0, 0, 240)
    Color(100, 0, 100), # Color 8: (100, 0, 100)
    Color(240, 0, 240), # Color 9: (240, 0, 240)
    Color(140, 140, 0), # Color 10: (140, 140, 0)
    Color(240, 240, 0), # Color 11: (240, 240, 0)
    Color(0, 140, 140), # Color 12: (0, 140, 140)
    Color(0, 240, 240), # Color 13: (0, 240, 240)
    Color(64, 64, 64),  # Color 14: (64, 64, 64)
    Color(160, 160, 160), # Color 15: (160, 160, 160)
    Color(240, 240, 240)  # Color 16: (240, 240, 240)
]

class File_Wrapper:
    def __init__(self, file_path, isbmp: bool = False):
        self.file_path = file_path
        self.folder_path, self.name = os.path.split(file_path)
        self.name, self.file_extension = os.path.splitext(self.name)
        self.isbmp = isbmp
        self.file = None
        self.read_buffer = bytearray(8)  # equivalent to C# byte[] with bufferSize = 8

        if os.path.exists(file_path):
            self.file_mode = 'r+b'  # Read/Write binary
        else:
            self.file_mode = 'w+b'  # Write/Read binary
            os.makedirs(self.folder_path, exist_ok=True)

    def to_custom_format(self):
        lines = ["ngrid_format"]
        write_str(lines, f"ngridMajorVersion = {self.majorVersion}")
        write_str(lines, f"ngridMinorVersion = {self.minorVersion}")
        write_str(lines, f"minBounds = {self.minBounds}")
        write_str(lines, f"maxBounds = {self.maxBounds}")
        write_str(lines, f"cellSize = {self.cellSize}")
        write_str(lines, f"cellCountX = {self.cellCountX}")
        write_str(lines, f"cellCountZ = {self.cellCountZ}")
        write_str(lines, f"cell_count = {len(self.cells)}")
        write_str(lines, f"heightSampleCountX = {self.height_sample_count_x}")
        write_str(lines, f"heightSampleCountZ = {self.height_sample_count_z}")
        write_str(lines, f"heightSampleOffsetX = {self.height_sample_offset_x}")
        write_str(lines, f"heightSampleOffsetZ = {self.height_sample_offset_z}")
        write_str(lines, f"min sample height = {self.min_height_sample}")
        write_str(lines, f"max sample height = {self.max_height_sample}")
        write_str(lines, f"height_samples_count = {len(self.height_samples)}")
        write_str(lines, f"hint_nodes_count = {len(self.hint_nodes)}")
        return "\n".join(lines)

    def get_Version(self):
        # 读取文件的内容，比如读取字符串
        self.majorVersion = self.read_byte()  # 假设你需要读取整个文件内容
        self.minorVersion = 0
        if self.majorVersion != 2:
            # not sure why this is short but the other is byte, might just be padding
            # note that the only known non-zero minor version to exist (other than unofficial 2.1) is 3.1, with no know difference from 3.0
            self.minorVersion = self.read_short()

    def get_Value(self):
        self.minBounds = self.read_vec3();
        self.maxBounds = self.read_vec3();
        self.cellSize = self.read_float();
        self.cellCountX = self.read_int();
        self.cellCountZ = self.read_int();
        if self.majorVersion == 7:
            self.read_cells_version7()
        else:
            self.read_cells_version5()
        self.read_height_samples()
        self.read_hint_nodes()

    def open(self):
        """Open the file in binary read/write mode."""
        self.file = open(self.file_path, self.file_mode)
        if self.isbmp == False:
            self.get_Version()
            self.get_Value()
    def clear(self):
        try:
            self.file.truncate(0)  # 清空文件内容，设置文件长度为0
        except Exception as e:
            print(f"Error clearing the file: {e}")
    def close(self):
        """Close the file."""
        if self.file:
            self.file.close()

    def seek(self, offset=-1, seek_origin=io.SEEK_SET):
        if offset != -1 or seek_origin != io.SEEK_SET:
            self.file.seek(offset, seek_origin)
        else:
            # 使用默认参数（无效），什么也不做
            pass

    def tell(self):
        """Get current file position."""
        if self.file:
            return self.file.tell()

    def get_length(self):
        """Get file length."""
        if self.file:
            current_pos = self.tell()
            self.seek(0, os.SEEK_END)
            length = self.tell()
            self.seek(current_pos, os.SEEK_SET)  # Return to original position
            return length
        return 0

    def read_all_text(self):
        """读取文件的所有内容"""
        if not self.file:
            raise ValueError("File is not opened.")
        return self.file.read().decode("utf-8", errors="ignore")  # 读取并解码为字符串，忽略无效字符

    def read(self, size):
        """按指定大小读取"""
        if not self.file:
            raise ValueError("File is not opened.")
        return self.file.read(size)

    def read_short(self, offset=-1):
        try:
            if offset != -1:
                self.seek(offset)
            
            # 读取2个字节
            read_bytes = self.file.read(2)
            if len(read_bytes) < 2:
                raise ValueError("Not enough data to read a short.")
            
            # 将2个字节转为整数，按小端顺序读取
            n = int.from_bytes(read_bytes, byteorder='little')
            return n
        except Exception as e:
            print(f"Error reading short: {e}")
            return 0
    
    def read_byte(self, offset=-1):
        try:
            if offset != -1:
                self.seek(offset)
            
            byte = self.file.read(1)
            if len(byte) < 1:
                raise ValueError("Not enough data to read a byte.")
            
            return byte[0]
        except Exception as e:
            print(f"Error reading byte: {e}")
            return 0

    def write(self, data):
        """Write data to the file."""
        if self.file:
            self.file.write(data)

    def read_int(self, offset=-1):
        try:
            self.seek(offset)
            byte_data = self.file.read(4)  # 读取4个字节
            if len(byte_data) < 4:
                raise ValueError("Cannot read enough bytes for an integer")
            # 将字节转换为整数，默认使用小端字节序
            return struct.unpack('<I', byte_data)[0]  # '<I'表示小端格式的无符号整数
        except Exception as e:
            print(f"Error reading int: {e}")
            return 0

    def read_float(self, offset=-1):
        try:
            self.seek(offset)
            byte_data = self.file.read(4)  # 读取4个字节
            if len(byte_data) < 4:
                raise ValueError("Cannot read enough bytes for a float")
            # 将字节转换为浮动数，默认使用小端字节序
            return struct.unpack('<f', byte_data)[0]  # '<f'表示小端格式的浮点数
        except Exception as e:
            print(f"Error reading float: {e}")
            return 0.0

    def read_vec3(self, offset=-1):
        x = self.read_float(offset)
        y = self.read_float()
        z = self.read_float()
        return vec3(x, y, z)

    def write_float(self, f, offset=-1):
        try:
            # 获取浮动的字节表示
            bytes_data = struct.pack('<f', f)  # < 表示小端字节序，f 表示浮动
            # 如果系统是大端字节序，需要反转字节
            if not self.is_little_endian():
                bytes_data = bytes_data[::-1]  # 反转字节数组
            print(f"Writing float: {f}, bytes: {bytes_data}")
            self.write_bytes(bytes_data, offset)
        except Exception as e:
            print(f"Error in write_float: {e}")
            raise  # 重新抛出异常，方便调试

    def read_string(self, length=-1, offset=-1):
        """Read a string (null-terminated or fixed length)."""
        self.seek(offset)
        if length < 0:
            string_data = b""
            while (byte := self.file.read(1)) != b'\x00':  # Null-terminated string
                string_data += byte
            return string_data.decode('utf-8')
        else:
            return self.file.read(length).decode('utf-8')

    def write_string(self, string, offset=-1):
        """Write a string (null-terminated)."""
        self.seek(offset)
        self.file.write(string.encode('utf-8') + b'\x00')

    def __str__(self):
        return f"{self.name}{self.file_extension}"

    def __del__(self):
        """Destructor to ensure the file is closed."""
        self.close()

    def get_file_position(self):
        return self.file.tell()

    def read_cells_version7(self):
        total_cell_count = self.cellCountX * self.cellCountZ  # This should be set accordingly
        self.cells = []

        for i in range(total_cell_count):
            cell = NavGridCell()
            cell.index = i

            cell.centerHeight = self.read_float()
            cell.sessionID = self.read_int()
            cell.arrivalCost = self.read_float()
            cell.isOpen = self.read_int() != 0
            cell.Heuristic = self.read_float()

            cell.x = self.read_short()
            cell.z = self.read_short()

            cell.actorList = self.read_int()
            self.read_int()  # unknown 1
            cell.goodCellSessionID = self.read_int()
            cell.hintHeight = self.read_float()
            self.read_short()  # unknown 2
            cell.arrivalDirection = self.read_short()
            cell.hintNode1 = self.read_short()
            cell.hintNode2 = self.read_short()

            self.cells.append(cell)

        for i in range(total_cell_count):
            self.cells[i].visionPathingFlags = VisionPathingFlags(self.read_short())

        for i in range(total_cell_count):
            self.cells[i].riverRegionFlags = RiverRegionFlags(self.read_byte())

            jungle_quadrant_and_main_region_flags = self.read_byte()
            self.cells[i].jungleQuadrantFlags = JungleQuadrantFlags(jungle_quadrant_and_main_region_flags & 0x0f)
            self.cells[i].mainRegionFlags = MainRegionFlags((jungle_quadrant_and_main_region_flags & ~0x0f) >> 4)

            nearest_lane_and_poi_flags = self.read_byte()
            self.cells[i].nearestLaneFlags = NearestLaneFlags(nearest_lane_and_poi_flags & 0x0f)
            self.cells[i].poiFlags = POIFlags((nearest_lane_and_poi_flags & ~0x0f) >> 4)

            ring_and_srx_flags = self.read_byte()
            self.cells[i].ringFlags = RingFlags(ring_and_srx_flags & 0x0f)
            self.cells[i].srxFlags = UnknownSRXFlags((ring_and_srx_flags & ~0x0f) >> 4)

        # Reading unknown block (8 blocks of 132 bytes)
        self.unknown_blockstartpos = self.get_file_position()
        print("Reading unknown block at position:", self.get_file_position())
        for i in range(8):
            for j in range(132):
                self.read_byte()

    def read_cells_version5(self):
        total_cell_count = self.cellCountX * self.cellCountZ  # This should be set accordingly
        self.cells = []

        # 遍历所有单元格
        for i in range(total_cell_count):
            cell = NavGridCell()
            cell.index = i

            # 读取核心数据
            cell.centerHeight = self.read_float()
            cell.sessionID = self.read_int()
            cell.arrivalCost = self.read_float()
            cell.isOpen = self.read_int() != 0
            cell.Heuristic = self.read_float()
            cell.actorList = self.read_int()

            # x 和 z 坐标
            cell.x = self.read_short()
            cell.z = self.read_short()

            # 其他一些数据
            self.read_float()  # additional cost
            self.read_float()  # hint as good cell
            self.read_int()  # additional cost count
            self.read_int()  # good cell session ID
            self.read_float()  # hint weight

            # 读取方向和标志
            arrival_direction = self.read_short()
            vision_pathing_flags = self.read_short()
            hint_node_1 = self.read_short()
            hint_node_2 = self.read_short()

            # 版本2特殊处理
            if self.majorVersion == 2 and hint_node_2 == 0:
                hint_node_2 = hint_node_1
                hint_node_1 = vision_pathing_flags

                vision_pathing_flags = (arrival_direction & ~0xff) >> 8
                arrival_direction &= 0xff

            cell.visionPathingFlags = vision_pathing_flags

            self.cells.append(cell)

        # 如果是版本5，读取额外的标志和数据块
        if self.majorVersion == 5:
            print(f"reading flag block: {self.file.tell()}")
            for i in range(total_cell_count):
                cell = self.cells[i]
                cell.riverRegionFlags = self.read_byte()

                jungle_quadrant_and_main_region_flags = self.read_byte()
                cell.jungleQuadrantFlags = jungle_quadrant_and_main_region_flags & 0x0f
                cell.mainRegionFlags = (jungle_quadrant_and_main_region_flags & ~0x0f) >> 4

            # 读取版本5的额外数据块
            print(f"reading unknown block: {self.file.tell()}")
            self.unknown_blockstartpos = self.get_file_position()
            for i in range(4):  # version 5 only has 4 blocks of 132 bytes each
                for j in range(132):
                    self.read_byte()

    # 读取高度样本的函数
    def read_height_samples(self):
        # 假设这些是已经从ngrid_file读取的值
        self.height_sample_count_x = self.read_int()
        self.height_sample_count_z = self.read_int()
        self.height_sample_offset_x = self.read_float()
        self.height_sample_offset_z = self.read_float()

        # 初始化变量
        self.min_height_sample = 0
        self.max_height_sample = 0
        self.height_samples = []

        total_count = self.height_sample_count_x * self.height_sample_count_z

        # 读取高度样本
        for i in range(total_count):
            sample = self.read_float()
            # 更新最小值
            if i == 0 or sample < self.min_height_sample:
                self.min_height_sample = sample
            # 更新最大值
            if i == 0 or sample > self.max_height_sample:
                self.max_height_sample = sample
            self.height_samples.append(sample)
        # return self.height_samples

    def read_hint_nodes(self):
        self.hint_nodes = []  # 初始化存储提示节点的列表

        for i in range(900):  # 外层循环遍历 900 行
            row_data = []  # 每行的提示节点数据

            # 读取每一行的 900 个 float 数据
            for j in range(900):
                distance = self.read_float()  # 读取距离数据
                row_data.append(distance)
            
            # 读取 2 个 short 数据（hint_x, hint_y）
            hint_x = self.read_short()
            hint_y = self.read_short()

            # 将每个行的数据加入到 hint_nodes 中
            self.hint_nodes.append((row_data, (hint_x, hint_y)))

        return self.hint_nodes

    def write_bytes(self, bytes_data, offset=-1):
        try:
            # 记录当前文件指针位置
            old_position = self.get_file_position()

            # 如果提供了偏移量，移动文件指针
            self.seek(offset)

            # 写入字节数据
            self.file.write(bytes_data)

            # 如果偏移量被指定，恢复文件指针位置
            if offset != -1:
                self.seek(old_position)
        except Exception as e:
            error_string = "Error writing to file:  "

            # 打印每个字节的值
            error_string += ' '.join([str(byte) for byte in bytes_data])

            error_string += f"\n{e.__class__.__name__}\n{e}"

            print(error_string)

    def write_byte(self, n, offset=-1):
        # 将整数n转换为字节（1字节）
        byte_data = struct.pack('<B', n)  # '<B'表示一个字节（unsigned char），小端字节序
        self.write_bytes(byte_data, offset)

    def write_int(self, n, offset=-1):
        # 使用小端字节序写入4字节
        # 如果值小于 0 或大于 4294967295，强制为无符号 32 位整数
        if n < 0x80000000:  # 小于 2^31，表示正数或零
            bytes_data = struct.pack('<i', n)  # 使用有符号 32 位整数格式
        else:  # 大于等于 2^31，表示无符号 32 位整数
            bytes_data = struct.pack('<I', n)  # 使用无符号 32 位整数格式
        self.write_bytes(bytes_data, offset)

    def write_float(self, f, offset=-1):
        # 使用小端字节序写入4字节浮点数
        bytes_data = struct.pack('<f', f)  # < 表示小端字节序，f 表示浮点数
        self.write_bytes(bytes_data, offset)

    def write_short(self, n, offset=-1):
        # 使用小端字节序写入2字节
        # 强制将数值限制在 -32768 到 32767 之间
        n = max(-32768, min(32767, n))
        bytes_data = struct.pack('<h', n)  # < 表示小端字节序，h 表示短整数
        self.write_bytes(bytes_data, offset)

    def write_color(self, color, offset=-1):
        """Write color in little-endian order (BGR)"""
        self.write_byte(color.b, offset)
        self.write_byte(color.g)
        self.write_byte(color.r)
    def write_vec3(self, v, offset = -1):
        self.write_float(v.x, offset)
        self.write_float(v.y)
        self.write_float(v.z)

    def get_bmp_byte_padding(self, count_x) -> int:
        bytes_per_pixel = 3  # 每个像素占 3 个字节 (RGB)
        bytes_per_row = count_x * bytes_per_pixel
        padded_bytes = 0

        # 如果每行字节数不是4的倍数，需要填充
        if bytes_per_row % 4 != 0:
            padded_bytes = 4 - (bytes_per_row % 4)

        return padded_bytes

    def check_vision_pathing_flag(self, flags, flag):
        # 模拟检查标志是否设置
        return (flags & flag) != 0

    def check_vision_pathing_flag_2(self, flags, mask):
        return (flags | mask) == flags

    def get_cell_color(self, flags):
        # 根据 flags 获取颜色
        color = walkableColor

        if self.check_vision_pathing_flag(flags, VisionPathingFlags.Brush):
            color = brushColor

        if self.check_vision_pathing_flag(flags, VisionPathingFlags.Wall):
            if color == brushColor:
                color = brushWallColor  # 作为透明墙处理
            else:
                color = wallColor

        if self.check_vision_pathing_flag(flags, VisionPathingFlags.TransparentWall):
            color = transparentWallColor

        if self.check_vision_pathing_flag(flags, VisionPathingFlags.AlwaysVisible):
            color = alwaysVisibleColor

        if self.check_vision_pathing_flag(flags, VisionPathingFlags.BlueTeamOnly):
            color = blueTeamOnlyColor

        if self.check_vision_pathing_flag(flags, VisionPathingFlags.RedTeamOnly):
            color = redTeamOnlyColor

        if self.check_vision_pathing_flag(flags, VisionPathingFlags.NeutralZoneVisiblity):
            if color == blueTeamOnlyColor:
                color = blueTeamNeutralZoneVisibilityColor
            elif color == redTeamOnlyColor:
                color = redTeamNeutralZoneVisibilityColor
            else:
                color = neutralZoneVisibilityColor

        return color

    def check_river_region_flag(self, flags, flag):
        """检查指定的标志位是否设置"""
        return (flags | flag) == flags

    def get_cell_color_r(self, flags):
        """根据 flags 计算并返回对应的颜色"""
        index = 0

        if self.check_river_region_flag(flags, RiverRegionFlags.JungleQuadrant):
            index |= 1

        if self.check_river_region_flag(flags, RiverRegionFlags.BaronPit):
            index |= 2

        if self.check_river_region_flag(flags, RiverRegionFlags.River):
            index |= 4

        if self.check_river_region_flag(flags, RiverRegionFlags.RiverEntrance):
            index |= 8

        if self.check_river_region_flag(flags, RiverRegionFlags.Unknown32):
            # 如果标志为 Unknown32，则添加第 16 位
            index |= 16

        return self.get_cell_color_i(index)

    def get_cell_color_i(self, flags):
        """
        根据给定的 flags 返回对应的颜色。
        如果 flags 超过了颜色数组的范围，则返回最后一个颜色。
        """
        index = flags

        # 如果 index 超过颜色数组的最大索引，则返回最后一个颜色
        if index >= len(flag_colors):
            index = len(flag_colors) - 1

        return flag_colors[index]

    def create_bmp_file(self, filepath: str, count_x: int, count_z: int) -> None:
        bmp_file = File_Wrapper(filepath, True)
        bmp_file.open()

        bmp_file.clear()  # 清空文件
    
        # BMP 文件头
        bmp_file.write(struct.pack('<H', 0x4D42))  # 'BM' 魔术字节 (2字节)

        header_byte_size = 14 + 0x28  # 14字节文件头 + 40字节信息头

        bytes_per_pixel = 3  # RGB = 3字节
        bytes_per_row = count_x * bytes_per_pixel
        padded_bytes = self.get_bmp_byte_padding(count_x)
        bytes_per_row += padded_bytes

        pixel_byte_size = bytes_per_row * count_z
        total_byte_size = header_byte_size + pixel_byte_size

        bmp_file.write_int(total_byte_size);

        bmp_file.write_int(0);
        bmp_file.write_int(header_byte_size);

        bmp_file.write_int(0x28);
        bmp_file.write_int(count_x);
        bmp_file.write_int(count_z);
        bmp_file.write_short(1);
        bmp_file.write_short(bytes_per_pixel * 8);
        bmp_file.write_int(0);
        bmp_file.write_int(pixel_byte_size);

        bmp_file.write_int(0);
        bmp_file.write_int(0);
        bmp_file.write_int(0);
        bmp_file.write_int(0);
        return bmp_file
        # ⚠️像素数据后面再写，这里只返回文件创建函数，像素数据需要后续写入

    def write_bmp_base(self, filepath, flags):
        bmp_file = self.create_bmp_file(filepath, self.cellCountX, self.cellCountZ)
        for i in range(len(self.cells)):
            # 根据传入的标志类型（flags）来获取相应的颜色
            color = self.get_cell_color_i(getattr(self.cells[i], flags))  # 动态获取标志属性
            if flags == "riverRegionFlags":
                color = self.get_cell_color_r(self.cells[i].riverRegionFlags)  # 动态获取标志属性
            bmp_file.write_color(color)
            if i % self.cellCountX == (self.cellCountX - 1):
                for j in range(self.get_bmp_byte_padding(self.cellCountX)):
                    bmp_file.write_byte(0)
        bmp_file.close()

    def write_visionPathing_bmp_file(self, filepath):
        bmp_file = self.create_bmp_file(filepath, self.cellCountX, self.cellCountZ)
        for i in range(len(self.cells)):
            # 处理 visionPathingFlags
            filtered_pathing_flags = self.cells[i].visionPathingFlags
            filtered_pathing_flags &= ~VisionPathingFlags.Unknown128  # 清除 Unknown128 标志

            # 获取颜色并写入输出
            vision_pathing_color = self.get_cell_color(filtered_pathing_flags)
            bmp_file.write_color(vision_pathing_color)

            # 如果当前单元格是行的最后一个
            if i % self.cellCountX == (self.cellCountX - 1):  
                # 对每一行末尾进行填充
                for j in range(self.get_bmp_byte_padding(self.cellCountX)):  # 这里应该是循环行数而非 `self.cellCountX`
                    bmp_file.write_byte(0)  # 填充一个字节
        bmp_file.close()  # 关闭文件

    def write_heightSample_bmp_file(self, filepath):
        bmp_file = self.create_bmp_file(filepath, self.height_sample_count_x, self.height_sample_count_z)
        heightDiff = self.max_height_sample - self.min_height_sample;
        # 处理除零错误
        if heightDiff == 0:
            heightDiff = 1  # 避免除以零，可以设置为 1 或其他默认值
        heightSamplePaddedBytes = self.get_bmp_byte_padding(self.height_sample_count_x);
        for i in range(len(self.height_samples)):
            sample = self.height_samples[i]
            lerp = (sample - self.min_height_sample) / heightDiff;
            sampleColor = heightSampleBaseColor * lerp
            bmp_file.write_color(sampleColor)
            if i % self.height_sample_count_x == (self.height_sample_count_x - 1):  
                # 对每一行末尾进行填充
                for j in range(heightSamplePaddedBytes):  # 这里应该是循环行数而非 `self.cellCountX`
                    bmp_file.write_byte(0)  # 填充一个字节
        bmp_file.close()  # 关闭文件

    def write_new_aimesh_ngrid_file(self, filepath):
        new_file = File_Wrapper(filepath, True)
        new_file.open()
        new_file.write_byte(self.majorVersion);
        new_file.write_short(self.minorVersion);
        new_file.write_vec3(self.minBounds);
        new_file.write_vec3(self.maxBounds);
        new_file.write_float(self.cellSize);
        new_file.write_int(self.cellCountX);
        new_file.write_int(self.cellCountZ);
        if self.majorVersion == 7:
            self.writecellsVersion7(new_file)
        elif self.majorVersion == 3 or self.majorVersion == 5:
            self.writecellsVersion5(new_file)
        else:
            print("Error: unsupported version number " + self.majorVersion)
        self.writeHeightSamples(new_file)
        self.writeHintNodes(new_file)
        new_file.close()  # 关闭文件

    def write_new_aimesh_ngrid_file_as_Version(self, filepath, version):
        new_file = File_Wrapper(filepath, True)
        new_file.open()
        new_file.write_byte(version);
        new_file.write_short(self.minorVersion);
        new_file.write_vec3(self.minBounds);
        new_file.write_vec3(self.maxBounds);
        new_file.write_float(self.cellSize);
        new_file.write_int(self.cellCountX);
        new_file.write_int(self.cellCountZ);
        if self.majorVersion == 7:
            self.writecellsVersion7to5(new_file)
        self.writeHeightSamples(new_file)
        self.writeHintNodes(new_file)
        new_file.close()  # 关闭文件

    def writecellsVersion7(self, new_file):
        totalCellCount = self.cellCountX * self.cellCountZ;
        # print(f"{totalCellCount}")

        for i in range(totalCellCount):
            new_file.write_float(self.cells[i].centerHeight)
            # print("{cell.centerHeight}")
            # print(f"{cell.sessionID}")
            new_file.write_int(self.cells[i].sessionID)
            new_file.write_float(self.cells[i].arrivalCost)
            # print("{cell.arrivalCost}")
            new_file.write_int(int(self.cells[i].isOpen))  # 使用布尔值转整数
            # print(f"{cell.Heuristic}")
            new_file.write_float(self.cells[i].Heuristic)

            new_file.write_short(self.cells[i].z)
            # print("{cell.z}")
            new_file.write_short(self.cells[i].x)
            # print("{cell.x}")

            new_file.write_int(self.cells[i].actorList)
            # print("{cell.actorList}")
            # print(f"{self.read_int(new_file.get_file_position())}")
            new_file.write_int(self.read_int(new_file.get_file_position()))  # 读取并写入未知数据
            # print("{self.read_int(new_file.get_file_position())}")
            # print(f"{cell.goodCellSessionID}")
            new_file.write_int(self.cells[i].goodCellSessionID)
            new_file.write_float(self.cells[i].hintHeight)
            # print("{cell.hintHeight}")
            new_file.write_short(self.read_short(new_file.get_file_position()))  # 读取并写入未知数据
            # print("{self.read_short(new_file.get_file_position())}")
            new_file.write_short(self.cells[i].arrivalDirection)
            # print("{cell.arrivalDirection}")
            new_file.write_short(self.cells[i].hintNode1)
            # print("{cell.hintNode1}")
            new_file.write_short(self.cells[i].hintNode2)
            # print("{cell.hintNode2}")

        # 第二步：写入 visionPathingFlags
        for cell in self.cells:
            new_file.write_short(cell.visionPathingFlags)

        # 第三步：写入 riverRegionFlags 和相关的 flags
        for cell in self.cells:
            new_file.write_byte(cell.riverRegionFlags)
            new_file.write_byte(self.read_byte(new_file.get_file_position()))  # 读取并写入未知数据
            new_file.write_byte(self.read_byte(new_file.get_file_position()))  # 读取并写入未知数据
            new_file.write_byte(cell.ringFlags)

        # 第四步：写入未知块（每块132字节）
        for _ in range(8):  # 8个块
            for _ in range(132):  # 每块132字节
                new_file.write_byte(self.read_byte(new_file.get_file_position()))

    def writecellsVersion5(self, new_file):
        totalCellCount = self.cellCountX * self.cellCountZ;

        for i in range(totalCellCount):
            new_file.write_float(self.cells[i].centerHeight)
            new_file.write_int(self.cells[i].sessionID)
            new_file.write_float(self.cells[i].arrivalCost)
            new_file.write_int(int(self.cells[i].isOpen))
            new_file.write_float(self.cells[i].Heuristic)
            new_file.write_int(self.cells[i].actorList)
            new_file.write_short(self.cells[i].x)
            new_file.write_short(self.cells[i].z)

            new_file.write_float(self.read_float(new_file.get_file_position()))
            new_file.write_float(self.read_float(new_file.get_file_position()))
            new_file.write_int(self.read_int(new_file.get_file_position()))
            new_file.write_int(self.cells[i].goodCellSessionID)
            new_file.write_float(self.cells[i].hintHeight)
            new_file.write_short(self.cells[i].arrivalDirection)
            new_file.write_short(int(self.cells[i].visionPathingFlags))
            new_file.write_short(self.cells[i].hintNode1)
            new_file.write_short(self.cells[i].hintNode2)

        if self.majorVersion == 5:
            for i in range(totalCellCount):
                new_file.write_byte(self.cells[i].riverRegionFlags)
                new_file.write_byte(self.read_byte(new_file.get_file_position()))

            for i in range(4):
                for j in range(132):
                    new_file.write_byte(self.read_byte(new_file.get_file_position()))

    def writecellsVersion7to5(self, new_file):
        totalCellCount = self.cellCountX * self.cellCountZ
        for i in range(totalCellCount):
            new_file.write_float(self.cells[i].centerHeight)
            new_file.write_int(self.cells[i].sessionID)
            new_file.write_float(self.cells[i].arrivalCost)
            new_file.write_int(int(self.cells[i].isOpen))
            new_file.write_float(self.cells[i].Heuristic)
            new_file.write_int(self.cells[i].actorList)
            new_file.write_short(self.cells[i].x)
            new_file.write_short(self.cells[i].z)
            new_file.write_float(0)
            new_file.write_float(0)
            new_file.write_int(0)
            new_file.write_int(self.cells[i].goodCellSessionID)
            new_file.write_float(self.cells[i].hintHeight)
            new_file.write_short(self.cells[i].arrivalDirection)
            new_file.write_short(int(self.cells[i].visionPathingFlags))
            new_file.write_short(self.cells[i].hintNode1)
            new_file.write_short(self.cells[i].hintNode2)

        for i in range(totalCellCount):
            new_file.write_byte(self.cells[i].riverRegionFlags)
            new_file.write_byte(self.cells[i].jungleQuadrantFlags)  # 读取并写入未知数据
            # new_file.write_byte(0)
        for i in range(4):
            for j in range(132):
                # 尝试找到未知块开始的位置，然后写入
                new_file.write_byte(self.read_byte(self.unknown_blockstartpos))

    def writeHeightSamples(self, new_file):
        new_file.write_int(self.height_sample_count_x)
        new_file.write_int(self.height_sample_count_z)
        new_file.write_float(self.height_sample_offset_x)
        new_file.write_float(self.height_sample_offset_z)

        totalCount = self.height_sample_count_x * self.height_sample_count_z
        for i in range(totalCount):
            new_file.write_float(self.height_samples[i])

    def writeHintNodes(self, new_file):
        for row_data, (hint_x, hint_y) in self.hint_nodes:
            # 写入每行的 900 个 float 数据
            for distance in row_data:
                new_file.write_float(distance)
            # 写入每行的 2 个 short 数据（hint_x, hint_y）
            new_file.write_short(hint_x)
            new_file.write_short(hint_y)