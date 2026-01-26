#submesh
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

if __name__ == '__main__':
    # 测试
    s = "UI_CastBar"
    hash_value = elf_hash(s)
    print(f"Elf hash for '{s}': {hash_value}, (十六进制): 0x{hash_value:X}")
    # 测试小写版本
    hash_value_lower = elf_hash_lower(s)
    print(f"Elf hash for '{s.lower()}': {hash_value_lower}, (十六进制): 0x{hash_value_lower:X}")