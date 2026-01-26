from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .base_value import*
from .spellData_obj import ObjectTags
from ...function.prop_text.obj_functions import*

@dataclass
class AbilityResourceSlotInfo:
    arType: u8 = None
    arBase: f32 = None
    arPerLevel: f32 = None
    arBaseStaticRegen: f32 = None
    arRegenPerLevel: f32 = None
    arIncrements: f32 = None
    arMaxSegments: i32 = None
    arHasRegenText: bool = None
    arDisplayAsPips: bool = None
    arOverrideSmallPipName: str = None
    arOverrideMediumPipName: str = None
    arOverrideLargePipName: str = None
    arOverrideSpacerName: str = None
    arAllowMaxValueToBeOverridden: bool = None

    def get_par_type(self):
        PAR_Type = ["MANA", "Energy", "None", "Shield", "Battlefury", "Dragonfury", "Rage", "Heat", "Gnarfury", "Ferocity", "BloodWell", "Wind", "Other"]
        return PAR_Type[self.arType]

    def to_custom_format(self):
        lines = []
        write_str(lines, str_base(self.get_par_type(), "PARType"))
        write_str(lines, value_to_custom_format(self.arBase, "BaseMP"))
        write_str(lines, value_to_custom_format(self.arPerLevel, "MPPerLevel"))
        write_str(lines, value_to_custom_format(self.arBaseStaticRegen, "BaseStaticMPRegen"))
        write_str(lines, value_to_custom_format(self.arRegenPerLevel, "MPRegenPerLevel"))
        write_str(lines, value_to_custom_format(self.arIncrements, "PARIncrements"))
        write_str(lines, value_to_custom_format(self.arMaxSegments, "PARMaxSegments"))
        write_str(lines, bool_to_custom_format(self.arHasRegenText, "PARHasRegenText"))
        return "\n".join(lines)

@dataclass
class AttackSlotData:
    mAttackTotalTime: Optional[f32] = None
    mAttackCastTime: Optional[f32] = None
    mAttackDelayOffsetPercent: Optional[f32] = None
    mAttackDelayCastOffsetPercentAttackSpeedRatio: Optional[f32] = None
    mAttackDelayCastOffsetPercent: Optional[f32] = None
    mAttackProbability: Optional[f32] = None
    mAttackName: Optional[str] = None

    def to_custom_format(self, get_name):
        lines = []
        write_str(lines, get_path_baseName(self.mAttackName, f"{get_name}"))
        write_str(lines, value_to_custom_format(self.mAttackTotalTime, f"{get_name}_AttackTotalTime"))
        write_str(lines, value_to_custom_format(self.mAttackCastTime, f"{get_name}_AttackCastTime"))
        write_str(lines, value_to_custom_format(self.mAttackDelayOffsetPercent, f"{get_name}_AttackDelayOffsetPercent"))
        write_str(lines, value_to_custom_format(self.mAttackDelayCastOffsetPercent, f"{get_name}_AttackDelayCastOffsetPercent"))
        write_str(lines, value_to_custom_format(self.mAttackProbability, f"{get_name}_Probability"))
        return "\n".join(lines)

@dataclass
class ToolSpellDesc:
    desc: str = None
    displayName: str = None

    def to_custom_format(self, get_name):
        lines = []
        write_str(lines, str_base(self.desc, f"{get_name}Desc"))
        write_str(lines, str_base(self.displayName, f"{get_name}DisplayName"))
        return "\n".join(lines)

@dataclass
class ToolPassiveData:
    name: str = None
    level: list[i32] = None

    def to_custom_format(self, get_name):
        lines = []
        write_str(lines, list_value(self.level, f"{get_name}Level"))
        return "\n".join(lines)

@dataclass
class ToolAiPresence:
    Unknown_ca762bfc: bool = None
    Unknown_b75b2ab8: bool = None
    Unknown_b66d0e47: bool = None
    Unknown_6175bb7b: bool = None
    easy: bool = None
    medium: bool = None
    hard: bool = None

