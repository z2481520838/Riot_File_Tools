from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .base_value import*
from ...function.prop_text.math import*
from ...function.prop_text.obj_functions import*
import os

@dataclass
class BankUnit:
    name: str = None
    bankPath: list[str] = None
    events: list[str] = None
    voiceOver: bool = None

@dataclass
class CensoredImage:
    image: str = None

@dataclass
class TimeBlendData:
    mTime: f32 = None

@dataclass
class TrackData:
    mName: str = None

@dataclass
class AnimationResourceData:
    mAnimationFilePath: str = None

@dataclass
class ParticleEventDataPair:
    mEffectKey: str = None
    mBoneName: str = None

@dataclass
class SubmeshVisibilityEventData:
    mShowSubmeshList: list[str] = None
    mHideSubmeshList: list[str] = None
    mName: str = None
    mStartFrame: f32 = None
    mEndFrame: f32 = None

@dataclass
class ParticleEventData:
    mEffectName: str = None
    mEffectKey: str = None
    mParticleEventDataPairList: list[Any] = None
    mName: str = None
    mIsKillEvent: bool = None
    mIsLoop: bool = None
    mStartFrame: f32 = None
    mEndFrame: f32 = None

@dataclass
class JointSnapEventData:
    mJointNameToOverride: str = None
    mJointNameToSnapTo: str = None
    mName: str = None
    mStartFrame: f32 = None
    mEndFrame: f32 = None

@dataclass
class SequencerClipData:
    mClipNameList: list[str] = None
    mFlags: u32 = None

@dataclass
class ConditionBoolClipData:
    mUpdaterType: u32 = None
    mChangeAnimationMidPlay: bool = None
    mTrueConditionClipName: str = None
    mFalseConditionClipName: str = None

@dataclass
class ParallelClipData:
    mClipNameList: list[str] = None

@dataclass
class SelectorPairData:
    mClipName: str = None
    mProbability: f32 = None

@dataclass
class SelectorClipData:
    mSelectorPairDataList: list[Any] = None
    mFlags: u32 = None

@dataclass
class FaceCameraEventData:
    YRotationDegrees: f32 = None

@dataclass
class ParametricPairData:
    mClipName: str = None
    mValue: f32 = None

@dataclass
class ParametricClipData:
    mUpdaterType: u32 = None
    mParametricPairDataList: list[Any] = None
    mMaskDataName: str = None
    mTrackDataName: str = None
    mFlags: u32 = None

@dataclass
class AtomicClipData:
    mTickDuration: f32 = None
    mAnimationResourceData: Optional[AnimationResourceData] = None
    mTrackDataName: str = None
    mMaskDataName: str = None
    mSyncGroupDataName: str = None
    mEventDataList: list[Any] = None
    mEventDataMap: Dict[str, Any] = None
    mName: str = None
    mFlags: u32 = None

@dataclass
class MaskData:
    mId: u32 = None
    mWeightList: list[f32] = None

@dataclass
class TrackData:
    mPriority: u8 = None
    mBlendMode: u8 = None

@dataclass
class SyncGroupData:
    pass

@dataclass
class animationGraphData:
    mCascadeBlendValue: f32 = None
    mClipDataMap: Dict[str, Any] = None
    mMaskDataMap: Dict[str, Any] = None
    mTrackDataMap: Dict[str, Any] = None
    mSyncGroupDataMap: Dict[str, Any] = None
    mClipDataList: list[Any] = None
    mTrackDataList: list[Any] = None
    mBlendDataTable: Dict[u64, Any] = None

AnimationGraphData = animationGraphData

@dataclass
class skinAudioProperties:
    sfxBankPath: list[str] = None
    voBankPath: list[str] = None
    sfxBankAssetPath: list[str] = None
    voBankAssetPath: list[str] = None
    tagEventList: list[str] = None
    bankUnits: list[Any] = None

SkinAudioProperties = skinAudioProperties

@dataclass
class skinAnimationProperties:
    animationGraphData: str = None

SkinAnimationProperties = skinAnimationProperties

@dataclass
class SkinMeshDataProperties_MaterialOverride:
    texture: str = None
    material: str = None
    submesh: str = None

