from ....build import*
from .....core.function.general import get_relative_path, extract_number
from .event_edit_card import Event_Edit_Card, Event_Edit_Card_Blnk
from .....core.function.blnd.create_blnd import create_new_project, create_event_resource

class EventData_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        self.event_resource_data = []
        self.event_list = ListWidget(self)
        self.event_list.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义右键菜单
        self.event_list.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键菜单事件
        self.build()

    def get_event_resource(self, pool):
        if len(self.event_resource_data) > 0:
            e_id = len(pool.mEventDataAry)
            return create_event_resource(self.event_resource_data, self.parent().parent().class_name_box.text(), e_id)
        return None

    def build_event_resource_layout(self):
        event_resource_layout = QVBoxLayout(self)
        self.event_resource_name_box = create_text_box(self, "EventName: ", event_resource_layout)
        self.event_map_layout = QVBoxLayout(self)
        event_resource_card = CardWidget(self)
        event_resource_card.setLayout(self.event_map_layout)
        event_resource_layout.addWidget(event_resource_card)
        self.layout.addLayout(event_resource_layout)

    def create_new_event(self):
        item = QListWidgetItem("New Event")
        event = self.event_edit_card.blnk_event_type_info_card.create_event_data("New Event", 0, 0, 0)
        self.event_resource_data.append(event)#这里要改
        item.setData(Qt.UserRole, event)
        self.event_list.addItem(item)
        self.event_map_layout.addWidget(self.event_list)
        self.selected_event(item)
        self.event_list.itemClicked.connect(self.show_current_event_info)

    def selected_event(self, item):
        self.event_list.setCurrentItem(item)
        self.show_current_event_info(item)

    def show_current_event_info(self, item):
        """参考selector_type"""
        self.blnk_event_info_card.setVisible(False)
        self.event_edit_card.setVisible(True)
        selected_data = self.event_list.currentItem().data(Qt.UserRole)
        self.event_edit_card.show_event_info(selected_data)
        self.event_edit_card.show_current_event_extra_info(selected_data)

    def save_event_data(self):
        selected_index = self.event_list.currentIndex().row()
        selected_event = self.event_list.currentItem()
        new_event = self.event_edit_card.create_event_data(selected_event)
        self.event_resource_data[selected_index] = new_event
        selected_event.setData(Qt.UserRole, new_event)

    def unselect_event(self):
        self.event_list.clearSelection()
        self.event_edit_card.setVisible(False)
        self.blnk_event_info_card.setVisible(True)
        self.event_edit_card.clear_all_type_info_text_box()

    def build_event_info_button(self,layout):
        event_button_layout = QHBoxLayout(self)
        new_event = PrimaryPushButton("新建事件", self)
        new_event.clicked.connect(self.create_new_event)
        save_event = PrimaryPushButton("保存数据", self)
        save_event.clicked.connect(self.save_event_data)
        unselect_event = PushButton("取消选中", self)
        unselect_event.clicked.connect(self.unselect_event)
        event_button_layout.addStretch()
        event_button_layout.addWidget(new_event)
        event_button_layout.addWidget(save_event)
        event_button_layout.addWidget(unselect_event)
        layout.addLayout(event_button_layout)

    def build_event_info_layout(self):
        event_info_layout = QVBoxLayout(self)
        self.blnk_event_info_card = create_child_card(Event_Edit_Card_Blnk(self), event_info_layout) #blnk
        self.event_edit_card = create_child_card(Event_Edit_Card(self), event_info_layout, None, False)
        self.build_event_info_button(event_info_layout)
        self.layout.addLayout(event_info_layout)

    def build(self):
        self.build_event_resource_layout()
        self.build_event_info_layout()
        self.layout.setStretch(0, 2)
        self.layout.setStretch(1, 3)


    def show_context_menu(self, pos):
        item = self.event_list.itemAt(pos)  # 获取当前点击的项目
        if item:
            menu = RoundMenu(parent=self)  # 创建菜单
            delete_data_action = Action(FIF.DELETE, 'Delete', self)  # 创建菜单项
            delete_data_action.triggered.connect(lambda: self.delete_data(item))  # 点击时触发
            menu.addAction(delete_data_action)  # 添加菜单项
            menu.exec_(self.event_list.mapToGlobal(pos))  # 显示菜单

    def delete_data(self, item):
        pass
