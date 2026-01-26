from enum import IntFlag

"""
AffectsTypeFlags = 0x6DA905E7
AffectsStatusFlags = 0xBEF7C58F
AffectsTypeTextFlags = 0xDEE0DBBA
AffectsStatusTextFlags = 0x102EF362
"""

class SpellDataFlags(IntFlag):
    AutoCast = 1 << 1
    InstantCast = 1 << 2
    PersistThroughDeath = 1 << 3
    NonDispellable = 1 << 4
    NoClick = 1 << 5
    AffectImportantBotTargets = 1 << 6
    AllowWhileTaunted = 1 << 7
    NotAffectZombie = 1 << 8
    AffectUntargetable = 1 << 9
    AffectEnemies = 1 << 10
    AffectFriends = 1 << 11
    AffectBuildings = 1 << 12
    NotAffectSelf = 1 << 13
    AffectNeutral = 1 << 14
    AffectMinions = 1 << 15
    AffectHeroes = 1 << 16
    AffectTurrets = 1 << 17
    AlwaysSelf = 1 << 18
    AffectDead = 1 << 19
    AffectNotPet = 1 << 20
    AffectBarrackOnly = 1 << 21
    IgnoreVisibilityCheck = 1 << 22
    NonTargetableAlly = 1 << 23
    NonTargetableEnemy = 1 << 24
    TargetableToAll = 1 << 25
    AffectWards = 1 << 26
    AffectUseable = 1 << 27
    IgnoreAllyMinion = 1 << 28
    IgnoreEnemyMinion = 1 << 29
    IgnoreLaneMinion = 1 << 30
    IgnoreClones = 1 << 31

class AffectsStatusFlags(IntFlag):
    IgnoreClones             = 1 << 0   # 1
    IgnoreZombies            = 1 << 1   # 2
    Unknown                  = 1 << 2   # 3
    AllowDead                = 1 << 3   # 8
    AllowUntargetableUseable = 1 << 4   # 16
    AllowUntargetable        = 1 << 5   # 32

class AffectsTypeFlags(IntFlag):
    AlliedChampions = 1 << 0
    EnemyChampions = 1 << 1
    AlliedBarracksMinions = 1 << 2
    EnemyBarracksMinions = 1 << 3
    AlliedWards = 1 << 4
    EnemyWards = 1 << 5
    AlliedTurrets = 1 << 6
    EnemyTurrets = 1 << 7
    AlliedInhibsAndNexus = 1 << 8
    EnemyInhibsAndNexus = 1 << 9
    AlliedNonBarracksMinions = 1 << 10
    NeutralNonBarracksMinions = 1 << 11
    EnemyNonBarracksMinions = 1 << 12
    AlwaysSelf = 1 << 13
    NeverSelf = 1 << 14
    Unknown = 1 << 15

# -------------------------
# 通用解码函数
# -------------------------
def decode_flags(value: int, enum_cls: IntFlag):
    """
    将整数 value 解码为 enum_cls 的枚举名列表
    :param value: 输入整数 (可以是 u32)
    :param enum_cls: 枚举类 (IntFlag)
    :return: [flag_name, ...]
    """
    value = value & 0xFFFFFFFF  # 限制为 u32
    # 按枚举定义顺序筛选被置位的标志
    names = [f.name for f in enum_cls if value & f]

    return " | ".join(names)  # value=0 时返回 ""

def reverse_flags(flag_string: str, enum_cls: IntFlag) -> int:
    """
    将标志名字符串翻转为整数值
    :param flag_string: 标志名字符串，如 "IgnoreClones | IgnoreZombies"
    :param enum_cls: 枚举类 (IntFlag)
    :return: 合成的整数值
    """
    # 去除空格并分割
    flag_names = [f.strip() for f in flag_string.split("|")]

    # 按标志名找到对应的枚举值并进行按位或运算
    result = 0
    for flag_name in flag_names:
        try:
            result |= enum_cls[flag_name].value
        except KeyError:
            print(f"未知标志: {flag_name}")  # 如果标志名不在枚举中，打印错误

    return result

