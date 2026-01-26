from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .base_value import*
from ...function.prop_text.math import*
from ...function.prop_text.obj_functions import*
import os

@dataclass
class VfxProbabilityTableData:
    keyTimes: List[float] = field(default_factory=list)
    keyValues: List[float] = field(default_factory=list)

    def to_custom_format(self, prefix="P"):
        """
        输出概率表格式：
        PX1=t v
        PX2=t v
        """
        lines = []
        for i, (t, v) in enumerate(zip(self.keyTimes, self.keyValues), start=1):
            write_str(lines, f"{prefix}{i}={t} {v}")
        return "\n".join(lines)

@dataclass
class VfxAnimatedColorVariableData:
    probabilityTables: List[VfxProbabilityTableData] = field(default_factory=list)
    times: List[f32] = field(default_factory=list)
    values: List[vec4] = field(default_factory=list)

    def to_custom_format(self, constantValue: vec4, prefix="value"):
        """
        输出概率表 + 动态颜色
        """
        lines = []
        # 概率表
        prefix_list = ["XP", "YP", "ZP", "AP"]
        for prob_table, pf in zip(self.probabilityTables, [prefix + s for s in prefix_list]):
            if prob_table.keyTimes and prob_table.keyValues:
                lines.append(prob_table.to_custom_format(prefix=pf))

        # 动态值(带时间戳)，先除以 constantValue
        for i, (t, v) in enumerate(zip(self.times, self.values), start=1):
            if isinstance(v, vec4):
                vx, vy, vz, va = v
                nx, ny, nz, na = safe_div_vec(v, constantValue)
                lines.append(f"{prefix}{i}={t} {nx} {ny} {nz} {na}")
            else:
                lines.append(f"{prefix}{i}={t} {v}")

        return "\n".join(lines)

@dataclass
class VfxAnimatedVector2fVariableData:
    probabilityTables: List[VfxProbabilityTableData] = field(default_factory=list)
    times: List[f32] = field(default_factory=list)
    values: List[vec2] = field(default_factory=list)

    def to_custom_format(self, constantValue: vec2, prefix="value"):
        """
        输出概率表 + 动态值
        """
        lines = []
        # 概率表
        prefix_list = ["XP", "YP"]
        for prob_table, pf in zip(self.probabilityTables, [prefix + s for s in prefix_list]):
            if prob_table.keyTimes and prob_table.keyValues:
                lines.append(prob_table.to_custom_format(prefix=pf))
        # 动态值(带时间戳)，先除以 constantValue
        for i, (t, v) in enumerate(zip(self.times, self.values), start=1):
            if isinstance(v, vec2):
                vx, vy = v
                nx, ny = safe_div_vec(v, constantValue)
                lines.append(f"{prefix}{i}={t} {nx} {ny}")
            else:
                lines.append(f"{prefix}{i}={t} {v}")

        return "\n".join(lines)

@dataclass
class VfxAnimatedVector3fVariableData:
    probabilityTables: List[VfxProbabilityTableData] = field(default_factory=list)
    times: List[f32] = field(default_factory=list)
    values: List[vec3] = field(default_factory=list)

    def to_custom_format(self, constantValue: vec3, prefix="value"):
        """
        输出概率表 + 动态值
        """
        lines = []
        # 概率表
        prefix_list = ["XP", "YP", "ZP"]
        for prob_table, pf in zip(self.probabilityTables, [prefix + s for s in prefix_list]):
            if prob_table.keyTimes and prob_table.keyValues:
                lines.append(prob_table.to_custom_format(prefix=pf))
        # 动态值(带时间戳)，先除以 constantValue
        for i, (t, v) in enumerate(zip(self.times, self.values), start=1):
            if isinstance(v, vec3):
                vx, vy, vz = v
                nx, ny, nz = safe_div_vec(v, constantValue)
                lines.append(f"{prefix}{i}={t} {nx} {ny} {nz}")
            else:
                lines.append(f"{prefix}{i}={t} {v}")

        return "\n".join(lines)

@dataclass
class VfxAnimatedFloatVariableData:
    probabilityTables: List[VfxProbabilityTableData] = field(default_factory=list)
    times: List[f32] = field(default_factory=list)
    values: List[f32] = field(default_factory=list)

    def to_custom_format(self, constantValue: f32, prefix="value"):
        """
        输出概率表 + 动态值
        """
        lines = []
        # 概率表
        for prob_table in self.probabilityTables:
            if prob_table.keyTimes and prob_table.keyValues:
                write_str(lines, obj_to_custom_format(prob_table, prefix + "P"))

        # 动态值（带时间戳）
        for i, (t, v) in enumerate(zip(self.times, self.values), start=1):
            if isinstance(v, f32):
                v0 = v
                if constantValue != 0:
                    lines.append(f"{prefix}{i}={t} {v0/constantValue}")
            else:
                lines.append(f"{prefix}{i}={t} {v}")

        return "\n".join(lines)

@dataclass
class ValueColor:
    constantValue: vec4 = field(default_factory=lambda: vec4(1, 1, 1, 1))
    dynamics: Optional[VfxAnimatedColorVariableData] = None

    def to_custom_format(self, prefix="value"):
        lines = []
        # constantValue 单行输出
        write_str(lines, color_constantValue(self.constantValue, prefix))
        # dynamics 输出
        write_str(lines, obj_to_custom_format_special(self.dynamics, self.constantValue, prefix))
        return "\n".join(lines)

