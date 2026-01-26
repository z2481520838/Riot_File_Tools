import tkinter as tk
from tkinter import filedialog
import os

MAX_DIFFS = 99999      # 最多打印多少个差异
BLOCK_SIZE = 4096  # 块读取，兼顾性能和精度


def choose_file(title):
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title=title)
    return path


def diff_binary(file1, file2):
    size1 = os.path.getsize(file1)
    size2 = os.path.getsize(file2)

    print(f'File A: {file1}')
    print(f'File B: {file2}')
    print(f'Size A: {size1} bytes')
    print(f'Size B: {size2} bytes')
    print('-' * 60)

    diffs = 0
    offset = 0

    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        while True:
            b1 = f1.read(BLOCK_SIZE)
            b2 = f2.read(BLOCK_SIZE)

            if not b1 or not b2:
                if b1 != b2:
                    print(f'[!] File length differs at offset 0x{offset:X}')
                break

            if b1 != b2:
                for i, (x, y) in enumerate(zip(b1, b2)):
                    if x != y:
                        abs_offset = offset + i
                        print(
                            f'Offset 0x{abs_offset:08X}: '
                            f'{x:02X} -> {y:02X}'
                        )
                        diffs += 1

            offset += BLOCK_SIZE

    if diffs == 0 and size1 == size2:
        print('✅ Files are IDENTICAL')
    else:
        print('-' * 60)
        print(f'❌ Total diffs found: {diffs}')


def main():
    print('Select first binary file...')
    file1 = choose_file('Select first binary file')
    if not file1:
        print('Canceled.')
        return

    print('Select second binary file...')
    file2 = choose_file('Select second binary file')
    if not file2:
        print('Canceled.')
        return

    print()
    diff_binary(file1, file2)


if __name__ == '__main__':
    main()
