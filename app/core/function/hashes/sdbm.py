class Sdbm:
    
    @staticmethod
    def hash(value: str) -> int:
        hash_value = 0
        for char in value:
            hash_value = ord(char) + 65599 * hash_value
        return hash_value & 0xFFFFFFFF

    @staticmethod
    def hash_with_key(key: str, value: str) -> int:
        hash_value = 0
        for char in key:
            hash_value = ord(char) + 65599 * hash_value
        for char in value:
            hash_value = ord(char) + 65599 * hash_value
        return hash_value & 0xFFFFFFFF

    @staticmethod
    def hash_with_delimiter(key: str, value: str, delimiter: str) -> int:
        hash_value = 0
        for char in key:
            hash_value = ord(char) + 65599 * hash_value
        hash_value = 65599 * hash_value + ord(delimiter)
        for char in value:
            hash_value = ord(char) + 65599 * hash_value
        return hash_value & 0xFFFFFFFF

    @staticmethod
    def hash_lower(value: str) -> int:
        return Sdbm.hash(value.lower())

    @staticmethod
    def hash_lower_with_key(key: str, value: str) -> int:
        return Sdbm.hash_with_key(key.lower(), value.lower())

    @staticmethod
    def hash_lower_with_delimiter(key: str, value: str, delimiter: str) -> int:
        return Sdbm.hash_with_delimiter(key.lower(), value.lower(), delimiter)

# 示例调用
value = "Run1_RAW"
key = "Sword2LHandSheath"
delimiter = ":"

print(Sdbm.hash(value))
print(Sdbm.hash_lower_with_key(value, key))