@dataclass
class ValueVector3:
    constantValue: vec3 = field(default_factory=lambda: vec3(0, 0, 0))
    dynamics: Optional[VfxAnimatedVector3fVariableData] = None

    def to_custom_format(self, prefix='value') -> str:
        lines = []
        # constantValue 单行输出
        if (prefix == "p-scale" or prefix == "p-xscale") and tuple(self.constantValue) == (0, 0, 0):
            self.constantValue = vec3(1, 1, 1)
        write_str(lines, obj_to_custom_format(self.constantValue, prefix))
        # dynamics 输出
        write_str(lines, obj_to_custom_format_special(self.dynamics, self.constantValue, prefix))
        return '\n'.join(lines)

IntegratedValueVector3 = ValueVector3

@dataclass
class ValueVector2:
    constantValue: vec2 = field(default_factory=lambda: vec2(0, 0))
    dynamics: Optional[VfxAnimatedVector2fVariableData] = None

    def to_custom_format(self, prefix='value') -> str:
        lines = []
        write_str(lines, obj_to_custom_format(self.constantValue, prefix))
        # dynamics 输出
        write_str(lines, obj_to_custom_format_special(self.dynamics, self.constantValue, prefix))
        return '\n'.join(lines)

IntegratedValueVector2 = ValueVector2

@dataclass
class ValueFloat:
    constantValue: Optional[f32] = field(default_factory=lambda: 0)
    dynamics: Optional[VfxAnimatedFloatVariableData] = None

    def to_custom_format(self, prefix: str) -> str:
        lines = []
        if self.constantValue != 0:
            write_str(lines, f"{prefix}={self.constantValue}")
        write_str(lines, obj_to_custom_format_special(self.dynamics, self.constantValue, prefix))
        return '\n'.join(lines)

IntegratedValueFloat = ValueFloat

@dataclass
class VfxShapeCylinder:
    flags: u8 = None
    radius: f32 = None
    height: f32 = None
    Size: vec3 = None

    def to_custom_format(self) -> str:
        lines = []
        return '\n'.join(lines)

VfxShapeSphere = VfxShapeCylinder
VfxShapeBox = VfxShapeCylinder

@dataclass
class VfxShapeLegacy:
    birthTranslation: Optional[ValueVector3] = None
    emitOffset: Optional[ValueVector3] = None
    emitRotationAngles: List[ValueFloat] = field(default_factory=list)
    emitRotationAxes: List[vec3] = field(default_factory=list)

    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, obj_to_custom_format(self.birthTranslation, "p-postoffset"))
        write_str(lines, obj_to_custom_format(self.emitOffset, "p-offset"))
        for i, angle in enumerate(self.emitRotationAngles, start=1):
            write_str(lines, obj_to_custom_format(angle, f"e-rotation{i}"))
        for i, axis in enumerate(self.emitRotationAxes, start=1):
            write_str(lines, obj_to_custom_format(axis, f"e-rotation{i}-axis"))
        return "\n".join(lines)

VfxShape = VfxShapeLegacy
Unknown_ee39916f = VfxShapeLegacy

@dataclass
class VfxMeshDefinitionData:
    mSimpleMeshName: str = None
    mMeshName: str = None
    mMeshSkeletonName: str = None
    mAnimationName: str = None
    mSubmeshesToDraw: list[hash] = None
    mSubmeshesToDrawAlways: list[hash] = None
    mLockMeshToAttachment: bool = None

    def append_subMesh(self, lines: list) -> None:
        # 确保 mSubmeshesToDraw 是一个列表，且不是 None
        if self.mSubmeshesToDraw is not None:
            # 创建一个空列表来保存有效的 submesh keys
            submesh_keys = []
            for key in self.mSubmeshesToDraw:
                if key is None:
                    continue  # 跳过未定义的对象
                submesh_keys.append(str(key))  # 将 key 转换为字符串（如果需要）
            # 将子网格列表的键值拼接为 "submesh-list=key0 key1 ..." 格式
            if submesh_keys != []:
                lines.append(f"submesh-list={' '.join(submesh_keys)}")

    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, get_path_baseName(self.mSimpleMeshName, "p-mesh"))
        write_str(lines, get_path_baseName(self.mMeshName, "p-skin"))
        write_str(lines, get_path_baseName(self.mMeshSkeletonName, "p-skeleton"))
        write_str(lines, get_path_baseName(self.mAnimationName, "p-animation"))
        self.append_subMesh(lines)
        return "\n".join(lines)

@dataclass
class VfxTrailDefinitionData:
    mMode: u8 = None
    mCutoff: f32 = None
    mBirthTilingSize: Optional[ValueVector3] = None
    mSmoothingMode: u8 = None
    mMaxAddedPerFrame: i32 = None

    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, value_to_custom_format(self.mMode, "p-trailmode"))
        write_str(lines, value_to_custom_format(self.mCutoff, "e-trail-cutoff"))
        write_str(lines, obj_to_custom_format(self.mBirthTilingSize, "e-tilesize"))
        return "\n".join(lines)

@dataclass
class VfxPrimitiveArbitraryQuad:
    type_: int = 1
    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, value_to_custom_format(self.type_, "p-type"))
        return "\n".join(lines)

