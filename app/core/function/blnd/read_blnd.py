from ..general import*
from ...objects.blnd.data_obj.blnd_data import*
from ...objects.blnd.data_obj.transition_data import*
from ...objects.blnd.data_obj.event_data import*
from ...objects.blnd.data_obj.mask_data import*
from ...objects.blnd.data_obj.clip_data import*
import os

def read_blnd(file):
    """解析 .blnd 文件"""
    header = read_blnd_header(file)
    pool = read_blnd_pool(file)
    return BlnderData(header, pool)

def read_blend_data(a, b):
    c = []
    if a > 0:
        for i in range(a):
            d = read_uint32(b)
            e = read_uint32(b)
            f = read_uint32(b)
            g = read_float(b)
            h = BlendData(d,e,f,g)
            c.append(h)
    return c

def read_transition_data(a, b):
    c = []
    if a > 0:
        for x in range(a):
            d = read_uint32(b)
            e = read_uint32(b)
            f = read_uint32(b)
            g = TransitionClipData(d,e,f)
            c.append(g)
        for _ in c:
            for y in range(_.TransitionToCount):
                h = read_uint32(b)
                i = read_uint32(b)
                j = TransitionToData(h,i)
                _.TransitionTo.append(j)
    return c

def read_track_data(a, b):
    c = []
    if a > 0:
        for x in range(a):
            start_pos = b.tell()
            d = read_uint32(b)
            e = read_float(b)
            f = read_uint32(b)
            g = read_uint32(b)
            h = read_str(b, 32)
            i = Track_Resource(d,e,f,g,h)
            i.get_start_pos(start_pos)
            c.append(i)
    return c

def read_class_data_offset(a, b):
    if a > 0:
        for x in range(a):
            c = read_int32(b)

def read_class_data(a, b):
    c = []
    if a > 0:
        for x in range(a):
            d = read_uint32(b)
            e = read_uint32(b)
            f = read_uint32(b)
            g = read_uint32(b)
            h = read_uint32(b)
            i = read_str(b)
            j = read_clipdata(b)
            c.append(ClipResource(d,e,f,g,h,i,j))
    return c

def read_clipdata(a):
    b = read_uint32(a)
    if b == 1:
        return read_atomic(a)
    elif b == 2:
        return read_selector(a)
    elif b == 3:
        return read_sequencer(a)
    elif b == 4:
        return read_parallel(a)
    elif b == 5:
        return read_multichild(a)
    elif b == 6:
        return read_parametric(a)
    elif b == 7:
        return read_conditionbool(a)
    elif b == 8:
        return read_conditionfloat(a)
    else:
        return None

def read_atomic(a):
    b = read_uint32(a)
    c = read_uint32(a)
    d = read_float(a)
    e = read_int32(a)
    f = read_int32(a) #eventaddr
    g = read_addr(a)
    h = read_addr(a)
    i = read_int32(a)
    j = read_int32(a)
    k = read_uint32(a)
    l = [read_uint32(a), read_uint32(a)]
    m = read_event_resource(f,a)
    n = None
    if j > 0:
        n = read_str(a)
    return AtomicClip(1,b,c,d,e,f,g,h,i,j,k,l,m,n)

def read_selector(a):
    b = read_uint32(a)
    c = read_uint32(a)
    d = []
    for x in range(c):
        e = read_uint32(a)
        f = read_float(a)
        d.append(SelectorPairData(e,f))
    return SelectorClip(2,b,c,d)
def read_sequencer(a):
    b = read_uint32(a)
    c = read_uint32(a)
    d = []
    for x in range(c):
        e = read_uint32(a)
        d.append(e)
    return SequencerClip(3,b,c,d)
def read_parallel(a):
    b = read_uint32(a)
    c = read_uint32(a)
    d = []
    for x in range(c):
        e = read_uint32(a)
        d.append(e)
    return ParallelClip(4,b,c,d)
