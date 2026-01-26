import os
import re
from typing import Dict

class HashesManager:
    def __init__(self):
        """
        初始化 HashTableManager，加载指定目录下的所有哈希表文件。
        """
        self.HASH_TABLE = {}
        # 假设路径已经初始化
    def start_load_hashes(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        MY_PROJECT_ROOT = os.path.dirname(current_dir)
        directory_path = os.path.join(current_dir, 'hashes_table')
        self.load_all_hash_maps(directory_path)

    def load_all_hash_maps(self, directory_path: str):
        """
        加载指定目录下的所有哈希表文件（.txt 以及 .txt.0/.txt.1 分片），并存储到 HASH_TABLE 中。
        :param directory_path: 哈希表文件所在的目录路径
        """
        try:
            grouped_files = {}

            # 遍历目录中的所有文件
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                if not os.path.isfile(file_path):
                    continue

                # 允许 .txt 和 .txt.N
                if filename.endswith('.txt') or re.match(r'.*\.txt\.\d+$', filename):
                    base_name = re.sub(r'\.\d+$', '', filename)  # 去掉分片编号
                    grouped_files.setdefault(base_name, []).append(file_path)

            # 按组加载
            for base_name, file_list in grouped_files.items():
                hash_map = {}
                for path in sorted(file_list):  # 保证 .0, .1 顺序
                    sub_map = self.load_hash_map(path)
                    hash_map.update(sub_map)  # 合并
                self.HASH_TABLE[base_name] = hash_map
            """
            if not self.HASH_TABLE:
                print("没有找到有效的哈希表文件")
            else:
                print("哈希表加载完成")
            """
        except Exception as e:
            print(f"哈希表加载失败: {e}")

    def load_hash_map(self, file_path: str) -> dict:
        """
        从一个文件加载哈希表数据。
        :param file_path: 哈希表文件路径
        :return: 加载的哈希表（字典）
        """
        hash_map = {}
        try:
            with open(file_path, 'r', encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split()
                        if len(parts) == 2:
                            hash_value = parts[0].strip()
                            readable_value = parts[1].strip()
                            hash_map[hash_value] = readable_value
        except Exception as e:
            print(f"Error loading hash file {file_path}: {e}")

        return hash_map

    def lookup_hash(self, hash_value: str, table_name: str = None) -> str or None:
            """
            根据哈希值查询对应的可读字符串。
            
            :param hash_value: 要查询的哈希值（通常是十六进制字符串，如 '0x4A252E92' 或 '4A252E92'）。
            :param table_name: 可选，指定要查询的哈希表名称（即文件名，如 'troy.txt'）。
                                如果为 None，则遍历所有已加载的哈希表。
            :return: 对应的可读字符串，如果未找到则返回 None。
            """
            # 确保哈希值是标准格式（例如，移除 '0x' 前缀，大写）以便匹配字典键
            normalized_hash = hash_value.lstrip('0x').upper()
            
            # 1. 查询指定的哈希表
            if table_name:
                if table_name in self.HASH_TABLE:
                    hash_map = self.HASH_TABLE[table_name]
                    return hash_map.get(normalized_hash, None)
                else:
                    # print(f"警告: 未找到名为 '{table_name}' 的哈希表。")
                    return None
            
            # 2. 遍历所有哈希表进行查询
            else:
                for map_name, hash_map in self.HASH_TABLE.items():
                    if normalized_hash in hash_map:
                        # 一旦找到匹配项，立即返回
                        return hash_map[normalized_hash]
                        
                # 遍历完所有表仍未找到
                return None

GLOBAL_HASH_MANAGER = HashesManager()
