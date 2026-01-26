from ...build import*
from ....core.objects.blnd.data_obj.clip_data import ParametricPairData, ParametricClip
from ....core.function.general import get_relative_path, extract_number

class ParametricClip_Edit_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()
        self.condition_float_pair_list = []
        self.condition_float_pair_listwidget = ListWidget(self)
        self.condition_float_pair_listwidget.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义右键菜单
        self.condition_float_pair_listwidget.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键菜单事件

    def build(self):
        parametric_clip_id_data_layout = QHBoxLayout()
        parametric_clip_edit_layout = QHBoxLayout()
        parametric_pair_list_layout = QVBoxLayout()
        parametric_pair_info_layout = QVBoxLayout()
        parametric_pair_info_button_layout = QHBoxLayout()
        self.parametric_clip_updatertype_box = create_text_box(self, "UpdaterType: ", parametric_clip_id_data_layout)
        self.parametric_clip_updatertype_box.setText("0")
        self.build_mask_data_check_box(parametric_clip_id_data_layout)
        self.build_track_data_check_box(parametric_clip_id_data_layout)
        parametric_clip_id_data_layout.setStretch(0, 1)
        parametric_clip_id_data_layout.setStretch(1, 1)
        parametric_clip_id_data_layout.setStretch(2, 1)
        parametric_pair_list_card = CardWidget(self)
        self.parametric_pair_list_card_layout = QVBoxLayout(parametric_pair_list_card)
        parametric_pair_list_card.setLayout(self.parametric_pair_list_card_layout)

        self.parametric_pair_info_blnk_card = CardWidget(self)
        parametric_pair_info_blnk_card_layout = QVBoxLayout(self.parametric_pair_info_blnk_card)
        empty_label = QLabel("Please select or add a piece of data.", self)
        parametric_pair_info_blnk_card_layout.addWidget(empty_label)
        parametric_pair_info_blnk_card_layout.addStretch()
        self.parametric_pair_info_blnk_card.setLayout(parametric_pair_info_blnk_card_layout)

        self.parametric_pair_info_card = CardWidget(self)
        parametric_pair_info_card_layout = QVBoxLayout(self.parametric_pair_info_card)
        self.clipid_box = create_text_box(self, "ClipID: ", parametric_pair_info_card_layout)
        self.value_box = create_text_box(self, "Value: ", parametric_pair_info_card_layout)
        parametric_pair_info_card_layout.addStretch()
        self.parametric_pair_info_card.setLayout(parametric_pair_info_card_layout)
        self.parametric_pair_info_card.setVisible(False)
        
        new_parametric_pair = PrimaryPushButton("新建数据", self)
        new_parametric_pair.clicked.connect(self.create_new_parametric_pair)
        save_parametric_pair = PrimaryPushButton("保存数据", self)
        save_parametric_pair.clicked.connect(self.save_parametric_pair_data)
        unselect_parametric_pair = PushButton("取消选中", self)
        unselect_parametric_pair.clicked.connect(self.unselect_parametric_pair)
        parametric_pair_info_button_layout.addStretch()
        parametric_pair_info_button_layout.addWidget(new_parametric_pair)
        parametric_pair_info_button_layout.addWidget(save_parametric_pair)
        parametric_pair_info_button_layout.addWidget(unselect_parametric_pair)

        parametric_pair_list_layout.addWidget(parametric_pair_list_card)
        parametric_pair_info_layout.addWidget(self.parametric_pair_info_blnk_card)
        parametric_pair_info_layout.addWidget(self.parametric_pair_info_card)
        parametric_pair_info_layout.addLayout(parametric_pair_info_button_layout)
        parametric_clip_edit_layout.addLayout(parametric_pair_list_layout)
        parametric_clip_edit_layout.addLayout(parametric_pair_info_layout)
        parametric_clip_edit_layout.setStretch(0, 1)  # name_layout 拉伸因子为 1
        parametric_clip_edit_layout.setStretch(1, 1)  # type_layout 拉伸因子为 1
        self.layout.addLayout(parametric_clip_id_data_layout)
        self.layout.addLayout(parametric_clip_edit_layout)

    def build_mask_data_check_box(self,layout):
        mask_data_layout = QHBoxLayout()
        mask_data_lable = QLabel("MaskData: ", self)
        mask_data_lable.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.mask_data_check_box = ComboBox(self)
        for t in self.parent().parent().current_blnder_data.pool.mMaskDataAry:
            data_name = t.mName
            self.mask_data_check_box.addItem(data_name, userData=t)
        self.mask_data_check_box.currentTextChanged.connect(self.selector_mask_data)
        self.mask_data_check_box.setPlaceholderText("None")
        self.mask_data_check_box.setCurrentIndex(-1)
        mask_data_layout.addWidget(mask_data_lable)
        mask_data_layout.addWidget(self.mask_data_check_box)
        layout.addLayout(mask_data_layout)

    def selector_mask_data(self):
        selected_index = self.mask_data_check_box.currentIndex()

    def build_track_data_check_box(self,layout):
        track_data_layout = QHBoxLayout()
        track_data_lable = QLabel("TrackData: ", self)
        track_data_lable.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.track_data_check_box = ComboBox(self)
        for t in self.parent().parent().current_blnder_data.pool.mBlendTrackAry:
            data_name = t.mName
            self.track_data_check_box.addItem(data_name, userData=t)
        self.track_data_check_box.currentTextChanged.connect(self.selector_track_data)
        self.track_data_check_box.setCurrentIndex(0)
        track_data_layout.addWidget(track_data_lable)
        track_data_layout.addWidget(self.track_data_check_box)
        layout.addLayout(track_data_layout)

    def selector_track_data(self):
        selected_index = self.track_data_check_box.currentIndex()

    def save_parametric_pair_data(self):
        current_index = self.condition_float_pair_listwidget.currentIndex().row()
        current_data = self.condition_float_pair_listwidget.currentItem()
        clipid = extract_number(self.clipid_box.text())
        probability = extract_number(self.value_box.text())
        new_data = ParametricPairData(clipid, probability)
        self.condition_float_pair_list[current_index] = new_data
        current_data.setData(Qt.UserRole, new_data)
        self.unselect_parametric_pair()

    def create_new_parametric_pair(self):
        item = QListWidgetItem(f"ConditionFloatPairData {len(self.condition_float_pair_list)}")
        parametric_pair = ParametricPairData(0, 0)
        self.condition_float_pair_list.append(parametric_pair)
        item.setData(Qt.UserRole, parametric_pair)
        self.condition_float_pair_listwidget.addItem(item)
        self.parametric_pair_list_card_layout.addWidget(self.condition_float_pair_listwidget)
        self.selected_parametric_pair(item)
        self.condition_float_pair_listwidget.itemClicked.connect(self.show_current_parametric_pair_info)

    def selected_parametric_pair(self, item):
        self.condition_float_pair_listwidget.setCurrentItem(item)
        self.show_current_parametric_pair_info(item)

    def show_current_parametric_pair_info(self, item):
        self.parametric_pair_info_card.setVisible(True)
        self.parametric_pair_info_blnk_card.setVisible(False)
        parametric_pair_data = self.condition_float_pair_listwidget.currentItem().data(Qt.UserRole)
        self.clipid_box.setText(f"{parametric_pair_data.mClipID}")
        self.value_box.setText(f"{parametric_pair_data.mValue}")

    def unselect_parametric_pair(self):
        self.condition_float_pair_listwidget.clearSelection()
        self.parametric_pair_info_card.setVisible(False)
        self.parametric_pair_info_blnk_card.setVisible(True)
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
        updater_type = extract_number(self.parametric_clip_updatertype_box.text())
        mask_id = self.mask_data_check_box.currentIndex() if self.mask_data_check_box.currentIndex() > -1 else None
        track_id = self.track_data_check_box.currentIndex() if self.track_data_check_box.currentIndex() > -1 else None
        sorted_condition_data_pairs = sorted(self.condition_float_pair_list, key=lambda x: x.mValue)
        clip_data = ParametricClip(mNumPairs=len(sorted_condition_data_pairs),
                                   mUpdaterType=updater_type,
                                   mMaskDataID=mask_id,
                                   mTrackDataID=track_id,
                                   mConditionFloatPairDataList=sorted_condition_data_pairs)
        pool.append_class(flag, name, clip_data)