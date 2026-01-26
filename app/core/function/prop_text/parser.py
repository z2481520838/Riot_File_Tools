from ...objects.prop_text.prop_text_obj import*
from ...objects.prop_text.base_value import*
import re
from typing import Any, Dict, List, Tuple, Optional, Type
from dataclasses import fields, is_dataclass
from collections.abc import Iterable
from ...manager.hashes.hashes_manager import GLOBAL_HASH_MANAGER

BASIC_TYPES = {
    "hash": hash,
    "bool": bool,
    "link": str,
    "string": str,
    "rgba": rgba,
    "vec2": vec2,
    "vec3": vec3,
    "vec4": vec4,
    "u64": u64,
    "i64": i64,
    "f64": f64,
    "u32": u32,
    "i32": i32,
    "f32": f32,
    "u16": u16,
    "i16": i16,
    "f16": f16,
    "u8": u8,
    "i8": i8,
    "f8": f8,
    "flag": flag,
    "mtx44": mtx44,
}

def convert_hash(hash_key: str):
    if not GLOBAL_HASH_MANAGER.HASH_TABLE:  # 避免空字典浪费循环
        raise ValueError("HASH_TABLE is empty, cannot parse embed without loaded hash tables.")

    key = hash_key[2:]  # 去掉 '0x'

    # 遍历嵌套字典查找
    for readable_dict in GLOBAL_HASH_MANAGER.HASH_TABLE.values():
        name = readable_dict.get(key)
        if name:
            return name, False  # 找到映射，非未知

    return key, True  # 未找到，标记为未知

# 辅助解析 vec4, vec3, vec2
def parse_vec(text: str, type_name: str):
    """
    根据 type_name 创建 vec 对象，如 'vec3', 'vec4'
    """
    # 提取数值
    try:
        parts = text.strip("{} ").replace(',', ' ').split()
        nums = [float(x) for x in parts if x]
    except Exception:
        nums = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', text)
        nums = list(map(float, nums))

    # 动态找到类
    cls = globals().get(type_name)  # 或者 TYPE_REGISTRY[type_name]
    if not cls:
        raise ValueError(f"Unsupported vec type: {type_name}")

    # 检查维度
    if len(nums) != len(fields(cls)):
        raise ValueError(f"{type_name} expects {len(fields(cls))} components, got {len(nums)}")

    return cls(*nums)

# 去除注释和空行
def preprocess(text: str) -> str:
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        clean_lines.append(line)
    return '\n'.join(clean_lines)

def parse_mtx44(text: str) -> "mtx44":
    """
    将形如：
    {
        -0.99999994, 0, 8.74227766e-08, 0
        0, 0.99999994, 0, 0
        -8.74227695e-08, 0, -0.999999881, 0
        0, 0, 0, 1
    }
    解析为 mtx44(rows=[[...], [...], ...])
    """
    inner_match = re.search(r'\{\s*(.*)\s*\}', text, re.S)
    if not inner_match:
        return mtx44()  # 默认单位矩阵
    inner = inner_match.group(1).strip()

    rows = []
    for line in inner.splitlines():
        line = line.strip()
        if not line:
            continue
        # 按逗号分割，每个元素转换为float
        nums = [float(x) for x in line.split(',') if x.strip()]
        rows.append(nums)
    return mtx44(rows=rows)

