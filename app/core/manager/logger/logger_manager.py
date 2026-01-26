import os
import json
import yaml
import pickle
import jsonpickle
from dataclasses import dataclass, field
from typing import Any

@dataclass
class SavePackage:
    data: Any = None
    path: str = None

class LoggerManager:
    """管理项目路径的 JSON 日志，内存缓存避免每次都读文件"""

    def __init__(self, log_dir: str = None, file_name: str = "path_logger.json"):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.cache_file = os.path.join(self.current_dir, file_name)
        self.path_logger = self.load_path_logger()  # 内存缓存

    def get_pkl_path(self):
        pkl_path = os.path.join(self.current_dir, "obj_pkl")
        os.makedirs(pkl_path, exist_ok=True)
        return pkl_path

    def load_path_logger(self) -> dict:
        """读取 JSON 文件到内存"""
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def get(self, key: str):
        """获取指定 key 对应的路径"""
        return self.path_logger.get(key)

    def save(self, key: str, path: str):
        """保存指定 key 的路径，更新内存并写回文件"""
        self.path_logger[key] = path
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.path_logger, f, indent=4, ensure_ascii=False)

    def load_json(self, json_data):
        return jsonpickle.decode(json_data)

    def save_json(self, data, file):
        path = self.get("animations_path")
        pkl_data = SavePackage(data, path)
        file.write(jsonpickle.dumps(pkl_data, indent=4))

    def save_yaml(self, data, file):
        path = self.get("animations_path")
        pkl_data = SavePackage(data, path)
        yaml.dump(pkl_data, file)
        # pickle.dump(pkl_data, file)

    def split_path(self, key):
        full_path = self.get(key)
        if full_path is not None:
            return os.path.split(full_path)
        return "", ""

LOGGERMANAGER = LoggerManager()
