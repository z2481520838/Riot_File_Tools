from .blnd_data import*
from .event_data import*
from .transition_data import*
from .mask_data import*
from ..function import*


def create_parametric_clip(class_ary, clip_name, condition_data_pairs, trackdataid = 0, u_type=0):
    """创建 ClipResource 实例并将其添加到 class_ary 中，并按值排序"""
    # 根据第二个值（value）进行排序，确保 -1 排在 0 前面
    sorted_condition_data_pairs = sorted(condition_data_pairs, key=lambda x: x[1])

    # 创建 clip_data_70_pair 数据
    clip_data_pair = []
    for data, value in sorted_condition_data_pairs:
        add_parametricpair_data(clip_data_pair, data, value)

    # 创建 ParametricClip 和 ClipResource
    parametric_clip = ParametricClip(mUpdaterType=u_type,mConditionFloatPairDataList=clip_data_pair, mTrackDataID=trackdataid)
    clip_resource = ClipResource(mUniqueID=len(class_ary), mName=clip_name, mClipData=parametric_clip)

    # 将创建的 ClipResource 添加到 class_ary 中
    class_ary.append(clip_resource)
def create_transition_data(data_list, value):
    """根据给定的 data_list 和 value 创建并返回一个填充的 transition_data_map"""
    transition_data_map = []
    add_transition_data(transition_data_map, data_list, value)
    return transition_data_map
def add_parametricpair_data(parametricpair, _id, value):
    """将 TransitionToData 实例添加到 transition_data_map 中"""
    parametricpair.append(ParametricPairData(_id, value))
    parametricpair.sort(key=lambda x: x.mValue)

def add_transition_data(transition_data_map, data_list, value):
    """将 TransitionToData 实例添加到 transition_data_map 中"""
    for i in data_list:
        transition_data_map.append(TransitionToData(i, value))
    transition_data_map.sort(key=lambda x: x.mToAnimId)

def append_atomicclip_data(a, name, endtick, trackdataid=0, flags=0, event=None,tick_duration=0.03333333507180214,mid=None,path_ary=None,animdataary=None,path=None,path_index=0,eventmap=None):
    b = AtomicClip(mEndTick=endtick,mAnimDataIndex=len(path_ary),mTrackDataID=trackdataid,mSyncGroup=0,mExtBuffer=[0, 0],mEventData=event,mTickDuration=tick_duration,mMaskDataID=mid)
    c = ClipResource(mFlags=flags,mUniqueID=len(a),mName=name,mClipData=b)
    d=["characters/aatrcx/skins/base/animations/"]
    append_animdata(animdataary, path_ary, Path_Record(Path=get_anim_path(d[path_index], path)))
    a.append(c)
    if event is not None:
        eventmap.append(event)

def append_transition_data(a, b, c):
    d = TransitionClipData(a,len(c),TransitionTo=c)
    b.append(d)
    # 按照FromAnimationID排序，避免顺序错乱
    b.sort(key=lambda x: x.FromAnimationID)
def append_track_data(a, b, c, d):
    e = Track_Resource(mBlendWeight=b,mBlendMode=c,mIndex=len(a),mName=d)
    a.append(e)
def create_event_data(a, b):
    c = []
    d = []
    for i in range(len(a)):
        c.append(EventNameHash(i, elf_hash_lower(a[i].mName)))
        d.append(EventFrame(i, a[i].mFrame))
    e = EventResource(mEventArray=a, mEventNameHash=c, mEventFrame=d, mName=b)
    return e
def append_mask_data(a, b, c):
    d = MaskResource(mFormatToken=1270564215,mName=b,mWeightList=c)
    a.append(d)
def append_sequencer_data(a, b, c):
    d = ClipResource(mUniqueID=len(c),mName=a,mClipData=SequencerClip(mPairsIDArr=b))
    c.append(d)
def append_parallel_data(a, b, c):
    d = ClipResource(mUniqueID=len(c),mName=a,mClipData=ParallelClip(mClipsIDArr=b))
    c.append(d)
def id_of_name(a, b, c):
    d = 0
    for e in a:
        if e.mName == b:
            d = a.mUniqueID
    return SelectorPairData(d, c)
