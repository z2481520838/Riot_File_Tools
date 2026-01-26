from ...objects.prop_text.prop_text_obj import*
from ...objects.prop_text.base_value import*
from .math import*
from ...objects.prop_text.spelldataFlags_obj import*
import os

def write_blank_Line(lines: list):
    lines.append("")

def write_str(lines: list, txt: str):
    if txt is not None and txt.strip():
        lines.append(txt)

def obj_to_custom_format(obj, to_name: str = None):
    if obj is not None:
        if to_name is None:
            return obj.to_custom_format()
        else:
            return obj.to_custom_format(to_name)

def bool_to_custom_format(value, to_name: str = None):
    if value is not None:
        return f"{to_name}={1 if value == True else 0}"

def str_base(obj, to_name: str = None):
    if obj is not None:
        return f"{to_name}={obj}"

def get_path_baseName(obj, to_name: str = None):
    if obj is not None:
        base = os.path.basename(obj)
        # 如果是字符串，去掉首尾的引号
        if isinstance(base, str):
            base = base.strip('"')
        return f"{to_name}={base}"

def value_to_custom_format(value_obj, to_name="base"):
    if value_obj is not None:
        return f"{to_name}={value_obj}"

def list_to_custom_format(list_obj, to_name="base"):
    lines = []
    if list_obj is not None:
        for i, v in enumerate(list_obj, start=1):
            write_str(lines, v.to_custom_format(i))
    return "\n".join(lines)

def field_pointer(obj):
    lines = []
    # 定义字段类型和输出的命名映射
    field_map = {
        'fieldAccelerationDefinitions': 'accel',       # 映射为 field-accel
        'fieldAttractionDefinitions': 'attract',       # 映射为 field-attract
        'fieldDragDefinitions': 'drag',                # 映射为 field-drag
        'fieldNoiseDefinitions': 'noise',              # 映射为 field-noise
        'fieldOrbitalDefinitions': 'orbit'             # 映射为 field-orbit
    }
    # 遍历每个字段和对应的命名
    for field_name, field_prefix in field_map.items():
        # 获取字段的列表（如果为空，初始化为一个空列表）
        field_list = getattr(obj, field_name, [])
        if not field_list:  # 如果字段列表为空（None 或 空列表），跳过该字段
            continue
        for index, field in enumerate(field_list, start=1):
            lines.append(f"field-{field_prefix}-{index}=\"{field_name.capitalize()}{index}\"")

    return "\n".join(lines)

def has_mesh(value) -> bool:
    """ 检查primitive是否符合特定类型条件并返回布尔值 """
    return bool(value is not None and ((value.type_ in {3, 6} and value.mMesh is not None) or value.type_ == 11))

def get_texture_type(is_mesh):
    return "p-meshtex" if is_mesh else "p-texture"

def field_data(obj, type_Name: str):
    lines = []
    if obj is not None:
        for index, value in enumerate(obj, start=1):
            lines.append("")
            lines.append(f"[{type_Name}{index}]")
            write_str(lines, obj_to_custom_format(value))
        return "\n".join(lines)

def texture_mode_fix(obj, type_Name: str):
    mode_type = ["clamp", "clamp", "clamp", "clamp", "clamp"]
    if obj is not None:
        return f"{type_Name}={mode_type[obj]}"

def obj_to_custom_format_mult(obj, is_mesh):
    if obj is not None:
        return obj.to_custom_format(is_mesh)

def obj_to_custom_format_material(obj, index: int):
    if obj is not None:
        return obj.to_custom_format(index)

def obj_to_custom_format_childParticle(obj, source):
    if obj is not None:
        return obj.to_custom_format(source)

def obj_to_custom_format_special(obj, constantValue, type_name="base"):
    if obj is not None:
        return obj.to_custom_format(constantValue, type_name)

def color_constantValue(value, type_name="base"):
    if value is not None:
        x, y, z, a = value
        if type_name == "e-rgba":
            x, y, z, a = [v * 255 if i < 4 else v for i,v in enumerate(value)]
        return vec4(x, y, z, a).to_custom_format(type_name)

def texture_mult_data(obj, is_mesh):
    lines = []
    type_Name = get_texture_type(is_mesh)
    if obj is not None:
        if isinstance(obj, str):
            # 如果是路径字符串
            write_str(lines, get_path_baseName(obj, f"{type_Name}-mult"))
        else:
            # 假设对象有自定义输出方法
            write_str(lines, obj_to_custom_format_mult(obj, type_Name))
        return "\n".join(lines)

def material_data(obj):
    lines = []
    if obj is not None:
        for i, material in enumerate(obj, start=1):
            write_str(lines, obj_to_custom_format_material(material, i))
        return "\n".join(lines)

