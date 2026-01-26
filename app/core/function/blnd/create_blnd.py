from ..general import get_relative_path, extract_number, fnv1a, elf_lower
from ..hashes.fnv1 import fnv1_lower
from ...objects.blnd.data_obj.blnd_data import*
from ...objects.blnd.data_obj.transition_data import*
from ...objects.blnd.data_obj.event_data import*
from ...objects.blnd.data_obj.mask_data import*
from ...objects.blnd.data_obj.clip_data import*

def create_new_project(a,b,c,d):
    header = BlnderHeader("r3d2", "blnd", 1)
    e = Path_Record(PathHash=fnv1a(c),Path=c)
    pool_instance = BlnderPool(
        mUseCascadeBlend=a,
        mCascadeBlendValue=b,
        mSkeleton=e,
        mTransitionData=[],
        mBlendTrackAry=[d],
        mClassAry=[],
        mMaskDataAry=[],
        mEventDataAry=[],
        mAnimDataAry=[],
        mAnimNames=[])  # 或者可以显式传入特定值
    pool_instance.sync_data()
    # 创建 BlnderData 实例，并传入 header 和 pool
    blnder_data = BlnderData(header, pool_instance)
    return blnder_data

def create_event_resource(a, b, c):
    d = []
    e = []
    for i in range(len(a)):
        d.append(EventNameHash(i, fnv1_lower(a[i].mName)))
        e.append(EventFrame(i, a[i].mFrame))
    f = EventResource(mUniqueID=c,mEventArray=a,mEventNameHash=d,mEventFrame=e,mName=b)
    return f