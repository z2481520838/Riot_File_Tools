from .resource import*
from .writable import*
from .binary_reader import*
from .event_resource import*
from .track_resource import*
from .mask_resource import*
from .memory import*
from .function import*
from enum import Enum

class ClipResource(Resource):
    class Flags(Enum):
        eNone_0 = 0x0
        eMain = 0x1
        eLoop = 0x2
        eContinue = 0x4
        ePlayOnce = 0x8

    def __init__(self, br):
        super().__init__(br)
        self.mFlags = br.read_uint32()  # 将int值转为Flags枚举
        self.mUniqueID = br.read_uint32()

        # 读取地址并跳转
        self.mNameOffset = br.read_addr_at_position(self.baseAddr)
        self.mClipDataOffset = br.read_addr_at_position(self.baseAddr)

        # 读取字符串和其他资源
        prev_position = br.tell()
        br.seek(self.mNameOffset)
        self.mName = br.read_cstring() if self.mNameOffset != 0 else None
        br.seek(self.mClipDataOffset)
        self.mClipData = ClipData.read(br) if self.mClipDataOffset != 0 else None
        br.seek(prev_position)

    def write(self, bw):
        # 写入数据
        bw.seek(self.baseAddr)
        bw.write(struct.pack('<I', self.mResourceSize))
        bw.write(struct.pack('<I', self.mFlags))
        bw.write(struct.pack('<I', self.mUniqueID))
        bw.write(struct.pack('<I', self.mNameOffset - self.baseAddr))
        bw.write(struct.pack('<I', self.mClipDataOffset - self.baseAddr))
        write_with_padding(self.mName, bw)
        # bw.write(self.mName.encode('utf-8') + b'\0')
        self.mClipData.write(bw)

class ClipData(Writable):
    class ClipTypes(Enum):
        eInvalid = 0x0
        eAtomic = 0x1
        eSelector = 0x2
        eSequencer = 0x3
        eParallel = 0x4
        eMultiChildClip = 0x5
        eParametric = 0x6
        eConditionBool = 0x7
        eConditionFloat = 0x8

    def __init__(self, br):
        self.mClipTypeID = br.read_uint32()

    @staticmethod
    def read(br):
        prevPosition = br.tell()
        clip_type = ClipData.ClipTypes(br.read_uint32())
        br.seek(prevPosition)
        if clip_type == ClipData.ClipTypes.eAtomic:
            return AtomicClip(br)
        elif clip_type == ClipData.ClipTypes.eSelector:
            return SelectorClip(br)
        elif clip_type == ClipData.ClipTypes.eSequencer:
            return SequencerClip(br)
        elif clip_type == ClipData.ClipTypes.eParallel:
            return ParallelClip(br)
        elif clip_type == ClipData.ClipTypes.eMultiChildClip:
            return MultiChildClip(br)
        elif clip_type == ClipData.ClipTypes.eParametric:
            return ParametricClip(br)
        elif clip_type == ClipData.ClipTypes.eConditionBool:
            return ConditionBoolClip(br)
        elif clip_type == ClipData.ClipTypes.eConditionFloat:
            return ConditionFloatClip(br)
        else:
            raise Exception("Invalid clip type")

    def write(self, bw):
        bw.write(struct.pack('<I', self.mClipTypeID))

