import sys
import struct
from .path_record import*
from .blend_data import*
from .binary_reader_extensions import*
from .track_resource import*
from .transitionclip_data import*
from .mask_resource import*
from .resource import*
from .binary_reader import*
from .event_resource import*
from .animation_resource import*
from .clip_resource import*
from .function import*

class PoolData(Resource):
    def __init__(self, br: BinaryReader):
        super().__init__(br)
        self.mFormatToken = br.read_uint32()
        self.mVersion = br.read_uint32()
        self.mNumClasses = br.read_uint32()
        self.mNumBlends = br.read_uint32()
        self.mNumTransitionData = br.read_uint32()
        self.mNumTracks = br.read_uint32()
        self.mNumAnimData = br.read_uint32()
        self.mNumMaskData = br.read_uint32()
        self.mNumEventData = br.read_uint32()
        self.mUseCascadeBlend = br.read_uint32() != 0
        self.mCascadeBlendValue = br.read_float()

        self.mBlendDataAryAddr = br.read_addr()
        self.mTransitionDataOffset = br.read_addr()
        self.mBlendTrackAryAddr = br.read_addr()
        self.mClassAryAddr = br.read_addr()
        self.mMaskDataAryAddr = br.read_addr()
        self.mEventDataAryAddr = br.read_addr()
        self.mAnimDataAryAddr = br.read_addr()
        self.mAnimNameCount = br.read_uint32()
        self.mAnimNamesOffset = br.read_addr()

        self.mSkeleton = br.read(PathRecord)
        self.mExtBuffer = [br.read_uint32()]
        self.mBlendDataAry = []
        self.mTransitionData = []
        self.mBlendTrackAry = []
        self.mMaskDataAry = []
        self.mEventDataAry = []
        self.mAnimDataAry = []
        self.mClassAry = []
        self.mAnimNames = []
        if self.mNumBlends != 0:
            self.mBlendDataAry = br.read_arr(self.mBlendDataAryAddr, self.mNumBlends, lambda br: br.read(BlendData))
        if self.mNumTransitionData != 0:
            self.mTransitionData = br.read_arr(self.mTransitionDataOffset, self.mNumTransitionData, lambda br: br.read(TransitionClipData))
        if self.mNumTracks != 0:
            self.mBlendTrackAry = br.read_arr(self.mBlendTrackAryAddr, self.mNumTracks, lambda br: br.read(TrackResource))
        if self.mNumMaskData != 0:
            self.mMaskDataAry = br.read_arr2(self.mMaskDataAryAddr, self.mNumMaskData, lambda br: br.read(MaskResource))
        if self.mNumEventData != 0:
            self.mEventDataAry = br.read_arr2(self.mEventDataAryAddr, self.mNumEventData, lambda br: br.read(EventResource))
        if self.mNumAnimData != 0:
            self.mAnimDataAry = br.read_arr2(self.mAnimDataAryAddr, self.mNumAnimData, lambda br: AnimResourceBase.read(br))
        if self.mNumClasses != 0:
            self.mClassAry = br.read_arr2(self.mClassAryAddr, self.mNumClasses, lambda br: br.read(ClipResource))
        if self.mAnimNameCount != 0:
            self.mAnimNames = br.read_arr(self.mAnimNamesOffset, self.mAnimNameCount, lambda br: br.read(PathRecord))

    def test(self, a, b):
        if a > 0:
            return a - b
        return 0
        
    def write(self, bw):
        # super().write(bw)
        bw.write(struct.pack('<I', 0))
        bw.write(struct.pack('<I', self.mFormatToken))
        bw.write(struct.pack('<I', self.mVersion))
        # 写入其他字段
        bw.write(struct.pack('<I', len(self.mClassAry)))
        bw.write(struct.pack('<I', len(self.mBlendDataAry)))
        bw.write(struct.pack('<I', len(self.mTransitionData)))
        bw.write(struct.pack('<I', len(self.mBlendTrackAry)))
        bw.write(struct.pack('<I', len(self.mAnimDataAry)))
        bw.write(struct.pack('<I', len(self.mMaskDataAry)))
        bw.write(struct.pack('<I', len(self.mEventDataAry)))
        bw.write(struct.pack('<I', int(self.mUseCascadeBlend)))
        bw.write(struct.pack('<f', self.mCascadeBlendValue))

        bw.write(struct.pack('<i', self.test(self.mBlendDataAryAddr, bw.tell())))
        bw.write(struct.pack('<i', self.test(self.mTransitionDataOffset, bw.tell())))
        bw.write(struct.pack('<i', self.test(self.mBlendTrackAryAddr, bw.tell())))
        bw.write(struct.pack('<i', self.test(self.mClassAryAddr, bw.tell())))
        bw.write(struct.pack('<i', self.test(self.mMaskDataAryAddr, bw.tell())))
        bw.write(struct.pack('<i', self.test(self.mEventDataAryAddr, bw.tell())))
        bw.write(struct.pack('<i', self.test(self.mAnimDataAryAddr, bw.tell())))
        bw.write(struct.pack('<I', self.mAnimNameCount))
        bw.write(struct.pack('<i', self.test(self.mAnimNamesOffset, bw.tell())))
        bw.write(struct.pack('<I', self.mSkeleton.pathHash))
        bw.write(struct.pack('<i', self.test(self.mSkeleton.pathOffset, bw.tell())))
        for ext in self.mExtBuffer:
            bw.write(struct.pack('<I', ext))

        # 写入数组地址和数据
        self.write_array(bw, self.mBlendDataAry)
        self.write_array(bw, self.mTransitionData)
        bw.seek(self.mBlendTrackAryAddr)
        self.write_array(bw, self.mBlendTrackAry)
        bw.seek(self.mClassAryAddr)
        for _ in self.mClassAry:
            bw.write(struct.pack('<i', _.baseAddr - self.mClassAryAddr))
        self.write_array(bw, self.mClassAry)
        
        # return_tell = bw.tell()
        bw.seek(self.mMaskDataAryAddr)
        for _ in self.mMaskDataAry:
            # print(f"{_.baseAddr - self.mMaskDataAryAddr}")
            bw.write(struct.pack('<i', _.baseAddr - self.mMaskDataAryAddr))
        # bw.seek(return_tell)
        for a in self.mMaskDataAry:
            bw.seek(a.baseAddr)
            a.write(bw)
            # self.write_array(bw, self.mMaskDataAry)
        bw.seek(self.mEventDataAryAddr)
        for _ in self.mEventDataAry:
            bw.write(struct.pack('<i', (_.baseAddr - bw.tell()) + (bw.tell() - self.mEventDataAryAddr)))
        bw.seek(self.mAnimDataAryAddr)
        self.write_array(bw, self.mAnimDataAry)
        bw.seek(self.mAnimNamesOffset)
        for _ in self.mAnimNames:
            bw.write(struct.pack('<I', _.pathHash))
            bw.write(struct.pack('<I', _.pathOffset - bw.tell()))
        for a in self.mAnimNames:
            write_with_padding(a.path, bw)
        write_with_padding(self.mSkeleton.path, bw)
        """
        self.write_array(bw, self.mEventDataAry)
        for ui in self.mExtBuffer:
            bw.write(struct.pack('<I', ui))"""

    def write_array(self, bw, arr):
        for item in arr:
            if item:
                item.write(bw)