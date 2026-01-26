#动作名，路径，事件名，bin.submesh...
def fnv1a(s, a2=0x811C9DC5):
    result = a2
    for char in s:
        result = 16777619 * (result ^ ord(char))  # ord(char) 获取字符的 ASCII 值
    return result & 0xFFFFFFFF

def fnv1a_lower(s):
    return fnv1a(s.lower())

if __name__ == '__main__':
    # 输入字符串
    s = "UI_CastBar"
    hash_value = fnv1a(s)
    print(f"fnv1a hash for '{s}': {hash_value}, (十六进制): 0x{hash_value:X}")
    # 测试小写版本
    hash_value_lower = fnv1a(s.lower())
    print(f"fnv1a hash for '{s.lower()}': {hash_value_lower}, (十六进制): 0x{hash_value_lower:X}")
