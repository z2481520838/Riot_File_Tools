from ....build import*
from .....core.function.general import get_relative_path, extract_number
from .event_type_info_card import (Blnk_Event_Type_Info_Card, Sound_Event_Type_Info_Card, Particle_Event_Type_Info_Card,
                                   Submesh_Event_Type_Info_Card, Fade_Event_Type_Info_Card, JointSnap_Event_Type_Info_Card,
                                   EnableLookAt_Event_Type_Info_Card)

class Event_Edit_Card_Blnk(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

class Event_Edit_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.event_type_info_cards = []
        self.build()

    def show_current_event_extra_info(self, data):
        selected_index = self.event_type_box.currentIndex()
        if selected_index == 0:
            self.clear_all_type_info_text_box()
        else:
            self.event_type_info_cards[selected_index].show_event_info(data)

    def clear_all_type_info_text_box(self):
        for _ in self.event_type_info_cards:
            _.clear_text_box()

    def selector_event_type(self):
        selected_index = self.event_type_box.currentIndex()
        for i, card in enumerate(self.event_type_info_cards):
            # 只显示当前选中的卡片，其他卡片隐藏
            card.setVisible(i == selected_index)

    def build_type_layout(self):
        type_layout = QHBoxLayout(self)
        self.event_name_box = create_text_box(self, "Name: ", type_layout)
        event_type_items = ["None","Sound","Particle","Submesh","Fade","JointSnap","EnableLookAt"]
        self.event_type_box = create_combo_box(self, "Type: ", "选择事件类型", event_type_items, type_layout, self.selector_event_type)
        self.layout.addLayout(type_layout)
        type_layout.setStretch(0, 2)
        type_layout.setStretch(1, 1)

    def build_value_layout(self):
        value_layout = QHBoxLayout(self)
        self.event_flags_box = create_text_box(self, "Flags: ", value_layout)
        self.event_frame_box = create_text_box(self, "Frame: ", value_layout)
        self.layout.addLayout(value_layout)

    def build_type_info_layout(self):
        self.blnk_event_type_info_card = create_child_card(Blnk_Event_Type_Info_Card(self), self.layout, self.event_type_info_cards) #blnk
        self.sound_event_type_info_card = create_child_card(Sound_Event_Type_Info_Card(self), self.layout, self.event_type_info_cards, False)
        self.particle_event_type_info_card = create_child_card(Particle_Event_Type_Info_Card(self), self.layout, self.event_type_info_cards, False)
        self.submesh_event_type_info_card = create_child_card(Submesh_Event_Type_Info_Card(self), self.layout, self.event_type_info_cards, False)
        self.fade_event_type_info_card = create_child_card(Fade_Event_Type_Info_Card(self), self.layout, self.event_type_info_cards, False)
        self.jointsnap_event_type_info_card = create_child_card(JointSnap_Event_Type_Info_Card(self), self.layout, self.event_type_info_cards, False)
        self.enablelookat_event_type_info_card = create_child_card(EnableLookAt_Event_Type_Info_Card(self), self.layout, self.event_type_info_cards, False)

    def build(self):
        self.build_type_layout()
        self.build_value_layout()
        self.build_type_info_layout()

    def show_event_info(self, event):
        self.event_name_box.setText(event.mName)
        self.event_type_box.setCurrentIndex(event.mEventTypeId)
        self.event_flags_box.setText(f"{event.mFlags}")
        self.event_frame_box.setText(f"{event.mFrame}")

    def create_event_data(self,selected_event):
        name = self.event_name_box.text()
        e_type = self.event_type_box.currentIndex()
        flags = extract_number(self.event_flags_box.text())
        frame = extract_number(self.event_frame_box.text())
        selected_event.setText(name)
        return self.event_type_info_cards[e_type].create_event_data(name, e_type, flags, frame)