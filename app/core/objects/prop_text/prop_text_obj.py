from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .base_value import*
from ...function.prop_text.math import*
from ...function.prop_text.obj_functions import*
from .spellData_obj import*
from .charData_obj import*
from .spelldataFlags_obj import*
from .vfxData_obj import*
from .skinData_obj import*
import os

@dataclass
class ResourceResolver:
    resourceMap: Dict[str, str] = field(default_factory=dict)  # 键值对为字符串，表示资源名称和其链接

    def __post_init__(self):
        # 可选：如果有其他初始化逻辑可以在这里实现
        pass

    def add_resource(self, key: str, value: str):
        """ 向resource_map中添加一个资源映射 """
        self.resourceMap[key] = value

    def get_resource(self, key: str) -> str:
        """ 根据key获取对应的资源链接 """
        
        # 如果 key 是字符串且是哈希形式的值，转换为整数
        if isinstance(key, str) and key.startswith("0x"):
            key = int(key, 16)  # 将十六进制字符串转换为整数
        
        # 查找 resourceMap 中的整数键
        return self.resourceMap.get(key, str(key))  # 如果没有找到，返回原始的 key（字符串形式）

@dataclass
class Entries:
    items: Dict[str, Any] = field(default_factory=dict)

    def get_resource_resolver(self, resource_key: str) -> str:
        """ 在 entries.items 中查找 ResourceResolver 并获取资源 """

        for key, obj in self.items.items():
            if isinstance(obj, ResourceResolver):
                # 如果找到 ResourceResolver 实例
                for res_key, res_val in obj.resourceMap.items():
                    # 比较去掉路径后的文件名
                    res_key = str(res_key)  # 将 key 转换为字符串
                    res_val = str(res_val)  # 将 val 转换为字符串
                    if os.path.basename(res_val) == resource_key:
                        # 如果 resource_key 与资源路径文件名匹配，直接返回 resource_key
                        return resource_key
                # 如果没有直接匹配，返回资源链接
                return obj.get_resource(resource_key)

        return resource_key

    def to_custom_format(self, not_vfx_only):
        lines = []
        for key, obj in self.items.items():
            if obj is None:
                continue  # 跳过未定义对象
            if not_vfx_only and isinstance(obj, SkinCharacterDataProperties):
                continue
            if hasattr(obj, "to_custom_format"):
                value_str = obj.to_custom_format(self)
                lines.append(f'{value_str}')
        return "\n".join(lines)

@dataclass
class PropFile:
    type: str = "PROP"
    version: int = 3
    linked: List[str] = field(default_factory=list)
    entries: Entries = None

    def to_custom_format(self, out_extra=False):
        lines = []
        if out_extra:
            lines.append("#PROP_text")
            lines.append(f"type={self.type}")
            lines.append(f"version={self.version}")

            if self.linked:
                linked_str = " ".join(self.linked)
                lines.append(f"linked=[{linked_str}]")

        if self.entries:
            # 自动将 dict 转为 Entries
            if isinstance(self.entries, dict):
                entries_obj = Entries(items=self.entries)
            else:
                entries_obj = self.entries

            if hasattr(entries_obj, "to_custom_format"):
                if out_extra:
                    lines.append("entries:")
                lines.append(entries_obj.to_custom_format(True))

        return "\n".join(lines)