@dataclass
class characterToolData:
    spellData: list[ToolSpellDesc] = None
    mapAIPresence: Dict[u32, Any] = None #未完成
    passLev1Desc: list[str] = None
    passiveData: list[Optional[ToolPassiveData]] = None
    searchTags: str = None
    searchTagsSecondary: str = None
    championId: i32 = None
    roles: str = None
    PARFadeColor: str = None
    magicRank: i32 = None
    LevelSpellEffectiveness: f32 = None
    difficultyRank: i32 = None
    description: str = None
    defenseRank: i32 = None
    classification: str = None
    ChasingAttackRangePercent: f32 = None
    botEnabled: bool = None
    botEnabledMM: bool = None
    attackRank: i32 = None

    def to_custom_format(self):
        lines = []
        write_str(lines, list_obj(self.spellData, "Spell"))
        write_str(lines, list_str(self.passLev1Desc, "PassLev1Desc"))
        write_str(lines, list_obj(self.passiveData, "Passive"))
        write_str(lines, str_base(self.searchTags, "SearchTags"))
        write_str(lines, str_base(self.searchTagsSecondary, "SearchTagsSecondary"))
        write_str(lines, value_to_custom_format(self.championId, "ChampionId"))
        write_str(lines, str_base(self.roles, "Roles"))
        write_str(lines, str_base(self.PARFadeColor, "PARFadeColor"))
        write_str(lines, value_to_custom_format(self.magicRank, "MagicRank"))
        write_str(lines, value_to_custom_format(self.LevelSpellEffectiveness, "LevelSpellEffectiveness"))
        write_str(lines, value_to_custom_format(self.difficultyRank, "DifficultyRank"))
        write_str(lines, str_base(self.description, "Description"))
        write_str(lines, value_to_custom_format(self.defenseRank, "DefenseRank"))
        write_str(lines, str_base(self.classification, "Classification"))
        write_str(lines, value_to_custom_format(self.ChasingAttackRangePercent, "ChasingAttackRangePercent"))
        write_str(lines, bool_to_custom_format(self.botEnabled, "BotEnabled"))
        write_str(lines, bool_to_custom_format(self.botEnabledMM, "BotEnabledMM"))
        write_str(lines, value_to_custom_format(self.attackRank, "AttackRank"))
        return "\n".join(lines)

@dataclass
class SkinFilterData:
    skinIds: list[u32] = None

@dataclass
class CharacterPassiveData:
    mParentPassiveBuff: str = None
    mComponentBuffs: list[str] = None
    mAllowOnClones: bool = None
    SkinFilter: Optional[SkinFilterData] = None

@dataclass
class ToolEducationData:
    firstItem: i32 = None
    skillOrder: i32 = None

@dataclass
class recSpellRankUpInfo:
    MapId: u32 = None
    position: str = None
    IsDefaultRecommendation: bool = None
    mDefaultPriority: list[u32] = None
    mEarlyLevelOverrides: list[u32] = None

@dataclass
class RecSpellRankUpInfolist:
    RecSpellRankUpInfos: list[Optional[recSpellRankUpInfo]] = None

@dataclass
class TakeCamp:
    Camp: u8 = None

@dataclass
class TerminatePath:
    Camp: u8 = None

@dataclass
class JunglePathRecommendation:
    OrderJunglePath: list[Optional[TakeCamp]] = None
    ChaosJunglePath: list[Optional[TakeCamp]] = None

@dataclass
class ItemRecommendationItemList:
    mItemList: list[u32] = None

@dataclass
class ItemRecommendationChoices:
    mChoices: list[u32] = None

@dataclass
class ItemRecommendationMatrixRow:
    mChoicesMap: Dict[str, Any] = None

@dataclass
class ItemRecommendationMatrix:
    mrows: list[Any] = None

@dataclass
class ItemRecommendationContext:
    mChampionId: u32 = None
    mMapID: u32 = None
    mModeNameStringId: str = None
    mPosition: str = None
    mIsDefaultPosition: bool = None
    mStartingItemMatrix: Optional[ItemRecommendationMatrix] = None
    mStartingItemBundles: Optional[ItemRecommendationItemList] = None
    UpgradeChoices: Dict[u32, Any] = None
    mPopularItems: list[str] = None
    mCompletedItemMatrix: Optional[ItemRecommendationMatrix] = None

@dataclass
class ItemRecommendationContextList:
    mAllStartingItemIds: Dict[u32, Any] = None
    mAllRecommendableItemIds: Dict[u32, Any] = None
    mContexts: list[Optional[ItemRecommendationContext]] = None

@dataclass
class ChampionRuneRecommendationsContext:
    pass

@dataclass
class catalogEntry:
    contentId: str = None
    itemID: u32 = None
    offerId: str = None

