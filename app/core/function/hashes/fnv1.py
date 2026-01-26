#blnd事件名
def fnv1(s, a2=0x811C9DC5):
    result = a2
    for char in s:
        result *= 16777619
        result ^= ord(char)
    return result & 0xFFFFFFFF

def fnv1_lower(s):
    return fnv1(s.lower())

if __name__ == '__main__':
    # 输入字符串
    s = "UI_CastBar"
    hash_value = fnv1(s)
    print(f"fnv1 hash for '{s}': {hash_value}, (十六进制): 0x{hash_value:X}")
    # 测试小写版本
    hash_value_lower = fnv1(s.lower())
    print(f"fnv1 hash for '{s.lower()}': {hash_value_lower}, (十六进制): 0x{hash_value_lower:X}")