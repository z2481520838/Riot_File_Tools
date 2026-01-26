import xxhash
import struct

def xxhash64(source: str, seed: int = 0) -> int:
    # 将字符串转换为 UTF-8 字节
    source_utf8 = source.encode('utf-8')

    # 如果字节长度大于512，使用更高效的处理方式（尽管在Python中通常不需要手动内存管理）
    if len(source_utf8) > 512:
        # 你可以选择在此处处理较大的数据，例如分块处理或缓存
        return xxhash.xxh64(source_utf8, seed=seed).intdigest()
    else:
        # 对于较小的数据直接计算哈希
        return xxhash.xxh64(source_utf8, seed=seed).intdigest()

# 示例使用
source = "HideGeo"
seed = 1
hash_value = xxhash64(source, seed)
print(f"Hash: {hash_value}")
