import struct
from typing import List
from .resource import*
from .writable import*
from .binary_reader import*
from .function import*
from enum import Enum

class EventResource(Resource):
    class EventNameHash(Writable):
        def __init__(self, br: BinaryReader):
            self.mDataID = br.read_uint32()
            self.mNameHash = br.read_uint32()

        def write(self, bw):
            bw.write(struct.pack('<I', self.mDataID))
            bw.write(struct.pack('<I', self.mNameHash))

    class EventFrame(Writable):
        def __init__(self, br: BinaryReader):
            self.mDataID = br.read_uint32()
            self.mFrame = br.read_float()

        def write(self, bw):
            bw.write(struct.pack('<I', self.mDataID))
            bw.write(struct.pack('<f', self.mFrame))

    def __init__(self, br: BinaryReader):
        super().__init__(br)
        self.mFormatToken = br.read_uint32()
        self.mVersion = br.read_uint32()
        self.mFlags = br.read_uint16()
        self.mNumEvents = br.read_uint16()
        self.mUniqueID = br.read_uint32()

        self.mEventOffsetArrayOffset = br.read_addr_at_position(self.baseAddr)
        self.mEventDataOffset = br.read_addr_at_position(self.baseAddr)
        self.mEventNameHashOffset = br.read_addr_at_position(self.baseAddr)
        self.mEventFrameOffset = br.read_addr_at_position(self.baseAddr)
        self.mNameOffset = br.read_addr_at_position(self.baseAddr)

        self.mExtBuffer = [br.read_uint32(), br.read_uint32()]
        self.mEventDataOffsetArr = []
        if self.mNumEvents > 0:
            for i in range(self.mNumEvents):
                self.mEventDataOffsetArr.append(br.read_uint32())
        prev_position = br.tell()
        if self.mEventOffsetArrayOffset != 0:
            self.mEventArray = br.read_arr2(self.mEventOffsetArrayOffset, self.mNumEvents, lambda br: BaseEventData.read(br), self.baseAddr)
        else:
            self.mEventArray = []
        # 这里多余了
        if self.mEventDataOffset != 0:
            br.seek(self.mEventDataOffset)
            self.mEventData = BaseEventData.read(br)
        else:
            self.mEventData = None
        # 到这里
        if self.mEventNameHashOffset != 0:
            br.seek(self.mEventNameHashOffset)
            self.mEventNameHash = []
            if self.mNumEvents > 0:
                for i in range(self.mNumEvents):
                    self.mEventNameHash.append(self.EventNameHash(br))
            # self.mEventNameHash = self.EventNameHash(br)
        else:
            self.mEventNameHash = None
        if self.mEventFrameOffset != 0:
            br.seek(self.mEventFrameOffset)
            self.mEventFrame = []
            if self.mNumEvents > 0:
                for i in range(self.mNumEvents):
                    self.mEventFrame.append(self.EventFrame(br))
        else:
            self.mEventFrame = None
        if self.mNameOffset != 0:
            br.seek(self.mNameOffset)
            self.mName = br.read_cstring()
        else:
            self.mName = None
        br.seek(prev_position)

    def write(self, bw):
        bw.write(struct.pack('<I', self.mResourceSize))
        bw.write(struct.pack('<I', self.mFormatToken))
        bw.write(struct.pack('<I', self.mVersion))
        bw.write(struct.pack('<H', self.mFlags))
        bw.write(struct.pack('<H', len(self.mEventArray)))
        bw.write(struct.pack('<I', self.mUniqueID))

        # Assume offsets are written
        bw.write(struct.pack('<i', determine(self.mEventOffsetArrayOffset, self.baseAddr)))  # Placeholder for mEventOffsetArrayOffset
        bw.write(struct.pack('<i', determine(self.mEventDataOffset, self.baseAddr)))  # Placeholder for mEventDataOffset
        bw.write(struct.pack('<i', determine(self.mEventNameHashOffset, self.baseAddr)))  # Placeholder for mEventNameHashOffset
        bw.write(struct.pack('<i', determine(self.mEventFrameOffset, self.baseAddr)))  # Placeholder for mEventFrameOffset
        bw.write(struct.pack('<i', determine(self.mNameOffset, self.baseAddr)))  # Placeholder for mNameOffset
        for ext in self.mExtBuffer:
            bw.write(struct.pack('<I', ext))
        if len(self.mEventDataOffsetArr) > 0:
            for offset in self.mEventDataOffsetArr:
                bw.write(struct.pack('<I', offset))
        # Write the event array data
        for event in self.mEventArray:
            event.write(bw)
        if self.mEventNameHash:
            bw.seek(self.mEventNameHashOffset)
            for _ in self.mEventNameHash:
                _.write(bw)

        if self.mEventFrame:
            bw.seek(self.mEventFrameOffset)
            for _ in self.mEventFrame:
                _.write(bw)

        if self.mName:
            bw.seek(self.mNameOffset)
            write_with_padding(self.mName, bw)
            # bw.write(self.mName.encode('utf-8') + b'\0')
        """if self.mEventData:
            self.mEventData.write(bw)

        """