def read_multichild(a):
    pass
def read_parametric(a):
    b = read_uint32(a)
    c = read_uint32(a)
    d = read_int32(a)
    e = read_addr(a)
    f = []
    for x in range(b):
        g = read_uint32(a)
        h = read_float(a)
        f.append(ParametricPairData(g,h))
    return ParametricClip(6,b,c,d,e,f)
def read_conditionbool(a):
    b = read_uint32(a)
    c = read_uint32(a)
    d = read_uint32(a)
    e = read_uint32(a) != 0
    f = []
    for x in range(c):
        g = read_uint32(a)
        h = read_uint32(a) != 0
        f.append(ConditionBoolClipData(g,h))
    return ConditionBoolClip(7,b,c,d,e,f)
def read_conditionfloat(a):
    b = read_uint32(a)
    c = read_uint32(a)
    d = read_uint32(a)
    e = read_uint32(a) != 0
    f = []
    for x in range(c):
        h = read_uint32(a)
        i = read_float(a)
        g = read_uint32(a)
        k = read_uint32(a)
        f.append(ConditionFloatPairData(h,i,g,k))
    return ConditionFloatClip(8,b,c,d,e,f)

def read_event_resource(a, b):
    if a > 0:
        c = read_uint32(b)
        d = read_uint32(b)
        e = read_uint32(b)
        f = read_uint16(b)
        g = read_uint16(b) #eventcount
        h = read_uint32(b)
        i = read_int32(b)
        j = read_int32(b)
        k = read_int32(b)
        l = read_int32(b)
        m = read_int32(b)
        n = [read_uint32(b), read_uint32(b)]
        o = read_uint32_list(g,b)
        p = read_event_map(g,b)
        q = read_event_hash_map(g,b)
        r = read_event_frame_map(g,b)
        s = read_str(b) #name
        return EventResource(c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s)
    return None

def read_event_map(a, b):
    c = []
    for i in range(a):
        c.append(read_event_info(b))
    return c

def read_event_info(a):
    b = read_uint32(a) #size
    c = read_uint32(a) #type
    return read_event_data(b, c, a)

def read_event_data(a, b, c):
    if b == 1:
        return read_sound_event(a, b, c)
    elif b == 2:
        return read_particle_event(a, b, c)
    elif b == 3:
        return read_submeshvisibility_event(a, b, c)
    elif b == 4:
        return read_fade_event(a, b, c)
    elif b == 5:
        return read_jointSnap_event(a, b, c)
    elif b == 6:
        return read_enablelookat_event(a, b, c)
    else:
        return None

def read_sound_event(a, b, c):
    d = read_uint32(c) #flags
    e = read_float(c) #frame
    f = read_int32(c) #nameoffset
    g = read_int32(c) #soundnameoffset
    h = read_str(c) #name
    i = read_str(c) #soundname
    return SoundEventData(a,b,d,e,f,h,g,i)

def read_particle_event(a, b, c):
    d = read_uint32(c) #flags
    e = read_float(c) #frame
    f = read_int32(c) #nameoffset
    g = read_int32(c) #effectnameoffset
    h = read_int32(c) #bonenameoffset
    i = read_int32(c) #targetbonenameoffset
    j = read_float(c) #endframe
    k = read_str(c) #name
    l = read_str(c) #effectname
    m = read_str(c) #bonename
    n = read_str(c) #targetbonename
    return ParticleEventData(a,b,d,e,f,k,g,h,i,j,l,m,n)

def read_submeshvisibility_event(a, b, c):
    d = read_uint32(c) #flags
    e = read_float(c) #frame
    f = read_int32(c) #nameoffset
    g = read_float(c) #endframe
    h = read_uint32(c) #showsubmeshhash
    i = read_uint32(c) #hidesubmeshhash
    j = read_str(c) #name
    return SubmeshVisibilityEventData(a,b,d,e,f,j,g,h,i)

