from ..general import*
from .write_navgrid import r_write_byte, r_write_int, r_write_short
from .draw_navgrid import get_vision_pathing_color, get_cell_flag_color, get_region_flag_color, heightSampleBaseColor
from ...objects.navgrid.navgrid_cell import (NavGridCell, VisionPathingFlags, RiverRegionFlags, 
                                             JungleQuadrantFlags, MainRegionFlags, NearestLaneFlags,
                                             POIFlags, RingFlags, UnknownSRXFlags, CellMap, HeightSampleVector, HeightSampleMap)

layer_flags = {
    "River Regions": "riverRegionFlags",
    "Jungle Quadrants": "jungleQuadrantFlags",  # 这里用到 pixmap 或其他特殊处理
    "Main Region": "mainRegionFlags",
    "Nearest Lane": "nearestLaneFlags",
    "POI Flags": "poiFlags",
    "Ring Flags": "ringFlags",
    "SRX Flags": "srxFlags"
}

def get_bmp_byte_padding(count_x) -> int:
    bytes_per_pixel = 3  # 每个像素占 3 个字节 (RGB)
    bytes_per_row = count_x * bytes_per_pixel
    padded_bytes = 0

    # 如果每行字节数不是4的倍数，需要填充
    if bytes_per_row % 4 != 0:
        padded_bytes = 4 - (bytes_per_row % 4)

    return padded_bytes

def create_bmp_file(bmp_file, count_x, count_z) -> None:
    # BMP 文件头
    write_binary(get_bytes_uint16(0x4D42), bmp_file)

    header_byte_size = 14 + 0x28  # 14字节文件头 + 40字节信息头

    bytes_per_pixel = 3  # RGB = 3字节
    bytes_per_row = count_x * bytes_per_pixel
    padded_bytes = get_bmp_byte_padding(count_x)
    bytes_per_row += padded_bytes

    pixel_byte_size = bytes_per_row * count_z
    total_byte_size = header_byte_size + pixel_byte_size

    r_write_int(bmp_file, total_byte_size)

    r_write_int(bmp_file, 0)
    r_write_int(bmp_file, header_byte_size)

    r_write_int(bmp_file, 0x28)
    r_write_int(bmp_file, count_x)
    r_write_int(bmp_file, count_z)
    r_write_short(bmp_file, 1)
    r_write_short(bmp_file, bytes_per_pixel * 8)
    r_write_int(bmp_file, 0)
    r_write_int(bmp_file, pixel_byte_size)

    r_write_int(bmp_file, 0)
    r_write_int(bmp_file, 0)
    r_write_int(bmp_file, 0)
    r_write_int(bmp_file, 0)
    return bmp_file
    # ⚠️像素数据后面再写，这里只返回文件创建函数，像素数据需要后续写入

def write_bmp_file(file, item, data):
    if item.text() == "Height Samples":
        write_heightSample_bmp_file(data, file)
    elif item.text() == "Vision Pathing":
        write_visionPathing_bmp_file(data, file)
    else:
        flags = layer_flags.get(item.text())
        # 这里根据item.text()再字典中的value来获取flags
        write_bmp_base(data, file, flags)

def write_bmp_base(data, file, flags):
    bmp_file = create_bmp_file(file, data.cellCountX, data.cellCountZ)
    cells = data.cellsmap.cells
    for i, cell in enumerate(cells):
        # 根据传入的标志类型（flags）来获取相应的颜色
        color = get_cell_flag_color(getattr(cell, flags))  # 动态获取标志属性
        if flags == "riverRegionFlags":
            color = get_region_flag_color(cell.riverRegionFlags)  # 动态获取标志属性
        r_write_color(bmp_file, color)
        if i % data.cellCountX == (data.cellCountX - 1):
            for j in range(get_bmp_byte_padding(data.cellCountX)):
                r_write_byte(bmp_file, 0)

def write_visionPathing_bmp_file(data, file):
    bmp_file = create_bmp_file(file, data.cellCountX, data.cellCountZ)
    cells = data.cellsmap.cells
    for i, cell in enumerate(cells):
        filtered_pathing_flags = cell.visionPathingFlags
        filtered_pathing_flags &= ~VisionPathingFlags.Unknown128

        vision_pathing_color = get_vision_pathing_color(filtered_pathing_flags)
        r_write_color(bmp_file, vision_pathing_color)

        if i % data.cellCountX == (data.cellCountX - 1):
            for j in range(get_bmp_byte_padding(data.cellCountX)):
                r_write_byte(bmp_file, 0)

def write_heightSample_bmp_file(data, file):
    height_samples = data.height_samples
    count = height_samples.vector.count
    bmp_file = create_bmp_file(file, count.x, count.y)
    heightDiff = height_samples.max_height_sample - height_samples.min_height_sample
    # 处理除零错误
    if heightDiff == 0:
        heightDiff = 1  # 避免除以零，可以设置为 1 或其他默认值
    heightSamplePaddedBytes = get_bmp_byte_padding(count.x)
    for i, sample in enumerate(height_samples.height_samples):
        lerp = (sample - height_samples.min_height_sample) / heightDiff
        sampleColor = heightSampleBaseColor * lerp
        r_write_color(bmp_file, sampleColor)
        if i % count.x == (count.x - 1):  
            # 对每一行末尾进行填充
            for j in range(heightSamplePaddedBytes):  # 这里应该是循环行数而非 `self.cellCountX`
                r_write_byte(bmp_file, 0)  # 填充一个字节

def r_write_color(file, color, offset=-1):
    """Write color in little-endian order (BGR)"""
    r_write_byte(file, color.b, offset)
    r_write_byte(file, color.g)
    r_write_byte(file, color.r)