class AtomicClip(ClipData):
    def __init__(self, br):
        super().__init__(br)
        self.mStartTick = br.read_uint32()
        self.mEndTick = br.read_uint32()
        self.mTickDuration = br.read_float()
        self.mAnimDataIndex = br.read_int32()
        self.mEventDataAddr = br.read_addr()
        self.mMaskDataAddr = br.read_addr()
        self.mTrackDataAddr = br.read_addr()
        self.mUpdaterDataOffset = br.read_addr()
        self.mSyncGroupNameOffset = br.read_addr()
        self.mSyncGroup = br.read_uint32()
        self.mExtBuffer = [br.read_uint32(), br.read_uint32()]
        prevPosition = br.tell()
        self.mEventData = br.read_resource(self.mEventDataAddr, EventResource)
        self.mMaskData = br.read_resource(self.mMaskDataAddr, MaskResource)
        self.mTrackData = br.read_resource(self.mTrackDataAddr, TrackResource)
        self.mUpdaterData = br.read_resource(self.mUpdaterDataOffset, UpdaterResource)
        br.seek(self.mSyncGroupNameOffset)
        if self.mSyncGroupNameOffset != 0:
            self.mSyncGroupName = br.read_cstring()
        else:
            self.mSyncGroupName = None
        br.seek(prevPosition)

    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<I', self.mStartTick))
        bw.write(struct.pack('<I', self.mEndTick))
        bw.write(struct.pack('<f', self.mTickDuration))
        bw.write(struct.pack('<i', self.mAnimDataIndex))
        bw.write(struct.pack('<i', self.determine(self.mEventDataAddr, bw.tell())))
        bw.write(struct.pack('<i', self.determine(self.mMaskDataAddr, bw.tell())))
        bw.write(struct.pack('<i', self.determine(self.mTrackDataAddr, bw.tell())))
        bw.write(struct.pack('<i', self.determine(self.mUpdaterDataOffset, bw.tell())))
        bw.write(struct.pack('<i', self.determine(self.mSyncGroupNameOffset, bw.tell())))
        # 写入其他资源
        bw.write(struct.pack('<I', self.mSyncGroup))
        for ext in self.mExtBuffer:
            bw.write(struct.pack('<I', ext))
        if self.mEventData:
            self.mEventData.write(bw)
        # if self.mMaskData:
            # bw.seek(self.mMaskDataAddr)
            # self.mMaskData.write(bw)
        if self.mSyncGroupName:
            write_with_padding(self.mSyncGroupName, bw)
            # bw.write(self.mSyncGroupName.encode('utf-8') + b'\0')
    def determine(self, a, b):
        if a > 0:
            return a - b
        return 0

class UpdaterResource(Resource): 
    def __init__(self, br):
        super().__init__(br)
        # mVersion
        # mNumUpdaters
        # mUpdaters: UpdaterData
    def write(self, bw):
        pass

class UpdaterData(Resource): 
    def __init__(self, br):
        super().__init__(br)
        # mInputType
        # mOutputType
        # mNumTransforms
        # mProcessors: AnimValueProcessorData[]
    def write(self, bw):
        pass

class AnimValueProcessorData(Resource): 
    def __init__(self, br):
        super().__init__(br)
        self.mProcessorType = br.read_uint16()
        br.read_uint16()
    def write(self, bw):
        pass

class SelectorClip(ClipData):
    class SelectorPairData(Writable):
        def __init__(self, br: BinaryReader):
            self.mClipID = br.read_uint32()
            self.mProbability = br.read_float()

        def write(self, bw):
            bw.write(struct.pack('<I', self.mClipID))
            bw.write(struct.pack('<f', self.mProbability))

    def __init__(self, br):
        super().__init__(br)
        self.mTrackIndex = br.read_uint32()
        self.mNumPairs = br.read_uint32()
        self.mSelectorPairDataArr = []
        for i in range(self.mNumPairs):
            self.mSelectorPairDataArr.append(self.SelectorPairData(br))

    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<I', self.mTrackIndex))
        bw.write(struct.pack('<I', self.mNumPairs))
        for i in self.mSelectorPairDataArr:
            i.write(bw)

class SequencerClip(ClipData):
    def __init__(self, br):
        super().__init__(br)
        self.mTrackIndex = br.read_uint32()
        self.mNumPairs = br.read_uint32()
        self.mPairsIDArr = []
        for i in range(self.mNumPairs):
            self.mPairsIDArr.append(br.read_uint32())

    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<I', self.mTrackIndex))
        bw.write(struct.pack('<I', self.mNumPairs))
        for i in self.mPairsIDArr:
            bw.write(struct.pack('<I', i))

