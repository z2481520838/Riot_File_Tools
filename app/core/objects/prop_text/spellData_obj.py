from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .base_value import*
from .targtingTypeData_obj import*
from ...function.prop_text.obj_functions import*

@dataclass
class Breakpoint:
    mLevel: u32 = None
    mAdditionalBonusAtThisLevel: f32 = None
    mBonusPerLevelAtAndAfter: f32 = None

@dataclass
class SpellEffectAmount:
    value: list[f32] = None
    def to_custom_format(self, get_name):
        lines = []
        write_str(lines, list_SpellEffectAmount(self.value, f"{get_name}Level"))
        return "\n".join(lines)

@dataclass
class SpellDataValue:
    mName: str = None
    mValues: list[f32] = None
    Unknown_3f95426c: bool = None
    mBaseP: f32 = None
    mFormula: str = None

@dataclass
class NamedDataValueCalculationPart:
    mDataValue: str = None

@dataclass
class StatBySubPartCalculationPart:
    mSubpart: Any = None
    mStat: u8 = None

@dataclass
class ByCharLevelFormulaCalculationPart:
    mValues: list[f32] = None
    Unknown_3f95426c: bool = None

@dataclass
class StatByNamedDataValueCalculationPart:
    mStat: u8 = None
    mStatFormula: u8 = None
    mDataValue: str = None

@dataclass
class ByCharLevelInterpolationCalculationPart:
    mStartValue: f32 = None
    mEndValue: f32 = None

@dataclass
class StatByCoefficientCalculationPart:
    mCoefficient: f32 = None
    mStat: u8 = None
    mStatFormula: u8 = None

@dataclass
class ByCharLevelBreakpointsCalculationPart:
    mLevel1Value: f32 = None
    mInitialBonusPerLevel: f32 = None
    mBreakpoints: list[Optional[Breakpoint]] = None

@dataclass
class NumberCalculationPart:
    mNumber: f32 = None

@dataclass
class Unknown_f3cbe7b2:
    mSpellCalculationKey: str = None

@dataclass
class EffectValueCalculationPart:
    mEffectIndex: i32 = None

@dataclass
class GameCalculation:
    mMultiplier: Optional[NumberCalculationPart] = None
    mPrecision: i32 = None
    mSimpleTooltipCalculationDisplay: u8 = None
    mFormulaParts: list[Any] = None
    mDisplayAsPercent: bool = None
    tooltipOnly: bool = None

@dataclass
class GameCalculationModified:
    mMultiplier: Optional[NamedDataValueCalculationPart] = None
    mModifiedGameCalculation: str = None
    tooltipOnly: bool = None

@dataclass
class SpellDataValueVector:
    SpellDataValues: list[Any] = None

@dataclass
class DrawablePositionLocator:
    basePosition: u32 = None
    distanceOffset: f32 = None
    orientationType: u32 = None
    # basePositionType = [0, 1, Target, 3, 4...]
    # orientationType = [0, 1, 2, MouseDir, 4...]
    def to_custom_format(self, get_name):
        lines = []
        write_str(lines, value_to_custom_format(self.basePosition, f"{get_name}_BasePosition"))
        write_str(lines, value_to_custom_format(self.distanceOffset, f"{get_name}_DistanceOffset"))
        write_str(lines, value_to_custom_format(self.orientationType, f"{get_name}_OrientationType"))
        return "\n".join(lines)

@dataclass
class FloatPerSpellLevel:
    mPerLevelValues: list[f32] = None
    mValueType: u32 = None

    def to_custom_format(self, get_name):
        lines = []
        write_str(lines, list_value_hasbase(self.mPerLevelValues, get_name))
        return "\n".join(lines)

@dataclass
class TargeterDefinitionMinimap:
    overrideBaseRange: Optional[FloatPerSpellLevel] = None

    def to_custom_format(self, get_name):
        lines = [f"[{get_name}]"]
        write_str(lines, "DrawableType=Minimap")
        write_str(lines, obj_to_custom_format(self.overrideBaseRange, "OverrideBaseRange"))
        write_blank_Line(lines)
        return "\n".join(lines)

