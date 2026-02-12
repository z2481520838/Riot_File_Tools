from ..build import*
from ...core.objects.blnd.data_obj.transition_data import TransitionToData, TransitionClipData
from ...core.objects.blnd.data_obj.blnd_data import Path_Record, BlendData, Track_Resource
from ...core.function.blnd.create_blnd import create_new_project, create_event_resource
from ...core.function.general import get_relative_path, extract_number, fnv1a
from ...core.objects.animation.read_anm import read_anm_file
from .child_ui.atomic_clip_edit.atomic_clip_edit_card import AtomicClip_Edit_Card
from .child_ui.selector_clip_edit_card import SelectorClip_Edit_Card
from .child_ui.sequencer_clip_edit_card import SequencerClip_Edit_Card
from .child_ui.parallel_clip_edit_card import ParallelClip_Edit_Card
from .child_ui.multichild_clip_edit_card import MultiChildClip_Edit_Card
from .child_ui.parametric_clip_edit_card import ParametricClip_Edit_Card
from .child_ui.conditionbool_clip_edit_card import ConditionBoolClip_Edit_Card
from .child_ui.conditionfloat_clip_edit_card import ConditionFloatClip_Edit_Card

class Blnk_Clip_Edit_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

    def create_clip_data(self, pool, name, flag):
        pass

