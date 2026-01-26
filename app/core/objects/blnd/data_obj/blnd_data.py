from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from ..function import*
from .event_data import*
from .clip_data import*
from .transition_data import*
import os

@dataclass
class BlendData:
    mFromAnimId: int = 0
    mToAnimId: int = 0
    mBlendFlags: int = 0
    mBlendTime: float = 0

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mFromAnimId))
        write_byte(new_file, get_bytes_uint32(self.mToAnimId))
        write_byte(new_file, get_bytes_uint32(self.mBlendFlags))
        write_byte(new_file, get_bytes_float(self.mBlendTime))

    def get_resource_size(self):
        return 16

@dataclass
class Track_Resource:
    mResourceSize: int = 0
    mBlendWeight: float = 0
    mBlendMode: int = 0
    mIndex: int = 0
    mName: str = None

    def get_start_pos(self, tell):
        self.start_pos = tell

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mResourceSize))
        write_byte(new_file, get_bytes_float(self.mBlendWeight))
        write_byte(new_file, get_bytes_uint32(self.mBlendMode))
        write_byte(new_file, get_bytes_uint32(self.mIndex))
        write_byte(new_file, get_bytes_str(self.mName, 32))

    def get_resource_size(self):
        return 48

@dataclass
class BlnderHeader:
    mEngineType: str = None
    mBinaryBlockType: str = None
    mBinaryBlockVersion: int = 1

    def write(self, new_file):
        write_byte(new_file, self.mEngineType.encode('utf-8'))
        write_byte(new_file, self.mBinaryBlockType.encode('utf-8'))
        write_byte(new_file, get_bytes_uint32(self.mBinaryBlockVersion))

@dataclass
class Path_Record:
    PathHash: int = 0
    PathOffset: int = 0
    Path: str = None

    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.PathHash))
        write_byte(new_file, get_bytes_uint32(self.PathOffset))
        new_file.seek(self.PathOffset + new_file.tell() - 4)
        write_with_padding(self.Path, new_file)

    def to_hash(self):
        return hash_string_fnv1a(self.Path)

