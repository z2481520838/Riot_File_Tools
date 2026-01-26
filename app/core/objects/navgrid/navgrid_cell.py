from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import IntFlag
from ..general import vector2

# 定义各个枚举类型
class VisionPathingFlags(IntFlag):
    Walkable = 0
    Brush = 1
    Wall = 2
    StructureWall = 4
    TransparentWall = 64
    Unknown128 = 128
    AlwaysVisible = 256
    BlueTeamOnly = 1024
    RedTeamOnly = 2048
    NeutralZoneVisiblity = 4096
    KnownFlags = Walkable | Brush | Wall | StructureWall | TransparentWall | Unknown128 | AlwaysVisible | BlueTeamOnly | RedTeamOnly | NeutralZoneVisiblity


class RiverRegionFlags(IntFlag):
    NonJungle = 0
    JungleQuadrant = 1
    BaronPit = 2
    Unobserved4 = 4
    Unobserved8 = 8
    River = 16
    Unknown32 = 32
    RiverEntrance = 64
    KnownFlags = NonJungle | JungleQuadrant | BaronPit | River | RiverEntrance


class JungleQuadrantFlags(IntFlag):
    None_ = 0
    NorthJungleQuadrant = 1
    EastJungleQuadrant = 2
    WestJungleQuadrant = 3
    SouthJungleQuadrant = 4
    LastKnownFlag = SouthJungleQuadrant


class MainRegionFlags(IntFlag):
    Spawn = 0
    Base = 1
    TopLane = 2
    MidLane = 3
    BotLane = 4
    TopSideJungle = 5
    BotSideJungle = 6
    TopSideRiver = 7
    BotSideRiver = 8
    TopSideBasePerimeter = 9
    BotSideBasePerimeter = 10
    TopSideLaneAlcove = 11
    BotSideLaneAlcove = 12
    LastKnownFlag = BotSideLaneAlcove


class NearestLaneFlags(IntFlag):
    BlueSideTopLane = 0
    BlueSideMidLane = 1
    BlueSideBotLane = 2
    RedSideTopLane = 3
    RedSideMidLane = 4
    RedSideBotLane = 5
    BlueSideTopNeutralZone = 6
    BlueSideMidNeutralZone = 7
    BlueSideBotNeutralZone = 8
    RedSideTopNeutralZone = 9
    RedSideMidNeutralZone = 10
    RedSideBotNeutralZone = 11
    LastKnownFlag = RedSideBotNeutralZone


class POIFlags(IntFlag):
    None_ = 0
    NearTurret = 1
    CloudDrakeWindTunnel = 2
    BaseGates = 2
    BaronPit = 3
    DragonPit = 4
    CampRedBuff = 5
    CampBlueBuff = 6
    CampGromp = 7
    CampKrugs = 8
    CampRaptors = 9
    CampMurkWolves = 10
    LastKnownFlag = CampMurkWolves


class RingFlags(IntFlag):
    BlueSpawnToNexus = 0
    BlueNexusToInhib = 1
    BlueInhibToInner = 2
    BlueInnerToOuter = 3
    BlueOuterToNeutral = 4
    RedSpawnToNexus = 5
    RedNexusToInhib = 6
    RedInhibToInner = 7
    RedInnerToOuter = 8
    RedOuterToNeutral = 9
    LastKnownFlag = RedOuterToNeutral


class UnknownSRXFlags(IntFlag):
    Walkable = 0
    Wall = 1
    TransparentWall = 2
    Brush = 3
    Unobserved4 = 4
    TopSideOceanDrakePuddle = 5
    BotSideOceanDrakePuddle = 6
    BlueTeamOnly = 7
    RedTeamOnly = 8
    Unobserved9 = 9
    Unobserved10 = 10
    BlueTeamOnlyNeutralZoneVisibility = 11
    RedTeamOnlyNeutralZoneVisibility = 12
    BrushWall = 13
    LastKnownFlag = BrushWall


# 使用 @dataclass 来简化类的定义
@dataclass
class NavGridCell:
    index: int = None
    visionPathingFlags: VisionPathingFlags = 0
    riverRegionFlags: RiverRegionFlags = 0
    jungleQuadrantFlags: JungleQuadrantFlags = 0
    mainRegionFlags: MainRegionFlags = 0
    nearestLaneFlags: NearestLaneFlags = 0
    poiFlags: POIFlags = 0
    ringFlags: RingFlags = 0
    srxFlags: UnknownSRXFlags = 0

    centerHeight: float = 0
    sessionID: int = 0
    arrivalCost: float = 0
    isOpen: float = 0
    Heuristic: float = 0

    pos: vector2 = None

    hasOverride: bool = False

    actorList: int = 0
    goodCellSessionID: int = 0
    hintHeight: float = 0
    arrivalDirection: int = 0
    hintNode1: int = 0
    hintNode2: int = 0
    unknown1: int = 0
    unknown2: int = 0
    additional_cost: float = 0
    hint_as_good_cell: float = 0
    additional_cost_count: int = 0
    good_cell_session_ID: int = 0
    hint_weight: float = 0

    # 默认构造函数已由 @dataclass 自动生成

@dataclass
class CellMap:
    cells: list = field(default_factory=list)
    unknown_block: list = field(default_factory=list)

@dataclass
class HeightSampleVector:
    count: vector2 = None
    offset: vector2 = None

@dataclass
class HeightSampleMap:
    vector: HeightSampleVector = None
    height_samples: list = field(default_factory=list)
    min_height_sample: float = 0
    max_height_sample: float = 0