@dataclass
class VfxPrimitiveRay:
    type_: int = 2
    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, value_to_custom_format(self.type_, "p-type"))
        return "\n".join(lines)

@dataclass
class VfxPrimitiveMesh:
    mMesh: Optional[VfxMeshDefinitionData] = None
    AlignPitchToCamera: bool = None
    AlignYawToCamera: bool = None
    type_: int = 3

    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, value_to_custom_format(self.type_, "p-type"))
        write_str(lines, obj_to_custom_format(self.mMesh))
        return "\n".join(lines)

@dataclass
class VfxPrimitiveCameraTrail:
    mTrail: Optional[VfxTrailDefinitionData] = None
    type_: int = 4
    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, value_to_custom_format(self.type_, "p-type"))
        write_str(lines, obj_to_custom_format(self.mTrail))
        return "\n".join(lines)

@dataclass
class VfxPrimitiveArbitraryTrail:
    mTrail: Optional[VfxTrailDefinitionData] = None
    type_: int = 5
    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, value_to_custom_format(self.type_, "p-type"))
        write_str(lines, obj_to_custom_format(self.mTrail))
        return "\n".join(lines)

@dataclass
class VfxBeamDefinitionData:
    mBirthTilingSize: Optional[ValueVector3] = None
    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, value_to_custom_format(self.mBirthTilingSize, "e-tilesize"))
        return "\n".join(lines)

@dataclass
class VfxPrimitiveBeam:
    mBeam: Optional[VfxBeamDefinitionData] = None
    mMesh: Optional[VfxMeshDefinitionData] = None
    type_: int = 6

    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, value_to_custom_format(self.type_, "p-type"))
        write_str(lines, obj_to_custom_format(self.mBeam))
        write_str(lines, obj_to_custom_format(self.mMesh))
        return "\n".join(lines)

@dataclass
class VfxPrimitiveAttachedMesh:
    type_: int = 11
    mMesh: Optional[VfxMeshDefinitionData] = None

    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, value_to_custom_format(self.type_, "p-type"))
        write_str(lines, obj_to_custom_format(self.mMesh))
        return "\n".join(lines)
        
@dataclass
class VfxTextureMultDefinitionData:
    textureMult: str = None
    texDivMult: vec2 = None
    uvScaleMult: Optional[ValueVector2] = None
    texAddressModeMult: u8 = None
    TextureMultFilpU: flag = None
    birthUvScrollRateMult: Optional[ValueVector2] = None
    ParticleIntegratedUvScrollMult: Optional[IntegratedValueVector2] = None
    particleUVScrollRateMult: Optional[IntegratedValueVector2] = None
    birthUVOffsetMult: Optional[ValueVector2] = None
    birthUvRotateRateMult: Optional[ValueFloat] = None
    emitterUvScrollRateMult: vec2 = None
    UvRotationMult: Optional[ValueFloat] = None

    def to_custom_format(self, type_Name) -> str:
        lines = []
        write_str(lines, get_path_baseName(self.textureMult, f"{type_Name}-mult"))
        write_str(lines, obj_to_custom_format(self.texDivMult, "p-texdiv-mult"))
        write_str(lines, texture_mode_fix(self.texAddressModeMult, "p-texture-mult-mode"))
        write_str(lines, UVScrollRate(self.birthUvScrollRateMult, self.particleUVScrollRateMult, "p-uvscroll-rgb-mult"))
        write_str(lines, obj_to_custom_format(self.birthUVOffsetMult, "e-uvoffset-mult"))
        write_str(lines, obj_to_custom_format(self.ParticleIntegratedUvScrollMult, "p-uvscroll-rgb-mult"))
        return "\n".join(lines)

@dataclass
class VfxReflectionDefinitionData:
    reflectionMapTexture: str = None
    reflectionOpacityDirect: f32 = None
    reflectionOpacityGlancing: f32 = None
    reflectionFresnelColor: vec4 = None
    reflectionFresnel: f32 = None
    fresnel: f32 = None
    fresnelColor: vec4 = None

    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, get_path_baseName(self.reflectionMapTexture, "p-reflection-map"))
        write_str(lines, value_to_custom_format(self.reflectionOpacityDirect, "p-reflection-opacity-direct"))
        write_str(lines, value_to_custom_format(self.reflectionOpacityGlancing, "p-reflection-opacity-glancing"))
        write_str(lines, obj_to_custom_format(self.reflectionFresnelColor, "p-reflection-fresnel-color"))
        write_str(lines, value_to_custom_format(self.fresnel, "p-fresnel"))
        write_str(lines, obj_to_custom_format(self.fresnelColor, "p-fresnel-color"))
        return "\n".join(lines)

@dataclass
class VfxDistortionDefinitionData:
    distortion: f32 = None
    distortionMode: u8 = None
    normalMapTexture: str = None

    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, value_to_custom_format(self.distortion, "p-distortion-power"))
        write_str(lines, value_to_custom_format(self.distortionMode, "p-distortion-mode"))
        write_str(lines, get_path_baseName(self.normalMapTexture, "p-normal-map"))
        return "\n".join(lines)

@dataclass
class VfxFlexShapeDefinitionData:
    scaleBirthScaleByBoundObjectSize: f32 = None
    scaleEmitOffsetByBoundObjectSize: f32 = None

    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, value_to_custom_format(self.scaleBirthScaleByBoundObjectSize, "p-flexscale"))
        write_str(lines, value_to_custom_format(self.scaleEmitOffsetByBoundObjectSize, "p-flexoffset"))
        return "\n".join(lines)

