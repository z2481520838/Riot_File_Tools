from ...build import*
from ....core.objects.blnd.data_obj.clip_data import MultiChildClip
from ....core.function.general import get_relative_path, extract_number

class MultiChildClip_Edit_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

    def create_clip_data(self, pool, name, flag):
        pass