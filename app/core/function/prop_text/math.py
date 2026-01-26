def format_number(n: float) -> str:
    if int(n) == n:
        return str(int(n))
    return f"{n:.9f}".rstrip('0').rstrip('.')

def safe_div_vec(vec, constant_vec):
    """
    对 ve3 或 ve4 进行安全除法。
    vec: ve3或ve4对象 (x,y,z[,a])
    constant_vec: ve3或ve4对象，用作除数
    返回同类型的元组 (x, y, z[, a])
    """
    vals = []
    for v_attr, c_attr in zip(vec, constant_vec):
        v = v_attr / c_attr if c_attr else v_attr
        # 转整数，如果结果正好是整数
        vals.append(int(v) if v == int(v) else v)
    return tuple(vals)