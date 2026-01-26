from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from ..function import*
from .event_data import*
from enum import Enum

class ClipFlags(Enum):
    eNone_0 = 0x0
    eMain = 0x1
    eLoop = 0x2
    eContinue = 0x4
    ePlayOnce = 0x8

@dataclass
class AtomicClip:
    mClipTypeID: int = 1
    mStartTick: int = 0
    mEndTick: int = 0
    mTickDuration: float = 0.03333333507180214
    mAnimDataIndex: int = 0
    mEventDataAddr: int = 0
    mMaskDataAddr: int = 0
    mTrackDataAddr: int = 0
    mUpdaterDataOffset: int = 0
    mSyncGroupNameOffset: int = 0
    mSyncGroup: int = 0
    mExtBuffer: list = field(default_factory=lambda: [0, 0])
    mEventData: Optional[EventResource] = None
    mSyncGroupName: str = None
    mTrackDataID: int = 0
    mMaskDataID: int = None

    def get_track_id(self):
        pass

    def get_mask_id(self):
        pass

    def record_start_pos(self, tell):
        self.start_pos = tell
        if self.mEventData is not None:
            tell += 52
            self.mEventData.record_start_pos(tell)

    def aligning_data(self):
        if self.mEventData is not None:
            self.mEventDataAddr = 32
            self.mEventData.aligning_data()

        if self.mSyncGroupName is not None:
            self.mSyncGroup = hash_string_fnv1a(self.mSyncGroupName)
            self.mSyncGroupNameOffset = 16
            if self.mEventData is not None:
                self.mSyncGroupNameOffset += self.mEventData.get_resource_size()

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mClipTypeID))
        write_byte(new_file, get_bytes_uint32(self.mStartTick))
        write_byte(new_file, get_bytes_uint32(self.mEndTick))
        write_byte(new_file, get_bytes_float(self.mTickDuration))
        write_byte(new_file, get_bytes_int32(self.mAnimDataIndex))
        write_byte(new_file, get_bytes_int32(self.mEventDataAddr))
        write_byte(new_file, get_bytes_int32(determine(self.mMaskDataAddr, new_file.tell())))
        write_byte(new_file, get_bytes_int32(determine(self.mTrackDataAddr, new_file.tell())))
        write_byte(new_file, get_bytes_int32(self.mUpdaterDataOffset))
        write_byte(new_file, get_bytes_int32(self.mSyncGroupNameOffset))
        write_byte(new_file, get_bytes_uint32(self.mSyncGroup))
        for ext in self.mExtBuffer:
            write_byte(new_file, get_bytes_uint32(ext))
        if self.mEventData:
            self.mEventData.ini_start_pos(new_file.tell())
            write_obj(self.mEventData, new_file)
        if self.mSyncGroupName is not None:
            write_with_padding(self.mSyncGroupName, new_file)

    def get_resource_size_and_event(self):
        base = self.get_resource_size()
        if self.mEventData is not None:
            base += self.mEventData.get_resource_size()
        return base

    def get_resource_size(self):
        base = 52
        if self.mSyncGroupName:
            base += get_bytes_str_with_padding(self.mSyncGroupName)
        if self.mEventData is not None:
            self.mEventData.get_resource_size()
        return base

@dataclass
class SelectorPairData:
    mClipID: int = 0
    mProbability: float = 0

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mClipID))
        write_byte(new_file, get_bytes_float(self.mProbability))

@dataclass
class SelectorClip:
    mClipTypeID: int = 2
    mTrackIndex: int = 0
    mNumPairs: int = 0
    mSelectorPairDataArr: list = field(default_factory=list)

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mClipTypeID))
        write_byte(new_file, get_bytes_uint32(self.mTrackIndex))
        write_byte(new_file, get_bytes_uint32(len(self.mSelectorPairDataArr)))
        for ext in self.mSelectorPairDataArr:
            write_obj(ext, new_file)

    def get_resource_size(self):
        return 12 + len(self.mSelectorPairDataArr) * 8

    def aligning_data(self):
        self.mNumPairs = len(self.mSelectorPairDataArr)

    def record_start_pos(self, tell):
        self.start_pos = tell

@dataclass
class SequencerClip:
    mClipTypeID: int = 3
    mTrackIndex: int = 0
    mNumPairs: int = 0
    mPairsIDArr: list = field(default_factory=list)

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mClipTypeID))
        write_byte(new_file, get_bytes_uint32(self.mTrackIndex))
        write_byte(new_file, get_bytes_uint32(len(self.mPairsIDArr)))
        for ext in self.mPairsIDArr:
            write_byte(new_file, get_bytes_uint32(ext))

    def get_resource_size(self):
        return 12 + self.mNumPairs * 4

    def aligning_data(self):
        self.mNumPairs = len(self.mPairsIDArr)

    def record_start_pos(self, tell):
        self.start_pos = tell

@dataclass
class ParallelClip:
    mClipTypeID: int = 4
    mClipFlag: int = 0
    mNumClips: int = 0
    mClipsIDArr: list = field(default_factory=list)

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mClipTypeID))
        write_byte(new_file, get_bytes_uint32(self.mClipFlag))
        write_byte(new_file, get_bytes_uint32(len(self.mClipsIDArr)))
        for ext in self.mClipsIDArr:
            write_byte(new_file, get_bytes_uint32(ext))

    def get_resource_size(self):
        return 12 + self.mNumClips * 4

    def aligning_data(self):
        self.mNumClips = len(self.mClipsIDArr)

    def record_start_pos(self, tell):
        self.start_pos = tell