@dataclass
class VfxAlphaErosionDefinitionData:
    erosionDriveCurve: Optional[ValueFloat] = None
    erosionFeatherIn: f32 = None
    erosionFeatherOut: f32 = None
    erosionSliceWidth: f32 = None
    erosionMapName: str = None
    UseLingerErosionDriveCurve: bool = None
    erosionMapChannelMixer: Optional[ValueColor] = None
    erosionMapAddressMode: u8 = None
    
@dataclass
class VfxSoftParticleDefinitionData:
    beginIn: f32 = None
    deltaIn: f32 = None
    beginOut: f32 = None
    deltaOut: f32 = None

    def to_custom_format(self) -> str:
        lines = []
        write_str(lines, value_to_custom_format(self.beginIn, "e-soft-in-depth"))
        write_str(lines, value_to_custom_format(self.deltaIn, "e-soft-in-depth-delta"))
        write_str(lines, value_to_custom_format(self.beginOut, "e-soft-out-depth"))
        write_str(lines, value_to_custom_format(self.deltaOut, "e-soft-out-depth-delta"))
        return "\n".join(lines)

@dataclass
class VfxChildIdentifier:
    effectKey: hash = None
    def to_custom_format(self, source) -> str:
        lines = []
        if self.effectKey is not None:
            # 获取 ResourceResolver 中的资源
            resource_key = source.get_resource_resolver(self.effectKey)
            # 检查 resource_key 是否是哈希值，若是，则保持原样并加上引号
            if isinstance(resource_key, (int, bytes)):  # 如果是哈希值
                resource_key = str(resource_key)
            lines.append(f"{get_path_baseName(resource_key, 'ChildParticleName')}.troy")
        return "\n".join(lines)

@dataclass
class VfxChildParticleSetDefinitionData:
    childrenIdentifiers: list[Optional[VfxChildIdentifier]] = None
    boneToSpawnAt: list[str] = None
    childEmitOnDeath: bool = None
    def to_custom_format(self, source) -> str:
        lines = []
        if self.childrenIdentifiers is not None:
            for child in self.childrenIdentifiers:
                lines.append(child.to_custom_format(source))
        if self.boneToSpawnAt is not None:
            for bone in self.boneToSpawnAt:
                write_str(lines, value_to_custom_format(bone, "ChildSpawnAtBone"))
        write_str(lines, bool_to_custom_format(self.childEmitOnDeath, "ChildEmitOnDeath"))
        return "\n".join(lines)

@dataclass
class VfxMaterialOverrideDefinitionData:
    priority: i32 = None
    subMeshName: str = None
    overrideBlendMode: i32 = None
    baseTexture: str = None
    transitionTexture: str = None
    transitionSample: f32 = None

    def to_custom_format(self, index: int):
        lines = []
        write_str(lines, value_to_custom_format(self.priority, f"MaterialOverride{index}Priority"))
        write_str(lines, get_path_baseName(self.subMeshName, f"MaterialOverride{index}SubMesh"))
        write_str(lines, value_to_custom_format(self.overrideBlendMode, f"MaterialOverride{index}BlendMode"))
        write_str(lines, get_path_baseName(self.baseTexture, f"MaterialOverride{index}Texture"))
        write_str(lines, get_path_baseName(self.transitionTexture, "MaterialOverrideTransMap"))
        write_str(lines, value_to_custom_format(self.transitionSample, "p-trans-sample"))
        return "\n".join(lines)

@dataclass
class VfxFieldAccelerationDefinitionData:
    isLocalSpace: bool = None
    acceleration: Optional[ValueVector3] = None
    radius: Optional[ValueFloat] = None

    def to_custom_format(self):
        lines = []
        write_str(lines, bool_to_custom_format(self.isLocalSpace, "f-localspace"))
        write_str(lines, obj_to_custom_format(self.acceleration, "f-accel"))
        write_str(lines, obj_to_custom_format(self.radius, "f-radius"))
        return "\n".join(lines)

@dataclass
class VfxFieldAttractionDefinitionData:
    isLocalSpace: bool = None
    position: Optional[ValueVector3] = None
    radius: Optional[ValueFloat] = None
    acceleration: Optional[ValueVector3] = None

    def to_custom_format(self):
        lines = []
        write_str(lines, bool_to_custom_format(self.isLocalSpace, "f-localspace"))
        write_str(lines, obj_to_custom_format(self.position, "f-pos"))
        write_str(lines, obj_to_custom_format(self.radius, "f-radius"))
        write_str(lines, obj_to_custom_format(self.acceleration, "f-accel"))
        return "\n".join(lines)

@dataclass
class VfxFieldNoiseDefinitionData:
    position: Optional[ValueVector3] = None
    radius: Optional[ValueFloat] = None
    frequency: Optional[ValueFloat] = None
    velocityDelta: Optional[ValueFloat] = None
    axisFraction: vec3 = None

    def to_custom_format(self):
        lines = []
        write_str(lines, obj_to_custom_format(self.position, "f-pos"))
        write_str(lines, obj_to_custom_format(self.radius, "f-radius"))
        write_str(lines, obj_to_custom_format(self.frequency, "f-period"))
        write_str(lines, obj_to_custom_format(self.velocityDelta, "f-veldelta"))
        write_str(lines, obj_to_custom_format(self.axisFraction, "f-axisfrac"))
        return "\n".join(lines)