@dataclass
class TargeterDefinitionRange:
    centerLocator: Optional[DrawablePositionLocator] = None
    overrideBaseRange: Optional[FloatPerSpellLevel] = None
    hideWithLineIndicator: bool = None
    useCasterBoundingBox: Optional[bool] = None
    textureOverrideName: str = None
    textureMaxGrowName: str = None

    def to_custom_format(self, get_name):
        lines = [f"[{get_name}]"]
        write_str(lines, "DrawableType=Range")
        write_str(lines, obj_to_custom_format(self.centerLocator, "Center"))
        write_str(lines, obj_to_custom_format(self.overrideBaseRange, "OverrideBaseRange"))
        write_str(lines, bool_to_custom_format(self.hideWithLineIndicator, "HideWithLineIndicator"))
        write_str(lines, bool_to_custom_format(self.useCasterBoundingBox, "UseCasterBoundingBox"))
        write_str(lines, get_path_baseName(self.textureOverrideName, "TextureOverride"))
        write_str(lines, get_path_baseName(self.textureMaxGrowName, "TextureMaxGrow"))
        write_blank_Line(lines)
        return "\n".join(lines)

@dataclass
class TargeterDefinitionLine:
    startLocator: Optional[DrawablePositionLocator] = None
    endLocator: Optional[DrawablePositionLocator] = None
    alwaysDraw: bool = None
    fallbackDirection: u32 = None
    lineStopsAtEndPosition: Optional[bool] = None
    minimumDisplayedRange: f32 = None
    lineWidth: Optional[FloatPerSpellLevel] = None
    overrideBaseRange: Optional[FloatPerSpellLevel] = None
    textureBaseOverrideName: str = None
    textureTargetOverrideName: str = None

    def to_custom_format(self, get_name):
        lines = [f"[{get_name}]"]
        write_str(lines, "DrawableType=Line")
        write_str(lines, obj_to_custom_format(self.startLocator, "Start"))
        write_str(lines, obj_to_custom_format(self.endLocator, "End"))
        write_str(lines, bool_to_custom_format(self.alwaysDraw, "AlwaysDraw"))
        write_str(lines, value_to_custom_format(self.fallbackDirection, "FallbackDirection"))
        write_str(lines, bool_to_custom_format(self.lineStopsAtEndPosition, "LineStopsAtEndPosition"))
        write_str(lines, obj_to_custom_format(self.lineWidth, "LineWidth"))
        write_str(lines, obj_to_custom_format(self.overrideBaseRange, "OverrideBaseRange"))
        write_str(lines, get_path_baseName(self.textureBaseOverrideName, "TextureBaseOverride"))
        write_str(lines, get_path_baseName(self.textureTargetOverrideName, "TextureTargetOverride"))
        write_blank_Line(lines)
        return "\n".join(lines)

@dataclass
class TargeterDefinitionCone:
    startLocator: Optional[DrawablePositionLocator] = None
    endLocator: Optional[DrawablePositionLocator] = None
    coneAngleDegrees: Optional[f32] = None
    coneRange: Optional[f32] = None
    textureConeOverrideName: str = None

    def to_custom_format(self, get_name):
        lines = [f"[{get_name}]"]
        write_str(lines, "DrawableType=Cone")
        write_str(lines, obj_to_custom_format(self.startLocator, "Start"))
        write_str(lines, obj_to_custom_format(self.endLocator, "End"))
        write_str(lines, value_to_custom_format(self.coneAngleDegrees, "ConeAngle")) #需要修正单位
        write_str(lines, value_to_custom_format(self.coneRange, "ConeRange"))
        write_str(lines, get_path_baseName(self.textureConeOverrideName, "TextureCone"))
        write_blank_Line(lines)
        return "\n".join(lines)

@dataclass
class TargeterDefinitionAoe:
    centerLocator: Optional[DrawablePositionLocator] = None
    isConstrainedToRange: bool = None
    constraintRange: Optional[FloatPerSpellLevel] = None
    overrideRadius: Optional[FloatPerSpellLevel] = None
    textureRadiusOverrideName: str = None

    def to_custom_format(self, get_name):
        lines = [f"[{get_name}]"]
        write_str(lines, "DrawableType=Aoe")
        write_str(lines, obj_to_custom_format(self.centerLocator, "Center"))
        write_str(lines, bool_to_custom_format(self.isConstrainedToRange, "IsConstrainedToRange"))
        write_str(lines, obj_to_custom_format(self.constraintRange, "ConstraintRange"))
        write_str(lines, obj_to_custom_format(self.overrideRadius, "OverrideRadius"))
        write_str(lines, get_path_baseName(self.textureRadiusOverrideName, "TextureOverride"))
        write_blank_Line(lines)
        return "\n".join(lines)