def map_affects_type_to_spell_data(value: int) -> SpellDataFlags:
    """
    将整数值转换为对应的 SpellDataFlags 组合
    :param value: 输入整数值（可以是多个标志组合的结果）
    :return: 对应的 SpellDataFlags 组合
    """
    result = SpellDataFlags(0)  # 初始值为 0，空标志

    # 检查每个标志组合
    if value & AffectsTypeFlags.AlliedChampions:
        result |= SpellDataFlags.AffectFriends | SpellDataFlags.AffectHeroes
    if value & AffectsTypeFlags.EnemyChampions:
        result |= SpellDataFlags.AffectEnemies | SpellDataFlags.AffectHeroes
    if value & AffectsTypeFlags.AlliedBarracksMinions:
        result |= SpellDataFlags.AffectFriends | SpellDataFlags.AffectBarrackOnly
    if value & AffectsTypeFlags.EnemyBarracksMinions:
        result |= SpellDataFlags.AffectEnemies | SpellDataFlags.AffectBarrackOnly
    if value & AffectsTypeFlags.AlliedWards:
        result |= SpellDataFlags.AffectFriends | SpellDataFlags.AffectWards
    if value & AffectsTypeFlags.EnemyWards:
        result |= SpellDataFlags.AffectEnemies | SpellDataFlags.AffectWards
    if value & AffectsTypeFlags.AlliedTurrets:
        result |= SpellDataFlags.AffectFriends | SpellDataFlags.AffectTurrets
    if value & AffectsTypeFlags.EnemyTurrets:
        result |= SpellDataFlags.AffectEnemies | SpellDataFlags.AffectTurrets
    if value & AffectsTypeFlags.AlliedInhibsAndNexus:
        result |= SpellDataFlags.AffectFriends | SpellDataFlags.AffectBuildings
    if value & AffectsTypeFlags.EnemyInhibsAndNexus:
        result |= SpellDataFlags.AffectEnemies | SpellDataFlags.AffectBuildings
    if value & AffectsTypeFlags.AlliedNonBarracksMinions:
        result |= SpellDataFlags.AffectFriends | SpellDataFlags.AffectMinions
    if value & AffectsTypeFlags.NeutralNonBarracksMinions:
        result |= SpellDataFlags.AffectNeutral | SpellDataFlags.AffectMinions
    if value & AffectsTypeFlags.EnemyNonBarracksMinions:
        result |= SpellDataFlags.AffectEnemies | SpellDataFlags.AffectMinions
    if value & AffectsTypeFlags.AlwaysSelf:
        result |= SpellDataFlags.AlwaysSelf
    if value & AffectsTypeFlags.NeverSelf:
        result |= SpellDataFlags.NotAffectSelf
    # 处理冲突：如果同时存在 AffectBarrackOnly 和 AffectMinions，移除 AffectBarrackOnly
    if result & SpellDataFlags.AffectMinions and result & SpellDataFlags.AffectBarrackOnly:
        result -= SpellDataFlags.AffectBarrackOnly
    return result

def map_affects_Status_to_spell_data(value: int) -> SpellDataFlags:
    """
    将整数值转换为对应的 SpellDataFlags 组合
    :param value: 输入整数值（可以是多个标志组合的结果）
    :return: 对应的 SpellDataFlags 组合
    """
    result = SpellDataFlags(0)  # 初始值为 0，空标志
    if value & AffectsStatusFlags.IgnoreClones:
        result |= SpellDataFlags.IgnoreClones
    if value & AffectsStatusFlags.IgnoreZombies:
        result |= SpellDataFlags.NotAffectZombie
    if value & AffectsStatusFlags.Unknown:
        result |= SpellDataFlags.NonDispellable
    if value & AffectsStatusFlags.AllowDead:
        result |= SpellDataFlags.AffectDead
    if value & AffectsStatusFlags.AllowUntargetableUseable:
        result |= SpellDataFlags.AffectUseable
    if value & AffectsStatusFlags.AllowUntargetable:
        result |= SpellDataFlags.AffectUntargetable
    return result

# -------------------------
# 示例
# -------------------------
if __name__ == "__main__":
    # print(reverse_flags(decode_flags(SpellDataFlags(4194304) | map_affects_type_to_spell_data(23567) | map_affects_Status_to_spell_data(0), SpellDataFlags), SpellDataFlags))
    # print(decode_flags(SpellDataFlags(4194304) | map_affects_type_to_spell_data(23567) | map_affects_Status_to_spell_data(0), SpellDataFlags))
    print(reverse_flags(decode_flags(SpellDataFlags(4194304) | map_affects_type_to_spell_data(23567) | map_affects_Status_to_spell_data(0), SpellDataFlags), SpellDataFlags))
    print(decode_flags(SpellDataFlags(2100228), SpellDataFlags))