@dataclass
class VfxFieldDragDefinitionData:
    position: Optional[ValueVector3] = None
    radius: Optional[ValueFloat] = None
    strength: Optional[ValueFloat] = None

    def to_custom_format(self):
        lines = []
        write_str(lines, obj_to_custom_format(self.position, "f-pos"))
        write_str(lines, obj_to_custom_format(self.radius, "f-radius"))
        write_str(lines, obj_to_custom_format(self.strength, "f-drag"))
        return "\n".join(lines)

@dataclass
class VfxFieldOrbitalDefinitionData:
    isLocalSpace: bool = None
    direction: Optional[ValueVector3] = None

    def to_custom_format(self):
        lines = []
        write_str(lines, bool_to_custom_format(self.isLocalSpace, "f-localspace"))
        write_str(lines, obj_to_custom_format(self.direction, "f-direction"))
        return "\n".join(lines)

VfxFieldAccelerationDefinitionDataInstance = VfxFieldAccelerationDefinitionData
VfxFieldAttractionDefinitionDataInstance = VfxFieldAttractionDefinitionData
VfxFieldDragDefinitionDataInstance = VfxFieldDragDefinitionData
VfxFieldNoiseDefinitionDataInstance = VfxFieldNoiseDefinitionData
VfxFieldOrbitalDefinitionDataInstance = VfxFieldOrbitalDefinitionData

@dataclass
class VfxFieldCollectionDefinitionData:
    fieldAccelerationDefinitions: list[Optional[VfxFieldAccelerationDefinitionData]] = None
    fieldAttractionDefinitions: list[Optional[VfxFieldAttractionDefinitionData]] = None
    fieldDragDefinitions: list[Optional[VfxFieldDragDefinitionData]] = None
    fieldNoiseDefinitions: list[Optional[VfxFieldNoiseDefinitionData]] = None
    fieldOrbitalDefinitions: list[Optional[VfxFieldOrbitalDefinitionData]] = None

@dataclass
class VfxFieldCollectionDefinitionData:
    fieldAccelerationDefinitions: list[Optional['VfxFieldAccelerationDefinitionData']] = None
    fieldAttractionDefinitions: list[Optional['VfxFieldAttractionDefinitionData']] = None
    fieldDragDefinitions: list[Optional['VfxFieldDragDefinitionData']] = None
    fieldNoiseDefinitions: list[Optional['VfxFieldNoiseDefinitionData']] = None
    fieldOrbitalDefinitions: list[Optional['VfxFieldOrbitalDefinitionData']] = None

    def to_custom_format(self):
        lines = []
        write_str(lines, field_data(self.fieldAccelerationDefinitions, "FieldAccelerationDefinitions"))
        write_str(lines, field_data(self.fieldAttractionDefinitions, "FieldAttractionDefinitions"))
        write_str(lines, field_data(self.fieldDragDefinitions, "FieldDragDefinitions"))
        write_str(lines, field_data(self.fieldNoiseDefinitions, "FieldNoiseDefinitions"))
        write_str(lines, field_data(self.fieldOrbitalDefinitions, "FieldOrbitalDefinitions"))
        return "\n".join(lines)

VfxFieldCollectionDefinitionDataInstance = VfxFieldCollectionDefinitionData

@dataclass
class VfxPaletteDefinitionData:
    paletteTexture: str = None
    palleteSrcMixColor: Optional[ValueColor] = None
    paletteSelector: Optional[ValueVector3] = None
    paletteCount: i32 = None

@dataclass
class VfxLingerDefinitionData:
    UseLingerRotation: flag = None
    UseLingerScale: flag = None
    LingerScale: Optional[ValueVector3] = None
    UseSeparateLingerColor: flag = None
    SeparateLingerColor: Optional[ValueColor] = None

@dataclass
class VfxEmitterFiltering:
    spectatorPolicy: u8 = None

@dataclass
class FlexValueVector2:
    pass