@dataclass
class TargeterDefinitionArc:
    startLocator: Optional[DrawablePositionLocator] = None
    endLocator: Optional[DrawablePositionLocator] = None
    isConstrainedToRange: bool = None
    constraintRange: Optional[FloatPerSpellLevel] = None
    overrideRadius: Optional[FloatPerSpellLevel] = None
    textureArcOverrideName: str = None
    thicknessOffset: f32 = None

    def to_custom_format(self, get_name):
        lines = [f"[{get_name}]"]
        write_str(lines, "DrawableType=Line")
        write_str(lines, obj_to_custom_format(self.startLocator, "Start"))
        write_str(lines, obj_to_custom_format(self.endLocator, "End"))
        write_str(lines, bool_to_custom_format(self.isConstrainedToRange, "IsConstrainedToRange"))
        write_str(lines, obj_to_custom_format(self.constraintRange, "ConstraintRange"))
        write_str(lines, obj_to_custom_format(self.overrideRadius, "OverrideRadius"))
        write_str(lines, get_path_baseName(self.textureArcOverrideName, "TextureOverride"))
        write_str(lines, value_to_custom_format(self.thicknessOffset, "ThicknessOffset"))
        write_blank_Line(lines)
        return "\n".join(lines)

@dataclass
class TargeterDefinitionWall:
    centerLocator: Optional[DrawablePositionLocator] = None
    thickness: Optional[FloatPerSpellLevel] = None
    length: Optional[FloatPerSpellLevel] = None

    def to_custom_format(self, get_name):
        lines = [f"[{get_name}]"]
        write_str(lines, "DrawableType=Wall")
        write_str(lines, obj_to_custom_format(self.centerLocator, "Center"))
        write_str(lines, obj_to_custom_format(self.thickness, "Thickness"))
        write_str(lines, obj_to_custom_format(self.length, "Length"))
        write_blank_Line(lines)
        return "\n".join(lines)

@dataclass
class TooltipInstanceListElement:
    _type: str = None
    typeIndex: i32 = None
    multiplier: f32 = None
    nameOverride: str = None
    Style: u32 = None

@dataclass
class TooltipInstanceList:
    levelCount: u32 = None
    elements: list[Any] = None

@dataclass
class TooltipInstanceSpell:
    mObjectName: str = None
    mFormat: str = None
    mLocKeys: Dict[str, str] = None
    mLists: Dict[str, Any] = None
    EnableExtendedTooltip: bool = None

@dataclass
class TooltipInstanceBuff:
    mObjectName: str = None
    mFormat: str = None
    mLocKeys: Dict[str, str] = None

@dataclass
class CustomTargeterDefinitions:
    mTargeterDefinitions: list[Any] = None

@dataclass
class SpellDataResourceClient:
    mUseTooltipFromAnotherSpell: str = None
    mTooltipData: Optional[TooltipInstanceSpell] = None
    mTargeterDefinitions: list[Optional[TargeterDefinitionRange]] = None
    mCustomTargeterDefinitions: Dict[str, Any] = None

    def to_custom_format(self):
        lines = []
        write_str(lines, list_count(self.mTargeterDefinitions, "NumSpellTargeters"))
        return "\n".join(lines)

@dataclass
class Defaultvisibility:
    mTargetControlsVisibility: bool = None

@dataclass
class EnterFOWVisibility:
    pass

@dataclass
class CircleMovement:
    mStartBoneName: str = None
    mAngularVelocity: f32 = None
    mLinearVelocity: f32 = None
    mLifetime: f32 = None

@dataclass
class FixedSpeedMovement:
    mProjectTargetToCastRange: bool = None
    mUseHeightOffsetAtEnd: bool = None
    mTracksTarget: bool = None
    mTargetHeightAugment: f32 = None
    mStartBoneName: str = None
    mSpeed: f32 = None
    mOffsetInitialTargetHeight: f32 = None

