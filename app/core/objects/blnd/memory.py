import struct
from typing import List
from .writable import*
from typing import List, Optional, Callable, Dict

class Memory:
    class MemoryMode:
        SizeEstimation = 1
        Writing = 2

    class Record:
        def __init__(self):
            self.addr = -1
            self.size = -1
            self.allocate = False

    # Initialize the memory state
    mode = None  # This will hold the current memory mode (SizeEstimation or Writing)
    memory: Dict[object, 'Memory.Record'] = {}

    @staticmethod
    def write(bw: io.BufferedWriter, wobj: Optional[Writable]):
        if wobj is None:
            return
        
        # Get the record for the object in memory
        record = Memory.memory.get(wobj)
        
        if Memory.mode == Memory.MemoryMode.SizeEstimation:
            if record is None:
                # Allocate a new record for the object
                record = Memory.Record()
                Memory.memory[wobj] = record
                prev_position = bw.tell()
                wobj.write(bw)
                record.size = bw.tell() - prev_position
            else:
                # Just write the object directly
                wobj.write(bw)
        else:
            if record is None:
                raise Exception("The object must be allocated at the previous stage")
            wobj.write(bw)

    @staticmethod
    def allocate(offset: int, wobj: Optional[Writable]):
        if wobj is None:
            return 0
        return Memory._allocate(offset, wobj, wobj.write)

    @staticmethod
    def allocate_string(offset: int, sobj: Optional[str]):
        if sobj is None:
            return 0
        return Memory._allocate(offset, sobj, lambda bw: Memory.write_cstring(bw, sobj))

    @staticmethod
    def allocate_array(offset: int, array: Optional[List[Writable]]):
        if array is None:
            return 0
        return Memory._allocate(offset, array, lambda bw: [obj.write(bw) for obj in array])

    @staticmethod
    def allocate_array2(offset: int, array: Optional[List[Writable]], base_addr: Optional[int] = None):
        if array is None:
            return 0
        return Memory._allocate(offset, array, lambda bw: Memory._allocate_array2_helper(bw, array, base_addr))

    @staticmethod
    def _allocate_array2_helper(bw, array, base_addr):
        addr = base_addr or bw.tell()
        for item in array:
            Memory.allocate(addr, item)
            addr += 4  # Assuming each item takes 4 bytes; adjust accordingly

    @staticmethod
    def _allocate(offset: int, obj: object, ctr: Callable[[io.BufferedWriter], None]):
        if obj is None:
            return 0

        # Get the record for the object in memory
        record = Memory.memory.get(obj)
        
        if Memory.mode == Memory.MemoryMode.SizeEstimation:
            if record is None:
                record = Memory.Record()
                Memory.memory[obj] = record
                prev_position = bw.tell()
                ctr(bw)
                record.size = bw.tell() - prev_position
                bw.seek(prev_position)  # Rewind the stream
            record.allocate = True
            return 0
        else:
            if record is None:
                raise Exception("The object must be allocated at the previous stage")
            if record.allocate:
                record.allocate = False
                prev_position = bw.tell()
                bw.seek(record.addr)  # Seek to the record address
                ctr(bw)
                bw.seek(prev_position)  # Rewind the stream
            return record.addr - offset

    @staticmethod
    def size_of(obj: object) -> int:
        if Memory.mode == Memory.MemoryMode.SizeEstimation:
            return 0
        else:
            record = Memory.memory.get(obj)
            if record is None:
                raise Exception("The object must be allocated at the previous stage")
            return record.size

    @staticmethod
    def process(ctr: Callable[[io.BufferedWriter], None]) -> bytearray:
        with io.BytesIO() as ms:
            with io.BufferedWriter(ms) as bw:
                Memory.mode = Memory.MemoryMode.SizeEstimation
                ctr(bw)
                
                addr = 0
                # Update addresses for all allocated records
                for record in Memory.memory.values():
                    if record.allocate:
                        record.addr = addr
                        addr += record.size

                Memory.mode = Memory.MemoryMode.Writing
                bw.seek(0)
                ctr(bw)
                
                return ms.getvalue()

    @staticmethod
    def write_cstring(bw: io.BufferedWriter, string: str):
        """Writes a null-terminated string."""
        bw.write(string.encode('utf-8') + b'\0')