def childParticle_data(obj, source):
    lines = []
    if obj is not None:
        write_str(lines, obj_to_custom_format_childParticle(obj, source))
        return "\n".join(lines)

def colorLookUpType_data(_x, _y):
    lines = []
    if _x is not None or _y is not None:
        # 默认值为1
        x = _x if _x else 1
        y = _y if _y else 1
        write_str(lines, f"p-colortype={x} {y}")
        return "\n".join(lines)

def add_fix_value(a, b, c):
    lines = []
    if a and a.type_ == 11 and a.mMesh and a.mMesh.mLockMeshToAttachment:
        if b is None:
            write_str(lines, "p-bindtoemitter=1")
        if c is None or not c:
            write_str(lines, "p-local-orient=1")
    return "\n".join(lines)

def add_fix_child_tex(obj):
    lines = []
    if obj.childParticleSetDefinition and obj.texture is None and obj.meshTextureName is None:
        obj.texture = "empty32.dds"
    return "\n".join(lines)

def UVScrollRate(a, b, c):
    lines = []
    if a is None or a.constantValue == vec2(0, 0):
        if b is not None and b.constantValue != vec2(0, 0):
            write_str(lines, obj_to_custom_format(b, c))
    else:
        write_str(lines, obj_to_custom_format(a, c))
    return "\n".join(lines)

def fix_uvMode(a):
    lines = []
    if a is not None:
        write_str(lines, bool_to_custom_format(True, "p-uvscroll-no-alpha"))
        # write_str(lines, value_to_custom_format(a, "p-uvmode"))
    return "\n".join(lines)

def attackspellData(a, get_name):
    lines = []
    if a is not None:
        for i, v in enumerate(a, start=1):
            write_str(lines, obj_to_custom_format(v, f"{get_name}{i}"))
    return "\n".join(lines)

def list_base(a, get_name):
    lines = []
    if a is not None:
        write_str(lines, f"{get_name}={' '.join(a)}")
    return "\n".join(lines)

def list_str(a, get_name):
    lines = []
    if a is not None:
        for i, v in enumerate(a, start=1):
            write_str(lines, get_path_baseName(v, f"{get_name}{i}"))
    return "\n".join(lines)

def list_obj(a, get_name):
    lines = []
    if a is not None:
        for i, v in enumerate(a, start=1):
            write_str(lines, obj_to_custom_format(v, f"{get_name}{i}"))
    return "\n".join(lines)

def list_value(a, get_name):
    lines = []
    if a is not None:
        for i, v in enumerate(a, start=1):
            write_str(lines, value_to_custom_format(v, f"{get_name}{i}"))
    return "\n".join(lines)

def list_SpellEffectAmount(a, get_name):
    lines = []
    if a is not None:
        for i, v in enumerate(a, start=0):
            write_str(lines, value_to_custom_format(v, f"{get_name}{i}Amount"))
    return "\n".join(lines)

def list_str_hasbase(a, get_name):
    lines = []
    if a is not None:
        for i, v in enumerate(a, start=0):
            name = get_name if i == 0 else f"{get_name}{i}"
            write_str(lines, get_path_baseName(v, name))
    return "\n".join(lines)

def list_value_hasbase(a, get_name):
    lines = []
    if a is not None:
        for i, v in enumerate(a, start=0):
            name = get_name if i == 0 else f"{get_name}{i}"
            write_str(lines, value_to_custom_format(v, name))
    return "\n".join(lines)

def list_count(a, get_name):
    lines = []
    if a is not None:
        write_str(lines, value_to_custom_format(len(a), get_name))
    return "\n".join(lines)

def fix_purchaseIdentities(a, get_name):
    lines = []
    if a is not None:
        if (a == ["Melee"]):
            write_str(lines, f"{get_name}=Yes")
        else:
            write_str(lines, f"{get_name}=No")
    return "\n".join(lines)

def get_TargetingType(a):
    lines = []
    if a is not None:
        write_str(lines, value_to_custom_format(a._type, "TargettingType"))
    return "\n".join(lines)

def targeter_data_list(a):
    lines = []
    if a is not None:
        for i, v in enumerate(a, start=1):
            write_str(lines, obj_to_custom_format(v, f"SpellTargeter{i}"))
    return "\n".join(lines)

def targeter_data(a):
    lines = []
    if a is not None:
        write_str(lines, targeter_data_list(a.mTargeterDefinitions))
    return "\n".join(lines)


def spelldataflags_fix(a, b, c):
    lines = []
    textFlags = decode_flags(SpellDataFlags(a) | map_affects_type_to_spell_data(b) | map_affects_Status_to_spell_data(c), SpellDataFlags)
    flags = reverse_flags(textFlags, SpellDataFlags)
    write_str(lines, value_to_custom_format(flags, "Flags"))
    write_str(lines, str_base(textFlags, "TextFlags"))
    return "\n".join(lines)