@dataclass
class StatStoneSet:
    name: str = None
    catalogEntry: Optional[catalogEntry] = None
    statStones: list[str] = None

@dataclass
class TargetTypeFilter:
    MinionsAreValid: bool = None
    ChampionsAreValid: bool = None

@dataclass
class TargetHasUnitTagFilter:
    UnitTags: Optional[ObjectTags] = None

@dataclass
class StatStoneEventToTrack:
    EventToTrack: u32 = None
    StatFilters: list[Optional[TargetTypeFilter]] = None

@dataclass
class StatStoneData:
    EventsToTrack: list[Optional[StatStoneEventToTrack]] = None
    category: str = None
    Milestones: list[u64] = None
    EpicStatStone: bool = None
    TriggeredFromScript: bool = None
    stoneName: str = None
    DataCollectionOnly: bool = None
    mNameTraKey: str = None
    catalogEntry: Optional[catalogEntry] = None
    mDescriptionTraKey: str = None

@dataclass
class recSpellRankUpInfo:
    MapId: u32 = None
    position: str = None
    IsDefaultPosition: bool = None
    IsDefaultRecommendation: bool = None
    mDefaultPriority: list[u8] = None
    mEarlyLevelOverrides: list[u8] = None

@dataclass
class SkinCharacterMetaDataProperties:
    useAudioProperties: bool = None

@dataclass
class ItemRecommendationOverrideContext:
    mMapID: u32 = None
    mModeNameStringId: str = None

@dataclass
class ItemRecommendationOverrideStartingItemSet:
    mStartingItems: list[str] = None

@dataclass
class ItemRecommendationOverrideStartingItemBundle:
    items: list[str] = None

@dataclass
class ItemRecOverrideRange:
    items: list[str] = None
    MaxCompletedItems: u32 = None

@dataclass
class ItemRecommendationCondition:
    mItem: str = None
    mGroupId: u8 = None

@dataclass
class ItemRecommendationOverride:
    mOverrideContexts: list[Any] = None
    mStartingItemSets: list[Any] = None
    StartingItemBundles: list[Any] = None
    mRecItemRanges: list[Any] = None
    mRecommendedItems: list[Any] = None

@dataclass
class ItemRecommendationOverrideSet:
    mOverrides: list[Any] = None

@dataclass
class PerkReplacement:
    mReplaceTarget: str = None
    mReplaceWith: str = None

@dataclass
class PerkReplacementList:
    mReplacements: list[Any] = None

