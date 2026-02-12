from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import os

@dataclass
class vector4:
    x: float
    y: float
    z: float
    a: float

@dataclass
class vector3:
    x: float
    y: float
    z: float

@dataclass
class vector2:
    x: float
    y: float

@dataclass
class Box:
    Min: vector3
    Max: vector3

@dataclass
class Sphere:
    position: vector3
    radius: float

@dataclass
class Circle:
    position: vector2
    radius: float

@dataclass
class Rectangle:
    origin : vector2
    size: vector2

@dataclass
class Color:
    r: int = 0
    g: int = 0
    b: int = 0

    def __mul__(self, value: float) -> 'Color':
        """Multiply the color by a float value."""
        r = int(self.r * value)
        g = int(self.g * value)
        b = int(self.b * value)
        return Color(r, g, b)

    def __eq__(self, other: 'Color') -> bool:
        """Compare two colors for equality."""
        return self.r == other.r and self.g == other.g and self.b == other.b

    def __ne__(self, other: 'Color') -> bool:
        """Check if two colors are not equal."""
        return not self.__eq__(other)