@dataclass
class SkinMeshDataProperties:
    skeleton: str = None
    simpleSkin: str = None
    texture: str = None
    glossTexture: str = None
    skinScale: f32 = None
    selfIllumination: f32 = None
    brushAlphaOverride: f32 = None
    overrideBoundingBox: Optional[vec3] = None
    usesSkinVO: bool = None
    boundingSphereRadius: Optional[f32] = None
    reflectionFresnelColor: rgba = None
    reflectionMap: str = None
    reflectionOpacityDirect: f32 = None
    reflectionFresnel: f32 = None
    initialSubmeshToHide: str = None
    submeshRenderOrder: str = None
    materialOverride: list[Any] = None

@dataclass
class SkinCharacterDataProperties_CharacterIdleEffect:
    effectKey: str = None
    boneName: str = None

@dataclass
class CharacterHealthBarDataRecord:
    unitHealthBarStyle: u8 = None

@dataclass
class SkinEmblem:
    mEmblemData: str = None
    mLoadingScreenAnchor: u32 = None

@dataclass
class CharacterHealthBarDataRecord:
    UnitBarKey: str = None
    unitHealthBarStyle: u8 = None

@dataclass
class SkinCharacterDataProperties:
    championSkinId: i32 = None
    skinClassification: u32 = None
    championSkinName: str = None
    metaDataTags: str = None
    loadscreen: Optional[str] = None
    loadscreenVintage: Optional[CensoredImage] = None
    skinAudioProperties: Optional[skinAudioProperties] = None
    skinAnimationProperties: Optional[skinAnimationProperties] = None
    skinMeshProperties: Optional[SkinMeshDataProperties] = None
    armorMaterial: str = None
    defaultAnimations: list[str] = None
    particleOverride_ChampionKillDeathParticle: str = None
    contextualActionRuleConfigFile: str = None
    Animations: str = None
    idleParticlesEffects: list[Any] = None
    iconAvatar: str = None
    mContextualActionData: str = None
    iconCircle: Optional[str] = None
    iconSquare: Optional[str] = None
    healthBarData: Optional[CharacterHealthBarDataRecord] = None
    mEmblems: list[Any] = None
    mResourceResolver: str = None

    def to_custom_format(self, source):
        return "SkinCharacterDataProperties {}"

@dataclass
class StaticMaterialShaderSamplerDef:
    samplerName: str = None
    textureName: str = None
    addressU: u32 = None
    addressV: u32 = None
    addressW: u32 = None

@dataclass
class StaticMaterialShaderParamDef:
    name: str = None
    value: vec4 = None

@dataclass
class StaticMaterialTechniqueDef:
    name: str = None
    passes: list[Any] = None

@dataclass
class StaticMaterialPassDef:
    shader: str = None
    blendEnable: bool = None
    srcColorBlendFactor: u32 = None
    srcAlphaBlendFactor: u32 = None
    dstColorBlendFactor: u32 = None
    dstAlphaBlendFactor: u32 = None

@dataclass
class StaticMaterialChildTechniqueDef:
    name: str = None
    parentName: str = None
    shaderMacros: Dict[str, str] = None

@dataclass
class DynamicMaterialDef:
    pass

@dataclass
class StaticMaterialDef:
    name: str = None
    samplerValues: list[Any] = None
    paramValues: list[Any] = None
    shaderMacros: Dict[str, str] = None
    techniques: list[Any] = None
    childTechniques: list[Any] = None
    dynamicMaterial: Optional[DynamicMaterialDef] =  None

@dataclass
class ContextualConditionCharacterMetadata:
    mCategory: str = None
    mData: str = None

@dataclass
class ContextualConditionRuleCooldown:
    mRuleCooldown: f32 = None

@dataclass
class ContextualConditionCharacterName:
    mCharacters: list[str] = None

@dataclass
class ContextualConditionCharacter:
    mCharacterType: u8 = None
    mChildConditions: list[Any] = None

@dataclass
class ContextualActionPlayVO:
    mSelfEventName: str = None
    mAllyEventName: str = None
    mEnemyEventName: str = None
    mSpectatorEventName: str = None
    mWaitTimeout: f32 = None

@dataclass
class ContextualRule:
    mRuleName: str = None
    mConditions: list[Any] = None
    mAudioAction: Any = None

@dataclass
class ContextualSituation:
    mRules: list[Any] = None

@dataclass
class ContextualActionData:
    mSituations: Dict[Any, Any] = None