@dataclass
class FixedTimeMovement:
    mTargetHeightAugment: f32 = None
    mProjectTargetToCastRange: bool = None
    mTravelTime: f32 = None
    mUseHeightOffsetAtEnd: bool = None
    mTracksTarget: bool = None
    mOffsetInitialTargetHeight: f32 = None

@dataclass
class HermiteSplineInfo:
    mStartPositionOffset: vec3 = None
    mControlPoint1: vec3 = None
    mControlPoint2: vec3 = None

@dataclass
class FixedSpeedSplineMovement:
    mTracksTarget: bool = None
    mStartBoneName: str = None
    mSplineInfo: Optional[HermiteSplineInfo] = None
    mUseMissilePositionAsOrigin: bool = None
    mSpeed: f32 = None

@dataclass
class AcceleratingMovement:
    mProjectTargetToCastRange: bool = None
    mAcceleration: f32 = None
    mMinSpeed: f32 = None
    mMaxSpeed: f32 = None
    mInitialSpeed: f32 = None
    mUseHeightOffsetAtEnd: bool = None
    mTracksTarget: bool = None
    mOffsetInitialTargetHeight: f32 = None
    mStartBoneName: str = None

@dataclass
class ObjectTags:
    mTagList: str = None
    mObjectTagList: list[str] = None
    def to_custom_format(self, get_name):
        lines = []
        write_str(lines, str_base(self.mTagList, get_name))
        return "\n".join(lines)

@dataclass
class UseAutoattackCastTimeData:
    pass

@dataclass
class BlendedLinearHeightSolver:
    pass

@dataclass
class VerticalFacingFaceTarget:
    pass

@dataclass
class VeritcalFacingMatchVelocity:
    pass

@dataclass
class CastOnHit:
    pass

@dataclass
class CastOnMovementComplete:
    pass

@dataclass
class DestroyOnMovementComplete:
    pass

@dataclass
class ReturnToCasterOnMovementComplete:
    mOverrideSpec: Any = None

@dataclass
class GravityHeightSolver:
    mGravity: f32 = None

@dataclass
class MissileSpecification:
    mMissileWidth: f32 = None
    movementComponent: Optional[FixedSpeedMovement] = None
    visibilityComponent: Optional[Defaultvisibility] = None
    heightSolver: Optional[BlendedLinearHeightSolver] =  None
    verticalFacing: Optional[VerticalFacingFaceTarget] =  None
    behaviors: list[Any] = None

@dataclass
class AbilityObject:
    mRootSpell: str = None
    mChildSpells: list[str] = None
    mLifetimeManuallyManaged: bool = None
    mName: str = None
    mType: u8 = None
    AbilityTraits: u32 = None

@dataclass
class PlatformSpellInfo:
    mPlatformEnabled: bool = None
    def to_custom_format(self):
        lines = []
        write_str(lines, bool_to_custom_format(self.mPlatformEnabled, "PlatformEnabled"))
        return "\n".join(lines)

@dataclass
class HasBuffCastRequirement:
    mBuffName: str = None
    mInvertResult: bool = None