@dataclass
class CharacterRecord:
    mCharacterName: str = None
    baseHP: f32 = None
    hpPerLevel: f32 = None
    baseStaticHPRegen: f32 = None
    hpRegenPerLevel: f32 = None
    healthBarHeight: f32 = None
    primaryAbilityResource: Optional[AbilityResourceSlotInfo] = None
    secondaryAbilityResource: Optional[AbilityResourceSlotInfo] = None
    baseDamage: f32 = None
    damagePerLevel: f32 = None
    baseArmor: f32 = None
    armorPerLevel: f32 = None
    baseSpellBlock: f32 = None
    spellBlockPerLevel: f32 = None
    baseMoveSpeed: f32 = None
    attackRange: f32 = None
    attackSpeed: f32 = None
    attackSpeedRatio: f32 = None
    attackSpeedPerLevel: f32 = None
    attackAutoInterruptPercent: f32 = None
    mAdaptiveForceToAbilityPowerWeight: f32 = None
    acquisitionRange: f32 = None
    basicAttack: Optional[AttackSlotData] = None
    extraAttacks: list[Optional[AttackSlotData]] = None
    critAttacks: list[Optional[AttackSlotData]] = None
    deathEventListeningRadius: f32 = None
    spellNames: list[str] = None
    extraSpells: list[str] = None
    mAbilities: list[str] = None
    passiveName: str = None
    passiveLuaName: str = None
    passiveDescription: str = None
    passiveSpell: str = None
    passiveToolTip: str = None
    passive1IconName: str = None
    lore1: str = None
    lore2: str = None
    tips1: str = None
    tips2: str = None
    tips3: str = None
    name: str = None
    weaponMaterials: list[str] = None
    selectionHeight: f32 = None
    selectionRadius: f32 = None
    pathfindingCollisionRadius: f32 = None
    unitTagsString: str = None
    mEducationToolData: Optional[ToolEducationData] =  None
    mAbilitySlotCC: list[i32] = None
    characterToolData: Optional[characterToolData] = None
    platformEnabled: bool = None
    recSpellRankUpInfo: list[Any] = None
    useRiotRelationships: bool = None
    flags: u32 = None
    purchaseIdentities: list[str] = None
    mPreferredPerkStyle: str = None
    mPerkReplacements: Optional[PerkReplacementList] = None
    mCharacterPassiveSpell: str = None
    mCharacterPassiveBuffs: list[Optional[CharacterPassiveData]] = None

    def to_custom_format(self, source):
        lines = [f"CharacterRecord={self.mCharacterName}"]
        write_str(lines, "[Data]")
        write_str(lines, value_to_custom_format(self.baseHP, "BaseHP"))
        write_str(lines, value_to_custom_format(self.hpPerLevel, "HPPerLevel"))
        write_str(lines, value_to_custom_format(self.baseStaticHPRegen, "BaseStaticHPRegen"))
        write_str(lines, value_to_custom_format(self.hpRegenPerLevel, "HPRegenPerLevel"))
        write_str(lines, obj_to_custom_format(self.primaryAbilityResource))
        write_str(lines, value_to_custom_format(self.baseDamage, "BaseDamage"))
        write_str(lines, value_to_custom_format(self.damagePerLevel, "DamagePerLevel"))
        write_str(lines, value_to_custom_format(self.baseArmor, "Armor"))
        write_str(lines, value_to_custom_format(self.armorPerLevel, "ArmorPerLevel"))
        write_str(lines, value_to_custom_format(self.baseSpellBlock, "SpellBlock"))
        write_str(lines, value_to_custom_format(self.spellBlockPerLevel, "SpellBlockPerLevel"))
        write_str(lines, value_to_custom_format(self.baseMoveSpeed, "MoveSpeed"))
        write_str(lines, value_to_custom_format(self.attackRange, "AttackRange"))
        write_str(lines, value_to_custom_format(self.attackSpeed, "AttackSpeed"))
        write_str(lines, value_to_custom_format(self.attackSpeedPerLevel, "AttackSpeedPerLevel"))
        write_str(lines, value_to_custom_format(self.attackAutoInterruptPercent, "AttackAutoInterruptPercent"))
        write_str(lines, value_to_custom_format(self.acquisitionRange, "AcquisitionRange"))
        write_str(lines, obj_to_custom_format(self.basicAttack, "BasicAttack")) #需要进一步完善
        write_str(lines, attackspellData(self.extraAttacks, "ExtraAttack")) #需要进一步完善
        write_str(lines, attackspellData(self.critAttacks, "CritAttack")) #需要进一步完善
        write_str(lines, value_to_custom_format(self.deathEventListeningRadius, "DeathEventListeningRadius"))
        write_str(lines, list_str(self.spellNames, "Spell"))
        write_str(lines, list_str(self.extraSpells, "ExtraSpell"))
        write_str(lines, str_base(self.passiveName, "Passive1Name"))
        write_str(lines, str_base(self.passiveLuaName, "Passive1LuaName"))
        write_str(lines, str_base(self.passiveSpell, "PassiveSpell"))
        write_str(lines, get_path_baseName(self.passive1IconName, "Passive1Icon"))
        write_str(lines, str_base(self.lore1, "Lore1"))
        write_str(lines, str_base(self.lore2, "Lore2"))
        write_str(lines, str_base(self.tips1, "Tips1"))
        write_str(lines, str_base(self.tips2, "Tips2"))
        write_str(lines, str_base(self.tips3, "Tips3"))
        write_str(lines, str_base(self.name, "Name"))
        write_str(lines, list_str(self.weaponMaterials, "WeaponMaterial"))
        write_str(lines, value_to_custom_format(self.selectionHeight, "SelectionHeight"))
        write_str(lines, value_to_custom_format(self.selectionRadius, "SelectionRadius"))
        write_str(lines, value_to_custom_format(self.pathfindingCollisionRadius, "PathfindingCollisionRadius"))
        write_str(lines, str_base(self.unitTagsString, "UnitTags"))
        write_str(lines, obj_to_custom_format(self.characterToolData))
        write_str(lines, bool_to_custom_format(self.platformEnabled, "PlatformEnabled"))
        write_str(lines, fix_purchaseIdentities(self.purchaseIdentities, "IsMelee"))
        write_blank_Line(lines)
        return "\n".join(lines)