class Create_Clip_Card_Interface(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()

    def build_info_layout(self, layout):
        info_layout = QHBoxLayout()
        name_layout = QHBoxLayout()
        type_layout = QHBoxLayout()
        flag_layout = QHBoxLayout()
        name_lable = QLabel("数据名称: ", self)
        name_lable.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.class_name_box = LineEdit(self)
        name_layout.addWidget(name_lable)
        name_layout.addWidget(self.class_name_box)

        type_lable = QLabel("数据类型: ", self)
        type_lable.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.type_box = ComboBox(self)
        self.type_box.setPlaceholderText("选择类型: ")
        type_items = ['Invalid', 'Atomic', 'Selector', 'Sequencer', 'Parallel', 'MultiChildClip', 'Parametric', 'ConditionBool', 'ConditionFloat']
        self.type_box.addItems(type_items)
        self.type_box.setCurrentIndex(-1)
        self.type_box.currentTextChanged.connect(self.selector_type)
        type_layout.addWidget(type_lable)
        type_layout.addWidget(self.type_box)

        flag_lable = QLabel("数据标志: ", self)
        flag_lable.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.class_flag_box = LineEdit(self)
        flag_layout.addWidget(flag_lable)
        flag_layout.addWidget(self.class_flag_box)
        info_layout.addLayout(name_layout)
        info_layout.addLayout(type_layout)
        info_layout.addLayout(flag_layout)
        info_layout.setStretch(0, 2)
        info_layout.setStretch(1, 1)
        info_layout.setStretch(2, 1)
        layout.addLayout(info_layout)

    def selector_type(self):
        selected_index = self.type_box.currentIndex()
        for i, card in enumerate(self.cards):
            card.setVisible(i == selected_index)

    def build_clip_layout(self, layout):
        self.cards = []
        self.blak_data_card = create_child_card(Blnk_Clip_Edit_Card(self), self.layout, self.cards)
        self.atomic_data_card = create_child_card(AtomicClip_Edit_Card(self), self.layout, self.cards, False)
        self.selector_data_card = create_child_card(SelectorClip_Edit_Card(self), self.layout, self.cards, False)
        self.sequencer_data_card = create_child_card(SequencerClip_Edit_Card(self), self.layout, self.cards, False)
        self.parallel_data_card = create_child_card(ParallelClip_Edit_Card(self), self.layout, self.cards, False)
        self.multichild_data_card = create_child_card(MultiChildClip_Edit_Card(self), self.layout, self.cards, False)
        self.parametric_clip_card = create_child_card(ParametricClip_Edit_Card(self), self.layout, self.cards, False)
        self.condition_bool_clip_card = create_child_card(ConditionBoolClip_Edit_Card(self), self.layout, self.cards, False)
        self.condition_float_clip_card = create_child_card(ConditionFloatClip_Edit_Card(self), self.layout, self.cards, False)

    def build(self):
        self.build_info_layout(self.layout)
        self.build_clip_layout(self.layout)

    def create_of_type(self, parent, itype):
        pool = parent.current_blnder_data.pool
        name = self.class_name_box.text()
        flag = extract_number(self.class_flag_box.text())
        # 将卡片添加到列表，根据itype来获取准确的卡片，并统一命名create
        self.cards[itype].create_clip_data(pool, name, flag)
        parent.show_blnd_data(parent.current_blnder_data)

    def save_data(self):
        parent = self.parent_widget
        self.create_of_type(parent, self.type_box.currentIndex())

    def on_set(self):
        pass

class Edit_Pool_Card_Interface(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()

    def build_cascade_blend_data_layout(self, layout):
        cascade_blend_data_layout = QHBoxLayout()
        self.use_cascade_blend_box = CheckBox("UseCascadeBlend", self)
        cascade_blend_data_layout.addWidget(self.use_cascade_blend_box)
        cascade_blend_data_layout.addStretch()
        self.cascade_blend_value_box = create_text_box(self, "CascadeBlendValue: ", cascade_blend_data_layout)
        layout.addLayout(cascade_blend_data_layout)

    def build_skeleton_data_layout(self, layout):
        skeleton_data_layout = QHBoxLayout()
        self.skeleton_path_box = create_text_box(self, "Skeleton: ", skeleton_data_layout)
        self.get_skeleton_button = PrimaryPushButton("选择文件", self)
        self.get_skeleton_button.clicked.connect(self.get_skeleton_path_from_dialog)
        self.get_skeleton_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        skeleton_data_layout.addWidget(self.get_skeleton_button)
        layout.addLayout(skeleton_data_layout)

    def get_skeleton_path_from_dialog(self):
        last_skeleton_file = self.parent_widget.path_logger.get("skeleton_file")
        default_directory = "" if last_skeleton_file is None else os.path.dirname(last_skeleton_file)
        file, _ = QFileDialog.getOpenFileName(self, "选择文件", default_directory, "Skl Files (*.skl)")
        self.get_skeleton_path(file)

    def get_skeleton_path(self, file):
        if not file:
            return
        try:
            self.parent_widget.path_logger.save("skeleton_file", file)
            path = get_relative_path(file, "DATA").lower()
            self.skeleton_path_box.setText(path)
            InfoBar.success(
                title="已加载文件: ",
                content=f"{file}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self.parent_widget
            )
        except Exception as e:
            InfoBar.error("错误", f"文件读取失败: {e}", parent=self.parent_widget)

    def build(self):
        create_text_label(self, "PoolData: ", self.layout)
        self.build_cascade_blend_data_layout(self.layout)
        self.build_skeleton_data_layout(self.layout)
        self.layout.addStretch()

    def save_data(self):
        pool = self.parent_widget.current_blnder_data.pool
        pool.mUseCascadeBlend = self.use_cascade_blend_box.isChecked()
        pool.mCascadeBlendValue = extract_number(self.cascade_blend_value_box.text())
        skeleton_path = self.skeleton_path_box.text()
        pool.mSkeleton = Path_Record(PathHash=fnv1a(skeleton_path),Path=skeleton_path)
        pool.sync_data()
        self.parent_widget.show_blnd_data(self.parent_widget.current_blnder_data)

    def on_set(self):
        self.show_pool_data()

    def show_pool_data(self):
        pool = self.parent_widget.current_blnder_data.pool
        self.use_cascade_blend_box.setChecked(pool.mUseCascadeBlend)
        self.cascade_blend_value_box.setText(f"{pool.mCascadeBlendValue}")
        self.skeleton_path_box.setText(pool.mSkeleton.Path)

class Create_Blend_Card_Interface(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        self.to_animation_list = []
        self.to_animation_listwidget = ListWidget(self)
        self.to_animation_listwidget.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义右键菜单
        self.to_animation_listwidget.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键菜单事件
        self.build(self.layout)

    def build(self, layout):
        self.build_blend_data_layout(self.layout)
        self.build_blend_edit_layout(self.layout)
        self.layout.setStretch(0, 2)
        self.layout.setStretch(1, 3)

    def selector_from_animation(self):
        pass

    def selector_to_animation(self):
        pass

    def build_blend_data_layout(self, layout):
        blend_data_layout = QVBoxLayout(self)
        self.from_animation_box = create_combo_box_label(self, "FromAnimation: ", blend_data_layout)
        load_objects_to_combobox(self.from_animation_box,self.parent_widget.current_blnder_data.pool.mClassAry,lambda o: o.mName)
        self.from_animation_box.setPlaceholderText("None")
        self.from_animation_box.setCurrentIndex(-1)
        self.from_animation_box.currentTextChanged.connect(self.selector_from_animation)
        blend_data_list_card = CardWidget(self)
        self.blend_data_list_card_layout = QVBoxLayout(self)
        blend_data_list_card.setLayout(self.blend_data_list_card_layout)
        self.blend_data_list_card_layout.addWidget(self.to_animation_listwidget)
        blend_data_layout.addWidget(blend_data_list_card)
        layout.addLayout(blend_data_layout)

    def build_blend_edit_layout(self, layout):
        blend_edit_layout = QVBoxLayout(self)

        self.blend_edit_blnk_card = CardWidget(self)
        blend_edit_blnk_card_layout = QVBoxLayout(self.blend_edit_blnk_card)
        empty_label = QLabel("Please select or add a piece of data.", self)
        blend_edit_blnk_card_layout.addWidget(empty_label)
        blend_edit_blnk_card_layout.addStretch()
        self.blend_edit_blnk_card.setLayout(blend_edit_blnk_card_layout)
        blend_edit_layout.addWidget(self.blend_edit_blnk_card)

        self.blend_edit_card = CardWidget(self)
        blend_edit_card_layout = QVBoxLayout(self)
        self.blend_edit_card.setLayout(blend_edit_card_layout)
        blend_edit_layout.addWidget(self.blend_edit_card)
        self.blend_edit_card.setVisible(False)

        self.to_animation_box = create_combo_box_label(self, "ToAnimation: ", blend_edit_card_layout)
        load_objects_to_combobox(self.to_animation_box,self.parent_widget.current_blnder_data.pool.mClassAry,lambda o: o.mName)
        self.to_animation_box.setPlaceholderText("None")
        self.to_animation_box.setCurrentIndex(-1)
        self.to_animation_box.currentTextChanged.connect(self.selector_to_animation)
        self.blend_flags_box = create_text_box(self, "BlendFlags: ", blend_edit_card_layout)
        self.blend_time_box = create_text_box(self, "BlendTime: ", blend_edit_card_layout)
        blend_edit_card_layout.addStretch()

        blend_edit_button_layout = QHBoxLayout()
        new_blend_to_data = PrimaryPushButton("新建数据", self)
        new_blend_to_data.clicked.connect(self.new_blend_to_data)
        save_blend_to_data = PrimaryPushButton("保存数据", self)
        save_blend_to_data.clicked.connect(self.save_blend_to_data)
        unselect_blend_to_data = PushButton("取消选中", self)
        unselect_blend_to_data.clicked.connect(self.unselect_blend_to_data)
        blend_edit_button_layout.addStretch()
        blend_edit_button_layout.addWidget(new_blend_to_data)
        blend_edit_button_layout.addWidget(save_blend_to_data)
        blend_edit_button_layout.addWidget(unselect_blend_to_data)
        blend_edit_layout.addLayout(blend_edit_button_layout)
        layout.addLayout(blend_edit_layout)

    def new_blend_to_data(self):
        from_animation_id = self.from_animation_box.currentIndex()
        item = QListWidgetItem(f"BlendData {len(self.to_animation_list)}")
        blend_to_data = BlendData(from_animation_id,-1)
        self.to_animation_list.append(blend_to_data)
        item.setData(Qt.UserRole, blend_to_data)
        self.to_animation_listwidget.addItem(item)
        self.selected_blend_to_data(item)
        self.to_animation_listwidget.itemClicked.connect(self.show_current_blend_to_data)
        self.show_current_blend_to_data(item)

    def selected_blend_to_data(self, item):
        self.to_animation_listwidget.setCurrentItem(item)
        self.show_current_blend_to_data(item)

    def show_current_blend_to_data(self, item):
        self.blend_edit_card.setVisible(True)
        self.blend_edit_blnk_card.setVisible(False)
        blend_to_data = self.to_animation_listwidget.currentItem().data(Qt.UserRole)
        self.to_animation_box.setCurrentIndex(blend_to_data.mToAnimId)
        self.blend_flags_box.setText(f"{blend_to_data.mBlendFlags}")
        self.blend_time_box.setText(f"{blend_to_data.mBlendTime}")

    def save_blend_to_data(self):
        from_animation = self.from_animation_box.currentData()
        from_animation_id = self.from_animation_box.currentIndex()
        current_index = self.to_animation_listwidget.currentIndex().row()
        current_data = self.to_animation_listwidget.currentItem()
        to_animation = self.to_animation_box.currentData()
        to_animation_id = self.to_animation_box.currentIndex()
        blend_flags = extract_number(self.blend_flags_box.text())
        blend_time = extract_number(self.blend_flags_box.text())
        new_data = BlendData(from_animation_id, to_animation_id, blend_flags, blend_time)
        self.to_animation_list[current_index] = new_data
        current_data.setText(f"{from_animation.mName} to {to_animation.mName}")
        current_data.setData(Qt.UserRole, new_data)
        self.unselect_blend_to_data()

    def unselect_blend_to_data(self):
        self.to_animation_listwidget.clearSelection()
        self.blend_edit_card.setVisible(False)
        self.blend_edit_blnk_card.setVisible(True)
        self.to_animation_box.setCurrentIndex(-1)
        self.blend_flags_box.clear()
        self.blend_time_box.clear()

    def show_context_menu(self, pos):
        item = self.to_animation_listwidget.itemAt(pos)  # 获取当前点击的项目
        if item:
            menu = RoundMenu(parent=self)  # 创建菜单
            delete_data_action = Action(FIF.DELETE, 'Delete', self)  # 创建菜单项
            delete_data_action.triggered.connect(lambda: self.delete_data(item))  # 点击时触发
            menu.addAction(delete_data_action)  # 添加菜单项
            menu.exec_(self.to_animation_listwidget.mapToGlobal(pos))  # 显示菜单

    def delete_data(self, item):
        pass

    def save_data(self):
        parent = self.parent_widget
        pool = parent.current_blnder_data.pool
        from_animation_id = self.from_animation_box.currentIndex()
        pool.extend_blend_data(self.to_animation_list)
        parent.show_blnd_data(parent.current_blnder_data)

    def on_set(self):
        pass

class Create_Transition_Card_Interface(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        self.transition_to_list = []
        self.transition_to_listwidget = ListWidget(self)
        self.transition_to_listwidget.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义右键菜单
        self.transition_to_listwidget.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键菜单事件
        self.build()

    def build(self):
        self.build_transition_data_layout(self.layout)
        self.build_transition_edit_layout(self.layout)
        self.layout.setStretch(0, 2)
        self.layout.setStretch(1, 3)

    def build_transition_data_layout(self, layout):
        transition_data_layout = QVBoxLayout(self)
        self.from_animation_box = create_combo_box_label(self, "FromAnimation: ", transition_data_layout)
        load_objects_to_combobox(self.from_animation_box,self.parent_widget.current_blnder_data.pool.mClassAry,lambda o: o.mName)
        self.from_animation_box.setPlaceholderText("None")
        self.from_animation_box.setCurrentIndex(-1)
        self.from_animation_box.currentTextChanged.connect(self.selector_from_animation)
        transition_data_list_card = CardWidget(self)
        self.transition_data_list_card_layout = QVBoxLayout(self)
        transition_data_list_card.setLayout(self.transition_data_list_card_layout)
        self.transition_data_list_card_layout.addWidget(self.transition_to_listwidget)
        transition_data_layout.addWidget(transition_data_list_card)
        layout.addLayout(transition_data_layout)

    def selector_from_animation(self):
        pass

    def selector_to_animation(self):
        pass

    def selector_transition_animation(self):
        pass

    def build_transition_edit_layout(self, layout):
        transition_edit_layout = QVBoxLayout(self)

        self.transition_edit_blnk_card = CardWidget(self)
        transition_edit_blnk_card_layout = QVBoxLayout(self.transition_edit_blnk_card)
        empty_label = QLabel("Please select or add a piece of data.", self)
        transition_edit_blnk_card_layout.addWidget(empty_label)
        transition_edit_blnk_card_layout.addStretch()
        self.transition_edit_blnk_card.setLayout(transition_edit_blnk_card_layout)
        transition_edit_layout.addWidget(self.transition_edit_blnk_card)

        self.transition_edit_card = CardWidget(self)
        transition_edit_card_layout = QVBoxLayout(self)
        self.transition_edit_card.setLayout(transition_edit_card_layout)
        transition_edit_layout.addWidget(self.transition_edit_card)
        self.transition_edit_card.setVisible(False)

        self.to_animation_box = create_combo_box_label(self, "ToAnimation: ", transition_edit_card_layout)
        load_objects_to_combobox(self.to_animation_box,self.parent_widget.current_blnder_data.pool.mClassAry,lambda o: o.mName)
        self.to_animation_box.setPlaceholderText("None")
        self.to_animation_box.setCurrentIndex(-1)
        self.to_animation_box.currentTextChanged.connect(self.selector_to_animation)

        self.transition_animation_box = create_combo_box_label(self, "TransitionAnimation: ", transition_edit_card_layout)
        load_objects_to_combobox(self.transition_animation_box,self.parent_widget.current_blnder_data.pool.mClassAry,lambda o: o.mName)
        self.transition_animation_box.setPlaceholderText("None")
        self.transition_animation_box.setCurrentIndex(-1)
        self.transition_animation_box.currentTextChanged.connect(self.selector_transition_animation)
        transition_edit_card_layout.addStretch()

        transition_edit_button_layout = QHBoxLayout()
        new_transition_to_data = PrimaryPushButton("新建数据", self)
        new_transition_to_data.clicked.connect(self.new_transition_to_data)
        save_transition_to_data = PrimaryPushButton("保存数据", self)
        save_transition_to_data.clicked.connect(self.save_transition_to_data)
        unselect_transition_to_data = PushButton("取消选中", self)
        unselect_transition_to_data.clicked.connect(self.unselect_transition_to_data)
        transition_edit_button_layout.addStretch()
        transition_edit_button_layout.addWidget(new_transition_to_data)
        transition_edit_button_layout.addWidget(save_transition_to_data)
        transition_edit_button_layout.addWidget(unselect_transition_to_data)
        transition_edit_layout.addLayout(transition_edit_button_layout)
        layout.addLayout(transition_edit_layout)

    def new_transition_to_data(self):
        item = QListWidgetItem(f"TransitionToData {len(self.transition_to_list)}")
        transition_to_data = TransitionToData(-1,-1)
        self.transition_to_list.append(transition_to_data)
        item.setData(Qt.UserRole, transition_to_data)
        self.transition_to_listwidget.addItem(item)
        self.selected_transition_to_data(item)
        self.transition_to_listwidget.itemClicked.connect(self.show_current_transition_to_data)

    def selected_transition_to_data(self, item):
        self.transition_to_listwidget.setCurrentItem(item)
        self.show_current_transition_to_data(item)

    def show_current_transition_to_data(self, item):
        self.transition_edit_card.setVisible(True)
        self.transition_edit_blnk_card.setVisible(False)
        transition_to_data = self.transition_to_listwidget.currentItem().data(Qt.UserRole)
        self.to_animation_box.setCurrentIndex(transition_to_data.mToAnimId)
        self.transition_animation_box.setCurrentIndex(transition_to_data.mTransitionAnimId)

    def save_transition_to_data(self):
        from_animation = self.from_animation_box.currentData()
        current_index = self.transition_to_listwidget.currentIndex().row()
        current_data = self.transition_to_listwidget.currentItem()
        to_animation = self.to_animation_box.currentData()
        to_animation_id = self.to_animation_box.currentIndex()
        transition_animation = self.transition_animation_box.currentData()
        transition_animation_id = self.transition_animation_box.currentIndex()
        new_data = TransitionToData(to_animation_id, transition_animation_id)
        self.transition_to_list[current_index] = new_data
        current_data.setText(f"{from_animation.mName} to {to_animation.mName}")
        current_data.setData(Qt.UserRole, new_data)
        self.unselect_transition_to_data()

    def unselect_transition_to_data(self):
        self.transition_to_listwidget.clearSelection()
        self.transition_edit_card.setVisible(False)
        self.transition_edit_blnk_card.setVisible(True)
        self.to_animation_box.setCurrentIndex(-1)
        self.transition_animation_box.setCurrentIndex(-1)

    def show_context_menu(self, pos):
        item = self.transition_to_listwidget.itemAt(pos)  # 获取当前点击的项目
        if item:
            menu = RoundMenu(parent=self)  # 创建菜单
            delete_data_action = Action(FIF.DELETE, 'Delete', self)  # 创建菜单项
            delete_data_action.triggered.connect(lambda: self.delete_data(item))  # 点击时触发
            menu.addAction(delete_data_action)  # 添加菜单项
            menu.exec_(self.transition_to_listwidget.mapToGlobal(pos))  # 显示菜单

    def delete_data(self, item):
        pass

    def save_data(self):
        parent = self.parent_widget
        pool = parent.current_blnder_data.pool
        from_animation_id = self.from_animation_box.currentIndex()
        self.transition_to_list.sort(key=lambda x: x.mToAnimId)
        if from_animation_id > -1:
            transition_data = TransitionClipData(from_animation_id, len(self.transition_to_list), TransitionTo=self.transition_to_list)
            pool.append_transition_data(transition_data)
            parent.show_blnd_data(parent.current_blnder_data)

    def on_set(self):
        pass

class Create_Track_Card_Interface(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build(self.layout)

    def build(self, layout):
        create_text_label(self, "TrackData: ", self.layout)
        self.blend_weight_box = create_text_box(self, "BlendWeight: ", self.layout)
        self.blend_mode_box = create_text_box(self, "BlendMode: ", self.layout)
        self.index_box = create_text_box(self, "Index: ", self.layout)
        self.name_box = create_text_box(self, "Name: ", self.layout)
        self.layout.addStretch()

    def on_set(self):
        pass

    def save_data(self):
        parent = self.parent_widget
        pool = parent.current_blnder_data.pool
        blend_weight = extract_number(self.blend_weight_box.text())
        blend_mode = extract_number(self.blend_mode_box.text())
        name = self.name_box.text()
        pool.create_track_data(blend_weight, blend_mode, name)
        parent.show_blnd_data(parent.current_blnder_data)

class Create_Mask_Card_Interface(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build(self.layout)

    def build(self, layout):
        pass

    def on_set(self):
        pass

class Type_Navigation(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)
        self.layout = QVBoxLayout(self)
        self.edit_pool_card_interface = Edit_Pool_Card_Interface(self.parent())
        self.create_blend_card_interface = Create_Blend_Card_Interface(self.parent())
        self.create_transition_card_interface = Create_Transition_Card_Interface(self.parent())
        self.create_track_card_interface = Create_Track_Card_Interface(self.parent())
        self.create_clip_card_interface = Create_Clip_Card_Interface(self.parent())
        self.create_mask_card_interface = Create_Mask_Card_Interface(self.parent())

        # add items to pivot
        self.addSubInterface(self.edit_pool_card_interface, 'edit_pool_card_interface', 'PoolData')
        self.addSubInterface(self.create_blend_card_interface, 'create_blend_card_interface', 'BlendData')
        self.addSubInterface(self.create_transition_card_interface, 'create_transition_card_interface', 'TransitionData')
        self.addSubInterface(self.create_track_card_interface, 'create_track_card_interface', 'TrackData')
        self.addSubInterface(self.create_clip_card_interface, 'create_clip_card_interface', 'ClipData')
        self.addSubInterface(self.create_mask_card_interface, 'create_mask_card_interface', 'MaskData')

        self.layout.addWidget(self.pivot)
        self.layout.addWidget(self.stackedWidget)
        self.stackedWidget.setCurrentWidget(self.create_clip_card_interface)
        self.pivot.setCurrentItem(self.create_clip_card_interface.objectName())
        self.pivot.currentItemChanged.connect(self.setCurrentWidget)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def setCurrentWidget(self, key):
        widget = self.findChild(QWidget, key)
        self.stackedWidget.setCurrentWidget(widget)
        widget.on_set()

    def addSubInterface(self, widget, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)

class Adjunction_Data(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.build_navigation()
        self.build_button_layout(self.viewLayout)
        self.reset()

    def build_navigation(self):
        self.type_navigation = Type_Navigation(self.parent())
        self.viewLayout.addWidget(self.type_navigation)

    def build_button_layout(self, layout):
        button_layout = QHBoxLayout()
        create_btn = PrimaryPushButton("创建", self)
        create_btn.clicked.connect(self.create_data_action)
        button_layout.addWidget(create_btn)
        clear_btn = PushButton("取消", self)
        clear_btn.clicked.connect(self._MessageBoxBase__onCancelButtonClicked)
        button_layout.addWidget(clear_btn)
        layout.addLayout(button_layout)

    def create_data_action(self):
        parent = self.parent()
        try:
            self.type_navigation.stackedWidget.currentWidget().save_data()
            InfoBar.success(
                title="成功: ",
                content="创建完成",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=parent
            )
            self.reject()
        except Exception as e:
            InfoBar.error("错误", f"创建失败: {e}", parent=parent)
            print(f"创建失败: {e}")

    def reset(self):
        # 允许布局随窗口大小变化
        self.widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.viewLayout.setSpacing(5)
        self.viewLayout.setContentsMargins(15, 15, 15, 15)
        # 移除父类中的 buttonGroup（取消显示底部按钮）
        self.buttonGroup.setParent(None)  # 移除按钮组
        self.setClosableOnMaskClicked(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        sync_window_position(self, 0.9)
