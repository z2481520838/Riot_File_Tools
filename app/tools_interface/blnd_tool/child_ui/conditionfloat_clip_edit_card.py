from ...build import*
from ....core.objects.blnd.data_obj.clip_data import ConditionFloatPairData, ConditionFloatClip
from ....core.function.general import get_relative_path, extract_number

class ConditionFloatClip_Edit_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.condition_float_pair_list = []
        self.condition_float_pair_listwidget = ListWidget(self)
        self.condition_float_pair_listwidget.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义右键菜单
        self.condition_float_pair_listwidget.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键菜单事件
        self.build()

    def build(self):
        condition_float_clip_id_data_layout = QHBoxLayout()
        condition_float_clip_edit_layout = QHBoxLayout()
        condition_float_pair_list_layout = QVBoxLayout()
        condition_float_pair_info_layout = QVBoxLayout()
        condition_float_pair_info_button_layout = QHBoxLayout()
        self.condition_float_clip_trackindex_box = create_text_box(self, "TrackIndex: ", condition_float_clip_id_data_layout)
        self.condition_float_clip_trackindex_box.setText("0")
        self.condition_float_clip_updatertype_box = create_text_box(self, "UpdaterType: ", condition_float_clip_id_data_layout)
        self.condition_float_clip_updatertype_box.setText("0")
        self.condition_float_clip_changeanimationmidplay_box = CheckBox("ChangeAnimationMidPlay",self)
        condition_float_clip_id_data_layout.addStretch()
        condition_float_clip_id_data_layout.addWidget(self.condition_float_clip_changeanimationmidplay_box)

        condition_float_pair_list_card = CardWidget(self)
        self.condition_float_pair_list_card_layout = QVBoxLayout(condition_float_pair_list_card)
        condition_float_pair_list_card.setLayout(self.condition_float_pair_list_card_layout)
        self.condition_float_pair_list_card_layout.addWidget(self.condition_float_pair_listwidget)

        self.condition_float_pair_info_blnk_card = CardWidget(self)
        condition_float_pair_info_blnk_card_layout = QVBoxLayout(self.condition_float_pair_info_blnk_card)
        empty_label = QLabel("Please select or add a piece of data.", self)
        condition_float_pair_info_blnk_card_layout.addWidget(empty_label)
        condition_float_pair_info_blnk_card_layout.addStretch()
        self.condition_float_pair_info_blnk_card.setLayout(condition_float_pair_info_blnk_card_layout)

        self.condition_float_pair_info_card = CardWidget(self)
        condition_float_pair_info_card_layout = QVBoxLayout(self.condition_float_pair_info_card)
        self.clipid_box = create_text_box(self, "ClipID: ", condition_float_pair_info_card_layout)
        self.value_box = create_text_box(self, "Value: ", condition_float_pair_info_card_layout)
        
        condition_float_pair_info_card_layout.addStretch()
        self.condition_float_pair_info_card.setLayout(condition_float_pair_info_card_layout)
        self.condition_float_pair_info_card.setVisible(False)
        
        new_condition_float_pair = PrimaryPushButton("新建数据", self)
        new_condition_float_pair.clicked.connect(self.create_new_condition_float_pair)
        save_condition_float_pair = PrimaryPushButton("保存数据", self)
        save_condition_float_pair.clicked.connect(self.save_condition_float_pair_data)
        unselect_condition_float_pair = PushButton("取消选中", self)
        unselect_condition_float_pair.clicked.connect(self.unselect_condition_float_pair)
        condition_float_pair_info_button_layout.addStretch()
        condition_float_pair_info_button_layout.addWidget(new_condition_float_pair)
        condition_float_pair_info_button_layout.addWidget(save_condition_float_pair)
        condition_float_pair_info_button_layout.addWidget(unselect_condition_float_pair)

        condition_float_pair_list_layout.addWidget(condition_float_pair_list_card)
        condition_float_pair_info_layout.addWidget(self.condition_float_pair_info_blnk_card)
        condition_float_pair_info_layout.addWidget(self.condition_float_pair_info_card)
        condition_float_pair_info_layout.addLayout(condition_float_pair_info_button_layout)
        condition_float_clip_edit_layout.addLayout(condition_float_pair_list_layout)
        condition_float_clip_edit_layout.addLayout(condition_float_pair_info_layout)
        condition_float_clip_edit_layout.setStretch(0, 1)  # name_layout 拉伸因子为 1
        condition_float_clip_edit_layout.setStretch(1, 1)  # type_layout 拉伸因子为 1
        self.layout.addLayout(condition_float_clip_id_data_layout)
        self.layout.addLayout(condition_float_clip_edit_layout)

    def save_condition_float_pair_data(self):
        current_index = self.condition_float_pair_listwidget.currentIndex().row()
        current_data = self.condition_float_pair_listwidget.currentItem()
        clipid = extract_number(self.clipid_box.text())
        value = extract_number(self.value_box.text())
        new_data = ConditionFloatPairData(clipid, value)
        self.condition_float_pair_list[current_index] = new_data
        current_data.setData(Qt.UserRole, new_data)
        self.unselect_condition_float_pair()

    def create_new_condition_float_pair(self):
        item = QListWidgetItem(f"ConditionFloatPairData {len(self.condition_float_pair_list)}")
        condition_float_pair = ConditionFloatPairData()
        self.condition_float_pair_list.append(condition_float_pair)
        item.setData(Qt.UserRole, condition_float_pair)
        self.condition_float_pair_listwidget.addItem(item)
        self.selected_condition_float_pair(item)
        self.condition_float_pair_listwidget.itemClicked.connect(self.show_current_condition_float_pair_info)

    def selected_condition_float_pair(self, item):
        self.condition_float_pair_listwidget.setCurrentItem(item)
        self.show_current_condition_float_pair_info(item)

    def show_current_condition_float_pair_info(self, item):
        self.condition_float_pair_info_card.setVisible(True)
        self.condition_float_pair_info_blnk_card.setVisible(False)
        condition_float_pair_data = self.condition_float_pair_listwidget.currentItem().data(Qt.UserRole)
        self.clipid_box.setText(f"{condition_float_pair_data.mClipID}")
        self.value_box.setText(f"{condition_float_pair_data.mValue}")

    def unselect_condition_float_pair(self):
        self.condition_float_pair_listwidget.clearSelection()
        self.condition_float_pair_info_card.setVisible(False)
        self.condition_float_pair_info_blnk_card.setVisible(True)
        self.clear_all_lineedit()

    def clear_all_lineedit(self):
        self.clipid_box.clear()
        self.value_box.clear()

    def show_context_menu(self, pos):
        item = self.condition_float_pair_listwidget.itemAt(pos)  # 获取当前点击的项目
        if item:
            menu = RoundMenu(parent=self)  # 创建菜单
            delete_data_action = Action(FIF.DELETE, 'Delete', self)  # 创建菜单项
            delete_data_action.triggered.connect(lambda: self.delete_data(item))  # 点击时触发
            menu.addAction(delete_data_action)  # 添加菜单项
            menu.exec_(self.condition_float_pair_listwidget.mapToGlobal(pos))  # 显示菜单

    def delete_data(self, item):
        pass

    def create_clip_data(self, pool, name, flag):
        track_id = extract_number(self.condition_float_clip_trackindex_box.text())
        updater_type = extract_number(self.condition_float_clip_updatertype_box.text())
        changeanimationmidplay = self.condition_float_clip_changeanimationmidplay_box.isChecked()
        clip_data = ConditionFloatClip(mTrackIndex=track_id,
                                      mNumPairs=len(self.condition_float_pair_list),
                                      mUpdaterType=updater_type,
                                      mChangeAnimationMidPlay=changeanimationmidplay,
                                      mConditionFloatPairDataList=self.condition_float_pair_list)
        pool.append_class(flag, name, clip_data)