@dataclass
class BlnderPool:
    mResourceSize: int = 0
    mFormatToken: int = 1514195421
    mVersion: int = 0
    mNumClasses: int = 0
    mNumBlends: int = 0
    mNumTransitionData: int = 0
    mNumTracks: int = 0
    mNumAnimData: int = 0
    mNumMaskData: int = 0
    mNumEventData: int = 0
    mUseCascadeBlend: bool = False
    mCascadeBlendValue: float = 0.0
    mBlendDataAryAddr: int = 0
    mTransitionDataOffset: int = 0
    mBlendTrackAryAddr: int = 0
    mClassAryAddr: int = 0
    mMaskDataAryAddr: int = 0
    mEventDataAryAddr: int = 0
    mAnimDataAryAddr: int = 0
    mAnimNameCount: int = 0
    mAnimNamesOffset: int = 0
    mSkeleton: Optional[Path_Record] = None
    mExtBuffer: list = field(default_factory=lambda: [0])
    mBlendDataAry: list = field(default_factory=list)
    mTransitionData: list = field(default_factory=list)
    mBlendTrackAry: list = field(default_factory=list)
    mMaskDataAry: list = field(default_factory=list)
    mEventDataAry: list = field(default_factory=list)
    mAnimDataAry: list = field(default_factory=list)
    mClassAry: list = field(default_factory=list)
    mAnimNames: list = field(default_factory=list)

    def get_data_count(self):
        self.mNumClasses=len(self.mClassAry)
        self.mNumBlends=len(self.mBlendDataAry)
        self.mNumTransitionData=len(self.mTransitionData)
        self.mNumTracks=len(self.mBlendTrackAry)
        self.mNumAnimData=len(self.mAnimDataAry)
        self.mNumMaskData=len(self.mMaskDataAry)
        self.mNumEventData=len(self.mEventDataAry)
        self.mAnimNameCount=len(self.mAnimNames)
        
    def write(self, new_file):
        write_byte(new_file, get_bytes_uint32(self.mResourceSize))
        write_byte(new_file, get_bytes_uint32(self.mFormatToken))
        write_byte(new_file, get_bytes_uint32(self.mVersion))
        write_byte(new_file, get_bytes_uint32(self.mNumClasses))
        write_byte(new_file, get_bytes_uint32(self.mNumBlends))
        write_byte(new_file, get_bytes_uint32(self.mNumTransitionData))
        write_byte(new_file, get_bytes_uint32(self.mNumTracks))
        write_byte(new_file, get_bytes_uint32(self.mNumAnimData))
        write_byte(new_file, get_bytes_uint32(self.mNumMaskData))
        write_byte(new_file, get_bytes_uint32(self.mNumEventData))
        write_byte(new_file, get_bytes_uint32(int(self.mUseCascadeBlend)))
        write_byte(new_file, get_bytes_float(self.mCascadeBlendValue))
        write_byte(new_file, get_bytes_int32(determine(self.mBlendDataAryAddr, new_file.tell())))
        write_byte(new_file, get_bytes_int32(determine(self.mTransitionDataOffset, new_file.tell())))
        write_byte(new_file, get_bytes_int32(determine(self.mBlendTrackAryAddr, new_file.tell())))
        write_byte(new_file, get_bytes_int32(determine(self.mClassAryAddr, new_file.tell())))
        write_byte(new_file, get_bytes_int32(determine(self.mMaskDataAryAddr, new_file.tell())))
        write_byte(new_file, get_bytes_int32(determine(self.mEventDataAryAddr, new_file.tell())))
        write_byte(new_file, get_bytes_int32(determine(self.mAnimDataAryAddr, new_file.tell())))
        write_byte(new_file, get_bytes_uint32(self.mAnimNameCount))
        write_byte(new_file, get_bytes_int32(determine(self.mAnimNamesOffset, new_file.tell())))
        write_byte(new_file, get_bytes_uint32(hash_string_fnv1a(self.mSkeleton.Path)))
        write_byte(new_file, get_bytes_int32(self.mSkeleton.PathOffset))
        write_uint32_list(self.mExtBuffer, new_file)
        write_obj_list(self.mBlendDataAry, new_file)
        write_obj_list(self.mTransitionData, new_file)
        for ts in self.mTransitionData:
            write_obj_list(ts.TransitionTo, new_file)
        write_obj_list(self.mBlendTrackAry, new_file)
        write_addr_list_at_baseaddr_class(self.mClassAry, new_file)
        write_obj_list(self.mClassAry, new_file)
        for i in range(len(self.mMaskDataAry)):
            count = len(self.mMaskDataAry)
            offset = count * 4
            if i > 0:
                m = count - i
                for t in range(m):
                    offset += self.mMaskDataAry[t].get_resource_size()
            write_byte(new_file, get_bytes_int32(offset))
        write_obj_list(self.mMaskDataAry, new_file)
        eventdata_offset_ary_pos = new_file.tell()
        for ev in self.mEventDataAry:
            write_byte(new_file, get_bytes_int32(ev - eventdata_offset_ary_pos))
        write_obj_list_or_null(self.mAnimDataAry, new_file)
        for _ in self.mAnimNames:
            write_byte(new_file, get_bytes_uint32(hash_string_fnv1a(_.Path)))
            write_byte(new_file, get_bytes_int32(_.PathOffset))
        for _ in self.mAnimNames:
            write_with_padding(_.Path, new_file)
        write_with_padding(self.mSkeleton.Path, new_file)

    def sync_event(self):
        for _ in self.mClassAry:
            if hasattr(_.mClipData, 'mEventData') and _.mClipData.mEventDataAddr != 0:
                self.mEventDataAry.append(_.mClipData.mEventData.start_pos)
        self.sync_data()
    def sync_data(self):
        self.aligning_data()
        self.get_all_offset()
        get_track_pos(self)
        get_mask_pos(self)
        self.get_data_count()
    def aligning_data(self):
        get_all_resource_size(self.mBlendTrackAry)
        get_all_resource_size(self.mClassAry)
        get_all_resource_size(self.mMaskDataAry)
        str_to_hash_list(self.mAnimNames)

    def get_all_offset(self):
        data_start = 108
        if len(self.mBlendDataAry) > 0:
            self.mBlendDataAryAddr = data_start
            for _ in self.mBlendDataAry:
                data_start += 16
        if len(self.mTransitionData) > 0:
            self.mTransitionDataOffset = data_start
            for _ in self.mTransitionData:
                data_start += 12
                if len(_.TransitionTo) > 0:
                    for k in _.TransitionTo:
                        data_start += 8
            count = len(self.mTransitionData)
            for i in range(count):
                offset = count * 12 - 8
                if i > 0:
                    m = count - i
                    offset = m * 12 - 8
                    for t in range(count - m):
                        offset += self.mTransitionData[t].get_data_size()
                self.mTransitionData[i].aligning_offset(offset)
        if len(self.mBlendTrackAry) > 0:
            self.mBlendTrackAryAddr = data_start
            for _ in self.mBlendTrackAry:
                _.get_start_pos(data_start)
                data_start += 48
        if len(self.mClassAry) > 0:
            self.mClassAryAddr = data_start
            self.mEventDataAry.clear()
            for index, _ in enumerate(self.mClassAry):
                _.aligning_data()
                _.record_start_pos(self.mClassAryAddr + len(self.mClassAry) * 4, self.mClassAry, index)
                if hasattr(_.mClipData, 'mEventData') and _.mClipData.mEventDataAddr != 0:
                    ev = _.mClipData.mEventData
                    ev.mUniqueID = len(self.mEventDataAry)
                    self.mEventDataAry.append(ev.start_pos)
                data_start += _.get_resource_size_and_event() + 4 # dataoffset = 4
        if len(self.mMaskDataAry) > 0:
            self.mMaskDataAryAddr = data_start
            data_start += len(self.mMaskDataAry)*4
            for _ in self.mMaskDataAry:
                _.aligning_data()
                _.get_start_pos(data_start)
                data_start += _.get_resource_size()
        if len(self.mEventDataAry) > 0:
            self.mEventDataAryAddr = data_start
            for _ in self.mEventDataAry:
                data_start += 4
                # _.aligning_data()
        if len(self.mAnimDataAry) > 0:
            self.mAnimDataAryAddr = data_start
            for _ in self.mAnimDataAry:
                if _ is None:
                    data_start += 4
                else:
                    data_start += _.get_resource_size()
        if len(self.mAnimNames) > 0:
            self.mAnimNamesOffset = data_start
            count = len(self.mAnimNames)
            for c in range(count):
                self.mAnimNames[c].PathOffset = (count - c) * 8 - 4
                if c > 0:
                    for d in range(c):
                        self.mAnimNames[c].PathOffset += get_bytes_str_with_padding(self.mAnimNames[d].Path)
            for _ in self.mAnimNames:
                data_start += 8 + get_bytes_str_with_padding(_.Path)
        self.mSkeleton.PathOffset = data_start - 100 # mSkeleton.PathOffset Pos = 100

    def get_track_pos(self):
        for _ in self.mClassAry:
            if hasattr(_.mClipData, 'mTrackDataID'):
                _.mClipData.mTrackDataAddr = self.mBlendTrackAry[_.mClipData.mTrackDataID].start_pos

    def get_mask_pos(self):
        for _ in self.mClassAry:
            if hasattr(_.mClipData, 'mMaskDataID'):
                if _.mClipData.mMaskDataID is not None:
                    _.mClipData.mMaskDataAddr = self.mMaskDataAry[_.mClipData.mMaskDataID].start_pos
    def append_atomicclip_data(self, name, endtick, trackdataid=0, flags=0, event=None,tick_duration=0.03333333507180214,mid=None,path=None,path_index=0):
        pass

    def add_transition_clip_data(self, a, b):
        c = TransitionClipData(a,len(b),TransitionTo=b)
        self.mTransitionData.append(c)
        # 按照FromAnimationID排序，避免顺序错乱
        self.mTransitionData.sort(key=lambda x: x.FromAnimationID)

    def add_transition_data(self, transition_data_map, data_list, value):
        """将 TransitionToData 实例添加到 transition_data_map 中"""
        for i in data_list:
            transition_data_map.append(TransitionToData(i, value))
        transition_data_map.sort(key=lambda x: x.mToAnimId)

    def create_track_data(self,a,b,c):
        d = Track_Resource(mBlendWeight=a,mBlendMode=b,mIndex=len(self.mBlendTrackAry),mName=c)
        self.mBlendTrackAry.append(d)
        self.sync_data()

    def extend_blend_data(self,data_list):
        self.mBlendDataAry.extend(data_list)
        self.sync_data()

    def append_blend_data(self,data):
        self.mBlendDataAry.append(data)
        self.sync_data()

    def append_transition_data(self,data):
        self.mTransitionData.append(data)
        self.mTransitionData.sort(key=lambda x: x.FromAnimationID)
        self.sync_data()

    def append_class(self,flags,name,data):
        self.mClassAry.append(ClipResource(mFlags=flags,mUniqueID=len(self.mClassAry),mName=name,mClipData=data))
        self.sync_data()

    def create_atomic_clip(self,a,b,c=0.03333333507180214,d=0,e=0,event=None,mid=None,path=None,syncgroupname=None):
        b = AtomicClip(mEndTick=b,mAnimDataIndex=len(self.mAnimNames),mTrackDataID=d,mEventData=event,mTickDuration=c,mMaskDataID=mid,mSyncGroupName=syncgroupname)
        c = ClipResource(mFlags=e,mUniqueID=len(self.mClassAry),mName=a,mClipData=b)
        self.mAnimDataAry.append(None)
        self.mAnimNames.append(Path_Record(Path=path))
        self.mClassAry.append(c)
        self.sync_data()

@dataclass
class BlnderData:
    header: Optional[BlnderHeader] = None
    pool: Optional[BlnderPool] = None

    def write(self, new_file):
        write_obj(self.header, new_file)
        write_obj(self.pool, new_file)