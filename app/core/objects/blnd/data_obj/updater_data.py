from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class UpdateTypes(Enum):
    LookAtSpellTargetAngleParametricUpdater = 0x0
    SkinScaleParametricUpdater = 0x1
    DisplacementParametricUpdater = 0x2
    TurnAngleParametricUpdater = 0x3
    MoveSpeedParametricUpdater = 0x4
    IsMovingParametricUpdater = 0x5
    FacingParametricUpdater = 0x6
    LookAtInterestAngleParametricUpdater = 0x7
    AttackSpeedParametricUpdater = 0x10
    LookAtSpellTargetDistanceParametricUpdater = 0x12
    LookAtSpellTargetHeightOffsetParametricUpdater = 0x13
    MovementDirectionParametricUpdater = 0x16
    IsAllyParametricUpdater = 0x20
    IsHomeguardParametricUpdater = 0x23

@dataclass
class UpdaterResource:
    mResourceSize: int = 0
    mVersion: int = 0
    mNumUpdaters: int = 0
    mUpdaterDataList: list = field(default_factory=list)

@dataclass
class UpdaterData:
    mInputType: int = 0
    mOutputType: int = 0
    mNumProcessors: int = 0
	mValueProcessorDataList: list = field(default_factory=list)

@dataclass
class LinearTransformProcessorData:
    mMultiplier: float = 0
    mIncrement: float = 0

@dataclass
class AnimValueProcessorData:
    mProcessorType: int = 0
    UnknownValue: int = 0

"""
ArenaOwnerLevelParametricUpdater
AttackSpeedParametricUpdater
DisplacementParametricUpdater
EquippedGearParametricUpdater
FacingAndMovementAngleParametricUpdater
FacingParametricUpdater
GrassSwayDirectionParametricUpdater
GrassSwayIntensityParametricUpdater
IBaseParametricUpdater
IBooleanParametricUpdater
IFloatParametricUpdater
IsAllyParametricUpdater
IsHomeguardParametricUpdater
IsInTerrainParametricUpdater
IsMovingParametricUpdater
IsRangedParametricUpdater
IsTurningParametricUpdater
LogicDriverBoolParametricUpdater
LogicDriverFloatParametricUpdater
LookAtGoldRedirectTargetAngleParametricUpdater
LookAtInterestAngleParametricUpdater
LookAtInterestDistanceParametricUpdater
LookAtSpellTargetAngleParametricUpdater
LookAtSpellTargetDistanceParametricUpdater
LookAtSpellTargetHeightOffsetParametricUpdater
MoveSpeedParametricUpdater
MovementDirectionParametricUpdater
MovingTowardEnemyParametricUpdater
ParBarPercentParametricUpdater
PathingAngleParametricUpdater
SkinScaleParametricUpdater
SlopeAngleParametricUpdater
TftArenaOwnerLevelParametricUpdater
TftArenaOwnerStreakParametricUpdater
TotalTurnAngleParametricUpdater
TurnAngleParametricUpdater
TurnAngleRemainingParametricUpdater
"""