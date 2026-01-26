import os
from ...objects.prop_text.prop_text_obj import Entries
from ...objects.prop_text.charData_obj import CharacterRecord
from ...objects.prop_text.spellData_obj import SpellObject
from ...objects.prop_text.vfxData_obj import VfxSystemDefinitionData
from PySide6.QtWidgets import QFileDialog, QApplication
from qfluentwidgets import (InfoBar)

def remove_name(text: str) -> str:
    """去掉第一行，用于预览"""
    lines = text.splitlines()
    if len(lines) > 1:
        return "\n".join(lines[1:])
    return ""  # 如果文本只有一行或为空，则返回空

def export_object(obj, entries_obj, folder, filename_attr, ext):
    """导出单个对象为文件"""
    # 获取文件名
    base_name = getattr(obj, filename_attr, None)
    if not base_name:
        return False  # 没有名字，跳过

    # 生成文本
    text = remove_name(obj.to_custom_format(entries_obj))

    # 处理非法字符
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in base_name)

    file_name = f"{safe_name}{ext}"
    file_path = os.path.join(folder, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    return True

def export_all_file(ui):
    """
    导出 entries 中的所有 VfxSystemDefinitionData / SpellObject / CharacterRecord
    """
    prop_file = ui.current_prop
    if not prop_file:
        InfoBar.info("提示:", "无内容可导出,请先转换", parent=ui)
        return

    folder = QFileDialog.getExistingDirectory(ui, "选择导出目录")
    if not folder:
        InfoBar.info("提示:", "导出已取消", parent=ui)
        return

    try:
        count = 0
        entries_obj = Entries(items=prop_file.entries)

        # 定义类型与其对应参数的映射表
        type_config = {
            VfxSystemDefinitionData: ("particleName", ".troy"),
            SpellObject: ("mScriptName", ".ini"),
            CharacterRecord: ("mCharacterName", ".ini")
        }

        # 简化后的循环逻辑
        for key, obj in prop_file.entries.items():
            # 获取该对象类型对应的配置，如果不在映射表中则返回 None
            config = type_config.get(type(obj))
            
            if config:
                attr_name, extension = config
                # 执行导出逻辑，如果成功则计数加 1
                if export_object(obj, entries_obj, folder, attr_name, extension):
                    count += 1

        InfoBar.success("成功", f"导出 {count} 个文件 到 {folder}", parent=ui)
    except Exception as e:
        InfoBar.error("导出失败:", f"{e}", parent=ui)

def export_file(ui):
    if not ui.current_prop:
        InfoBar.info("提示:", "没有内容可导出", parent=ui)
        return
    file_path, _ = QFileDialog.getSaveFileName(ui, "保存导出文件", "", "Ini Files (*.ini);;All Files (*.*)")
    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(ui.outputBox.toPlainText().strip())
            InfoBar.success("已导出文件:", f"{file_path}", parent=ui)
        except Exception as e:
            InfoBar.error("导出失败:", f"{e}", parent=ui)
    else:
        InfoBar.info("提示:", "导出已取消", parent=ui)

def copy_output(ui):
    if not ui.current_prop:
        InfoBar.info("提示:", "没有内容可复制", parent=ui)
        return
    QApplication.clipboard().setText(ui.outputBox.toPlainText().strip())
    InfoBar.success("", "结果已复制到剪贴板", parent=ui)

def clear_input(ui):
    if not ui.current_prop:
        InfoBar.info("提示:", "暂未发现输入", parent=ui)
        return
    ui.inputBox.clear()

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_')).rstrip()
