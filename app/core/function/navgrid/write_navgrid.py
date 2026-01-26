import os
import io
from ..general import*

def write_navgrid_from_version(navgrid, version, file):
    header = navgrid.header
    write_navgrid_header_from_version(header, version, file)
    write_navgrid_data_from_version(navgrid, version, file)

def write_navgrid_header_from_version(header, version, file):
    write_binary(get_bytes_uint8(version), file)
    if version != 2:
        write_binary(get_bytes_uint16(header.minor), file)

def write_navgrid_data_from_version(navgrid, version, file):
    data = navgrid.data
    write_vector3(data.minBounds, file)
    write_vector3(data.maxBounds, file)
    write_binary(get_bytes_float(data.cellSize), file)
    write_binary(get_bytes_uint32(data.cellCountX), file)
    write_binary(get_bytes_uint32(data.cellCountZ), file)
    write_cells(version, data, file)
    write_height_samples(data, file)
    write_hint_nodes(data, file)

def write_navgrid(navgrid, file):
    header = navgrid.header
    write_navgrid_header(header, file)
    write_navgrid_data(navgrid, file)

def write_navgrid_header(header, file):
    write_binary(get_bytes_uint8(header.major), file)
    if header.major != 2:
        write_binary(get_bytes_uint16(header.minor), file)

def write_navgrid_data(navgrid, file):
    major = navgrid.header.major
    data = navgrid.data
    write_vector3(data.minBounds, file)
    write_vector3(data.maxBounds, file)
    write_binary(get_bytes_float(data.cellSize), file)
    write_binary(get_bytes_uint32(data.cellCountX), file)
    write_binary(get_bytes_uint32(data.cellCountZ), file)
    # cell_map = write_cells(major, cellCountX * cellCountZ, file)
    # height_samples = write_height_samples(file)
    # hint_nodes = write_hint_nodes(file)

def write_cells(version, data, file):
    if version == 7:
        write_cells_from_version7(data, file)
    elif version == 3 or version == 5:
        write_cells_from_version5(data, file)
    else:
        print("Error: unsupported version number " + version)

def write_cells_base_data(cell, file):
    r_write_float(file, cell.centerHeight)
    r_write_int(file, cell.sessionID)
    r_write_float(file, cell.arrivalCost)
    r_write_float(file, cell.isOpen)
    r_write_float(file, cell.Heuristic)

def write_cells_all_data_leagcy(cell, file):
    r_write_int(file, cell.actorList)
    r_write_short(file, cell.pos.x)
    r_write_short(file, cell.pos.y)
    r_write_float(file, cell.additional_cost)
    r_write_float(file, cell.hint_as_good_cell)
    r_write_int(file, cell.additional_cost_count)
    r_write_int(file, cell.good_cell_session_ID)
    r_write_float(file, cell.hint_weight)
    r_write_short(file, cell.arrivalDirection)
    r_write_short(file, int(cell.visionPathingFlags))
    r_write_short(file, cell.hintNode1)
    r_write_short(file, cell.hintNode2)

def write_cells_from_version2(cell_count, file):
    cells = data.cellsmap.cells
    for cell in cells:
        write_cells_base_data(cell, file)
        write_cells_all_data_leagcy(cell, file)

def write_cells_from_version5(data, file):
    cells = data.cellsmap.cells
    unknown_block = data.cellsmap.unknown_block
    for cell in cells:
        write_cells_base_data(cell, file)
        write_cells_all_data_leagcy(cell, file)
    for cell in cells:
        r_write_byte(file, cell.riverRegionFlags)
        jungleQuadrantFlags = int(cell.jungleQuadrantFlags) & 0x0F
        mainRegionFlags = (int(cell.mainRegionFlags) & 0x0F) << 4
        r_write_byte(file, jungleQuadrantFlags | mainRegionFlags)
    for i in range(4):
        for byte in unknown_block[i]:
            r_write_byte(file, byte)

