import struct
from typing import List

def hash_string_fnv1a(s, a2=0x811C9DC5):
    result = a2
    for char in s:
        result = 16777619 * (result ^ ord(char))  # ord(char) 获取字符的 ASCII 值
    return result & 0xFFFFFFFF

# submesh
def elf_hash(to_hash):
    hash_value = 0
    high = 0
    for char in to_hash:
        hash_value = (hash_value << 4) + ord(char)  # 相当于 (hash << 4) + (byte)char

        high = hash_value & 0xF0000000
        if high != 0:
            hash_value ^= high >> 24  # 如果 high 不为0，执行高位右移并异或

        hash_value &= ~high  # 清除高位

    return hash_value & 0xFFFFFFFF  # 确保返回32位的哈希值

def elf_hash_lower(value):
    return elf_hash(value.lower())
def str_to_hash_list(a):
    for b in a:
        b.PathHash = hash_string_fnv1a(b.Path)
def get_all_offset(a):
    data_start = 108
    if len(a.mBlendDataAry) > 0:
        a.mBlendDataAryAddr = data_start
        for _ in a.mBlendDataAry:
            data_start += 16
    if len(a.mTransitionData) > 0:
        a.mTransitionDataOffset = data_start
        for _ in a.mTransitionData:
            data_start += 12
            if len(_.TransitionTo) > 0:
                for k in _.TransitionTo:
                    data_start += 8
        for i in range(len(a.mTransitionData)):
            count = len(a.mTransitionData)
            offset = count * 12 - 8
            if i > 0:
                m = count - i
                offset = m * 12 - 8
                for t in range(count - m):
                    offset += a.mTransitionData[t].get_data_size()
            a.mTransitionData[i].aligning_offset(offset)
    if len(a.mBlendTrackAry) > 0:
        a.mBlendTrackAryAddr = data_start
        for _ in a.mBlendTrackAry:
            _.get_start_pos(data_start)
            data_start += 48
    if len(a.mClassAry) > 0:
        a.mClassAryAddr = data_start
        for _ in a.mClassAry:
            _.aligning_data()
            data_start += _.get_resource_size_and_event() + 4 # dataoffset = 4
    if len(a.mMaskDataAry) > 0:
        a.mMaskDataAryAddr = data_start
        data_start += len(a.mMaskDataAry)*4
        for _ in a.mMaskDataAry:
            _.aligning_data()
            _.get_start_pos(data_start)
            data_start += _.get_resource_size()
    if len(a.mEventDataAry) > 0:
        a.mEventDataAryAddr = data_start
        for _ in a.mEventDataAry:
            data_start += 4
            # _.aligning_data()
    if len(a.mAnimDataAry) > 0:
        a.mAnimDataAryAddr = data_start
        for _ in a.mAnimDataAry:
            if _ is None:
                data_start += 4
            else:
                data_start += _.get_resource_size()
    if len(a.mAnimNames) > 0:
        a.mAnimNamesOffset = data_start
        count = len(a.mAnimNames)
        for c in range(count):
            a.mAnimNames[c].PathOffset = (count - c) * 8 - 4
            if c > 0:
                for d in range(c):
                    a.mAnimNames[c].PathOffset += get_bytes_str_with_padding(a.mAnimNames[d].Path)
        for _ in a.mAnimNames:
            data_start += 8 + get_bytes_str_with_padding(_.Path)
    a.mSkeleton.PathOffset = data_start - 100 # mSkeleton.PathOffset Pos = 100

def get_track_pos(a):
    for _ in a.mClassAry:
        if hasattr(_.mClipData, 'mTrackDataID'):
            _.mClipData.mTrackDataAddr = a.mBlendTrackAry[_.mClipData.mTrackDataID].start_pos

def get_mask_pos(a):
    for _ in a.mClassAry:
        if hasattr(_.mClipData, 'mMaskDataID'):
            if _.mClipData.mMaskDataID is not None:
                _.mClipData.mMaskDataAddr = a.mMaskDataAry[_.mClipData.mMaskDataID].start_pos

def get_all_resource_size(a):
    for b in a:
        b.mResourceSize = b.get_resource_size()

