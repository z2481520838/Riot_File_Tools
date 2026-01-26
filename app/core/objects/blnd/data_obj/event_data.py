from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from ..function import*
import os

@dataclass
class EventData:
    mResourceSize: int = 0
    mEventTypeId: int = 0
    mFlags: int = 0
    mFrame: float = 0
    mNameOffset: int = 0
    mName: str = None

@dataclass
class EnableLookAtEventData(EventData):
    mEndFrame: float = 0
    mEnableLookAt: int = 0
    mLockCurrentValues: int = 0

    def get_value_size(self):
        return 12

    def get_resource_size(self):
        return 32 + get_bytes_str_with_padding(self.mName)

    def get_name_offset(self):
        self.mEventTypeId = 6
        self.mNameOffset = 20 + self.get_value_size()

@dataclass
class SubmeshVisibilityEventData(EventData):
    mEndFrame: float = 0
    mShowSubmeshHash: int = 0
    mHideSubmeshHash: int = 0

    def get_value_size(self):
        return 12

    def get_resource_size(self):
        return 32 + get_bytes_str_with_padding(self.mName)

    def get_name_offset(self):
        self.mEventTypeId = 3
        self.mNameOffset = 20 + self.get_value_size()

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mResourceSize))
        write_byte(new_file, get_bytes_uint32(self.mEventTypeId))
        write_byte(new_file, get_bytes_uint32(self.mFlags))
        write_byte(new_file, get_bytes_float(self.mFrame))
        write_byte(new_file, get_bytes_int32(self.mNameOffset))
        write_byte(new_file, get_bytes_float(self.mEndFrame))
        write_byte(new_file, get_bytes_uint32(self.mShowSubmeshHash))
        write_byte(new_file, get_bytes_uint32(self.mHideSubmeshHash))
        write_with_padding(self.mName, new_file)
        
@dataclass
class FadeEventData(EventData):
    mTimeToFade: float = 0
    mTargetAlpha: float = 0
    mEndFrame: float = 0

    def get_value_size(self):
        return 12

    def get_resource_size(self):
        return 32 + get_bytes_str_with_padding(self.mName)

    def get_name_offset(self):
        self.mEventTypeId = 4
        self.mNameOffset = 20 + self.get_value_size()

@dataclass
class JointSnapEventData(EventData):
    mEndFrame: float = 0
    mJointToOverrideIdx: int = 0
    mJointToSnapToIdx: int = 0

    def get_value_size(self):
        return 8

    def get_resource_size(self):
        return 28 + get_bytes_str_with_padding(self.mName)

    def get_name_offset(self):
        self.mEventTypeId = 5
        self.mNameOffset = 20 + self.get_value_size()

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mResourceSize))
        write_byte(new_file, get_bytes_uint32(self.mEventTypeId))
        write_byte(new_file, get_bytes_uint32(self.mFlags))
        write_byte(new_file, get_bytes_float(self.mFrame))
        write_byte(new_file, get_bytes_int32(self.mNameOffset))
        write_byte(new_file, get_bytes_float(self.mEndFrame))
        write_byte(new_file, get_bytes_uint16(self.mJointToOverrideIdx))
        write_byte(new_file, get_bytes_uint16(self.mJointToSnapToIdx))
        write_with_padding(self.mName, new_file)

@dataclass
class SoundEventData(EventData):
    mSoundNameOffset: int = 0
    mSoundName: str = None

    def get_value_size(self):
        return 4

    def get_resource_size(self):
        return 24 + get_bytes_str_with_padding(self.mName) + get_bytes_str_with_padding(self.mSoundName)

    def get_name_offset(self):
        self.mEventTypeId = 1
        self.mNameOffset = 20 + self.get_value_size()
        self.mSoundNameOffset = self.mNameOffset + get_bytes_str_with_padding(self.mName)

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mResourceSize))
        write_byte(new_file, get_bytes_uint32(self.mEventTypeId))
        write_byte(new_file, get_bytes_uint32(self.mFlags))
        write_byte(new_file, get_bytes_float(self.mFrame))
        write_byte(new_file, get_bytes_int32(self.mNameOffset))
        write_byte(new_file, get_bytes_int32(self.mSoundNameOffset))
        write_with_padding(self.mName, new_file)
        write_with_padding(self.mSoundName, new_file)

@dataclass
class ParticleEventData(EventData):
    mEffectNameOffset: int = 0
    mBoneNameOffset: int = 0
    mTargetBoneNameOffset: int = 0
    mEndFrame: float = 0
    mEffectName: str = None
    mBoneName: str = None
    mTargetBoneName: str = None

    def get_value_size(self):
        return 16

    def get_resource_size(self):
        # 创建包含需要计算的字段的列表
        fields = [self.mName, self.mEffectName, self.mBoneName, self.mTargetBoneName]
        # 使用列表推导式计算每个字段的大小，并求和
        padding_size = sum(get_bytes_str_with_padding(field) for field in fields)
        # 返回最终的资源大小
        return 36 + padding_size

    def get_name_offset(self):
        self.mEventTypeId = 2
        name_start = 20 + self.get_value_size()
        self.mNameOffset = name_start
        name_start += get_bytes_str_with_padding(self.mName)
        self.mEffectNameOffset = name_start
        name_start += get_bytes_str_with_padding(self.mEffectName)
        self.mBoneNameOffset = name_start
        name_start += get_bytes_str_with_padding(self.mBoneName)
        self.mTargetBoneNameOffset = name_start

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mResourceSize))
        write_byte(new_file, get_bytes_uint32(self.mEventTypeId))
        write_byte(new_file, get_bytes_uint32(self.mFlags))
        write_byte(new_file, get_bytes_float(self.mFrame))
        write_byte(new_file, get_bytes_int32(self.mNameOffset))
        write_byte(new_file, get_bytes_int32(self.mEffectNameOffset))
        write_byte(new_file, get_bytes_int32(self.mBoneNameOffset))
        write_byte(new_file, get_bytes_int32(self.mTargetBoneNameOffset))
        write_byte(new_file, get_bytes_float(self.mEndFrame))
        write_with_padding(self.mName, new_file)
        write_with_padding(self.mEffectName, new_file)
        write_with_padding(self.mBoneName, new_file)
        write_with_padding(self.mTargetBoneName, new_file)