# 先传入主要的数据组，计算大小和顺序，再获取位置和偏移
def create_blnd_data():
    # 创建 BlnderHeader 和 BlnderPool 实例
    path_recode_instance = Path_Record(Path="characters/aatrcx/skins/base/aatrox.aatroxbanner.skl")  # 或者可以显式传入特定值
    path_recode_instance.PathHash = path_recode_instance.to_hash()
    header_instance = BlnderHeader()  # 或者可以显式传入特定值
    track_ary=[]
    animdata_ary=[]
    anim_names=[]
    # 重要提示：transition_data对id的顺序要求很严谨，要按照id从小到大依次排列，如果大的id出现在前面，那么比该id小的都会被忽略
    transition_map = []
    event_data_map = []
    class_ary = []
    mask_ary = []

    append_track_data(track_ary, 1, 2, "TURN")
    append_track_data(track_ary, 1, 0, "BannerToggle")
    append_track_data(track_ary, 1, 0, "BuffPose")
    append_track_data(track_ary, 1, 0, "Recall")
    append_track_data(track_ary, 1, 1, "Ult")
    append_track_data(track_ary, 1, 0, "Wings")
    append_track_data(track_ary, 1, 0, "UpperBody")
    append_track_data(track_ary, 1, 0, "Default")
    append_mask_data(mask_ary,"Ult",[0] * 71 + [1] * 5 + [0] * 51)
    append_mask_data(mask_ary,"empty",[0] * 127)
    append_mask_data(mask_ary,"UpperBody",[0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0,1,0,1,1,0,0,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    append_mask_data(mask_ary,"Wings",[0] * 5 + [1] * 8 + [0] * 4 + [1] * 8+[0] * 102)
    append_mask_data(mask_ary,"BUFFBONE",[0] * 84 + [1] * 1 + [0] * 42)
    append_atomicclip_data(class_ary, "Idle1", 56, 7, 2,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Unsheath_Idle1.AatroxBanner")

    event_data_0 = []
    event_data_0.append(SubmeshVisibilityEventData(
                        mFlags=4,
                        mName='uk_e0b58fed',
                        mEndFrame=-1,
                        mShowSubmeshHash=elf_hash_lower("Shoulder")
                    ))
    event_data_0.append(ParticleEventData(
                        mFlags=2,
                        mName='uk_65309fbd',
                        mFrame=7,
                        mEndFrame=-1,
                        mEffectName='Aatrox_Base_AA_Trail_02.troy',
                        mBoneName='C_Buffbone_GLB_Layout_Loc',
                        mTargetBoneName='',
                    ))
    event_0 = create_event_data(event_data_0, "Attack2")
    append_atomicclip_data(class_ary, "Attack2", 69, 7,event=event_0,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Attack1.AatroxBanner",eventmap=event_data_map)


    event_data_1 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_e0b58fed',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Shoulder")),
                    ParticleEventData(mFlags=2,mName='uk_64309e2a',mFrame=7,mEndFrame=-1,mEffectName='Aatrox_Base_AA_Trail_03.troy',
                        mBoneName='C_Buffbone_GLB_Layout_Loc',
                        mTargetBoneName='',
                    )]
    event_1 = create_event_data(event_data_1, "Attack3")
    append_atomicclip_data(class_ary, "Attack3", 70, 7,event=event_1,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Attack3.AatroxBanner",eventmap=event_data_map)


    event_data_2 = [ParticleEventData(mFlags=2,mName='Vfx',mFrame=7,mEndFrame=-1,mEffectName='Aatrox_Base_AA_Crit_Trail.troy',
                        mBoneName='C_Buffbone_GLB_Layout_Loc',
                        mTargetBoneName='',
                    )]
    event_2 = create_event_data(event_data_2, "Crit")
    append_atomicclip_data(class_ary, "Crit", 44, 7,event=event_2,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Crit.AatroxBanner",eventmap=event_data_map)

    event_data_3 = [ParticleEventData(mFlags=2,mName='Death_Particle',mEndFrame=-1,mEffectName='Aatrox_Base_Death_ambers.troy',
                        mBoneName='C_Buffbone_GLB_Layout_Loc',
                        mTargetBoneName='',
                    ),
                    SoundEventData(mFlags=1,mName='Audio_Sfx',mSoundName="Play_sfx_aatrox_base_death_buffactivate"),
                    SubmeshVisibilityEventData(mFlags=4,mName='uk_fb23d9a1',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner")),
                    SubmeshVisibilityEventData(mFlags=4,mName='uk_fb23d9a1',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("wings"))]
    event_3 = create_event_data(event_data_3, "death")
    append_atomicclip_data(class_ary, "death", 59, 7,event=event_3,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Death",eventmap=event_data_map)

    append_atomicclip_data(class_ary, "Channel_Wndup", 59, 7, 2,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Channel_Windup")
    append_atomicclip_data(class_ary, "Channel", 30, 7, 2,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Channel.AatroxBanner")

    event_data_4 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mFrame=217,mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings"),mHideSubmeshHash=elf_hash_lower("Shoulder")),
                    JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                    ParticleEventData(mFlags=2,mName='Vfx',mFrame=87,mEndFrame=-1,mEffectName='Aatrox_Base_Recall_Ground.troy',mBoneName='root',mTargetBoneName=''),
                    ParticleEventData(mFlags=2,mName='uk_094de3df',mFrame=90,mEndFrame=-1,mEffectName='Aatrox_Base_Recall_Beam.troy',mBoneName='Weapon_Heart',mTargetBoneName='L_Middle1'),
                    ParticleEventData(mFlags=2,mName='uk_2c0ddcf8',mFrame=95,mEndFrame=-1,mEffectName='Aatrox_Base_Recall_Weapon_glow.troy',mBoneName='Weapon_Heart',mTargetBoneName=''),
                    ParticleEventData(mFlags=2,mName='uk_2c0ddcf8',mFrame=95,mEndFrame=-1,mEffectName='Aatrox_Base_Recall_Hand_glow.troy',mBoneName='L_Middle1',mTargetBoneName=''),
                    SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mFrame=217,mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_4 = create_event_data(event_data_4, "uk_909068b6")
    append_atomicclip_data(class_ary, "uk_909068b6", 260, 7,event=event_4,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Recall.AatroxBanner",eventmap=event_data_map)
    append_atomicclip_data(class_ary, "unsheath", 26, 7, 8,tick_duration=0.0285714287,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_UnSheath.AatroxBanner")

    sequencer_clip_0 = ClipResource(mFlags=8,mUniqueID=len(class_ary),mName='Idle_In',mClipData=SequencerClip(mPairsIDArr=[len(class_ary)-1, len(class_ary)+1]))
    class_ary.append(sequencer_clip_0)

    selector_clip_0 = SelectorClip(mSelectorPairDataArr=[SelectorPairData(0, 80)])
    class_ary.append(ClipResource(mFlags=2,mUniqueID=len(class_ary),mName='uk_914db254',mClipData=selector_clip_0))

    event_data_5 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_5 = create_event_data(event_data_5, "Run_Base")
    append_atomicclip_data(class_ary, "Run_Base", 30, 7,6,event=event_5,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Unsheath_run01.AatroxBanner",eventmap=event_data_map)

    event_data_6 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_6 = create_event_data(event_data_6, "Run_Haste")
    append_atomicclip_data(class_ary, "Run_Haste", 28, 7,6,event=event_6,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_sheath_run_haste.AatroxBanner",eventmap=event_data_map)
    append_atomicclip_data(class_ary, "Stunned", 40, 7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Stunned")
    append_atomicclip_data(class_ary, "Spell3", 10, 7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Spell3.AatroxBanner")

    event_data_7 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings")),
                    JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                    SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_7 = create_event_data(event_data_7, "Spell4")
    append_atomicclip_data(class_ary, "Spell4", 49, 7,event=event_7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_into.AatroxUpdate",eventmap=event_data_map)

    event_data_8 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_8 = create_event_data(event_data_8, "uk_81cc0ed")
    append_atomicclip_data(class_ary,"uk_81cc0ed",1,4,6,mid=0,event=event_8,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT",eventmap=event_data_map)

    append_parallel_data("uk_07a8c133", [len(class_ary)-2, len(class_ary)-1], class_ary)

    event_data_9 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_9 = create_event_data(event_data_9, "uk_9f7ba4d4")
    append_atomicclip_data(class_ary,"uk_9f7ba4d4",14,4,mid=0,event=event_9,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_spell4.AatroxUpdate",eventmap=event_data_map)
    append_atomicclip_data(class_ary, "Joke", 149, 7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Joke.AatroxBanner")
    append_atomicclip_data(class_ary, "Laugh", 144, 7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Laugh.AatroxBanner")

    event_data_10 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings"),mHideSubmeshHash=elf_hash_lower("Shoulder")),
                     ParticleEventData(mFlags=2,mName='uk_4d1cc496',mEndFrame=-1,mEffectName='Aatrox_Base_R_Attack_02.troy',mBoneName='C_Buffbone_GLB_Layout_Loc',mTargetBoneName='')]
    event_10 = create_event_data(event_data_10, "Attack2_Ult")
    append_atomicclip_data(class_ary, "Attack2_Ult", 72, 7,tick_duration=0.0303030312,event=event_10,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_Attack2.AatroxUpdate",eventmap=event_data_map)

    event_data_11 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_1ec1acee',mEndFrame=5,mHideSubmeshHash=elf_hash_lower("BODY")),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_1ec1acee',mEndFrame=5,mHideSubmeshHash=elf_hash_lower("Sword")),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_1ec1acee',mEndFrame=5,mHideSubmeshHash=elf_hash_lower("Shoulder")),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_1ec1acee',mEndFrame=5,mHideSubmeshHash=elf_hash_lower("Wings")),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=29,mHideSubmeshHash=elf_hash_lower("banner")),]
    event_11 = create_event_data(event_data_11, "Recall_Winddown")
    append_atomicclip_data(class_ary, "Recall_Winddown", 92, 7,event=event_11,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Recall_Winddown.AatroxBanner",eventmap=event_data_map)

    event_data_12 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings")),
                     JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_12 = create_event_data(event_data_12, "uk_6bddf209")
    append_atomicclip_data(class_ary, "uk_6bddf209", 41, 7,2,event=event_12,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_Idle.AatroxUpdate",eventmap=event_data_map)

    event_data_13 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_13 = create_event_data(event_data_13, "Dance_Loop")
    append_atomicclip_data(class_ary, "Dance_Loop", 140, 7,6,event=event_13,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Dance_Loop.AatroxBanner",eventmap=event_data_map)

    event_data_14 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                     ParticleEventData(mFlags=2,mName='Vfx',mFrame=24,mEndFrame=-1,mEffectName='Aatrox_Base_Dance_Ground.troy',mBoneName='BUFFBONE_GLB_GROUND_LOC',mTargetBoneName='')]
    event_14 = create_event_data(event_data_14, "Dance_Windup")
    append_atomicclip_data(class_ary, "Dance_Windup", 99, 7,8,event=event_14,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Dance_Windup.AatroxBanner",eventmap=event_data_map)
    append_sequencer_data("Dance", [len(class_ary)-1, len(class_ary)-2], class_ary)

    event_data_15 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings")),
                     ParticleEventData(mFlags=2,mName='uk_4d1cc496',mFrame=13,mEndFrame=-1,mEffectName='Aatrox_Base_R_Attack_01.troy',mBoneName='C_Buffbone_GLB_Layout_Loc',mTargetBoneName='')]
    event_15 = create_event_data(event_data_15, "Attack1_Ult")
    append_atomicclip_data(class_ary, "Attack1_Ult", 72, 7,event=event_15,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_Attack1.AatroxUpdate",eventmap=event_data_map)


    event_data_16 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings")),
                        JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_16 = create_event_data(event_data_16, "uk_78000693")
    append_atomicclip_data(class_ary, "uk_78000693", 49, 7,8,event=event_16,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_into.AatroxUpdate",eventmap=event_data_map)
    append_sequencer_data("Idle_Ult", [len(class_ary)-6], class_ary)

    event_data_17 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings")),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_17 = create_event_data(event_data_17, "Spell3_ULT")
    append_atomicclip_data(class_ary, "Spell3_ULT", 25, 7,tick_duration=0.0250000004,event=event_17,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Spell3_ULT.AatroxUpdate",eventmap=event_data_map)
    append_sequencer_data("Attack", [len(class_ary)+1, 1, 2], class_ary)

    event_data_18 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_e0b58fed',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Shoulder")),
                     ParticleEventData(mFlags=2,mName='uk_77c2b3bd',mFrame=7,mEndFrame=-1,mEffectName='Aatrox_Base_AA_Trail_01.troy',
                        mBoneName='C_Buffbone_GLB_Layout_Loc',
                        mTargetBoneName='',
                    )]
    event_18 = create_event_data(event_data_18, "Attack1")
    append_atomicclip_data(class_ary, "Attack1", 69, 7,event=event_18,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Sheath_to_Attack.AatroxBanner",eventmap=event_data_map)
    event_data_19 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_19 = create_event_data(event_data_19, "uk_40ce9a19")
    append_atomicclip_data(class_ary, "uk_40ce9a19", 26, 7,event=event_19,tick_duration=0.0250000004,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_UnSheath.AatroxBanner",eventmap=event_data_map)
    append_atomicclip_data(class_ary, "Unsheath_run01", 30, 7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Unsheath_Run01.AatroxBanner")
    append_atomicclip_data(class_ary, "Unsheath_idle1", 56, 7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Unsheath_idle1.AatroxBanner")

    event_data_20 = [JointSnapEventData(mFlags=5,mName='uk_5c70164b',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=70),
                     ParticleEventData(mFlags=2,mName='Trail_01',mFrame=11,mEndFrame=-1,mEffectName='Aatrox_Base_Q_Trail_01.troy',mBoneName='C_Buffbone_GLB_Layout_Loc',mTargetBoneName='')]
    event_20 = create_event_data(event_data_20, "uk_03ea19ca")
    append_atomicclip_data(class_ary, "uk_03ea19ca", 24, 7,event=event_20,tick_duration=0.0285714287,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ground_Q1.AatroxBanner",eventmap=event_data_map)

    event_data_21 = [ParticleEventData(mFlags=2,mName='Trail_02',mFrame=14,mEndFrame=-1,mEffectName='Aatrox_Base_Q_Trail_02.troy',mBoneName='C_Buffbone_GLB_Layout_Loc',mTargetBoneName='')]
    event_21 = create_event_data(event_data_21, "uk_bc1ab241")
    append_atomicclip_data(class_ary, "uk_bc1ab241", 28, 7,event=event_21,tick_duration=0.0285714287,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ground_Q2.AatroxBanner",eventmap=event_data_map)

    event_data_22 = [ParticleEventData(mFlags=2,mName='Trail_03',mFrame=6,mEndFrame=-1,mEffectName='Aatrox_Base_Q_Trail_03.troy',mBoneName='C_Buffbone_GLB_Layout_Loc',mTargetBoneName=''),
                     JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-20,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_22 = create_event_data(event_data_22, "uk_4c364faa")
    append_atomicclip_data(class_ary, "uk_4c364faa", 23, 7,event=event_22,tick_duration=0.03125,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ground_Q3.AatroxBanner",eventmap=event_data_map)

    event_data_23 = [ParticleEventData(mFlags=2,mName='Passive_Attack',mFrame=8,mEndFrame=-1,mEffectName='Aatrox_Base_P_Attack_trail.troy',mBoneName='C_Buffbone_GLB_Layout_Loc',mTargetBoneName=''),
                     JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_23 = create_event_data(event_data_23, "Passive_Attack")
    append_atomicclip_data(class_ary, "Passive_Attack", 30, 7,event=event_23,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Passive_Attack.AatroxBanner",eventmap=event_data_map)

    event_data_24 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_24 = create_event_data(event_data_24, "Passive_Idle")
    append_atomicclip_data(class_ary, "Passive_Idle", 68, 7,event=event_24,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Passive_Idle.AatroxBanner",eventmap=event_data_map)

    event_data_25 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_25 = create_event_data(event_data_25, "Passive_Run")
    append_atomicclip_data(class_ary, "Passive_Run", 32, 7,tick_duration=0.0285714287,event=event_25,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Passive_Run.AatroxBanner",eventmap=event_data_map)

    append_atomicclip_data(class_ary,"uk_ce422692",20,6,mid=2,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ground_Q1_to_UnsheathRun.AatroxUpdate")

    event_data_26 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_26 = create_event_data(event_data_26, "uk_9cd7f5fb")
    append_atomicclip_data(class_ary, "uk_9cd7f5fb", 29, 7,event=event_26,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ReSheath_Fullbody.AatroxBanner",eventmap=event_data_map)

    event_data_27 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_27 = create_event_data(event_data_27, "uk_15d251f3")
    append_atomicclip_data(class_ary, "uk_15d251f3", 128, 7,tick_duration=0.03125,event=event_27,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_sheath_run01.AatroxBanner",eventmap=event_data_map)

    append_atomicclip_data(class_ary,"uk_86446416",210,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Idle1.AatroxBanner")

    event_data_28 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_fc64a8bf',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings"),mHideSubmeshHash=elf_hash_lower("Shoulder")),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_fc64a8bf',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_28 = create_event_data(event_data_28, "uk_a373d323")
    append_atomicclip_data(class_ary, "uk_a373d323", 20, 5,6,mid=1,event=event_28,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_wings_null.AatroxUpdate",eventmap=event_data_map)

    append_sequencer_data("Spell1_A", [len(class_ary)-11], class_ary)
    append_sequencer_data("Spell1_B", [len(class_ary)-11], class_ary)
    append_atomicclip_data(class_ary,"Idle_in_sheath",34,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Idle_in_sheath.AatroxBanner")

    event_data_29 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_29 = create_event_data(event_data_29, "uk_f07fd7cc")
    append_atomicclip_data(class_ary, "uk_f07fd7cc", 104, 4,mid=1,event=event_29,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Death_Run.AatroxUpdate",eventmap=event_data_map)
    append_atomicclip_data(class_ary,"uk_b46112a0",26,6,mid=2,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_unsheath.AatroxBanner")
    append_parallel_data("uk_310b016b", [len(class_ary)-19,len(class_ary)-1], class_ary)
    append_atomicclip_data(class_ary,"Q1_INTO_Idle",51,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ground_Q1_INTO_Idle.AatroxBanner")
    append_atomicclip_data(class_ary,"Q1_INTO_Run",44,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Q1_INTO_Run.AatroxBanner")
    append_atomicclip_data(class_ary,"uk_cfd415c3",39,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ground_Q1_INTO_PassiveIdle.AatroxBanner")

    event_data_30 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_30 = create_event_data(event_data_30, "uk_e03d739a")
    append_atomicclip_data(class_ary, "uk_e03d739a", 31, 7,event=event_30,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Passive_Q1_INTO_Run1.AatroxBanner",eventmap=event_data_map)

    event_data_31 = [JointSnapEventData(mFlags=5,mName='uk_c6d3acea',mEndFrame=3,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_31 = create_event_data(event_data_31, "uk_920e7f4a")
    append_atomicclip_data(class_ary, "uk_920e7f4a", 28, 7,event=event_31,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Passive_INTO_Idle1.AatroxBanner",eventmap=event_data_map)

    append_atomicclip_data(class_ary,"Q2_INTO_Run",27,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Q2_INTO_Run.AatroxBanner")

    event_data_32 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_32 = create_event_data(event_data_32, "uk_8c6718c1")
    append_atomicclip_data(class_ary, "uk_8c6718c1", 16, 7,event=event_32,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Passive_Q2_INTO_Run.AatroxBanner",eventmap=event_data_map)

    append_atomicclip_data(class_ary,"uk_2377aa8e",36,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ground_Q2_To_PassiveIdle.AatroxBanner")
    append_atomicclip_data(class_ary,"Q2_INTO_Idle",37,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ground_Q2_To_Idle.AatroxBanner")
    append_atomicclip_data(class_ary,"uk_15ebcb35",87,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Passive_INTO_Shlth.AatroxBanner")

    event_data_33 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_33 = create_event_data(event_data_33, "uk_8c94bce6")
    append_atomicclip_data(class_ary, "uk_8c94bce6", 20, 5,6,mid=3,event=event_33,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_wings_null.AatroxUpdate",eventmap=event_data_map)

    event_data_34 = [JointSnapEventData(mFlags=5,mName='WeaponSnap',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_34 = create_event_data(event_data_34, "Attack_INTO_Run")
    append_atomicclip_data(class_ary, "Attack_INTO_Run", 21, 7,event=event_34,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Attack_INTO_Run.AatroxBanner",eventmap=event_data_map)
    append_atomicclip_data(class_ary,"uk_3dc15dd3",65,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ground_Q3_INTO_Idle1.AatroxBanner")
    append_atomicclip_data(class_ary,"Q3_INTO_Passive_Idle",41,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ground_Q3_INTO_Passive_Idle.AatroxBanner")
    append_atomicclip_data(class_ary,"Q3_INTO_PassiveRun",27,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ground_Q3_INTO_PassiveRun.AatroxBanner")
    append_atomicclip_data(class_ary,"Q3_INTO_Run",38,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ground_Q3_INTO_Run.AatroxBanner")
    append_atomicclip_data(class_ary,"IDLE_INTO_PASSIVE_RUN",18,7,path_ary=anim_names,animdataary=animdata_ary,path="IDLE_INTO_PASSIVE_RUN.AatroxBanner")

    event_data_35 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings"),mHideSubmeshHash=elf_hash_lower("banner")),
                     JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_35 = create_event_data(event_data_35, "Run_Ult")
    append_atomicclip_data(class_ary, "Run_Ult", 82, 7,event=event_35,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_Run.AatroxUpdate",eventmap=event_data_map)
    append_atomicclip_data(class_ary,"Spell3_to_walk",26,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Spell3_to_walk.AatroxBanner")
    append_atomicclip_data(class_ary,"Spell3_Dash_to_walk",26,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Spell3_Dash_to_walk.AatroxUpdate")
    append_sequencer_data("Spell_Dash", [len(class_ary)+1], class_ary)
    append_atomicclip_data(class_ary,"Spell3_Dash",16,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Spell3_Dash.AatroxBanner")
    append_sequencer_data("Dash_Running", [len(class_ary)+1], class_ary)
    append_atomicclip_data(class_ary,"Spell_Dash_Running",12,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Spell_Dash_Running.AatroxBanner")
    append_sequencer_data("Dash_Passive", [len(class_ary)+1], class_ary)

    event_data_36 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_36 = create_event_data(event_data_36, "Spell3_Dash_Passive")
    append_atomicclip_data(class_ary, "Spell3_Dash_Passive", 12, 7,event=event_36,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Spell3_Dash_Passive.AatroxBanner",eventmap=event_data_map)

    event_data_37 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=9,mShowSubmeshHash=elf_hash_lower("Wings")),
                     ParticleEventData(mFlags=2,mName='uk_b4d56fa9',mFrame=0.600000024,mEndFrame=-1,mEffectName='Aatrox_Base_R_Revive_end.troy',mBoneName='C_Buffbone_GLB_Layout_Loc',mTargetBoneName=''),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner")),]
    event_37 = create_event_data(event_data_37, "Death_Finisher4")
    append_atomicclip_data(class_ary, "Death_Finisher4", 20, 7,1,event=event_37,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Death_Finisher4.AatroxUpdate",eventmap=event_data_map)

    append_atomicclip_data(class_ary,"Death_INTO_Idle",50,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Death_INTO_Idle.AatroxBanner")
    append_atomicclip_data(class_ary,"Death_INTO_Run",42,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Death_Death_INTO_Run.AatroxBanner")

    event_data_38 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner")),]
    event_38 = create_event_data(event_data_38, "uk_17991a43")
    append_atomicclip_data(class_ary, "uk_17991a43", 104, 7,event=event_38,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Death_Idle.AatroxUpdate",eventmap=event_data_map)

    event_data_39 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner")),]
    event_39 = create_event_data(event_data_39, "Death_Run")
    append_atomicclip_data(class_ary, "Death_Run", 104, 7,event=event_39,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Death_Run.AatroxUpdate",eventmap=event_data_map)
    append_sequencer_data("ULT_Dash", [len(class_ary)+1,len(class_ary)+2], class_ary)

    event_data_40 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings"))]
    event_40 = create_event_data(event_data_40, "ULT_Spell_Dash")
    append_atomicclip_data(class_ary, "ULT_Spell_Dash", 14, 7,tick_duration=0.0399999991,event=event_40,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_Spell_Dash.AatroxUpdate",eventmap=event_data_map)

    event_data_41 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings"))]
    event_41 = create_event_data(event_data_41, "ULT_Spell_Dash_to_run")
    append_atomicclip_data(class_ary, "ULT_Spell_Dash_to_run", 39, 7,event=event_41,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_Spell_Dash_to_run.AatroxUpdate",eventmap=event_data_map)
    append_atomicclip_data(class_ary,"Spell3_Unsheath",9,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Spell3_Unsheath.AatroxBanner")
    append_atomicclip_data(class_ary,"Spell3_Unsheath_to_Idle",20,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Spell3_Unsheath_to_Idle.AatroxBanner")
    append_atomicclip_data(class_ary,"Spell3_Unsheath_to_Run",21,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Spell3_Unsheath_to_Run.AatroxBanner")
    append_sequencer_data("Spell3_Unsheath_Idle", [len(class_ary)-3,len(class_ary)-2], class_ary)
    append_atomicclip_data(class_ary,"Spell3_Passive",9,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Spell3_Passive.AatroxBanner")
    append_atomicclip_data(class_ary,"Spell3_Passive_to_Run",34,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Spell3_Passive_to_Run.AatroxBanner")

    event_data_42 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings")),
                     JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                     ParticleEventData(mFlags=2,mName='Trail_01',mFrame=12,mEndFrame=-1,mEffectName='Aatrox_Base_Q_Trail_01.troy',mBoneName='C_Buffbone_GLB_Layout_Loc',mTargetBoneName='')]
    event_42 = create_event_data(event_data_42, "uk_c24fed8f")
    append_atomicclip_data(class_ary, "uk_c24fed8f", 38, 7,event=event_42,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_Q1.AatroxUpdate",eventmap=event_data_map)
    append_atomicclip_data(class_ary,"Death_INTO_PassiveRun",41,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Death_INTO_PassiveRun.AatroxBanner")

    event_data_43 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings")),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_43 = create_event_data(event_data_43, "uk_1be3b11b")
    append_atomicclip_data(class_ary, "uk_1be3b11b", 12, 7,tick_duration=0.0285714287,event=event_43,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Death_Death_INTO_Run1.AatroxUpdate",eventmap=event_data_map)

    event_data_44 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings")),
                     ParticleEventData(mFlags=2,mName='Trail_02',mFrame=14,mEndFrame=-1,mEffectName='Aatrox_Base_Q_Trail_02.troy',mBoneName='C_Buffbone_GLB_Layout_Loc',mTargetBoneName='')]
    event_44 = create_event_data(event_data_44, "uk_676cbf56")
    append_atomicclip_data(class_ary, "uk_676cbf56", 43, 7,event=event_44,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_Q2.AatroxUpdate",eventmap=event_data_map)

    event_data_45 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings")),
                     JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                     ParticleEventData(mFlags=2,mName='Trail_03',mFrame=7,mEndFrame=-1,mEffectName='Aatrox_Base_Q_Trail_03.troy',mBoneName='C_Buffbone_GLB_Layout_Loc',mTargetBoneName='')]
    event_45 = create_event_data(event_data_45, "uk_9b190e91")
    append_atomicclip_data(class_ary, "uk_9b190e91", 43, 7,event=event_45,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_Q3.AatroxUpdate",eventmap=event_data_map)

    c_id = len(class_ary)
    condition_data_pairs = [(c_id - 16, 30), (c_id - 15, 100)]
    create_parametric_clip(class_ary, 'uk_acf3975f', condition_data_pairs, 7, 2)

    append_atomicclip_data(class_ary,"Death_INTO_PassiveIdle",38,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Death_INTO_PassiveIdle.AatroxBanner")
    append_atomicclip_data(class_ary,"Death_INTO_Idle",50,7,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Death_INTO_Idle.AatroxBanner")

    event_data_46 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_46 = create_event_data(event_data_46, "uk_f3be56ef")
    append_atomicclip_data(class_ary, "uk_f3be56ef", 260,3,event=event_46,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Recall.AatroxBanner",eventmap=event_data_map)
    append_parallel_data("Recall", [len(class_ary)-1, 7], class_ary)
    append_parallel_data("Death_Idle", [len(class_ary)-5, len(class_ary)+1], class_ary)

    event_data_47 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_fc64a8bf',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings"),mHideSubmeshHash=elf_hash_lower("Shoulder")),
                     JointSnapEventData(mFlags=5,mName='WeaponSnap',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_47 = create_event_data(event_data_47, "uk_ece40c1c")
    append_atomicclip_data(class_ary, "uk_ece40c1c", 104, 5,mid=1,event=event_47,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Death_Run.AatroxUpdate",eventmap=event_data_map)

    event_data_48 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                     ParticleEventData(mFlags=2,mName='uk_6837297e',mFrame=24,mEndFrame=-1,mEffectName='Aatrox_Base_Passive_Sheathe_Sword.troy',mBoneName='C_Buffbone_GLB_Layout_Loc',mTargetBoneName='')]
    event_48 = create_event_data(event_data_48, "ReSheath_Fullbody")
    append_atomicclip_data(class_ary, "ReSheath_Fullbody", 29, 7,event=event_48,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ReSheath_Fullbody.AatroxBanner",eventmap=event_data_map)

    event_data_49 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_fc64a8bf',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings"),mHideSubmeshHash=elf_hash_lower("Shoulder")),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_49 = create_event_data(event_data_49, "ULT_Idlein")
    append_atomicclip_data(class_ary, "ULT_Idlein", 62, 7,event=event_49,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_Idlein.AatroxUpdate",eventmap=event_data_map)

    event_data_50 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_50 = create_event_data(event_data_50, "Passive_Attack_out")
    append_atomicclip_data(class_ary, "Passive_Attack_out", 25, 7,tick_duration=0.0294117648,event=event_50,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Passive_Attack_out.AatroxBanner",eventmap=event_data_map)

    event_data_51 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_51 = create_event_data(event_data_51, "TowerAttack")
    append_atomicclip_data(class_ary, "TowerAttack", 54, 7,event=event_51,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_TowerAttack.AatroxUpdate",eventmap=event_data_map)
    append_sequencer_data("taunt", [len(class_ary)+1,len(class_ary)+2], class_ary)

    event_data_52 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                     SubmeshVisibilityEventData(mFlags=4,mName='Wings',mFrame=159,mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings"),mHideSubmeshHash=elf_hash_lower("banner")),
                     SubmeshVisibilityEventData(mFlags=4,mName='Wings',mFrame=159,mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("Shoulder")),
                     ParticleEventData(mFlags=2,mName='uk_fca8c63b',mFrame=37,mEndFrame=-1,mEffectName='Aatrox_Base_Taunt_Ground.troy',mBoneName='BUFFBONE_GLB_GROUND_LOC',mTargetBoneName='')]
    event_52 = create_event_data(event_data_52, "Taunt_Start")
    append_atomicclip_data(class_ary, "Taunt_Start", 185, 7,event=event_52,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Taunt.AatroxBanner",eventmap=event_data_map)

    event_data_53 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                     SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings"),mHideSubmeshHash=elf_hash_lower("banner")),
                     SubmeshVisibilityEventData(mFlags=4,mName='Wings',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("Shoulder"))]
    event_53 = create_event_data(event_data_53, "Taunt_loop")
    append_atomicclip_data(class_ary, "Taunt_loop", 50, 7,2,event=event_53,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Taunt_loop.AatroxBanner",eventmap=event_data_map)

    event_data_54 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78)]
    event_54 = create_event_data(event_data_54, "Unsheath_to_Passive")
    append_atomicclip_data(class_ary, "Unsheath_to_Passive", 25, 7,event=event_54,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Unsheath_to_Passive.AatroxBanner",eventmap=event_data_map)

    event_data_55 = [JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_fc64a8bf',mEndFrame=11,mShowSubmeshHash=elf_hash_lower("Wings"),mHideSubmeshHash=elf_hash_lower("Shoulder")),
                     SubmeshVisibilityEventData(mFlags=4,mName='Hide_Banner',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_55 = create_event_data(event_data_55, "ULT_out")
    append_atomicclip_data(class_ary, "ULT_out", 22, 7,tick_duration=0.03125,event=event_55,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_out.AatroxUpdate",eventmap=event_data_map)

    event_data_56 = [SubmeshVisibilityEventData(mFlags=4,mName='Wings',mFrame=11,mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings"),mHideSubmeshHash=elf_hash_lower("Shoulder")),
                     JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_fc64a8bf',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_56 = create_event_data(event_data_56, "ULT_TowerAttack")
    append_atomicclip_data(class_ary, "ULT_TowerAttack", 54, 7,event=event_56,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_TowerAttack.AatroxUpdate",eventmap=event_data_map)

    append_atomicclip_data(class_ary,"Buffbones",10,2,6,mid=4,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Buffbones.AatroxUpdate")

    event_data_57 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_ce081cb4',mFrame=11,mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings"),mHideSubmeshHash=elf_hash_lower("banner"))]
    event_57 = create_event_data(event_data_57, "ULT_out_to_passive_idle")
    append_atomicclip_data(class_ary, "ULT_out_to_passive_idle", 25, 7,event=event_57,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_out_to_passive_idle.AatroxUpdate",eventmap=event_data_map)
    append_sequencer_data("ult_taunt", [len(class_ary)+1,len(class_ary)+2], class_ary)

    event_data_58 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_ce081cb4',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings")),
                     ParticleEventData(mFlags=2,mName='uk_fca8c63b',mFrame=37,mEndFrame=-1,mEffectName='Aatrox_Base_Taunt_Ground.troy',mBoneName='BUFFBONE_GLB_GROUND_LOC',mTargetBoneName=''),
                     JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_58 = create_event_data(event_data_58, "Ult_Taunt_Start")
    append_atomicclip_data(class_ary, "Ult_Taunt_Start", 185, 7,event=event_58,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_Taunt.AatroxUpdate",eventmap=event_data_map)

    event_data_59 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_ce081cb4',mEndFrame=-1,mShowSubmeshHash=elf_hash_lower("Wings")),
                     JointSnapEventData(mFlags=5,mName='uk_6fd8bac2',mEndFrame=-1,mJointToOverrideIdx=70,mJointToSnapToIdx=78),
                     SubmeshVisibilityEventData(mFlags=4,mName='uk_ec37ee56',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_59 = create_event_data(event_data_59, "ULT_Taunt_loop")
    append_atomicclip_data(class_ary, "ULT_Taunt_loop", 50, 7,event=event_59,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_ULT_Taunt_loop.AatroxUpdate",eventmap=event_data_map)

    clip_data_0_sub=[]
    clip_data_0_sub.append(ConditionFloatPairData(11, 0,0,0))
    clip_data_0_sub.append(ConditionFloatPairData(12, 480,0,0))
    clip_data_0 = ConditionFloatClip(mUpdaterType=4,mChangeAnimationMidPlay=True,mConditionFloatPairDataList=clip_data_0_sub)
    class_ary.append(ClipResource(mUniqueID=len(class_ary),mName='Run',mClipData=clip_data_0))

    clip_data_1_sub=[]
    clip_data_1_sub.append(ConditionFloatPairData(44, 0,0,0))
    clip_data_1_sub.append(ConditionFloatPairData(12, 550,0,0))
    clip_data_1 = ConditionFloatClip(mUpdaterType=4,mChangeAnimationMidPlay=True,mConditionFloatPairDataList=clip_data_1_sub)
    class_ary.append(ClipResource(mUniqueID=len(class_ary),mName='Run_Sheath',mClipData=clip_data_1))

    event_data_60 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_1ec1acee')]
    event_60 = create_event_data(event_data_60, "Respawn")
    append_atomicclip_data(class_ary, "Respawn", 92, 7,event=event_60,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Recall_Winddown.AatroxBanner",eventmap=event_data_map)

    event_data_61 = [SubmeshVisibilityEventData(mFlags=4,mName='uk_02fe42bf',mEndFrame=-1,mHideSubmeshHash=elf_hash_lower("banner"))]
    event_61 = create_event_data(event_data_61, "BannerOff")
    append_atomicclip_data(class_ary, "BannerOff", 69, 1,mid=1,event=event_61,path_ary=anim_names,animdataary=animdata_ary,path="Aatrox_Attack1.AatroxBanner",eventmap=event_data_map)

    aligning_data_list(event_data_map)
    get_all_resource_size(track_ary)
    get_all_resource_size(class_ary)
    get_all_resource_size(mask_ary)
    get_all_resource_size(event_data_map)
    for _ in anim_names:
        _.PathHash = _.to_hash()

    pool_instance = BlnderPool(
        mSkeleton=path_recode_instance,
        mTransitionData=transition_map,
        mBlendTrackAry=track_ary,
        mClassAry=class_ary,
        mMaskDataAry=mask_ary,
        mEventDataAry=event_data_map,
        mAnimDataAry=animdata_ary,
        mAnimNames=anim_names)  # 或者可以显式传入特定值
    get_all_offset(pool_instance)
    get_track_pos(pool_instance)
    get_mask_pos(pool_instance)
    pool_instance.get_data_count()
    # 创建 BlnderData 实例，并传入 header 和 pool
    blnder_data = BlnderData(header_instance, pool_instance)
    return blnder_data