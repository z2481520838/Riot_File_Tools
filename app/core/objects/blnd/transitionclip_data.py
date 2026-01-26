import struct
from typing import List
from .writable import*

class TransitionClipData(Writable):
    class TransitionToData(Writable):
        def __init__(self, br):
            self.mToAnimId = br.read_uint32()
            # print(f"{self.mToAnimId}")
            self.mTransitionAnimId = br.read_uint32()
            # print(f"{self.mTransitionAnimId}")

        def write(self, bw):
            # 写入数据
            bw.write(struct.pack('<I', self.mToAnimId))
            bw.write(struct.pack('<I', self.mTransitionAnimId))

    def __init__(self, br):
        """"找到TransitionToCount和offset之后,跳到实际位置循环查找TransitionToCount个TransitionToData,最后跳回原位置"""
        self.FromAnimationID = br.read_uint32()  # Reading FromAnimationID
        self.TransitionToCount = br.read_uint32()  # Reading TransitionToCount
        # 重点关注这里
        self.TransitionToOffsetAddr = br.tell()
        # Iterating over each TransitionTo and reading it
        self.TransitionToOffset = br.read_uint32()  # Calculate the offset by adding the current position and the read offset
        return_offset = br.tell()  # Store the current position
        self.TransitionToArrayAddr = self.TransitionToOffsetAddr + self.TransitionToOffset
        br.seek(self.TransitionToArrayAddr)  # Seek to the calculated offset
        self.TransitionTo = []
        # print(f"{return_offset}")
        # print(f"{TransitionToArrayAddr}")
        for _ in range(self.TransitionToCount):
            self.TransitionTo.append(self.TransitionToData(br))  # Add TransitionToData object to the list
        br.seek(return_offset)  # Seek back to the original position

    """def __init__(self, br):
        self.mFromAnimId = br.read_uint32()
        self.mTransitionToCount = br.read_uint32()
        
        # 读取从当前位置开始的 mTransitionToArray
        mOffsetFromSelf = br.read_uint32()
        self.mTransitionToArray = []

        # 读取 TransitionToData 数组
        # for _ in range(self.mTransitionToCount):
            # self.mTransitionToArray.append(self.TransitionToData(br))"""

    def write(self, bw):
        # 写入 TransitionClipData 数据
        bw.write(struct.pack('<I', self.FromAnimationID))
        bw.write(struct.pack('<I', self.TransitionToCount))
        pre_addr = bw.tell()
        # 假设偏移量是通过 mOffsetFromSelf 计算的，这里只写死一个值
        bw.write(struct.pack('<I', self.TransitionToOffset))  # mOffsetFromSelf
        # print(f"{self.TransitionToOffset}")
        return_offset = bw.tell()  # Store the current position
        data_addr = pre_addr + self.TransitionToOffset
        bw.seek(data_addr)  # Seek to the calculated offset
        # 写入 TransitionToData 数组
        for transition_to in self.TransitionTo:
            transition_to.write(bw)
        bw.seek(return_offset)  # Seek back to the original position