@dataclass
class EventNameHash:
    mDataID: int = 0
    mNameHash: int = 0

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mDataID))
        write_byte(new_file, get_bytes_uint32(self.mNameHash))

@dataclass
class EventFrame:
    mDataID: int = 0
    mFrame: float = 0

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mDataID))
        write_byte(new_file, get_bytes_float(self.mFrame))

@dataclass
class EventResource:
    mResourceSize: int = 0
    mFormatToken: int = 0
    mVersion: int = 0
    mFlags: int = 0
    mNumEvents: int = 0
    mUniqueID: int = 0
    mEventOffsetArrayOffset: int = 0
    mEventDataOffset: int = 0
    mEventNameHashOffset: int = 0
    mEventFrameOffset: int = 0
    mNameOffset: int = 0
    mExtBuffer: list = field(default_factory=lambda: [4294967295, 4294967295])
    mEventDataOffsetArr: list = field(default_factory=list)
    mEventArray: list = field(default_factory=list)
    mEventNameHash: list = field(default_factory=list)
    mEventFrame: list = field(default_factory=list)
    mName: str = None

    def ini_start_pos(self, pos):
        self.start_pos = pos

    def record_start_pos(self, tell):
        self.start_pos = tell

    def get_data_pos(self):
        if not hasattr(self, 'start_pos'):  # 检查属性是否已定义
            raise ValueError("start_pos is not initialized yet")
        return self.start_pos

    def get_resource_size(self):
        var_0 = 48 + get_bytes_str_with_padding(self.mName)
        var_0 += 4 * len(self.mEventDataOffsetArr)
        # print(f"{var_0}")
        for data in self.mEventArray:
            var_0 += data.get_resource_size()
        # print(f"{var_0}")
        for name in self.mEventNameHash:
            var_0 += 8
        # print(f"{var_0}")
        for frame in self.mEventFrame:
            var_0 += 8
        # print(f"{var_0}")
        return var_0

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mResourceSize))
        write_byte(new_file, get_bytes_uint32(self.mFormatToken))
        write_byte(new_file, get_bytes_uint32(self.mVersion))
        write_byte(new_file, get_bytes_uint16(self.mFlags))
        write_byte(new_file, get_bytes_uint16(len(self.mEventArray)))
        write_byte(new_file, get_bytes_uint32(self.mUniqueID))

        write_byte(new_file, get_bytes_int32(self.mEventOffsetArrayOffset))
        write_byte(new_file, get_bytes_int32(self.mEventDataOffset))
        write_byte(new_file, get_bytes_int32(self.mEventNameHashOffset))
        write_byte(new_file, get_bytes_int32(self.mEventFrameOffset))
        write_byte(new_file, get_bytes_int32(self.mNameOffset))
        write_uint32_list(self.mExtBuffer, new_file)
        write_uint32_list(self.mEventDataOffsetArr, new_file)
        write_obj_list(self.mEventArray, new_file)
        write_obj_list(self.mEventNameHash, new_file)
        write_obj_list(self.mEventFrame, new_file)
        write_with_padding(self.mName, new_file)

    def aligning_data(self):
        data_count = len(self.mEventArray)
        self.mNumEvents = data_count
        base_offset = 0
        self.mEventDataOffsetArr.clear()
        base_data_offset = 48 + data_count * 4
        for i in range(data_count):
            if i > 0:
                base_data_offset += self.mEventArray[i - 1].get_resource_size()
                self.mEventDataOffsetArr.append(base_data_offset)
            else:
                self.mEventDataOffsetArr.append(base_data_offset)
        self.mEventOffsetArrayOffset = 48
        base_offset = self.mEventOffsetArrayOffset
        self.mEventDataOffset = 48 + self.mNumEvents * 4
        base_offset = self.mEventDataOffset
        for data in self.mEventArray:
            base_offset += data.get_resource_size()
            data.get_name_offset()
        self.mEventNameHashOffset = base_offset
        for data in self.mEventNameHash:
            base_offset += 8
        self.mEventFrameOffset = base_offset
        for data in self.mEventFrame:
            base_offset += 8
        self.mNameOffset = base_offset
"""关于mUniqueID：在创建时，遍历所有class，将class的eventresource自动收进一个list，根据此list的长度进行编号，这样就算中间有修改或删除，也会自动对齐"""