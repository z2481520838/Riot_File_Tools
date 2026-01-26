from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from ..general import vector3
from ...function.general import*

@dataclass
class AnmHeader:
    magic: str = None
    version: int = 0

@dataclass
class AnimationFile:
    header: AnmHeader = None
    data: Optional[Any] = None

@dataclass
class AnimationFile_Compressed:
    resourceSize : int = 0
    formatToken: str = None
    flags: int = 0
    jointCount: int = 0
    frameCount: int = 0
    jumpCacheCount: int = 0
    duration: float = 0
    FrameDuration: float = 0 #提前使用1/FrameDuration
    translationMin: vector3 = None
    translationMax: vector3 = None
    scaleMin: vector3 = None
    scaleMax: vector3 = None
    """
    framesOffset: int = 0
    jumpCachesOffset: int = 0
    jointNameHashesOffset: int = 0
    """

@dataclass
class AnimationFile_:
    skeletonId: int = 0
    trackCount: int = 0
    frameCount: int = 0
    FrameDuration: float = 0 #提前使用1/FrameDuration

@dataclass
class AnimationFile_V4:
    resourceSize : int = 0
    formatToken: int = 0
    version_s: int = 0
    flags: int = 0
    trackCount: int = 0
    frameCount: int = 0
    FrameDuration: float = 0
    """
    tracksOffset: int = 0
    assetNameOffset: int = 0
    timeOffset: int = 0
    vectorsOffset: int = 0
    rotationsOffset: int = 0
    framesOffset: int = 0
    """

@dataclass
class AnimationFile_V5:
    resourceSize : int = 0
    formatToken: int = 0
    version_s: int = 0
    flags: int = 0
    trackCount: int = 0
    framesPerTrack: int = 0
    FrameDuration: float = 0
    """
    jointHashesOffset: int = 0
    assetNameOffset: int = 0
    timeOffset: int = 0
    vectorsOffset: int = 0
    rotationsOffset: int = 0
    framesOffset: int = 0
    """

