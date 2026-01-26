from ...build import*
from ....core.objects.blnd.data_obj.clip_data import SequencerClip
from ....core.function.general import get_relative_path, extract_number

class SequencerClip_Edit_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()
        self.sequencer_pair_list = []
        self.sequencer_pair_listwidget = ListWidget(self)
        self.sequencer_pair_listwidget.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义右键菜单
        self.sequencer_pair_listwidget.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键菜单事件

    def build(self):
        sequencer_clip_edit_layout = QHBoxLayout()
        sequencer_pair_list_layout = QVBoxLayout()
        sequencer_pair_info_layout = QVBoxLayout()
        sequencer_pair_info_button_layout = QHBoxLayout()
        self.sequencer_clip_trackid_box = create_text_box(self, "TrackIndex: ", sequencer_pair_list_layout)
        sequencer_pair_list_card = CardWidget(self)
        self.sequencer_pair_list_card_layout = QVBoxLayout(sequencer_pair_list_card)
        sequencer_pair_list_card.setLayout(self.sequencer_pair_list_card_layout)

        self.sequencer_pair_info_blnk_card = CardWidget(self)
        sequencer_pair_info_blnk_card_layout = QVBoxLayout(self.sequencer_pair_info_blnk_card)
        empty_label = QLabel("Please select or add a piece of data.", self)
        sequencer_pair_info_blnk_card_layout.addWidget(empty_label)
        sequencer_pair_info_blnk_card_layout.addStretch()
        self.sequencer_pair_info_blnk_card.setLayout(sequencer_pair_info_blnk_card_layout)
        
        
        self.sequencer_pair_info_card = CardWidget(self)
        sequencer_pair_info_card_layout = QVBoxLayout(self.sequencer_pair_info_card)
        self.clipid_box = create_text_box(self, "ClipID: ", sequencer_pair_info_card_layout)
        sequencer_pair_info_card_layout.addStretch()
        self.sequencer_pair_info_card.setLayout(sequencer_pair_info_card_layout)
        self.sequencer_pair_info_card.setVisible(False)
        
        new_sequencer_pair = PrimaryPushButton("新建数据", self)
        new_sequencer_pair.clicked.connect(self.create_new_sequencer_pair)
        save_sequencer_pair = PrimaryPushButton("保存数据", self)
        save_sequencer_pair.clicked.connect(self.save_sequencer_pair_data)
        unselect_sequencer_pair = PushButton("取消选中", self)
        unselect_sequencer_pair.clicked.connect(self.unselect_sequencer_pair)
        sequencer_pair_info_button_layout.addStretch()
        sequencer_pair_info_button_layout.addWidget(new_sequencer_pair)
        sequencer_pair_info_button_layout.addWidget(save_sequencer_pair)
        sequencer_pair_info_button_layout.addWidget(unselect_sequencer_pair)

        sequencer_pair_list_layout.addWidget(sequencer_pair_list_card)
        sequencer_pair_info_layout.addWidget(self.sequencer_pair_info_blnk_card)
        sequencer_pair_info_layout.addWidget(self.sequencer_pair_info_card)
        sequencer_pair_info_layout.addLayout(sequencer_pair_info_button_layout)
        sequencer_clip_edit_layout.addLayout(sequencer_pair_list_layout)
        sequencer_clip_edit_layout.addLayout(sequencer_pair_info_layout)

        self.layout.addLayout(sequencer_clip_edit_layout)


    def save_sequencer_pair_data(self):
        current_index = self.sequencer_pair_listwidget.currentIndex().row()
        current_data = self.sequencer_pair_listwidget.currentItem()
        new_data = extract_number(self.clipid_box.text())
        self.sequencer_pair_list[current_index] = new_data
        current_data.setData(Qt.UserRole, new_data)
        self.unselect_sequencer_pair()

    def create_new_sequencer_pair(self):
        item = QListWidgetItem(f"Pairs Data {len(self.sequencer_pair_list)}")
        sequencer_pair = 0
        self.sequencer_pair_list.append(sequencer_pair)#这里要改
        item.setData(Qt.UserRole, sequencer_pair)
        self.sequencer_pair_listwidget.addItem(item)
        self.sequencer_pair_list_card_layout.addWidget(self.sequencer_pair_listwidget)
        self.selected_sequencer_pair(item)
        self.sequencer_pair_listwidget.itemClicked.connect(self.show_current_sequencer_pair_info)

    def selected_sequencer_pair(self, item):
        self.sequencer_pair_listwidget.setCurrentItem(item)
        self.show_current_sequencer_pair_info(item)

    def show_current_sequencer_pair_info(self, item):
        self.sequencer_pair_info_card.setVisible(True)
        self.sequencer_pair_info_blnk_card.setVisible(False)
        sequencer_pair_data = self.sequencer_pair_listwidget.currentItem().data(Qt.UserRole)
        self.clipid_box.setText(f"{sequencer_pair_data}")

    def unselect_sequencer_pair(self):
        self.sequencer_pair_listwidget.clearSelection()
        self.sequencer_pair_info_card.setVisible(False)
        self.sequencer_pair_info_blnk_card.setVisible(True)
        self.clipid_box.clear()

    def show_context_menu(self, pos):
        item = self.sequencer_pair_listwidget.itemAt(pos)  # 获取当前点击的项目
        if item:
            menu = RoundMenu(parent=self)  # 创建菜单
            delete_data_action = Action(FIF.DELETE, 'Delete', self)  # 创建菜单项
            delete_data_action.triggered.connect(lambda: self.delete_data(item))  # 点击时触发
            menu.addAction(delete_data_action)  # 添加菜单项
            menu.exec_(self.sequencer_pair_listwidget.mapToGlobal(pos))  # 显示菜单

    def delete_data(self, item):
        pass

    def create_clip_data(self, pool, name, flag):
        clip_data = SequencerClip(mTrackIndex=extract_number(self.sequencer_clip_trackid_box.text()),
                                  mNumPairs=len(self.sequencer_pair_list),
                                  mPairsIDArr=self.sequencer_pair_list)
        pool.append_class(flag, name, clip_data)