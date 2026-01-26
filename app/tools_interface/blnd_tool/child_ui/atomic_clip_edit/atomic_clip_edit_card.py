from ....build import*
from .....core.objects.blnd.data_obj.clip_data import AtomicClip
from .....core.function.general import get_relative_path, extract_number
from .....core.objects.animation.read_anm import read_anm_file
from .event_data_card import EventData_Card

class AtomicClip_Edit_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()

    def build_time_data_layout(self):
        time_data_layout = QHBoxLayout()
        self.start_frame_box = create_text_box(self, "StartFrame: ", time_data_layout)
        self.end_frame_box = create_text_box(self, "EndFrame: ", time_data_layout)
        self.tick_duration_box = create_text_box(self, "TickDuration: ", time_data_layout)
        self.layout.addLayout(time_data_layout)

    def build_visibility_data_layout(self):
        visibility_data_layout = QHBoxLayout()
        track_data_layout = QHBoxLayout()
        track_data_lable = QLabel("TrackData: ", self)
        track_data_lable.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.track_data_box = ComboBox(self)
        for t in self.parent().parent().current_blnder_data.pool.mBlendTrackAry:
            data_name = t.mName
            self.track_data_box.addItem(data_name, userData=t)
        self.track_data_box.currentTextChanged.connect(self.selector_track_data)
        self.selector_default_track_data(self.track_data_box)
        track_data_layout.addWidget(track_data_lable)
        track_data_layout.addWidget(self.track_data_box)
        visibility_data_layout.addLayout(track_data_layout)

        mask_data_layout = QHBoxLayout()
        mask_data_lable = QLabel("MaskData: ", self)
        mask_data_lable.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.mask_data_box = ComboBox(self)
        for t in self.parent().parent().current_blnder_data.pool.mMaskDataAry:
            data_name = t.mName
            self.mask_data_box.addItem(data_name, userData=t)
        self.mask_data_box.currentTextChanged.connect(self.selector_mask_data)
        self.mask_data_box.setPlaceholderText("None")
        self.mask_data_box.setCurrentIndex(-1)
        mask_data_layout.addWidget(mask_data_lable)
        mask_data_layout.addWidget(self.mask_data_box)
        visibility_data_layout.addLayout(mask_data_layout)
        self.syncGroupName_box = create_text_box(self, "SyncGroupName: ", visibility_data_layout)
        self.syncGroupName_box.setText("None")
        self.layout.addLayout(visibility_data_layout)
        visibility_data_layout.setStretch(0, 1)  # name_layout 拉伸因子为 1
        visibility_data_layout.setStretch(1, 1)  # type_layout 拉伸因子为 1
        visibility_data_layout.setStretch(2, 1)  # type_layout 拉伸因子为 1

    def build_anim_data_layout(self):
        anim_data_layout = QHBoxLayout()
        anim_file_lable = QLabel("AnimData: ", self)
        anim_file_lable.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.anim_file_box = ComboBox(self)
        self.anim_file_box.setPlaceholderText("选择动画数据: ")
        for f in self.parent().parent().anm_files:
            file_name = os.path.basename(f)
            self.anim_file_box.addItem(file_name, userData=f)
        self.anim_file_box.currentTextChanged.connect(self.selector_anim_data)
        self.anim_file_box.setCurrentIndex(-1)
        anim_data_layout.addWidget(anim_file_lable)
        anim_data_layout.addWidget(self.anim_file_box)
        self.layout.addLayout(anim_data_layout)

    def build_event_data_layout(self):
        create_text_label(self, "EventData: ", self.layout)
        self.event_data_card = EventData_Card(self)
        self.layout.addWidget(self.event_data_card)

    def build(self):
        self.build_time_data_layout()
        self.build_visibility_data_layout()
        self.build_anim_data_layout()
        self.build_event_data_layout()

    def selector_default_track_data(self, box):
        # 遍历所有条目
        for index in range(box.count()):
            item_data = box.itemData(index)
            
            # 检查 mName 是否为 'Default'
            if item_data and item_data.mName == 'Default':
                # 如果找到匹配的条目，设置当前选中的索引
                box.setCurrentIndex(index)
                return  # 找到后可以退出函数，不需要继续遍历
            
        # 如果没有找到 'Default'，则默认设置为第一个索引
        box.setCurrentIndex(0)

    def selector_track_data(self):
        selected_index = self.track_data_box.currentIndex()

    def selector_mask_data(self):
        selected_index = self.mask_data_box.currentIndex()

    def selector_anim_data(self):
        selected_data = self.anim_file_box.currentData()
        anm_data = self.start_read_anm_file(selected_data)
        start_frame = 0
        end_frame = 30
        tick_duration = 0.03333333507180214
        if anm_data.header.magic ==  "r3d2canm":
            end_frame = round(anm_data.data.duration/0.03333334, 1)
            end_frame = int(end_frame)
        else:
            if anm_data.header.version == 5:
                end_frame = anm_data.data.framesPerTrack - 1
            else:
                end_frame = anm_data.data.frameCount - 1
        self.parent().class_flag_box.setText("0")
        self.parent().class_name_box.setText(os.path.splitext(os.path.basename(selected_data))[0])
        self.start_frame_box.setText(f"{start_frame}")
        self.end_frame_box.setText(f"{end_frame}")
        self.tick_duration_box.setText(f"{tick_duration}")

    def start_read_anm_file(self, path):
        try:
            with open(path, 'rb') as file:
                return read_anm_file(file)
        except Exception as e:
            # 捕获异常并抛出，便于在调用时处理
            raise ValueError(f"无法加载文件 {path}: {e}")

    def create_clip_data(self, pool, name, flag):
        end_frame = extract_number(self.end_frame_box.text())
        tick_duration = extract_number(self.tick_duration_box.text())
        track_id = self.track_data_box.currentIndex()
        event_data = self.event_data_card.get_event_resource(pool)
        mask_id = self.mask_data_box.currentIndex() if self.mask_data_box.currentIndex() > -1 else None
        path = get_relative_path(self.anim_file_box.currentData(), "DATA").lower()
        syncgroupname = None if self.syncGroupName_box.text() == "None" else self.syncGroupName_box.text()
        pool.create_atomic_clip(name,end_frame,tick_duration,track_id,flag,event_data,mask_id,path,syncgroupname)