class BaseEventData(Resource):
    class EventType(Enum):
        SoundEventData = 0x1
        ParticleEventData = 0x2
        SubmeshVisibilityEventData = 0x3
        FadeEventData = 0x4
        JointSnapEventData = 0x5
        EnableLookAtEventData = 0x6

    def __init__(self, br: BinaryReader):
        super().__init__(br)
        self.mEventTypeId = br.read_uint32()
        self.mFlags = br.read_uint32()
        self.mFrame = br.read_float()
        self.mNameOffset = br.read_addr_at_position(self.baseAddr)

        prev_position = br.tell()
        if self.mNameOffset != 0:
            br.seek(self.mNameOffset)
            self.mName = br.read_cstring()
        else:
            self.mName = None

        br.seek(prev_position)

    @staticmethod
    def read(br: BinaryReader):
        prev_position = br.tell()
        br.seek(prev_position + 4)  # Skip mResourceSize
        event_type = BaseEventData.EventType(br.read_uint32())
        br.seek(prev_position)

        if event_type == BaseEventData.EventType.SoundEventData:
            return SoundEventData(br)
        elif event_type == BaseEventData.EventType.ParticleEventData:
            return ParticleEventData(br)
        elif event_type == BaseEventData.EventType.SubmeshVisibilityEventData:
            return SubmeshVisibilityEventData(br)
        elif event_type == BaseEventData.EventType.FadeEventData:
            return FadeEventData(br)
        elif event_type == BaseEventData.EventType.JointSnapEventData:
            return JointSnapEventData(br)
        elif event_type == BaseEventData.EventType.EnableLookAtEventData:
            return EnableLookAtEventData(br)
        # Add more cases for other event types
        else:
            raise Exception("Invalid event type")

    def write(self, bw):
        # super().write(bw)
        bw.seek(self.baseAddr)
        bw.write(struct.pack('<I', self.mResourceSize))
        bw.write(struct.pack('<I', self.mEventTypeId))
        bw.write(struct.pack('<I', self.mFlags))
        bw.write(struct.pack('<f', self.mFrame))
        bw.write(struct.pack('<i', determine(self.mNameOffset, self.baseAddr)))
        prev_position = bw.tell()
        bw.seek(self.mNameOffset)
        write_with_padding(self.mName, bw)
        bw.seek(prev_position)

class JointSnapEventData(BaseEventData):
    def __init__(self, br: BinaryReader):
        super().__init__(br)
        self.mEndFrame = br.read_float()
        self.mJointToOverrideIdx = br.read_uint16()
        self.mJointToSnapToIdx = br.read_uint16()

    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<f', self.mEndFrame))
        bw.write(struct.pack('<H', self.mJointToOverrideIdx))
        bw.write(struct.pack('<H', self.mJointToSnapToIdx))

