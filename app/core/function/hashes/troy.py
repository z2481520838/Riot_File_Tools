def compute_troy_hash(section: str, property_name: str) -> int:
    """
    实现 League Hashes 中 TroyViewModel 使用的哈希计算逻辑。
    该算法将 Section 和 Property 字符串连接起来，使用 DJB 哈希变体（乘数 65599）。
    结构：
    [section]
    property_name=0

    Args:
        section: 哈希的第一部分字符串 (Section)。
        property_name: 哈希的第二部分字符串 (Property)。

    Returns:
        32位无符号整数哈希值。
    """
    
    # 检查输入是否为 None 或空，如果为 None，则返回 0，模拟 C# 中的 early return
    if section is None or property_name is None:
        return 0

    # 常量定义
    MULTIPLIER = 65599
    SECTION_SEPARATOR_VALUE = 42
    # 32位无符号整数掩码，用于模拟 C# 的 uint 溢出
    MASK = 0xFFFFFFFF
    
    hash_value = 0
    
    # 预处理：转换为小写
    section_lower = section.lower()
    property_lower = property_name.lower()
    
    # --- 第一部分：处理 Section 字符串 ---
    # 公式: hash = char + 65599 * hash
    for char in section_lower:
        # ord(char) 获取字符的 ASCII 值
        hash_value = (ord(char) + MULTIPLIER * hash_value) & MASK
        
    # --- 中间步骤：插入分隔常量 42 ---
    # 公式: hash = 65599 * hash + 42
    hash_value = (MULTIPLIER * hash_value + SECTION_SEPARATOR_VALUE) & MASK
    
    # --- 第二部分：处理 Property 字符串 ---
    # 公式: hash = char + 65599 * hash
    for char in property_lower:
        hash_value = (ord(char) + MULTIPLIER * hash_value) & MASK
        
    return hash_value

if __name__ == '__main__':
    # --- 示例用法 (非核心逻辑，仅供测试) ---
    section_input = "AscensionBackground"
    property_input = "RegionX"
    result = compute_troy_hash(section_input, property_input)
    print(f"输入: [{section_input}, {property_input}]")
    print(f"哈希结果 (十进制): {result}")
    print(f"哈希结果 (十六进制): 0x{result:X}")