@dataclass
class MultiChildClip:
    mClipTypeID: int = 5

    def record_start_pos(self, tell):
        self.start_pos = tell

@dataclass
class ParametricPairData:
    mClipID: int = 0
    mValue: float = 0

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mClipID))
        write_byte(new_file, get_bytes_float(self.mValue))

@dataclass
class ParametricClip:
    mClipTypeID: int = 6
    mNumPairs: int = 0
    mUpdaterType: int = 0
    mMaskDataAddr: int = 0
    mTrackDataAddr: int = 0
    mConditionFloatPairDataList: list = field(default_factory=list) # 需要按Value大小排序
    mTrackDataID: int = 0
    mMaskDataID: int = None

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mClipTypeID))
        write_byte(new_file, get_bytes_uint32(len(self.mConditionFloatPairDataList)))
        write_byte(new_file, get_bytes_uint32(self.mUpdaterType))
        write_byte(new_file, get_bytes_int32(self.mMaskDataAddr))
        write_byte(new_file, get_bytes_int32(determine(self.mTrackDataAddr, new_file.tell())))
        for i in self.mConditionFloatPairDataList:
            write_obj(i, new_file)

    def get_resource_size(self):
        return 20 + len(self.mConditionFloatPairDataList) * 8

    def aligning_data(self):
        self.mNumPairs = len(self.mConditionFloatPairDataList)

    def record_start_pos(self, tell):
        self.start_pos = tell

@dataclass
class ConditionBoolClipData:
    mClipID: int = 0
    mCondition: bool = False

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mClipID))
        write_byte(new_file, get_bytes_uint32(int(self.mCondition)))

@dataclass
class ConditionBoolClip:
    mClipTypeID: int = 7
    mTrackIndex: int = 0
    mNumPairs: int = 0
    mUpdaterType: int = 0
    mChangeAnimationMidPlay: bool = False
    mPairsIDArr: list = field(default_factory=list)

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mClipTypeID))
        write_byte(new_file, get_bytes_uint32(self.mTrackIndex))
        write_byte(new_file, get_bytes_uint32(len(self.mPairsIDArr)))
        write_byte(new_file, get_bytes_uint32(self.mUpdaterType))
        write_byte(new_file, get_bytes_uint32(int(self.mChangeAnimationMidPlay)))
        write_obj_list(self.mPairsIDArr, new_file)

    def get_resource_size(self):
        return 20 + len(self.mPairsIDArr) * 8

    def aligning_data(self):
        self.mNumPairs = len(self.mPairsIDArr)

    def record_start_pos(self, tell):
        self.start_pos = tell

@dataclass
class ConditionFloatPairData:
    mClipID: int = 0
    mValue: float = 0
    mUnknown0: int = 0
    mUnknown1: int = 0

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mClipID))
        write_byte(new_file, get_bytes_float(self.mValue))
        write_byte(new_file, get_bytes_uint32(self.mUnknown0))
        write_byte(new_file, get_bytes_uint32(self.mUnknown1))

@dataclass
class ConditionFloatClip:
    mClipTypeID: int = 8
    mTrackIndex: int = 0
    mNumPairs: int = 0
    mUpdaterType: int = 0
    mChangeAnimationMidPlay: bool = False
    mConditionFloatPairDataList: list = field(default_factory=list)

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mClipTypeID))
        write_byte(new_file, get_bytes_uint32(self.mTrackIndex))
        write_byte(new_file, get_bytes_uint32(len(self.mConditionFloatPairDataList)))
        write_byte(new_file, get_bytes_uint32(self.mUpdaterType))
        write_byte(new_file, get_bytes_uint32(int(self.mChangeAnimationMidPlay)))
        for i in self.mConditionFloatPairDataList:
            write_obj(i, new_file)

    def get_resource_size(self):
        return 20 + len(self.mConditionFloatPairDataList) * 16

    def aligning_data(self):
        self.mNumPairs = len(self.mConditionFloatPairDataList)

    def record_start_pos(self, tell):
        self.start_pos = tell

@dataclass
class ClipResource:
    mResourceSize: int = 0
    mFlags: int = 0
    mUniqueID: int = 0
    mNameOffset: int = 0
    mClipDataOffset: int = 0
    mName: str = None
    mClipData: Optional[Any] = None

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mResourceSize))
        write_byte(new_file, get_bytes_uint32(self.mFlags))
        write_byte(new_file, get_bytes_uint32(self.mUniqueID))
        write_byte(new_file, get_bytes_uint32(self.mNameOffset))
        write_byte(new_file, get_bytes_uint32(self.mClipDataOffset))
        write_with_padding(self.mName, new_file)
        write_obj(self.mClipData, new_file)

    def get_resource_size(self):
        return 20 + get_bytes_str_with_padding(self.mName) + self.mClipData.get_resource_size()

    def get_resource_size_and_event(self):
        if hasattr(self.mClipData, 'mEventData'):
            return 20 + get_bytes_str_with_padding(self.mName) + self.mClipData.get_resource_size_and_event()
        return self.get_resource_size()

    def aligning_data(self):
        self.mNameOffset = 20
        self.mClipDataOffset = 20 + get_bytes_str_with_padding(self.mName)
        self.mClipData.aligning_data()

    def record_start_pos(self, tell, arr, a):
        number_class = len(arr)
        and_size = 0
        b = number_class - a
        for i in range(number_class - b):
            and_size += arr[i].get_resource_size_and_event()

        self.start_pos = and_size + tell
        data_tell = self.start_pos + 20 + get_bytes_str_with_padding(self.mName)
        self.mClipData.record_start_pos(data_tell)