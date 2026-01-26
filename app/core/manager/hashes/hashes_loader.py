from PySide6.QtCore import Qt, QObject, Signal, Slot
from qfluentwidgets import InfoBar, StateToolTip, IndeterminateProgressRing, InfoBarIcon, InfoBarPosition
import threading
import sys
from ....components.wait_bar import WaitBar
from .hashes_manager import GLOBAL_HASH_MANAGER

class HashLoadSignal(QObject):
    finished = Signal(object)
    failed = Signal(str)

hash_load_signals = HashLoadSignal()

def load_hashes_worker():
    try:
        GLOBAL_HASH_MANAGER.start_load_hashes()
        hash_load_signals.finished.emit(GLOBAL_HASH_MANAGER)
        
    except Exception as e:
        hash_load_signals.failed.emit(f"哈希表加载失败: {e}")

def start_hash_loading_flow(window):

    @Slot(object)
    def finalize_load(manager_instance):
        if manager_instance:
            window.load_bar.update_data(InfoBarIcon.SUCCESS, "成功:", "喜大普奔,哈希表已加载完毕!", 2000)
    @Slot(str)
    def handle_load_failure(error_message):
        window.load_bar.update_data(InfoBarIcon.ERROR, "错误:", error_message, 2000)

    hash_load_signals.finished.connect(finalize_load)
    hash_load_signals.failed.connect(handle_load_failure)
    window.load_bar = WaitBar("等待", "正在加载哈希表,稍安勿躁......", window)
    window.load_bar.show()

    thread = threading.Thread(target=load_hashes_worker)
    thread.start()