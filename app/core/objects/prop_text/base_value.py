from typing import List, Optional
from dataclasses import dataclass, field

# --- 数值类 ---

f8 = float
u8 = int
i8 = int
f16 = float
u16 = int
i16 = int
f32 = float
u32 = int
i32 = int
f64 = float
u64 = int
i64 = int
flag = bool

@dataclass
class mtx44:
    rows: List[List[float]] = field(default_factory=lambda: [[0.0]*4 for _ in range(4)])

@dataclass
class vec2:
    x: float
    y: float

    def __getitem__(self, idx):
        return (self.x, self.y)[idx]

    def __iter__(self):
        yield self.x
        yield self.y

    def to_custom_format(self, prefix: str) -> str:
        lines = []
        if tuple((self.x, self.y)) != (0, 0):
            lines.append(f"{prefix}={self.x} {self.y}")
        return  '\n'.join(lines)

@dataclass
class vec3:
    x: float
    y: float
    z: float

    def __getitem__(self, idx):
        return (self.x, self.y, self.z)[idx]

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def to_custom_format(self, prefix: str) -> str:
        lines = []
        if tuple((self.x, self.y, self.z)) != (0, 0, 0):
            lines.append(f"{prefix}={self.x} {self.y} {self.z}")
        return  '\n'.join(lines)
        
@dataclass
class vec4:
    x: float
    y: float
    z: float
    a: float

    def __getitem__(self, idx):
        return (self.x, self.y, self.z, self.a)[idx]

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z
        yield self.a

    def to_custom_format(self, prefix: str) -> str:
        lines = []
        if tuple((self.x, self.y, self.z, self.a)) != (0, 0, 0, 0):
            lines.append(f"{prefix}={self.x} {self.y} {self.z} {self.a}")
        return  '\n'.join(lines)

rgba = vec4

def format_number(n: float) -> str:
    """
    格式化数字，整数去掉小数点，小数最多保留9位，去除末尾多余0
    """
    if int(n) == n:
        return str(int(n))
    return f"{n:.9f}".rstrip('0').rstrip('.')