from ...build import*
from ....core.objects.blnd.data_obj.clip_data import ParallelClip
from ....core.function.general import get_relative_path, extract_number

class ParallelClip_Edit_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()
        self.parallel_pair_list = []
        self.parallel_pair_listwidget = ListWidget(self)
        self.parallel_pair_listwidget.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义右键菜单
        self.parallel_pair_listwidget.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键菜单事件

    def build(self):
        parallel_clip_edit_layout = QHBoxLayout()
        parallel_pair_list_layout = QVBoxLayout()
        parallel_pair_info_layout = QVBoxLayout()
        parallel_pair_info_button_layout = QHBoxLayout()
        self.parallel_clip_clipflag_box = create_text_box(self, "ClipFlag: ", parallel_pair_list_layout)
        parallel_pair_list_card = CardWidget(self)
        self.parallel_pair_list_card_layout = QVBoxLayout(parallel_pair_list_card)
        parallel_pair_list_card.setLayout(self.parallel_pair_list_card_layout)

        self.parallel_pair_info_blnk_card = CardWidget(self)
        parallel_pair_info_blnk_card_layout = QVBoxLayout(self.parallel_pair_info_blnk_card)
        empty_label = QLabel("Please select or add a piece of data.", self)
        parallel_pair_info_blnk_card_layout.addWidget(empty_label)
        parallel_pair_info_blnk_card_layout.addStretch()
        self.parallel_pair_info_blnk_card.setLayout(parallel_pair_info_blnk_card_layout)
        
        
        self.parallel_pair_info_card = CardWidget(self)
        parallel_pair_info_card_layout = QVBoxLayout(self.parallel_pair_info_card)
        self.clipid_box = create_text_box(self, "ClipID: ", parallel_pair_info_card_layout)
        parallel_pair_info_card_layout.addStretch()
        self.parallel_pair_info_card.setLayout(parallel_pair_info_card_layout)
        self.parallel_pair_info_card.setVisible(False)
        
        new_parallel_pair = PrimaryPushButton("新建数据", self)
        new_parallel_pair.clicked.connect(self.create_new_parallel_pair)
        save_parallel_pair = PrimaryPushButton("保存数据", self)
        save_parallel_pair.clicked.connect(self.save_parallel_pair_data)
        unselect_parallel_pair = PushButton("取消选中", self)
        unselect_parallel_pair.clicked.connect(self.unselect_parallel_pair)
        parallel_pair_info_button_layout.addStretch()
        parallel_pair_info_button_layout.addWidget(new_parallel_pair)
        parallel_pair_info_button_layout.addWidget(save_parallel_pair)
        parallel_pair_info_button_layout.addWidget(unselect_parallel_pair)

        parallel_pair_list_layout.addWidget(parallel_pair_list_card)
        parallel_pair_info_layout.addWidget(self.parallel_pair_info_blnk_card)
        parallel_pair_info_layout.addWidget(self.parallel_pair_info_card)
        parallel_pair_info_layout.addLayout(parallel_pair_info_button_layout)
        parallel_clip_edit_layout.addLayout(parallel_pair_list_layout)
        parallel_clip_edit_layout.addLayout(parallel_pair_info_layout)

        self.layout.addLayout(parallel_clip_edit_layout)


    def save_parallel_pair_data(self):
        current_index = self.parallel_pair_listwidget.currentIndex().row()
        current_data = self.parallel_pair_listwidget.currentItem()
        new_data = extract_number(self.clipid_box.text())
        self.parallel_pair_list[current_index] = new_data
        current_data.setData(Qt.UserRole, new_data)
        self.unselect_parallel_pair()

    def create_new_parallel_pair(self):
        item = QListWidgetItem(f"Pairs Data {len(self.parallel_pair_list)}")
        parallel_pair = 0
        self.parallel_pair_list.append(parallel_pair)#这里要改
        item.setData(Qt.UserRole, parallel_pair)
        self.parallel_pair_listwidget.addItem(item)
        self.parallel_pair_list_card_layout.addWidget(self.parallel_pair_listwidget)
        self.selected_parallel_pair(item)
        self.parallel_pair_listwidget.itemClicked.connect(self.show_current_parallel_pair_info)

    def selected_parallel_pair(self, item):
        self.parallel_pair_listwidget.setCurrentItem(item)
        self.show_current_parallel_pair_info(item)

    def show_current_parallel_pair_info(self, item):
        self.parallel_pair_info_card.setVisible(True)
        self.parallel_pair_info_blnk_card.setVisible(False)
        parallel_pair_data = self.parallel_pair_listwidget.currentItem().data(Qt.UserRole)
        self.clipid_box.setText(f"{parallel_pair_data}")

    def unselect_parallel_pair(self):
        self.parallel_pair_listwidget.clearSelection()
        self.parallel_pair_info_card.setVisible(False)
        self.parallel_pair_info_blnk_card.setVisible(True)
        self.clipid_box.clear()

    def show_context_menu(self, pos):
        item = self.parallel_pair_listwidget.itemAt(pos)  # 获取当前点击的项目
        if item:
            menu = RoundMenu(parent=self)  # 创建菜单
            delete_data_action = Action(FIF.DELETE, 'Delete', self)  # 创建菜单项
            delete_data_action.triggered.connect(lambda: self.delete_data(item))  # 点击时触发
            menu.addAction(delete_data_action)  # 添加菜单项
            menu.exec_(self.parallel_pair_listwidget.mapToGlobal(pos))  # 显示菜单

    def delete_data(self, item):
        pass

    def create_clip_data(self, pool, name, flag):
        clip_data = ParallelClip(mClipFlag=extract_number(self.parallel_clip_clipflag_box.text()),
                                 mNumClips=len(self.parallel_pair_list),
                                 mClipsIDArr=self.parallel_pair_list)
        pool.append_class(flag, name, clip_data)