@dataclass
class VfxEmitterDefinitionData:
    timeBeforeFirstEmission: Optional[f32] = None
    rate: Optional[ValueFloat] = None
    particleLifetime: Optional[ValueFloat] = None
    particleLingerType: u8 = None
    particleLinger: Optional[f32] = 0
    lifetime: Optional[f32] = None
    rateByVelocityFunction: Optional[ValueVector2] = None
    fieldCollectionDefinition: Optional[VfxFieldCollectionDefinitionData] = None
    isSingleParticle: Optional[flag] = None
    childParticleSetDefinition: Optional[VfxChildParticleSetDefinitionData] = None
    emitterLinger: Optional[f32] = None
    emitterName: str = "GroupPartName"
    keywordsExcluded: list[str] = None
    rotationOverride: vec3 = None
    disabled: bool = None
    importance: u8 = None
    Filtering: Optional[VfxEmitterFiltering] = None
    bindWeight: Optional[ValueFloat] = None
    FlexShapeDefinition: Optional[VfxFlexShapeDefinitionData] = None
    scaleBirthScaleByBoundObjectSize: f32 = None
    scaleBirthScaleByBoundObjectHeight: f32 = None
    velocity: Optional[ValueVector3] = None
    drag: Optional[ValueVector3] = None
    birthOrbitalVelocity: Optional[ValueVector3] = None
    birthVelocity: Optional[ValueVector3] = None
    birthDrag: Optional[ValueVector3] = None
    acceleration: Optional[ValueVector3] = None
    birthAcceleration: Optional[ValueVector3] = None
    worldAcceleration: Optional[IntegratedValueVector3] = None
    emissionMeshScale: f32 = None
    emissionMeshName: str = None
    SpawnShape: Optional[VfxShapeLegacy] = None
    shape: Optional[VfxShape] = None
    EmitterPosition: Optional[ValueVector3] = None
    primitive: Optional[VfxPrimitiveArbitraryQuad] = None
    particleColorTexture: str = None
    blendMode: Optional[u8] = None
    birthColor: Optional[ValueColor] = None
    color: Optional[ValueColor] = None
    useLingerColor: flag = None
    lingerColor: Optional[ValueColor] = None
    _pass: Optional[i16] = None
    distortionDefinition: Optional[VfxDistortionDefinitionData] = None
    colorLookUpTypeX: u8 = None
    colorLookUpTypeY: u8 = None
    colorLookUpScales: vec2 = None
    alphaRef: Optional[u8] = None
    censorModulateValue: vec4 = None
    colorLookUpOffsets: vec2 = None
    sliceTechniqueRange: f32 = None
    alphaErosionDefinition: Optional[VfxAlphaErosionDefinitionData] = None
    Unknown_cb13aff1: f32 = None
    disableBackfaceCull: bool = None
    uvParallaxScale: f32 = None
    softParticleParams: Optional[VfxSoftParticleDefinitionData] = None
    depthBiasFactors: vec2 = None
    miscRenderFlags: Optional[u8] = None
    Unknown_d1ee8634: flag = None
    uvScrollAlphaMult: flag = None
    isFollowingTerrain: flag = None
    stencilRef: u8 = None
    meshRenderFlags: u8 = None
    colorRenderFlags: u8 = None
    bState: u32 = None
    hasPostRotateOrientation: flag = None
    isDirectionOriented: flag = None
    isRandomStartFrame: flag = None
    isLocalOrientation: Optional[flag] = None
    isRotationEnabled: flag = None
    isGroundLayer: flag = None
    useEmissionMeshNormalForBirth: flag = None
    useNavmeshMask: flag = None
    doesCastShadow: flag = None
    reflectionDefinition: Optional[VfxReflectionDefinitionData] = None
    birthRotation0: Optional[ValueVector3] = None
    rotation0: Optional[IntegratedValueVector3] = None
    birthRotationalVelocity0: Optional[ValueVector3] = None
    particleIsLocalOrientation: Optional[flag] = None
    isUniformScale: Optional[flag] = None
    ParticlesShareRandomValue: flag = None
    uvScrollClamp: flag = None
    materialOverrideDefinitions: list[Optional[VfxMaterialOverrideDefinitionData]] = None
    directionVelocityScale: f32 = None
    directionVelocityMinScale: f32 = None
    birthScale0: Optional[ValueVector3] = None
    scale0: Optional[ValueVector3] = None
    texture: str = None
    meshTextureName: str = None
    startFrame: u16 = None
    frameRate: f32 = None
    birthFrameRate: Optional[ValueFloat] = None
    numFrames: u16 = None
    birthUvScrollRate: Optional[ValueVector2] = None
    birthUVOffset: Optional[ValueVector2] = None
    texDiv: vec2 = None
    texDivMult: vec2 = None
    texAddressModeBase: u8 = None
    emitterUvScrollRate: vec2 = None
    particleUVScrollRate: Optional[ValueVector2] = None
    textureMult: Optional[VfxTextureMultDefinitionData] = None
    birthUvScrollRateMult: Optional[ValueVector2] = None
    birthUVOffsetMult: Optional[ValueVector2] = None
    texAddressModeMult: u8 = None
    particleUVScrollRateMult: Optional[ValueVector2] = None
    uvScale: Optional[ValueVector2] = None
    uvMode: Optional[u8] = None
    uvRotation: Optional[ValueFloat] = None
    TextureFlipU: flag = None
    paletteDefinition: Optional[VfxPaletteDefinitionData] = None
    particleUVRotateRateMult: Optional[IntegratedValueFloat] = None
    Linger: Optional[VfxLingerDefinitionData] = None
    birthScale1: Optional[ValueFloat] = None
    scale1: Optional[ValueFloat] = None
    birthRotation1: Optional[ValueFloat] = None
    particleBind: vec2 = None
    scaleBias: vec2 = None
    flexBirthUVOffset: Optional[FlexValueVector2] = None
    orientation: u32 = None

    def to_custom_format(self, source):
        lines = [f"[{self.emitterName.replace(' ', '_')}]"]
        write_str(lines, value_to_custom_format(self.timeBeforeFirstEmission, "e-timeoffset"))
        write_str(lines, obj_to_custom_format(self.rate, "e-rate"))
        write_str(lines, obj_to_custom_format(self.particleLifetime, "p-life"))
        write_str(lines, value_to_custom_format(self.particleLinger, "p-linger"))
        write_str(lines, value_to_custom_format(self.lifetime, "e-life"))
        write_str(lines, obj_to_custom_format(self.rateByVelocityFunction, "e-ratebyvel"))
        write_str(lines, field_pointer(self.fieldCollectionDefinition))
        write_str(lines, bool_to_custom_format(self.isSingleParticle, "single-particle"))
        write_str(lines, childParticle_data(self.childParticleSetDefinition, source))
        write_str(lines, add_fix_child_tex(self))
        write_str(lines, value_to_custom_format(self.emitterLinger, "e-linger"))
        write_str(lines, list_str(self.keywordsExcluded, "KeywordsExcluded"))
        write_str(lines, bool_to_custom_format(self.disabled, "e-disabled"))
        write_str(lines, obj_to_custom_format(self.bindWeight, "p-bindtoemitter"))
        write_str(lines, obj_to_custom_format(self.FlexShapeDefinition))
        write_str(lines, value_to_custom_format(self.scaleBirthScaleByBoundObjectSize, "p-flexscale"))
        write_str(lines, value_to_custom_format(self.scaleBirthScaleByBoundObjectHeight, "p-scalebyheight"))
        write_str(lines, obj_to_custom_format(self.velocity, "Particle-Velocity"))
        write_str(lines, obj_to_custom_format(self.drag, "Particle-Drag"))
        write_str(lines, obj_to_custom_format(self.birthOrbitalVelocity, "p-orbitvel"))
        write_str(lines, obj_to_custom_format(self.birthVelocity, "p-vel"))
        write_str(lines, obj_to_custom_format(self.birthDrag, "p-drag"))
        write_str(lines, obj_to_custom_format(self.birthAcceleration, "p-accel"))
        write_str(lines, obj_to_custom_format(self.worldAcceleration, "p-worldaccel"))
        write_str(lines, value_to_custom_format(self.emissionMeshScale, "e-shape-scale"))
        write_str(lines, get_path_baseName(self.emissionMeshName, "e-shape-name"))
        write_str(lines, obj_to_custom_format(self.SpawnShape))
        write_str(lines, obj_to_custom_format(self.shape))
        write_str(lines, obj_to_custom_format(self.EmitterPosition, "p-postoffset"))
        write_str(lines, obj_to_custom_format(self.primitive))
        write_str(lines, get_path_baseName(self.particleColorTexture, "p-rgba"))
        write_str(lines, value_to_custom_format(self.blendMode, "rendermode"))
        write_str(lines, obj_to_custom_format(self.birthColor, "e-rgba"))
        write_str(lines, obj_to_custom_format(self.color, "p-xrgba"))
        write_str(lines, value_to_custom_format(self._pass, "pass"))
        write_str(lines, obj_to_custom_format(self.distortionDefinition))
        write_str(lines, colorLookUpType_data(self.colorLookUpTypeX, self.colorLookUpTypeY))
        write_str(lines, obj_to_custom_format(self.colorLookUpScales, "p-colorscale"))
        write_str(lines, value_to_custom_format(self.alphaRef, "e-alpharef"))
        write_str(lines, obj_to_custom_format(self.censorModulateValue, "e-censor-modulate"))
        write_str(lines, obj_to_custom_format(self.colorLookUpOffsets, "p-coloroffset"))
        write_str(lines, value_to_custom_format(self.sliceTechniqueRange, "p-alphaslicerange"))
        write_str(lines, bool_to_custom_format(self.disableBackfaceCull, "p-backfaceon"))
        write_str(lines, obj_to_custom_format(self.softParticleParams))
        write_str(lines, value_to_custom_format(self.miscRenderFlags, "flag-disable-z"))
        write_str(lines, bool_to_custom_format(self.uvScrollAlphaMult, "p-uvscroll-alpha-mult"))
        write_str(lines, bool_to_custom_format(self.isFollowingTerrain, "p-followterrain"))
        write_str(lines, value_to_custom_format(self.meshRenderFlags, "flag-force-animated-mesh-z-write"))
        write_str(lines, bool_to_custom_format(self.isDirectionOriented, "p-vecalign"))
        write_str(lines, bool_to_custom_format(self.isRandomStartFrame, "p-randomstartframe"))
        write_str(lines, bool_to_custom_format(self.isLocalOrientation, "e-local-orient"))
        write_str(lines, bool_to_custom_format(self.isRotationEnabled, "p-xquadrot-on"))
        write_str(lines, bool_to_custom_format(self.useEmissionMeshNormalForBirth, "e-shape-use-normal-for-birth"))
        write_str(lines, bool_to_custom_format(self.doesCastShadow, "p-shadow"))
        write_str(lines, obj_to_custom_format(self.reflectionDefinition))
        write_str(lines, obj_to_custom_format(self.birthRotation0, "p-quadrot"))
        write_str(lines, obj_to_custom_format(self.rotation0, "p-xquadrot"))
        write_str(lines, obj_to_custom_format(self.birthRotationalVelocity0, "p-rotvel"))
        write_str(lines, bool_to_custom_format(self.particleIsLocalOrientation, "p-local-orient"))
        write_str(lines, bool_to_custom_format(self.isUniformScale, "uniformscale"))
        write_str(lines, bool_to_custom_format(self.uvScrollClamp, "p-uvscroll-rgb-clamp"))
        write_str(lines, material_data(self.materialOverrideDefinitions))
        write_str(lines, value_to_custom_format(self.directionVelocityScale, "p-vec-velocity-scale"))
        write_str(lines, value_to_custom_format(self.directionVelocityMinScale, "p-vec-velocity-minscale"))
        write_str(lines, obj_to_custom_format(self.birthScale0, "p-scale"))
        write_str(lines, obj_to_custom_format(self.scale0, "p-xscale"))
        write_str(lines, get_path_baseName(self.texture, get_texture_type(has_mesh(self.primitive))))
        write_str(lines, get_path_baseName(self.meshTextureName, "p-meshtex"))
        write_str(lines, value_to_custom_format(self.frameRate, "p-frameRate"))
        write_str(lines, value_to_custom_format(self.startFrame, "p-startframe"))
        write_str(lines, obj_to_custom_format(self.birthFrameRate, "e-framerate"))
        write_str(lines, value_to_custom_format(self.numFrames, "p-numframes"))
        write_str(lines, UVScrollRate(self.birthUvScrollRate, self.particleUVScrollRate, "p-uvscroll-rgb"))
        write_str(lines, obj_to_custom_format(self.birthUVOffset, "e-uvoffset"))
        write_str(lines, obj_to_custom_format(self.texDiv, "p-texdiv"))
        write_str(lines, obj_to_custom_format(self.texDivMult, "p-texdiv-mult"))
        write_str(lines, value_to_custom_format(self.orientation, "p-simpleorient"))
        write_str(lines, texture_mode_fix(self.texAddressModeBase, "p-texture-mode"))
        write_str(lines, texture_mult_data(self.textureMult, has_mesh(self.primitive)))
        write_str(lines, UVScrollRate(self.birthUvScrollRateMult, self.particleUVScrollRateMult, "p-uvscroll-rgb-mult"))
        write_str(lines, obj_to_custom_format(self.birthUVOffsetMult, "e-uvoffset-mult"))
        write_str(lines, texture_mode_fix(self.texAddressModeMult, "p-texture-mult-mode"))
        write_str(lines, fix_uvMode(self.uvMode))
        write_str(lines, obj_to_custom_format(self.scaleBias, "p-scalebias"))
        write_str(lines, add_fix_value(self.primitive, self.bindWeight, self.particleIsLocalOrientation))
        write_str(lines, obj_to_custom_format(self.fieldCollectionDefinition))
        write_blank_Line(lines)
        return "\n".join(lines)