@dataclass
class SpellDataResource:
    flags: u32 = 0
    mAffectsTypeFlags: u32 = 0
    mAffectsStatusFlags: u32 = 0
    mRequiredUnitTags: Optional[ObjectTags] =  None
    mExcludedUnitTags: Optional[ObjectTags] =  None
    mPlatformSpellInfo: Optional[PlatformSpellInfo] =  None
    mSpellTags: list[str] = None
    mCastRequirementsTarget: list[Any] = None
    mAlternateName: str = None
    mDisplayName: str = None
    mDescription: str = None
    mDynamicTooltip: str = None
    mDynamicExtended: str = None
    mEffectAmount: list[Optional[SpellEffectAmount]] = None
    mDataValues: list[Optional[SpellDataValue]] = None
    Unknown_f9c2333e: Dict[hash, Any] = None
    mSpellCalculations: Dict[str, Any] = None
    DataValuesModeOverride: Dict[str, Any] = None
    mCoefficient: f32 = None
    mCoefficient2: f32 = None
    mAnimationName: str = None
    mAnimationLoopName: str = None
    mAnimationWinddownName: str = None
    mImgIconName: list[str] = None
    mChannelDuration: list[f32] = None
    mMinimapIconName: str = None
    mCastTime: f32 = None
    cooldownTime: list[f32] = None
    mMaxAmmo: list[i32] = None
    mAmmoRechargeTime: list[f32] = None
    mAmmoNotAffectedByCDR: bool = None
    delayCastOffsetPercent: f32 = None
    mApplyMaterialOnHitSound: bool = None
    delayTotalTimePercent: f32 = None
    mPreCastLockoutDeltaTime: f32 = None
    mPostCastLockoutDeltaTime: f32 = None
    mCasterPositionEndOfCastUpdate: u8 = None
    cannotBeSuppressed: bool = None
    canCastWhileDisabled: bool = None
    canCastOrQueueWhileCasting: bool = None
    mSpellRevealsChampion: bool = None
    mDoesNotConsumeCooldown: bool = None
    mUseChargeChanneling: bool = None
    cantCastWhileRooted: bool = None
    mDisableCastBar: bool = None
    mDoNotNeedToFaceTarget: bool = None
    mCursorChangesInTerrain: bool = None
    mUseMinimapTargeting: bool = None
    alwaysSnapFacing: bool = None
    mIgnoreRangeCheck: bool = None
    useAnimatorFramerate: bool = None
    mMinimapIconDisplayFlag: u16 = None
    mCanMoveWhileChanneling: bool = None
    mShowChannelBar: bool = None
    mCanTriggerChargeSpellWhileDisabled: bool = None
    mCantCancelWhileWindingUp: bool = None
    mCantCancelWhileChanneling: bool = None
    mChannelIsInterruptedByDisables: bool = None
    mChannelIsInterruptedByAttacking: bool = None
    castRangeUseBoundingBoxes: bool = None
    bIsToggleSpell: bool = None
    mDoesntBreakChannels: bool = None
    mUpdateRotationWhenCasting: bool = None
    mConsideredAsAutoAttack: bool = None
    mUseAutoattackCastTimeData: Optional[UseAutoattackCastTimeData] = None
    mProjectTargetToCastRange: bool = None
    mIsDisabledWhileDead: bool = None
    canOnlyCastWhileDead: bool = None
    mLineMissileEndsAtTargetPoint: bool = None
    mLineMissileTrackUnits: bool = None
    bHaveHitEffect: bool = None
    bHaveAfterEffect: bool = None
    mUseAutoattackCastTime: bool = None
    mRollForCriticalHit: bool = None
    castRange: list[f32] = None
    castRangeDisplayOverride: list[f32] = None
    mLookAtPolicy: u32 = None
    castRadius: list[f32] = None
    castRadiusSecondary: list[f32] = None
    castConeAngle: f32 = None
    castConeDistance: f32 = None
    luaOnMissileUpdateDistanceInterval: f32 = None
    mMissileSpec: Optional[MissileSpecification] = None
    mCastType: u32 = None
    castFrame: f32 = None
    mFloatVarsDecimals: list[i32] = None
    manaUiOverride: list[f32] = None
    missileSpeed: f32 = None
    MissileAccel: f32 = None
    MissileGravity: f32 = None
    mMissileTargetHeightAugment: f32 = None
    MissileMaxSpeed: Optional[f32] = None
    MissileMinSpeed: Optional[f32] = None
    MissileFixedTravelTime: f32 = None
    mMissileLifetime: f32 = None
    mMissileEffectName: str = None
    mMissileEffectKey: str = None
    mMissileEffectEnemyName: str = None
    mMissileEffectEnemyKey: str = None
    mMissileBoneName: str = None
    mMissileUnblockable: bool = None
    mMissileBlockTriggersOnDestroy: bool = None
    bHaveHitBone: bool = None
    mHitBoneName: str = None
    mana: list[f32] = None
    mLineWidth: f32 = None
    mHitEffectOrientType: u32 = None
    mHitEffectName: str = None
    mHitEffectKey: str = None
    mAfterEffectName: str = None
    mDeathRecapPriority: i32 = None
    mParticleStartOffset: vec3 = None
    selectionPriority: u32 = None
    mTargetingType: u8 = None
    mTargetingTypeData: Optional[Self] = None
    mSpellCooldownOrSealedQueueThreshold: Optional[f32] = None
    mDimensionBehavior: u8 = None
    mCastingBreaksStealth: bool = None
    mClientData: Optional[SpellDataResourceClient] = None

    def to_custom_format(self):
        lines = ["[SpellData]"]
        write_str(lines, spelldataflags_fix(self.flags, self.mAffectsTypeFlags, self.mAffectsStatusFlags))
        # write_str(lines, value_to_custom_format(self.flags, "Flags"))
        # write_str(lines, value_to_custom_format(self.mAffectsTypeFlags, "AffectsTypeFlags"))
        # write_str(lines, value_to_custom_format(self.mAffectsStatusFlags, "AffectsStatusFlags"))
        write_str(lines, obj_to_custom_format(self.mRequiredUnitTags, "RequiredUnitTags"))
        write_str(lines, obj_to_custom_format(self.mExcludedUnitTags, "ExcludedUnitTags"))
        write_str(lines, obj_to_custom_format(self.mPlatformSpellInfo))
        write_str(lines, list_base(self.mSpellTags, "SpellTags"))
        write_str(lines, str_base(self.mAlternateName, "AlternateName"))
        write_str(lines, str_base(self.mDisplayName, "DisplayName"))
        write_str(lines, str_base(self.mDescription, "Description"))
        write_str(lines, str_base(self.mDynamicTooltip, "DynamicTooltip"))
        write_str(lines, str_base(self.mDynamicExtended, "DynamicExtended"))
        write_str(lines, list_obj(self.mEffectAmount, "Effect"))
        write_str(lines, value_to_custom_format(self.mCoefficient, "Coefficient"))
        write_str(lines, value_to_custom_format(self.mCoefficient2, "Coefficient2"))
        write_str(lines, str_base(self.mAnimationName, "AnimationName"))
        write_str(lines, str_base(self.mAnimationLoopName, "AnimationLoopName"))
        write_str(lines, list_str_hasbase(self.mImgIconName, "InventoryIcon"))
        write_str(lines, list_value_hasbase(self.mChannelDuration, "ChannelDuration"))
        write_str(lines, get_path_baseName(self.mMinimapIconName, "MinimapIcon"))
        write_str(lines, value_to_custom_format(self.mCastTime, "OverrideCastTime"))
        write_str(lines, list_value_hasbase(self.cooldownTime, "Cooldown"))
        write_str(lines, list_value_hasbase(self.mMaxAmmo, "MaxAmmo"))
        write_str(lines, list_value_hasbase(self.mAmmoRechargeTime, "AmmoRechargeTime"))
        write_str(lines, bool_to_custom_format(self.mAmmoNotAffectedByCDR, "AmmoNotAffectedByCDR"))
        write_str(lines, value_to_custom_format(self.delayCastOffsetPercent, "DelayCastOffsetPercent"))
        write_str(lines, value_to_custom_format(self.delayTotalTimePercent, "DelayTotalTimePercent"))
        write_str(lines, bool_to_custom_format(self.mApplyMaterialOnHitSound, "ApplyMaterialOnHitSound"))
        write_str(lines, bool_to_custom_format(self.cannotBeSuppressed, "CannotBeSuppressed"))
        write_str(lines, bool_to_custom_format(self.canCastWhileDisabled, "CanCastWhileDisabled"))
        write_str(lines, bool_to_custom_format(self.canCastOrQueueWhileCasting, "CanCastOrQueueWhileCasting"))
        write_str(lines, bool_to_custom_format(self.mSpellRevealsChampion, "SpellRevealsChampion"))
        write_str(lines, bool_to_custom_format(self.mUseChargeChanneling, "UseChargeChanneling"))
        write_str(lines, bool_to_custom_format(self.cantCastWhileRooted, "CantCastWhileRooted"))
        write_str(lines, bool_to_custom_format(self.mDisableCastBar, "DisableCastBar"))
        write_str(lines, bool_to_custom_format(self.mDoNotNeedToFaceTarget, "DoNotNeedToFaceTarget"))
        write_str(lines, bool_to_custom_format(self.mCursorChangesInTerrain, "CursorChangesInTerrain"))
        write_str(lines, bool_to_custom_format(self.mUseMinimapTargeting, "UseMinimapTargeting"))
        write_str(lines, bool_to_custom_format(self.alwaysSnapFacing, "AlwaysSnapFacing"))
        write_str(lines, bool_to_custom_format(self.mIgnoreRangeCheck, "IgnoreRangeCheck"))
        write_str(lines, bool_to_custom_format(self.useAnimatorFramerate, "UseAnimatorFramerate"))
        write_str(lines, value_to_custom_format(self.mMinimapIconDisplayFlag, "MinimapIconDisplayFlag"))
        write_str(lines, bool_to_custom_format(self.mCanMoveWhileChanneling, "CanMoveWhileChanneling"))
        write_str(lines, bool_to_custom_format(self.mShowChannelBar, "ShowChannelBar"))
        write_str(lines, bool_to_custom_format(self.mCanTriggerChargeSpellWhileDisabled, "CanTriggerChargeSpellWhileDisabled"))
        write_str(lines, bool_to_custom_format(self.mCantCancelWhileWindingUp, "CantCancelWhileWindingUp"))
        write_str(lines, bool_to_custom_format(self.mCantCancelWhileChanneling, "CantCancelWhileChanneling"))
        write_str(lines, bool_to_custom_format(self.mChannelIsInterruptedByDisables, "ChannelIsInterruptedByDisables"))
        write_str(lines, bool_to_custom_format(self.mChannelIsInterruptedByAttacking, "ChannelIsInterruptedByAttacking"))
        write_str(lines, bool_to_custom_format(self.castRangeUseBoundingBoxes, "CastRangeUseBoundingBoxes"))
        write_str(lines, bool_to_custom_format(self.bIsToggleSpell, "IsToggleSpell"))
        write_str(lines, bool_to_custom_format(self.mDoesntBreakChannels, "DoesntBreakChannels"))
        write_str(lines, bool_to_custom_format(self.mUpdateRotationWhenCasting, "UpdateRotationWhenCasting"))
        write_str(lines, bool_to_custom_format(self.mConsideredAsAutoAttack, "ConsideredAsAutoAttack"))
        write_str(lines, bool_to_custom_format(self.mProjectTargetToCastRange, "ProjectTargetToCastRange"))
        write_str(lines, bool_to_custom_format(self.mIsDisabledWhileDead, "IsDisabledWhileDead"))
        write_str(lines, bool_to_custom_format(self.canOnlyCastWhileDead, "CanOnlyCastWhileDead"))
        write_str(lines, bool_to_custom_format(self.mLineMissileEndsAtTargetPoint, "LineMissileEndsAtTargetPoint"))
        write_str(lines, bool_to_custom_format(self.mLineMissileTrackUnits, "LineMissileTrackUnits"))
        write_str(lines, bool_to_custom_format(self.bHaveHitEffect, "HaveHitEffect"))
        write_str(lines, bool_to_custom_format(self.bHaveAfterEffect, "HaveAfterEffect"))
        write_str(lines, bool_to_custom_format(self.mUseAutoattackCastTime, "UseAutoattackCastTime"))
        write_str(lines, bool_to_custom_format(self.mRollForCriticalHit, "RollForCriticalHit"))
        write_str(lines, list_value_hasbase(self.castRange, "CastRange"))
        write_str(lines, list_value_hasbase(self.castRangeDisplayOverride, "CastRangeDisplayOverride"))
        write_str(lines, list_value_hasbase(self.castRadius, "CastRadius"))
        write_str(lines, list_value_hasbase(self.castRadiusSecondary, "CastRadiusSecondary"))
        write_str(lines, value_to_custom_format(self.mLookAtPolicy, "LookAtPolicy"))
        write_str(lines, value_to_custom_format(self.castConeAngle, "CastConeAngle"))
        write_str(lines, value_to_custom_format(self.castConeDistance, "CastConeDistance"))
        write_str(lines, value_to_custom_format(self.luaOnMissileUpdateDistanceInterval, "LuaOnMissileUpdateDistanceInterval"))
        write_str(lines, value_to_custom_format(self.mCastType, "CastType"))
        write_str(lines, value_to_custom_format(self.castFrame, "CastFrame"))
        write_str(lines, list_value(self.mFloatVarsDecimals, "FloatVarsDecimals"))
        write_str(lines, value_to_custom_format(self.MissileGravity, "MissileGravity"))
        write_str(lines, value_to_custom_format(self.mMissileTargetHeightAugment, "MissileTargetHeightAugment"))
        write_str(lines, value_to_custom_format(self.missileSpeed, "MissileSpeed"))
        write_str(lines, value_to_custom_format(self.MissileAccel, "MissileAccel"))
        write_str(lines, value_to_custom_format(self.MissileMaxSpeed, "MissileMaxSpeed"))
        write_str(lines, value_to_custom_format(self.MissileMinSpeed, "MissileMinSpeed"))
        write_str(lines, value_to_custom_format(self.MissileFixedTravelTime, "MissileFixedTravelTime"))
        write_str(lines, value_to_custom_format(self.mMissileLifetime, "MissileLifetime"))
        write_str(lines, str_base(self.mMissileEffectName, "MissileEffect")) #需要重写函数
        write_str(lines, str_base(self.mMissileEffectKey, "MissileEffect")) #需要重写函数
        write_str(lines, str_base(self.mMissileEffectEnemyName, "MissileEffectEnemy")) #需要重写函数
        write_str(lines, str_base(self.mMissileEffectEnemyKey, "MissileEffectEnemy")) #需要重写函数
        write_str(lines, str_base(self.mMissileBoneName, "MissileBoneName"))
        write_str(lines, bool_to_custom_format(self.mMissileUnblockable, "MissileUnblockable"))
        write_str(lines, bool_to_custom_format(self.mMissileBlockTriggersOnDestroy, "MissileBlockTriggersOnDestroy"))
        write_str(lines, bool_to_custom_format(self.bHaveHitBone, "HaveHitBone"))
        write_str(lines, str_base(self.mHitBoneName, "HitBoneName"))
        write_str(lines, list_value(self.mana, "ManaCost"))
        write_str(lines, value_to_custom_format(self.mLineWidth, "LineWidth"))
        write_str(lines, value_to_custom_format(self.mHitEffectOrientType, "HitEffectOrientType"))
        write_str(lines, str_base(self.mHitEffectName, "HitEffectName")) #需要重写函数
        write_str(lines, str_base(self.mHitEffectKey, "HitEffectName")) #需要重写函数
        write_str(lines, str_base(self.mAfterEffectName, "AfterEffectName"))
        write_str(lines, value_to_custom_format(self.mDeathRecapPriority, "DeathRecapPriority"))
        write_str(lines, obj_to_custom_format(self.mParticleStartOffset, "ParticleStartOffset"))
        write_str(lines, value_to_custom_format(self.selectionPriority, "SelectionPriority"))
        write_str(lines, value_to_custom_format(self.mTargetingType, "TargettingType"))
        write_str(lines, get_TargetingType(self.mTargetingTypeData))
        write_str(lines, obj_to_custom_format(self.mClientData))
        write_blank_Line(lines)
        write_str(lines, targeter_data(self.mClientData))
        return "\n".join(lines)