# 递归解析嵌套结构的核心函数
def parse_block(text: str, cls: type) -> Any:
    obj_kwargs = {}
    cls_fields = {f.name.lower(): f.name for f in fields(cls)}  # 将字段名转换为小写字典

    # 去除最外层的ClassName { }标签
    inner_match = re.search(r'\{(.*)\}\s*$', text, re.S)
    if not inner_match:
        raise ValueError(f"Cannot find block content for class {cls.__name__}")
    inner = inner_match.group(1).strip()

    # 按行拆分，但要支持list的{}和嵌套结构，使用堆栈解析（简易版）
    lines = split_lines_balanced(inner)
    for line in lines:
        m = re.match(r'(\w+):\s*([\w\[\],]+)\s*=\s*(.+)', line, re.S)
        if not m:
            continue
        field_name, type_name, value = m.groups()
        value = value.strip()
        is_unkonwn = False
        if field_name.startswith("0x"):
            field_name, unkonwn = convert_hash(field_name)
            is_unkonwn = unkonwn
        # 使用小写的字段名进行匹配
        field_name_lower = field_name.lower()
        

        # 如果字段名是 _pass，直接处理
        
        if is_unkonwn:
            field_name_lower = f"unknown_{field_name_lower}"
        if field_name_lower == "pass" or field_name_lower == "type":
            field_name_lower = f"_{field_name_lower}"  # 确保字段名与实际字段名匹配
        if field_name_lower not in cls_fields:
            print(field_name)
            continue

        field_name = cls_fields[field_name_lower]

        if type_name.startswith("option[") and type_name.endswith("]"):
            obj_kwargs[field_name] = parse_option(type_name, value)
        elif type_name.startswith('list[') or type_name.startswith('list2['):
            inner_type = type_name[type_name.index('[') + 1 : -1]  # 自动截取方括号里的类型
            val_list = parse_list(value, inner_type, cls, field_name)
            obj_kwargs[field_name] = val_list
        elif type_name.startswith('map['):
            d = parse_map(value, cls, field_name)
            obj_kwargs[field_name] = d
        elif type_name in BASIC_TYPES:
            if type_name.startswith('vec'):
                obj_kwargs[field_name] = parse_vec(value, type_name)
            elif type_name == "mtx44":
                obj_kwargs[field_name] = parse_mtx44(value)
            elif type_name == "rgba":
                obj_kwargs[field_name] = parse_vec(value, "vec4")
            else:
                val = parse_basic_value(type_name, value)
                obj_kwargs[field_name] = val
        elif type_name == 'embed' or type_name == 'pointer':
            sub_obj = parse_embed(value)
            obj_kwargs[field_name] = sub_obj
        else:
            obj_kwargs[field_name] = value

    return cls(**obj_kwargs)

def unwrap_braces_once(s: str) -> str:
    """去掉一层最外层的大括号 { ... }，如果没有则原样返回"""
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        return s[1:-1].strip()
    return s

def parse_option(type_name: str, value: str):
    """
    解析 option[T] 格式
    支持 option[vec*] 和 option[基本类型]
    """
    assert type_name.startswith("option[") and type_name.endswith("]")
    inner_type = type_name[len("option["):-1].strip()

    # option 没值
    if not (value.startswith("{") and value.endswith("}")):
        return None

    inner_val_str = unwrap_braces_once(value)  # 去掉第一层 {}

    if inner_type.startswith("vec"):
        # vec 通常是 {{ ... }}，还需要再剥一层
        inner_val_str = unwrap_braces_once(inner_val_str)
        return parse_vec(inner_val_str, inner_type) if inner_val_str else None

    # 其他类型直接丢给 basic
    return parse_basic_value(inner_type, inner_val_str)

def parse_basic_value(type_name: str, value: str):
    value = value.strip()
    if not value:  # 空字符串直接返回 None
        return None

    if type_name in ('string', 'hash'):
        # 去除前后可能的双引号或单引号
        v = value.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        return v

    # 处理布尔值（bool / flag 类型）
    if type_name in ('bool', 'flag'):
        bool_map = {'true': True, '1': True, 'false': False, '0': False, 'none': None}
        return bool_map.get(value.lower(), None)  # 默认为 None，如果无效则返回 None

    conv = BASIC_TYPES.get(type_name)
    if conv:
        return conv(value)
    # 默认返回原字符串
    return value

# 解析list
def parse_list(text: str, elem_type_str: str, parent_cls: type, field_name: str) -> List:
    """
    解析list块，格式：
    = {
        val1
        val2
        ...
    }
    elem_type_str类型名
    """
    # 去除外层 {}
    inner_match = re.search(r'\{\s*(.*)\s*\}', text, re.S)
    if not inner_match:
        return []
    inner = inner_match.group(1).strip()

    # 分割元素，可能是简单值，也可能是嵌套结构（比如list[pointer])
    elems = split_lines_balanced(inner)

    result = []
    for elem in elems:
        elem = elem.strip()
        # 简单类型直接转换
        if elem_type_str in BASIC_TYPES:
            if elem_type_str.startswith('vec'):
                result.append(parse_vec(elem, elem_type_str))
            elif elem_type_str == "hash":
                if elem.startswith("0x"):
                    # 如果是数字类型的哈希（即数字串），保持为原样
                    result.append(elem)
                else:
                    # 如果是带双引号的字符串，则去掉引号并加入结果
                    result.append(elem.strip('"'))
            elif elem_type_str == 'f64' or elem_type_str == 'f32' or elem_type_str == 'f16' or elem_type_str == 'f8':
                result.append(float(elem))
            else:
                conv = BASIC_TYPES[elem_type_str]
                val = conv(elem)
                result.append(val)
        elif elem_type_str == 'pointer' or elem_type_str == 'embed':
            # 形如 ClassName { ... }
            sub_obj = parse_embed(elem)
            result.append(sub_obj)
        else:
            print(f"Warning: Undefined type{elem_type_str}")
            # 其他情况尝试当字符串
            result.append(elem)
    return result

