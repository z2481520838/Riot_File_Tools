from ..build import*
from ...core.objects.blnd.data_obj.blnd_data import Track_Resource
from ...core.function.blnd.create_blnd import create_new_project
from ...core.function.general import get_relative_path, extract_number
from ...core.manager.logger.logger_manager import LOGGERMANAGER

class Start_Create(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.widget.setFixedSize(600,350)
        self.ini_main()
        self.auto_choose_path()
        self.reset()

    def auto_choose_path(self):
        last_skeleton_file = LOGGERMANAGER.get("skeleton_file")
        self.choose_skl(last_skeleton_file)

    def reset(self):
        # 允许布局随窗口大小变化
        self.widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.viewLayout.setSpacing(5)
        self.viewLayout.setContentsMargins(10, 10, 10, 10)
        # 移除父类中的 buttonGroup（取消显示底部按钮）
        self.buttonGroup.setParent(None)  # 移除按钮组
        self.setClosableOnMaskClicked(True)

    def add_path_bar(self, layout, tip, lable):
        main_layout = QVBoxLayout()
        tip_bar = QLabel(tip, self)
        sub_layout = QHBoxLayout()
        path_box = LineEdit(self)
        chose_path_btn = PrimaryPushButton(lable, self)
        chose_path_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sub_layout.addWidget(path_box)
        sub_layout.addWidget(chose_path_btn)
        main_layout.addWidget(tip_bar)
        main_layout.addLayout(sub_layout)
        # main_layout.addStretch()
        layout.addLayout(main_layout)
        return path_box, chose_path_btn

    def choose_skl_from_dialog(self):
        last_skeleton_file = LOGGERMANAGER.get("skeleton_file")
        default_directory = "" if last_skeleton_file is None else os.path.dirname(last_skeleton_file)
        file, _ = QFileDialog.getOpenFileName(self, "选择文件", default_directory, "Skl Files (*.skl)")
        self.choose_skl(file)

    def choose_skl(self, file):
        if not file:
            return
        try:
            LOGGERMANAGER.save("skeleton_file", file)
            path = get_relative_path(file, "DATA").lower()
            self.skeleton_path_box.setText(path)
            InfoBar.success(
                title="已加载文件: ",
                content=f"{file}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self.parent()
            )
            self.sync_get_animations_folder(file)
        except Exception as e:
            InfoBar.error("错误", f"文件读取失败: {e}", parent=self.parent())

    def sync_get_animations_folder(self, file):
        current_skin_dir = os.path.dirname(file)
        animations_dir = os.path.join(current_skin_dir, "animations")
        # 如果不存在，则把最后一级目录替换为 base
        if not os.path.exists(animations_dir):
            base_skin_dir = os.path.join(os.path.dirname(current_skin_dir), "base")  # 上一级 + base
            animations_dir = os.path.join(base_skin_dir, "animations")
        self.choose_anm_path(animations_dir)
        LOGGERMANAGER.save("current_skin_path", current_skin_dir)

    def choose_anm_path_from_dialog(self):
        # 打开文件夹选择对话框
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", "", QFileDialog.Option.ShowDirsOnly)
        self.choose_anm_path(folder)

    def choose_anm_path(self, folder):
        if not folder:
            return

        # 获取该文件夹中的所有 .anm 文件（不对子文件夹生效）
        # anm_files = [f for f in os.listdir(folder) if f.endswith('.anm') and os.path.isfile(os.path.join(folder, f))]
        anm_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.anm') and os.path.isfile(os.path.join(folder, f))]

        if not anm_files:
            InfoBar.warning("警告", "文件夹中没有 .anm 文件", parent=self.parent())
            return
        try:
            LOGGERMANAGER.save("animations_path", folder)
            path = get_relative_path(folder, "DATA").lower()
            self.anim_path_box.setText(path)
            self.parent().anm_files = anm_files
            InfoBar.success(
                title="已加载文件夹: ",
                content=f"{folder} 中包含 {len(anm_files)} 个 .anm 文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self.parent()
            )
        except Exception as e:
            InfoBar.error("错误", f"文件读取失败: {e}", parent=self.parent())

    def ini_main(self):
        # 输出框
        card = CardWidget(self)
        base_layout = QVBoxLayout(card)
        # 保存 path_box 引用
        self.skeleton_path_box, self.skl_button = self.add_path_bar(base_layout, "选择骨骼文件", "选择文件")
        self.anim_path_box, self.anim_button = self.add_path_bar(base_layout, "选择动画路径", "选择目录")
        self.skl_button.clicked.connect(self.choose_skl_from_dialog)
        self.anim_button.clicked.connect(self.choose_anm_path_from_dialog)

        self.build_track_data_layout(base_layout)
        self.build_cascade_blend_data_layout(base_layout)
        base_layout.addStretch()

        button_layout = QHBoxLayout()
        create_btn = PrimaryPushButton("创建", self)
        create_btn.clicked.connect(self.create)
        button_layout.addWidget(create_btn)
        clear_btn = PushButton("取消", self)
        clear_btn.clicked.connect(self._MessageBoxBase__onCancelButtonClicked)
        button_layout.addWidget(clear_btn)
        base_layout.addLayout(button_layout)

        card.setLayout(base_layout)
        self.viewLayout.addWidget(card)

    def build_track_data_layout(self, layout):
        track_info_layout = QVBoxLayout()
        track_data_layout = QHBoxLayout()
        create_text_label(self, "DefaultTrackData: ", layout)
        self.track_name_box = create_text_box(self, "Name: ", track_data_layout, "Default")
        self.blend_weight_box = create_text_box(self, "BlendWeight: ", track_data_layout, "1")
        self.blend_mode_box = create_text_box(self, "BlendMode: ", track_data_layout, "0")
        track_info_layout.addLayout(track_data_layout)
        layout.addLayout(track_info_layout)

    def build_cascade_blend_data_layout(self, layout):
        create_text_label(self, "CascadeBlend: ", layout)
        cascade_blend_data_layout = QHBoxLayout()
        self.use_cascade_blend_box = CheckBox("UseCascadeBlend", self)
        cascade_blend_data_layout.addWidget(self.use_cascade_blend_box)
        cascade_blend_data_layout.addStretch()
        self.cascade_blend_value_box = create_text_box(self, "CascadeBlendValue: ", cascade_blend_data_layout, "0")
        layout.addLayout(cascade_blend_data_layout)

    def create(self):
        parent = self.parent()
        try:
            use_cascade_blend = self.use_cascade_blend_box.isChecked()
            cascade_blend_value = extract_number(self.cascade_blend_value_box.text())
            skeleton_path = self.skeleton_path_box.text()
            blend_weight = extract_number(self.blend_weight_box.text())
            blend_mode = extract_number(self.blend_mode_box.text())
            track_name = self.track_name_box.text()
            default_track = Track_Resource(mBlendWeight=blend_weight,mBlendMode=blend_mode,mIndex=0,mName=track_name)
            parent.current_blnder_data = create_new_project(use_cascade_blend, cascade_blend_value, skeleton_path, default_track)
            parent.show_blnd_data(parent.current_blnder_data)
            self.parent().adjunction_data()
            InfoBar.success(
                title="成功: ",
                content="新项目已创建",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=parent
            )
            self.reject()
        except Exception as e:
            InfoBar.error("错误", f"创建失败: {e}", parent=parent)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # self.widget.setFixedSize(self.size()*0.6)
        if self.isVisible():  # 如果弹出窗口是可见的
            self.updateWindowPosition()

    def updateWindowPosition(self):
        if self.parent():
            parent_pos = self.parent().pos()  # 获取父窗口的位置
            parent_size = self.parent().size()  # 获取父窗口的大小
            window_size = self.size()  # 获取弹出窗口的大小

            # 计算弹出窗口的中心位置
            center_x = parent_pos.x() + (parent_size.width() - window_size.width()) // 2
            center_y = parent_pos.y() + (parent_size.height() - window_size.height()) // 2

            # 设置弹出窗口的最终位置
            self.move(center_x, center_y)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DataViewer()
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec())