def get_bytes_str(string, length):
    """
    获取字符串的字节表示，并按指定长度填充至适当的长度。
    如果字符串超过了指定的长度，会截断至指定长度。
    如果字符串小于指定的长度，会使用 null 字节（\0）填充。

    :param string: 要处理的字符串
    :param length: 字符串的最大长度（包括 null 终结符）
    :return: 返回处理后的字节数组
    """
    # 对字符串进行 UTF-8 编码
    str_bytes = string.encode('utf-8')
    
    # 确保字符串以 null 结尾，并根据长度填充或截断
    str_bytes = str_bytes[:length-1] + b'\0'  # 添加 null 终结符并确保不超过指定长度
    
    # 使用 padding 填充至指定的长度（如果有必要）
    return str_bytes.ljust(length, b'\0')  # 返回填充后的字节数组

def get_bytes_str_with_padding(string):
    encoded_name = None
    if string is None:
        encoded_name = b'\0'
    else:
        # 将 string 编码为 UTF-8
        encoded_name = string.encode('utf-8') + b'\0'
    
    # 计算当前编码后的长度
    current_length = len(encoded_name)  # +1 是因为我们将要添加 \0
    
    # 计算填充字节数，使总长度对齐到 4 的倍数
    padding_length = (4 - current_length % 4) % 4  # 计算需要的填充字节数
    
    # 填充零字节
    encoded_name += b'\0' * padding_length
    return len(encoded_name)  # 返回填充后的字节数组

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

def aligning_data(a):
    a.aligning_data()

def aligning_data_list(a):
    for b in a:
        b.aligning_data()

def write_with_padding(path, bw):
    # 将 path 编码为 UTF-8
    encoded_name = path.encode('utf-8') + b'\0'
    
    # 计算当前编码后的长度
    current_length = len(encoded_name)  # +1 是因为我们将要添加 \0
    
    # 计算填充字节数，使总长度对齐到 4 的倍数
    padding_length = (4 - current_length % 4) % 4  # 计算需要的填充字节数
    
    # 填充零字节
    encoded_name += b'\0' * padding_length
    
    # 写入数据
    bw.write(encoded_name)

def determine(a, b):
    if a > 0:
        return a - b
    return 0

def write_string(bw, string, length):
    # 将字符串编码为 UTF-8 字节
    encoded_string = string.encode('utf-8')
    
    # 如果编码后的字符串长度小于指定长度，填充空字符（零字节）
    if len(encoded_string) < length:
        padding_length = length - len(encoded_string)  # 计算填充的字节数
        encoded_string += b'\0' * padding_length  # 填充零字节
    
    # 如果编码后的字符串长度大于指定长度，截断到指定长度
    elif len(encoded_string) > length:
        encoded_string = encoded_string[:length]  # 截断多余的字节
    
    # 返回填充或截断后的字节数据
    # return encoded_string
    bw.write(encoded_string)

def write_byte(a, b):
    a.write(b)

def write_obj(a, b):
    a.write(b)

def write_uint32_list(a, b):
    for c in a:
        write_byte(b, get_bytes_uint32(c))

def write_float_list(a, b):
    for c in a:
        write_byte(b, get_bytes_float(c))

def write_obj_list(a, b):
    if len(a) > 0:
        for c in a:
            c.write(b)

def write_obj_list_or_null(a, b):
    if len(a) > 0:
        for c in a:
            if c is None:
                write_byte(b, get_bytes_uint32(0))
            else:
                c.write(b)

def write_addr_list(a, b):
    if len(a) > 0:
        for c in range(len(a)):
            distance = (len(a) - c) * 4
            if c > 0:
                for d in range(c):
                    distance += a[d].mResourceSize
            write_byte(b, get_bytes_int32(distance))

def write_addr_list_at_baseaddr(a, b):
    if len(a) > 0:
        for c in range(len(a)):
            distance = (len(a) - c) * 4 + 4 * c
            if c > 0:
                for d in range(c):
                    distance += a[d].mResourceSize
            write_byte(b, get_bytes_int32(distance))

def write_addr_list_at_baseaddr_class(a, b):
    if len(a) > 0:
        for c in range(len(a)):
            distance = (len(a) - c) * 4 + 4 * c
            if c > 0:
                for d in range(c):
                    distance += a[d].get_resource_size_and_event()
            write_byte(b, get_bytes_int32(distance))

def append_animdata(a, b, c):
    a.append(None)
    b.append(c)

def get_anim_path(a, b):
    return a + b + ".anm"