# 解析map[hash,embed]
def collect_block(text: str) -> tuple[str, str]:
    """
    给定以 { 开头的一段，返回完整的 { ... } 内容，以及剩余文本
    """
    depth = 0
    block = []
    for i, ch in enumerate(text):
        block.append(ch)
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return "".join(block), text[i+1:]
    raise ValueError("Unbalanced braces in block")

def parse_map(value: str, parent_cls: type, field_name: str, debug: bool = False) -> Dict[Any, Any]:
    """
    更稳健的 parse_map：基于索引扫描解析键和值，能正确处理:
      "key" = ClassName { ... }
      0x1234 = ClassName { ... }
      key : type = value
      "key" = "string"
      key = 123 / 0x1234
      key = { ... }   (内联 list/map)
    debug=True 会打印解析过程
    """
    d = {}

    m = re.search(r'\{\s*(.*)\s*\}\s*$', value, re.S)
    if not m:
        raise ValueError(f"Invalid map format for field: {field_name}")
    inner = m.group(1)
    n = len(inner)
    i = 0

    def skip_space():
        nonlocal i
        while i < n and inner[i].isspace():
            i += 1

    def read_quoted():
        nonlocal i
        assert inner[i] == '"'
        j = i + 1
        while j < n:
            if inner[j] == '"' and inner[j-1] != '\\':
                break
            j += 1
        if j >= n:
            raise ValueError("Unterminated quoted string in map")
        s = inner[i+1:j]
        i = j + 1
        return s

    def read_token():
        nonlocal i
        # identifier-like token
        m = re.match(r'[A-Za-z_][\w/]*', inner[i:])
        if not m:
            return None
        tok = m.group(0)
        i += len(tok)
        return tok

    def read_number_or_hex():
        nonlocal i
        m = re.match(r'0x[0-9A-Fa-f]+|\d+', inner[i:])
        if not m:
            return None
        tok = m.group(0)
        i += len(tok)
        if tok.startswith('0x'):
            return int(tok, 16)
        else:
            return int(tok, 10)

    while True:
        skip_space()
        if i >= n:
            break

        # --- parse key ---
        if inner[i] == '"':
            key_raw = read_quoted()
            key = key_raw
        elif inner.startswith('0x', i) or inner[i].isdigit():
            # numeric/hex key
            key = read_number_or_hex()
        else:
            # bare token key
            tok = read_token()
            if tok is None:
                # skip until newline
                nxt = inner.find('\n', i)
                if nxt == -1:
                    break
                i = nxt + 1
                continue
            key = tok

        skip_space()

        # typed key: key : type = value
        typ = None
        if i < n and inner[i] == ':':
            i += 1
            skip_space()
            # read until '='
            j = i
            while j < n and inner[j] != '=':
                j += 1
            typ = inner[i:j].strip()
            i = j
        # consume '=' if present (or skip to next '=')
        if i < n and inner[i] == '=':
            i += 1
        else:
            # find next '='
            j = inner.find('=', i)
            if j == -1:
                break
            i = j + 1

        skip_space()
        if i >= n:
            break

        # --- parse value ---
        val = None
        # string value
        if inner[i] == '"':
            val = read_quoted()
        # class embed: Identifier { ... }
        elif inner[i].isalpha() or inner[i] == '_':
            # read identifier
            id_start = i
            id_tok = read_token()
            skip_space()
            if i < n and inner[i] == '{':
                # object block starting here
                block, _ = collect_block(inner[i:])
                obj_text = f"{id_tok} {block}"
                obj = parse_embed(obj_text.strip())
                if obj is None:
                    print(f"parse_embed failed for class {id_tok} at map field {field_name} key {key!r}")
                val = obj
                i += len(block)  # advance past block
            else:
                # bare identifier (enum/keyword)
                val = id_tok
        # inline block { ... } (list or map literal)
        elif inner[i] == '{':
            block, _ = collect_block(inner[i:])
            # if typed as list[*], try parse_list
            if typ and 'list' in typ:
                # extract inner type name from typ like list[embed]
                m_type = re.search(r'list\[(\w+)\]', typ)
                elem_type = m_type.group(1) if m_type else None
                if elem_type:
                    val = parse_list(block, elem_type, parent_cls, field_name)
                else:
                    val = block
            else:
                # fallback: keep raw block or try parse_map recursively?
                # attempt parse_map when typ indicates map
                if typ and typ.startswith('map['):
                    val = parse_map(block, parent_cls, field_name)
                else:
                    # keep raw block text
                    val = block
            i += len(block)
        else:
            # number or hex or fallback token until newline
            num = read_number_or_hex()
            if num is not None:
                val = num
            else:
                # read until newline or next top-level separator
                j = i
                while j < n and inner[j] != '\n':
                    j += 1
                val = inner[i:j].strip()
                i = j

        # store key normalization: convert hex string key to readable form if needed
        # if key is a string like '0x...' convert as before
        if isinstance(key, str) and key.startswith('0x') and GLOBAL_HASH_MANAGER.HASH_TABLE:
            conv_key, is_unk = convert_hash(key)
            if is_unk:
                d[key] = val
            else:
                d[conv_key] = val
        else:
            d[key] = val

        if debug:
            print(f"[parse_map] stored key={repr(key)} -> {type(val).__name__}: {repr(val) if isinstance(val,(str,int)) else type(val)}")

        # advance past any trailing whitespace/newlines before next item
        skip_space()
        # skip an optional newline delimiter
        if i < n and inner[i] == '\n':
            i += 1
        # loop continues

    return d

