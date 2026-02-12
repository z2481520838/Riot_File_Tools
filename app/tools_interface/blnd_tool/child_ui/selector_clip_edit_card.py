from ...build import*
from ....core.objects.blnd.data_obj.clip_data import SelectorPairData, SelectorClip
from ....core.function.general import get_relative_path, extract_number

class SelectorClip_Edit_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.selector_pair_list = []
        self.selector_pair_listwidget = ListWidget(self)
        self.selector_pair_listwidget.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义右键菜单
        self.selector_pair_listwidget.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键菜单事件
        self.build()

    def build(self):
        selector_clip_edit_layout = QHBoxLayout()
        selector_pair_list_layout = QVBoxLayout()
        selector_pair_info_layout = QVBoxLayout()
        selector_pair_info_button_layout = QHBoxLayout()
        self.selector_clip_trackid_box = create_text_box(self, "TrackIndex: ", selector_pair_list_layout)
        selector_pair_list_card = CardWidget(self)
        self.selector_pair_list_card_layout = QVBoxLayout(selector_pair_list_card)
        selector_pair_list_card.setLayout(self.selector_pair_list_card_layout)
        self.selector_pair_list_card_layout.addWidget(self.selector_pair_listwidget)

        self.selector_pair_info_blnk_card = CardWidget(self)
        selector_pair_info_blnk_card_layout = QVBoxLayout(self.selector_pair_info_blnk_card)
        empty_label = QLabel("Please select or add a piece of data.", self)
        selector_pair_info_blnk_card_layout.addWidget(empty_label)
        selector_pair_info_blnk_card_layout.addStretch()
        self.selector_pair_info_blnk_card.setLayout(selector_pair_info_blnk_card_layout)

        self.selector_pair_info_card = CardWidget(self)
        selector_pair_info_card_layout = QVBoxLayout(self.selector_pair_info_card)
        self.clipid_box = create_text_box(self, "ClipID: ", selector_pair_info_card_layout)
        self.probability_box = create_text_box(self, "Probability: ", selector_pair_info_card_layout)
        selector_pair_info_card_layout.addStretch()
        self.selector_pair_info_card.setLayout(selector_pair_info_card_layout)
        self.selector_pair_info_card.setVisible(False)
        
        new_selector_pair = PrimaryPushButton("新建数据", self)
        new_selector_pair.clicked.connect(self.create_new_selector_pair)
        save_selector_pair = PrimaryPushButton("保存数据", self)
        save_selector_pair.clicked.connect(self.save_selector_pair_data)
        unselect_selector_pair = PushButton("取消选中", self)
        unselect_selector_pair.clicked.connect(self.unselect_selector_pair)
        selector_pair_info_button_layout.addStretch()
        selector_pair_info_button_layout.addWidget(new_selector_pair)
        selector_pair_info_button_layout.addWidget(save_selector_pair)
        selector_pair_info_button_layout.addWidget(unselect_selector_pair)

        selector_pair_list_layout.addWidget(selector_pair_list_card)
        selector_pair_info_layout.addWidget(self.selector_pair_info_blnk_card)
        selector_pair_info_layout.addWidget(self.selector_pair_info_card)
        selector_pair_info_layout.addLayout(selector_pair_info_button_layout)
        selector_clip_edit_layout.addLayout(selector_pair_list_layout)
        selector_clip_edit_layout.addLayout(selector_pair_info_layout)

        self.layout.addLayout(selector_clip_edit_layout)

    def save_selector_pair_data(self):
        current_index = self.selector_pair_listwidget.currentIndex().row()
        current_data = self.selector_pair_listwidget.currentItem()
        clipid = extract_number(self.clipid_box.text())
        probability = extract_number(self.probability_box.text())
        new_data = SelectorPairData(clipid, probability)
        self.selector_pair_list[current_index] = new_data
        current_data.setData(Qt.UserRole, new_data)
        self.unselect_selector_pair()

    def create_new_selector_pair(self):
        item = QListWidgetItem(f"Selector Pair {len(self.selector_pair_list)}")
        selector_pair = SelectorPairData(0, 0)
        self.selector_pair_list.append(selector_pair)#这里要改
        item.setData(Qt.UserRole, selector_pair)
        self.selector_pair_listwidget.addItem(item)
        self.selected_selector_pair(item)
        self.selector_pair_listwidget.itemClicked.connect(self.show_current_selector_pair_info)

    def selected_selector_pair(self, item):
        self.selector_pair_listwidget.setCurrentItem(item)
        self.show_current_selector_pair_info(item)

    def show_current_selector_pair_info(self, item):
        self.selector_pair_info_card.setVisible(True)
        self.selector_pair_info_blnk_card.setVisible(False)
        selector_pair_data = self.selector_pair_listwidget.currentItem().data(Qt.UserRole)
        self.clipid_box.setText(f"{selector_pair_data.mClipID}")
        self.probability_box.setText(f"{selector_pair_data.mProbability}")

    def unselect_selector_pair(self):
        self.selector_pair_listwidget.clearSelection()
        self.selector_pair_info_card.setVisible(False)
        self.selector_pair_info_blnk_card.setVisible(True)
        self.clear_all_lineedit()

    def clear_all_lineedit(self):
        self.clipid_box.clear()
        self.probability_box.clear()

    def show_context_menu(self, pos):
        item = self.selector_pair_listwidget.itemAt(pos)  # 获取当前点击的项目
        if item:
            menu = RoundMenu(parent=self)  # 创建菜单
            delete_data_action = Action(FIF.DELETE, 'Delete', self)  # 创建菜单项
            delete_data_action.triggered.connect(lambda: self.delete_data(item))  # 点击时触发
            menu.addAction(delete_data_action)  # 添加菜单项
            menu.exec_(self.selector_pair_listwidget.mapToGlobal(pos))  # 显示菜单

    def delete_data(self, item):
        pass

    def create_clip_data(self, pool, name, flag):
        clip_data = SelectorClip(mTrackIndex=extract_number(self.selector_clip_trackid_box.text()),
                                 mNumPairs=len(self.selector_pair_list),
                                 mSelectorPairDataArr=self.selector_pair_list)
        pool.append_class(flag, name, clip_data)