def read_fade_event(a, b, c):
    d = read_uint32(c) #flags
    e = read_float(c) #frame
    f = read_int32(c) #nameoffset
    g = read_float(c) #timetofade
    h = read_float(c) #targetalpha
    i = read_float(c) #endframe
    j = read_str(c) #name
    return FadeEventData(a,b,d,e,f,j,g,h,i)

def read_jointSnap_event(a, b, c):
    d = read_uint32(c) #flags
    e = read_float(c) #frame
    f = read_int32(c) #nameoffset
    g = read_float(c) #endframe
    h = read_uint16(c) #jointtooverrideidx
    i = read_uint16(c) #jointtosnaptoidx
    j = read_str(c) #name
    return JointSnapEventData(a,b,d,e,f,j,g,h,i)

def read_enablelookat_event(a, b, c):
    d = read_uint32(c) #flags
    e = read_float(c) #frame
    f = read_int32(c) #nameoffset
    g = read_float(c) #endframe
    h = read_uint32(c) #enablelookat
    i = read_uint32(c) #lockcurrentvalues
    j = read_str(c) #name
    return EnableLookAtEventData(a,b,d,e,f,j,g,h,i)

def read_event_hash_map(a, b):
    c = []
    for i in range(a):
        c.append(read_event_hash(b))
    return c

def read_event_hash(a):
    b = read_uint32(a)
    c = read_uint32(a)
    return EventNameHash(b,c)

def read_event_frame_map(a, b):
    c = []
    for i in range(a):
        c.append(read_event_frame(b))
    return c

def read_event_frame(a):
    b = read_uint32(a)
    c = read_float(a)
    return EventFrame(b,c)

def read_mask_data_offset(a, b):
    if a > 0:
        for x in range(a):
            c = read_int32(b)

def read_mask_map(a, b):
    c = []
    if a > 0:
        for i in range(a):
            c.append(read_mask_data(b))
    return c

def read_mask_data(a):
    start_pos = a.tell()
    b = read_uint32(a)
    c = read_uint32(a)
    d = read_uint32(a)
    e = read_uint16(a)
    f = read_uint16(a) #count
    g = read_uint32(a)
    h = read_int32(a)
    i = read_int32(a)
    j = read_int32(a)
    k = read_str(a,32)
    l = [read_uint32(a),read_uint32(a)]
    m = read_weight_list(f,a)
    n = MaskResource(b,c,d,e,f,g,h,i,j,k,l,m)
    n.get_start_pos(start_pos)
    return n

def read_weight_list(a,b):
    c = []
    for x in range(a):
        c.append(read_float(b))
    # JointHash
    for y in range(a):
        read_uint64(b)
    # JointNdx
    for z in range(a):
        read_uint32(b)
        read_uint32(b)
    return c

def read_event_data_addr(a, b):
    if a > 0:
        for x in range(a):
            c = read_int32(b)

def read_anim_data(a, b):
    c = []
    if a > 0:
        for i in range(a):
            d = read_int32(b)
            if d == 0:
                c.append(None)
            else:
                c.append(True)
    return c

def read_animnames_offset(a, b):
    c = []
    if a > 0:
        for i in range(a):
            d = read_uint32(b)
            e = read_int32(b)
            c.append(Path_Record(d,e))
    return c

def read_animnames(a, b):
    for c in a:
        c.Path = read_str(b)