# 解析embed块（嵌套对象）
def parse_embed(text: str) -> Any:
    """
    解析形如 ClassName { ... } 的块
    自动定位类ClassName，调用parse_block
    """
    text = text.strip()
    if text == "null":
        return None   # 特殊处理 null
    m = re.match(r'(\w+)\s*\{', text)
    if not m:
        raise ValueError(f"Invalid embed block: {text[:30]}...")  # 如果没有匹配到，抛出异常
    class_name = m.group(1)

    if class_name.startswith("0x"):
        class_name, is_unkonwn = convert_hash(class_name)
        if is_unkonwn:
            class_name = f"Unknown_{class_name}"

    # 打印检查映射类的调试信息
    # print(f"Mapping class_name to class: {class_name}")
    
    # 根据class_name映射到Python数据类
    cls = globals().get(class_name)
    # cls = {k.lower(): v for k, v in globals().items()}.get(class_name.lower())
    if not cls:
        print(class_name)
        # print(f"Warning: Unknown class name {class_name} in embed, skipping.")  # 如果class_name无法映射，打印警告并跳过
        return None

    return parse_block(text, cls)

# 工具函数：拆分多行文本为多个“语义块”（支持{}平衡），用于分割list元素或map键值对
def split_lines_balanced(text: str) -> List[str]:
    results = []
    current = []
    depth = 0
    i = 0
    while i < len(text):
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        if c == '\n' and depth == 0:
            line = ''.join(current).strip()
            if line:
                results.append(line)
            current = []
        else:
            current.append(c)
        i += 1
    last_line = ''.join(current).strip()
    if last_line:
        results.append(last_line)
    return results

# 工具函数：拆分map键值对，注意键和值的平衡嵌套
def split_pairs_balanced(text: str) -> List[tuple]:
    pairs = []
    depth = 0
    current = []
    key = None
    i = 0
    length = len(text)
    while i < length:
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        if c == '=' and depth == 0:
            key = ''.join(current).strip()
            current = []
            i += 1
            # 读取value直到分割或结尾
            value_chars = []
            depth_val = 0
            while i < length:
                ch = text[i]
                if ch == '{':
                    depth_val += 1
                elif ch == '}':
                    depth_val -= 1
                if depth_val < 0:
                    break
                # 检测到分隔符且depth_val==0结束
                if ch == '\n' and depth_val == 0:
                    break
                value_chars.append(ch)
                i += 1
            value = ''.join(value_chars).strip()
            pairs.append((key, value))
            current = []
            continue
        else:
            current.append(c)
            i += 1
    return pairs

