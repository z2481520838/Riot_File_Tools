from dataclasses import dataclass, field

@dataclass
class Self:
    _type: int = 0

@dataclass
class Target:
    _type: int = 1,

@dataclass
class Area:
    _type: int = 2

@dataclass
class Cone:
    _type: int = 3

@dataclass
class SelfAoe:
    _type: int = 4

@dataclass
class TargetOrLocation:
    _type: int = 5

@dataclass
class Location:
    _type: int = 6

@dataclass
class Direction:
    _type: int = 7

direction = Direction

@dataclass
class DragDirection:
    _type: int = 8

@dataclass
class LineTargetToCaster:
    _type: int = 9

@dataclass
class LocationClamped:
    _type: int = 11

@dataclass
class Invalid:
    _type: int = 255