def sync_id(a, b, c):
    for _ in a:
        if hasattr(_.mClipData, 'mTrackDataID'):  # 检查对象是否有 mTrackDataID 属性
            d = _.mClipData.mTrackDataAddr  # 获取 mTrackDataAddr

            for index, t in enumerate(b):  # 遍历 b 列表并获取索引
                if t.start_pos == d:  # 如果 t.start_pos 与 d 匹配
                    _.mClipData.mTrackDataID = index  # 将 mTrackDataID 设置为 b 中的索引
                    break  # 结束内层循环，找到后不再继续
            # 如果你希望在未找到匹配时做些处理，可以在这里添加额外的逻辑
        if hasattr(_.mClipData, 'mMaskDataID'):  # 检查对象是否有 mMaskDataID 属性
            e = _.mClipData.mMaskDataAddr  # 获取 mTrackDataAddr

            for index, t in enumerate(c):  # 遍历 b 列表并获取索引
                if t.start_pos == e:  # 如果 t.start_pos 与 e 匹配
                    _.mClipData.mMaskDataID = index  # 将 mMaskDataID 设置为 b 中的索引
                    break  # 结束内层循环，找到后不再继续
                
def read_path_record_pre(file):
    pathHash = read_uint32(file)
    pathOffset = read_int32(file)
    return Path_Record(pathHash, pathOffset)

def read_blnd_header(file):
    enginetype = read_str(file, 4)
    binaryblocktype = read_str(file, 4)
    binaryblockversion = read_uint32(file)
    return BlnderHeader(enginetype, binaryblocktype, binaryblockversion)

def read_blnd_pool(file):
    ResourceSize = read_uint32(file)
    FormatToken = read_uint32(file)
    Version = read_uint32(file)
    NumClasses = read_uint32(file)
    NumBlends = read_uint32(file)
    NumTransitionData = read_uint32(file)
    NumTracks = read_uint32(file)
    NumAnimData = read_uint32(file)
    NumMaskData = read_uint32(file)
    NumEventData = read_uint32(file)
    UseCascadeBlend = read_uint32(file) != 0
    CascadeBlendValue = read_float(file)
    BlendDataAryAddr = read_addr(file)
    TransitionDataOffset = read_addr(file)
    BlendTrackAryAddr = read_addr(file)
    ClassAryAddr = read_addr(file)
    MaskDataAryAddr = read_addr(file)
    EventDataAryAddr = read_addr(file)
    AnimDataAryAddr = read_addr(file)
    AnimNameCount = read_uint32(file)
    AnimNamesOffset = read_addr(file)
    Skeleton = read_path_record_pre(file)
    ExtBuffer = [read_int32(file)]
    EventDataAry = [] #后续优化
    BlendDataAry = read_blend_data(NumBlends, file)
    TransitionData = read_transition_data(NumTransitionData, file)
    BlendTrackAry = read_track_data(NumTracks, file)
    read_class_data_offset(NumClasses, file)
    ClassAry = read_class_data(NumClasses, file)
    read_mask_data_offset(NumMaskData, file)
    MaskDataAry = read_mask_map(NumMaskData, file)
    read_event_data_addr(NumEventData, file)
    AnimDataAry = read_anim_data(NumAnimData, file)
    AnimNames = read_animnames_offset(AnimNameCount, file)
    read_animnames(AnimNames, file)
    Skeleton.Path = read_str(file)
    sync_id(ClassAry, BlendTrackAry, MaskDataAry)
    return BlnderPool(ResourceSize, 
                      FormatToken, 
                      Version, 
                      NumClasses, 
                      NumBlends, 
                      NumTransitionData, 
                      NumTracks, 
                      NumAnimData, 
                      NumMaskData, 
                      NumEventData, 
                      UseCascadeBlend, 
                      CascadeBlendValue, 
                      BlendDataAryAddr, 
                      TransitionDataOffset, 
                      BlendTrackAryAddr, 
                      ClassAryAddr, 
                      MaskDataAryAddr, 
                      EventDataAryAddr, 
                      AnimDataAryAddr, 
                      AnimNameCount, 
                      AnimNamesOffset, 
                      Skeleton, 
                      ExtBuffer, 
                      BlendDataAry, 
                      TransitionData,
                      BlendTrackAry,
                      MaskDataAry,
                      EventDataAry,
                      AnimDataAry,
                      ClassAry,
                      AnimNames)