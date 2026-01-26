import os
import re
import tkinter as tk
from tkinter import filedialog

def convert_to_hex_and_split(number):
    """
    将大整数转换为十六进制字符串并拆分为两部分。
    :param number: 要转换的大整数
    :return: 两个十六进制部分（每部分8个字符）
    """
    hex_str = hex(number)[2:].lower()  # 转换为十六进制并去掉 '0x'
    hex_str = hex_str.zfill(16)  # 确保16进制字符串有16位

    # 拆分成两部分，每部分8个字符
    part1 = hex_str[:8]
    part2 = hex_str[8:]

    return part1, part2

def load_data_from_file(filename='hashes.binhashes.txt'):
    """
    从文件中加载数据，将十六进制值和名称存储在字典中
    :param filename: 文件名，默认为 'hashes.binhashes.txt'
    :return: 字典，键为十六进制值，值为对应的名称
    """
    data_dict = {}
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()  # 去掉每行的前后空格
                if not line or len(line.split()) != 2:  # 跳过空行或格式不正确的行
                    continue
                try:
                    hex_part, name = line.split()
                    data_dict[hex_part.lower()] = name  # 使用小写十六进制值作为字典的键
                except ValueError:
                    # 如果行内没有两个值，则跳过该行
                    print(f"Skipping invalid line: {line}")
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
    except Exception as e:
        print(f"An error occurred while loading the file: {e}")
    
    return data_dict

def lookup(hex_value, data_dict):
    """
    查找十六进制值对应的名称。
    :param hex_value: 十六进制值
    :param data_dict: 存储十六进制值和名称的字典
    :return: 对应的名称，如果没有找到返回 'Unknown'
    """
    return data_dict.get(hex_value.lower(), f"Unknown ({hex_value})")

def replace_large_numbers_in_text(text, data_dict):
    """
    替换文本中的所有大数为格式：大数 // 名称1, 名称2
    :param text: 原始文本
    :param data_dict: 存储十六进制值和名称的字典
    :return: 替换后的文本
    """
    # 匹配包含 TransitionClipBlendData 或 TimeBlendData 的行，并且这些行之前是大数
    pattern = r"(\d+)(?=\s*=\s*(TransitionClipBlendData|TimeBlendData))"

    def replacer(match):
        num_str = match.group(1)
        num = int(num_str)

        # 拆分大数为两个十六进制部分
        part1, part2 = convert_to_hex_and_split(num)

        # 查找对应的名称
        name1 = lookup(part1, data_dict)
        name2 = lookup(part2, data_dict)

        # 返回替换后的格式
        return f"{num_str}    // {name1}, {name2}"

    # 替换文本中的所有匹配项
    return re.sub(pattern, replacer, text)

def select_file():
    """
    打开文件选择对话框，允许用户选择输入文件
    :return: 用户选择的文件路径
    """
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    file_path = filedialog.askopenfilename(title="选择要处理的文本文件", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")))
    return file_path

def main():
    """
    主函数，读取文件，处理大数并替换
    """
    # 获取当前脚本的路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建目标文件路径
    target_file_path = os.path.join(script_dir, 'hashes_table', 'hashes.binhashes.txt')

    # 读取文件中的数据到字典
    data_dict = load_data_from_file(target_file_path)

    # 如果字典为空，表示文件读取失败或没有数据
    if not data_dict:
        print("No data available for lookup.")
        return

    # 让用户选择要处理的输入文件
    input_file_path = select_file()

    if not input_file_path:
        print("没有选择输入文件，退出程序。")
        return

    try:
        with open(input_file_path, 'r', encoding='utf-8') as input_file:
            text = input_file.read()

        # 执行替换操作
        replaced_text = replace_large_numbers_in_text(text, data_dict)

        # 自动在原文件的目录下生成一个输出文件
        output_file_path = os.path.splitext(input_file_path)[0] + "_replaced.py"

        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(replaced_text)

        print(f"替换完成！已保存至: {output_file_path}")

    except FileNotFoundError:
        print(f"Error: The file '{input_file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