# 主解析函数
def parse_prop_text(text: str) -> Dict[str, Any]:
    """
    解析整个PROP_text文件，返回entries字典，值为对应对象实例
    """
    clean_text = preprocess(text)
    # 找entries部分
    m = re.search(r'entries:\s*map\[hash,embed\]\s*=\s*\{(.*)\}\s*$', clean_text, re.S)
    if not m:
        raise ValueError("Cannot find entries block")
    entries_block = m.group(1).strip()

    # entries是多组"key"=Class { ... }形式
    entries_pairs = split_pairs_balanced(entries_block)
    entries = {}
    for k, v in entries_pairs:
        key = k.strip().strip('"')
        obj = parse_embed(v)
        entries[key] = obj
    return entries

def format_obj(obj, indent=0):
    INDENT = 4
    prefix = ' ' * indent

    def is_simple_list(lst):
        return all(not is_dataclass(i) and not isinstance(i, (list, dict)) for i in lst)

    # 针对ve3, vec4 一行输出
    if type(obj).__name__ in ('vec2', 'vec3', 'vec4'):
        vals = ", ".join(f"{c}={getattr(obj, c)}" for c in obj.__dataclass_fields__)
        return f"{type(obj).__name__}({vals})"

    if isinstance(obj, list):
        if not obj:
            return "[]"
        if is_simple_list(obj):
            return "[" + ", ".join(repr(i) for i in obj) + "]"
        else:
            lines = ["["]
            for item in obj:
                lines.append(' ' * (indent + INDENT) + format_obj(item, indent + INDENT) + ",")
            lines.append(prefix + "]")
            return "\n".join(lines)

    if isinstance(obj, dict):
        if not obj:
            return "{}"
        lines = ["{"]
        for k, v in obj.items():
            lines.append(f"{' ' * (indent + INDENT)}{repr(k)}: {format_obj(v, indent + INDENT)},")
        lines.append(prefix + "}")
        return "\n".join(lines)

    if is_dataclass(obj):
        cls_name = obj.__class__.__name__
        lines = [f"{cls_name}("]
        for f in fields(obj):
            val = getattr(obj, f.name)
            if val is None:
                continue  # 跳过None字段
            val_str = format_obj(val, indent + INDENT)
            lines.append(f"{' ' * (indent + INDENT)}{f.name}={val_str},")
        lines.append(prefix + ")")
        return "\n".join(lines)

    # 基础类型和其他
    return repr(obj)

def parse_prop_text(text: str) -> PropFile:
    text = preprocess(text)

    # 解析 type 字段
    m_type = re.search(r'type:\s*string\s*=\s*"([^"]+)"', text)
    type_value = m_type.group(1) if m_type else "PROP"

    # 解析 version 字段
    m_version = re.search(r'version:\s*u32\s*=\s*(\d+)', text)
    version_value = int(m_version.group(1)) if m_version else 3

    # 解析 linked 字段，简单提取所有字符串
    m_linked = re.search(r'linked:\s*list\[string\]\s*=\s*\{\s*([^}]+)\}', text, re.S)
    linked_list = []
    if m_linked:
        linked_raw = m_linked.group(1)
        linked_list = re.findall(r'"([^"]+)"', linked_raw)

    # 解析 entries 字段，复用之前写的函数
    entries = {}
    m_entries = re.search(r'entries:\s*map\[hash,embed\]\s*=\s*\{(.*)\}\s*$', text, re.S)
    if m_entries:
        entries_block = m_entries.group(1).strip()
        entries_pairs = split_pairs_balanced(entries_block)
        for k, v in entries_pairs:
            key = k.strip().strip('"')
            if key.startswith("0x"):
                key, is_unkonwn = convert_hash(key)
            obj = parse_embed(v)
            entries[key] = obj

    return PropFile(type=type_value, version=version_value, linked=linked_list, entries=entries)