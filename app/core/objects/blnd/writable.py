from abc import ABC, abstractmethod
import io

# 定义一个抽象类 Writable，要求所有继承类实现 write 方法
class Writable(ABC):
    @abstractmethod
    def write(self, bw: io.BytesIO) -> None:
        pass  # 强制子类实现这个方法