@dataclass
class BuffData:
    mDescription: str = None
    mFloatVarsDecimals: list[i32] = None
    mTooltipData: Optional[TooltipInstanceBuff] = None
    mShowDuration: bool = None

    def to_custom_format(self):
        lines = ["[BuffData]"]
        write_str(lines, str_base(self.mDescription, "DynamicTooltip"))
        write_str(lines, list_value(self.mFloatVarsDecimals, "FloatVarsDecimals"))
        write_blank_Line(lines)
        return "\n".join(lines)

@dataclass
class Unknown_150d1b92:
    Unknown_e38f54f7: u32 = None
    Unknown_0717e686: bool = None

@dataclass
class Unknown_b09016f6:
    EffectTag: u32 = None
    EffectCalculation: Optional[GameCalculation] = None

@dataclass
class BotsSpellData:
    DamageTag: u32 = None
    Unknown_6d548702: Optional[GameCalculation] = None
    Unknown_ec17e271: list[Any] = None
    Unknown_38382c53: list[Any] = None

@dataclass
class SpellObject:
    mScriptName: str = None
    mSpell: Optional[SpellDataResource] = None
    mBuff: Optional[BuffData] = None
    BotData: Optional[BotsSpellData] = None

    def to_custom_format(self, source):
        lines = [f"SpellDataResource={self.mScriptName}"]
        write_str(lines, obj_to_custom_format(self.mSpell))
        write_str(lines, obj_to_custom_format(self.mBuff))
        return "\n".join(lines)