class ParametricClip(ClipData):
    class ParametricPairData(Writable):
        def __init__(self, br):
            self.mClipID = br.read_uint32()
            self.mValue = br.read_float()

        def write(self, bw):
            bw.write(struct.pack('<I', self.mClipID))
            bw.write(struct.pack('<f', self.mValue))

    def __init__(self, br):
        super().__init__(br)
        self.mNumPairs = br.read_uint32()
        self.mUpdaterType = br.read_uint32()
        
        self.mMaskDataAddr = br.read_addr()
        self.mTrackDataAddr = br.read_addr()

        prevPosition = br.tell()
        self.mMaskData = br.read_resource(self.mMaskDataAddr, MaskResource)
        self.mTrackData = br.read_resource(self.mTrackDataAddr, TrackResource)
        br.seek(prevPosition)
        
        self.mConditionFloatPairDataList = []
        for i in range(self.mNumPairs):
            self.mConditionFloatPairDataList.append(self.ParametricPairData(br))
        
    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<I', self.mNumPairs))
        bw.write(struct.pack('<I', self.mUpdaterType))
        bw.write(struct.pack('<i', determine(self.mMaskDataAddr, bw.tell())))
        bw.write(struct.pack('<i', determine(self.mTrackDataAddr, bw.tell())))
        for i in self.mConditionFloatPairDataList:
            i.write(bw)
        # 获取当前写入位置
        # current_position = bw.stream.tell()  # 获取当前流的位置
        
        # 写入 mMaskData 和 mTrackData
        # bw.write(Memory.Allocate(current_position, self.mMaskData))
        # bw.write(Memory.Allocate(current_position, self.mTrackData))

class MultiChildClip(ClipData):
    def __init__(self, br):
        super().__init__(br)
    def write(self, bw):
        pass

class ParallelClip(ClipData):
    def __init__(self, br):
        super().__init__(br)
        self.mClipFlag = br.read_addr()
        self.mNumClips = br.read_uint32()
        self.mClipsIDArr = []
        for i in range(self.mNumClips):
            self.mClipsIDArr.append(br.read_uint32())

    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<I', self.mClipFlag))
        bw.write(struct.pack('<I', self.mNumClips))
        for i in self.mClipsIDArr:
            bw.write(struct.pack('<I', i))

class ConditionBoolClip(ClipData):
    class ConditionBoolClipData(Writable):
        def __init__(self, br: BinaryReader):
            self.mClipID = br.read_uint32()
            self.mCondition = br.read_uint32() != 0

        def write(self, bw):
            bw.write(struct.pack('<I', self.mClipID))
            bw.write(struct.pack('<I', int(self.mCondition)))

    def __init__(self, br):
        super().__init__(br)
        self.mTrackIndex = br.read_uint32()
        self.mNumPairs = br.read_uint32()
        self.mUpdaterType = br.read_uint32()
        self.mChangeAnimationMidPlay = br.read_uint32() != 0  # 根据读取的值判断是否改变动画中途播放
        self.mPairsIDArr = []
        for i in range(self.mNumPairs):
            self.mPairsIDArr.append(self.ConditionBoolClipData(br))

    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<I', self.mTrackIndex))
        bw.write(struct.pack('<I', self.mNumPairs))
        bw.write(struct.pack('<I', self.mUpdaterType))
        bw.write(struct.pack('<I', int(self.mChangeAnimationMidPlay)))
        for i in self.mPairsIDArr:
            i.write(bw)


class ConditionFloatClip(ClipData):
    class ConditionFloatPairData(Writable):
        def __init__(self, br: BinaryReader):
            self.mClipID = br.read_uint32()
            self.mValue = br.read_float()
            self.mUnknown0 = br.read_uint32()
            self.mUnknown1 = br.read_uint32()

        def write(self, bw):
            bw.write(struct.pack('<I', self.mClipID))
            bw.write(struct.pack('<f', self.mValue))
            bw.write(struct.pack('<I', self.mUnknown0))
            bw.write(struct.pack('<I', self.mUnknown1))
    def __init__(self, br):
        super().__init__(br)
        self.mTrackIndex = br.read_uint32()
        self.mNumPairs = br.read_uint32()
        self.mUpdaterType = br.read_uint32()
        self.mChangeAnimationMidPlay = br.read_uint32() != 0  # 根据读取的值判断是否改变动画中途播放
        self.mConditionFloatPairDataList = []
        for i in range(self.mNumPairs):
            self.mConditionFloatPairDataList.append(self.ConditionFloatPairData(br))

    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<I', self.mTrackIndex))
        bw.write(struct.pack('<I', self.mNumPairs))
        bw.write(struct.pack('<I', self.mUpdaterType))
        bw.write(struct.pack('<I', int(self.mChangeAnimationMidPlay)))
        for i in self.mConditionFloatPairDataList:
            i.write(bw)