@dataclass
class VfxSystemDefinitionData:
    complexEmitterDefinitionData: List[Any] = field(default_factory=list)
    # 暂未实现写入SimpleEmitterDefinitionData
    SimpleEmitterDefinitionData: List[Any] = field(default_factory=list)
    buildUpTime: f32 = None
    visibilityRadius: f32 = None
    particleName: str = "ParticleName"
    particlePath: str = "ParticlePath"
    soundOnCreateDefault: str = None
    soundPersistentDefault: str = None
    overrideScaleCap: Optional[f32] = None
    flags: u16 = None
    mIsPoseAfterimage: bool = None
    transform: mtx44 = None
    scaleDynamicallyWithAttachedBone: bool = None
    # not fpund bin type
    SoundEndsOnEmitterEnd: flag = None
    SoundsPlayWhileOffScreen: flag = None
    SimulateWhileOffScreen: flag = None
    SimulateOncePerFrame: flag = None
    SimulateEveryFrame: flag = None
    PersistThruRevive: flag = None
    PersistThruDeath: flag = None
    KeepOrientationAfterSpellCast: flag = None

    def to_custom_format(self, source):
        lines = [f"ParticleName={self.particleName}"]
        if self.complexEmitterDefinitionData:
            for emitter in self.complexEmitterDefinitionData:
                lines.append(emitter.to_custom_format(source))
        system_str = self.out_system()
        lines.append(f'{system_str}')
        return "\n".join(lines)

    def out_group(self) -> str:
        lines = []
        return "\n".join(lines)
    
    def out_system(self) -> str:
        lines = ["[System]"]
        for i, emitter in enumerate(self.complexEmitterDefinitionData, start=1):
            # 注意索引从1开始
            lines.append(f"GroupPart{i}={emitter.emitterName.replace(' ', '_')}")
            if emitter.importance is not None:
                ImportanceValue = ["Low", "Unknown", "High", "Unknown", "Unknown"]
                lines.append(f"GroupPart{i}Importance={ImportanceValue[emitter.importance]}")
            # 验证
            # if emitter.meshRenderFlags is not None and emitter.primitive is None:
                # TypeValue = ["Simple", "complex", "Unknown", "Unknown", "Unknown"]
                # lines.append(f"GroupPart{i}Type={TypeValue[emitter.meshRenderFlags]}")

        write_str(lines, value_to_custom_format(self.buildUpTime, "build-up-time"))
        write_str(lines, value_to_custom_format(self.visibilityRadius, "group-vis"))
        write_str(lines, value_to_custom_format(self.soundOnCreateDefault, "SoundOnCreate"))
        write_str(lines, value_to_custom_format(self.soundPersistentDefault, "SoundPersistent"))
        lines.append("SimulateEveryFrame=1")
        lines.append("SimulateWhileOffScreen=1")
        write_str(lines, value_to_custom_format(self.flags, "flags"))
        write_str(lines, value_to_custom_format(self.overrideScaleCap, "group-scale-cap"))
        write_blank_Line(lines)
        return "\n".join(lines)