class FadeEventData(BaseEventData):
    def __init__(self, br: BinaryReader):
        super().__init__(br)
        self.mTimeToFade = br.read_float()
        self.mTargetAlpha = br.read_float()
        self.mEndFrame = br.read_float()

    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<f', self.mTimeToFade))
        bw.write(struct.pack('<f', self.mTargetAlpha))
        bw.write(struct.pack('<f', self.mEndFrame))

class SubmeshVisibilityEventData(BaseEventData):
    def __init__(self, br: BinaryReader):
        super().__init__(br)
        self.mEndFrame = br.read_float()
        self.mShowSubmeshHash = br.read_uint32()
        self.mHideSubmeshHash = br.read_uint32()

    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<f', self.mEndFrame))
        bw.write(struct.pack('<I', self.mShowSubmeshHash))
        bw.write(struct.pack('<I', self.mHideSubmeshHash))

class SoundEventData(BaseEventData):
    def __init__(self, br: BinaryReader):
        super().__init__(br)
        self.mSoundNameOffset = self.baseAddr + br.read_uint32()

        prev_position = br.tell()
        br.seek(self.mSoundNameOffset)
        if self.mSoundNameOffset != 0:
            self.mSoundName = br.read_cstring()
        else:
            self.mSoundName = None
        br.seek(prev_position)

    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<I', determine(self.mSoundNameOffset, self.baseAddr)))
        prev_position = bw.tell()
        bw.seek(self.mSoundNameOffset)
        write_with_padding(self.mSoundName, bw)
        bw.seek(prev_position)

class ParticleEventData(BaseEventData):
    def __init__(self, br: BinaryReader):
        super().__init__(br)
        self.mEffectNameOffset = br.read_addr_at_position(self.baseAddr)
        self.mBoneNameOffset = br.read_addr_at_position(self.baseAddr)
        self.mTargetBoneNameOffset = br.read_addr_at_position(self.baseAddr)
        self.mEndFrame = br.read_float()

        prev_position = br.tell()
        if self.mEffectNameOffset != 0:
            br.seek(self.mEffectNameOffset)
            self.mEffectName = br.read_cstring()
        if self.mBoneNameOffset != 0:
            br.seek(self.mBoneNameOffset)
            self.mBoneName = br.read_cstring()
        if self.mTargetBoneNameOffset != 0:
            br.seek(self.mTargetBoneNameOffset)
            self.mTargetBoneName = br.read_cstring()
        br.seek(prev_position)

    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<i', determine(self.mEffectNameOffset, self.baseAddr)))
        bw.write(struct.pack('<i', determine(self.mBoneNameOffset, self.baseAddr)))
        bw.write(struct.pack('<i', determine(self.mTargetBoneNameOffset, self.baseAddr)))
        bw.write(struct.pack('<f', self.mEndFrame))
        prev_position = bw.tell()
        if self.mEffectNameOffset != 0:
            bw.seek(self.mEffectNameOffset)
            write_with_padding(self.mEffectName, bw)
        if self.mBoneNameOffset != 0:
            bw.seek(self.mBoneNameOffset)
            write_with_padding(self.mBoneName, bw)
        if self.mTargetBoneNameOffset != 0:
            bw.seek(self.mTargetBoneNameOffset)
            write_with_padding(self.mTargetBoneName, bw)
        bw.write(struct.pack('<f', self.mEndFrame))
        bw.seek(prev_position)


class EnableLookAtEventData(BaseEventData):
    def __init__(self, br: BinaryReader):
        super().__init__(br)
        self.mEndFrame = br.read_float()
        self.mEnableLookAt = br.read_uint32()
        self.mLockCurrentValues = br.read_uint32()

    def write(self, bw):
        super().write(bw)
        bw.write(struct.pack('<f', self.mEndFrame))
        bw.write(struct.pack('<I', self.mEnableLookAt))
        bw.write(struct.pack('<I', self.mLockCurrentValues))