def write_cells_from_version7(data, file):
    cells = data.cellsmap.cells
    unknown_block = data.cellsmap.unknown_block
    for cell in cells:
        write_cells_base_data(cell, file)
        r_write_short(file, cell.pos.x)
        r_write_short(file, cell.pos.y)
        r_write_int(file, cell.actorList)
        r_write_int(file, cell.unknown1)
        r_write_int(file, cell.goodCellSessionID)
        r_write_float(file, cell.hintHeight)
        r_write_short(file, cell.unknown2)
        r_write_short(file, cell.arrivalDirection)
        r_write_short(file, cell.hintNode1)
        r_write_short(file, cell.hintNode2)

    for cell in cells:
        r_write_short(file, cell.visionPathingFlags)

    for cell in cells:
        r_write_byte(file, cell.riverRegionFlags)
        jungleQuadrantFlags = int(cell.jungleQuadrantFlags) & 0x0F
        mainRegionFlags = (int(cell.mainRegionFlags) & 0x0F) << 4
        r_write_byte(file, jungleQuadrantFlags | mainRegionFlags)
        nearestLaneFlags = int(cell.nearestLaneFlags) & 0x0F
        poiFlags = (int(cell.poiFlags) & 0x0F) << 4
        r_write_byte(file, nearestLaneFlags | poiFlags)
        ringFlags = int(cell.ringFlags) & 0x0F
        srxFlags = (int(cell.srxFlags) & 0x0F) << 4
        r_write_byte(file, ringFlags | srxFlags)

    for line in unknown_block:
        for byte in line:
            r_write_byte(file, byte)

def write_height_samples(data, file):
    height_samples = data.height_samples
    vector = height_samples.vector
    r_write_int(file, vector.count.x)
    r_write_int(file, vector.count.y)
    r_write_float(file, vector.offset.x)
    r_write_float(file, vector.offset.y)

    for height_sample in height_samples.height_samples:
        r_write_float(file, height_sample)

def write_hint_nodes(data, file):
    for row_data, hint in data.hint_nodes:
        # 写入每行的 900 个 float 数据
        for distance in row_data:
            r_write_float(file, distance)
        # 写入每行的 2 个 short 数据（hint_x, hint_y）
        r_write_short(file, hint.x)
        r_write_short(file, hint.y)

def r_seek(file, offset=-1, seek_origin=io.SEEK_SET):
    if offset != -1 or seek_origin != io.SEEK_SET:
        file.seek(offset, seek_origin)
    else:
        # 使用默认参数（无效），什么也不做
        pass

def r_write_bytes(file, bytes_data, offset=-1):
    try:
        # 记录当前文件指针位置
        old_position = file.tell()

        # 如果提供了偏移量，移动文件指针
        r_seek(file, offset)

        # 写入字节数据
        file.write(bytes_data)

        # 如果偏移量被指定，恢复文件指针位置
        if offset != -1:
            r_seek(file, old_position)
    except Exception as e:
        error_string = "Error writing to file:  "

        # 打印每个字节的值
        error_string += ' '.join([str(byte) for byte in bytes_data])

        error_string += f"\n{e.__class__.__name__}\n{e}"

        print(error_string)

def r_write_byte(file, n, offset=-1):
    # 将整数n转换为字节（1字节）
    byte_data = struct.pack('<B', n)  # '<B'表示一个字节（unsigned char），小端字节序
    r_write_bytes(file, byte_data, offset)

def r_write_int(file, n, offset=-1):
    # 使用小端字节序写入4字节
    # 如果值小于 0 或大于 4294967295，强制为无符号 32 位整数
    if n < 0x80000000:  # 小于 2^31，表示正数或零
        bytes_data = struct.pack('<i', n)  # 使用有符号 32 位整数格式
    else:  # 大于等于 2^31，表示无符号 32 位整数
        bytes_data = struct.pack('<I', n)  # 使用无符号 32 位整数格式
    r_write_bytes(file, bytes_data, offset)

def r_write_float(file, f, offset=-1):
    # 使用小端字节序写入4字节浮点数
    bytes_data = struct.pack('<f', f)  # < 表示小端字节序，f 表示浮点数
    r_write_bytes(file, bytes_data, offset)

def r_write_short(file, n, offset=-1):
    # 使用小端字节序写入2字节
    # 强制将数值限制在 -32768 到 32767 之间
    # n = max(-32768, min(32767, n))
    bytes_data = struct.pack('<H', n)  # < 表示小端字节序，h 表示短整数
    r_write_bytes(file, bytes_data, offset)
