from ..build import*
from ...core.manager.logger.logger_manager import LOGGERMANAGER
from ...components.dialog_widget import DialogWidget
from ...core.function.navgrid.write_navgrid import write_navgrid_from_version
from pathlib import Path

class Options_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.build()

    def build(self):
        self.build_path_label(self.layout)
        file_info_layout = QHBoxLayout(self)
        self.name_label = create_text_box(self, "Name:", file_info_layout)
        self.select_version = create_combo_box_label(self, "Version:", file_info_layout)
        for version in [2, 5, 7]:
            self.select_version.addItem(f"Version_{version}", userData=version)
        self.select_version.setCurrentIndex(1)
        self.layout.addLayout(file_info_layout)
        self.layout.addStretch()
        create_text_label(self, "Tips: Patch 4.20 only supports version 5!", self.layout)
        last_aimesh_ngrid_filename = LOGGERMANAGER.split_path("aimesh_ngrid_file")[1]
        new_aimesh_ngrid_filename = os.path.splitext(last_aimesh_ngrid_filename)[0] + "_Fix"
        self.name_label.setText(new_aimesh_ngrid_filename)

    def build_path_label(self, layout):
        self.path_label = create_text_box(self, "Path:", layout)
        select_path_button = create_button(self, "Select Path", self.select_path, layout.itemAt(0), True, 1)
        last_aimesh_ngrid_filepath = LOGGERMANAGER.split_path("aimesh_ngrid_file")[0]
        self.path_label.setText(last_aimesh_ngrid_filepath)

    def select_path(self):
        last_aimesh_ngrid_filepath = LOGGERMANAGER.split_path("aimesh_ngrid_file")[0]
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", last_aimesh_ngrid_filepath, QFileDialog.Option.ShowDirsOnly)
        if not folder:
            return
        try:
            self.path_label.setText(folder)
        except Exception as e:
            InfoBar.error("错误", f"{e}", parent=self)

class NavGrid_ExportOptions(DialogWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.build()

    def build(self):
        create_text_label(self, "ExportOptions:", self.viewLayout)
        self.options_card = Options_Card(self)
        self.viewLayout.addWidget(self.options_card)
        self.build_button(self.viewLayout)

    def build_button(self, layout):
        button_layout = QHBoxLayout(self)
        export_button = create_button(self, "Export", self.export_action, button_layout, False, 1)
        cancel_button = create_button(self, "Cancel", self.reject, button_layout, False)
        layout.addLayout(button_layout)

    def export_action(self):
        target_version = self.options_card.select_version.currentData()
        print(f"{self.parent().current_navgrid_data.header}")
        file_path = self.options_card.path_label.text()
        file_name = self.options_card.name_label.text()
        if file_path and file_name:
            file = os.path.join(file_path, f"{file_name}.aimesh_ngrid")
            print(file)
            try:
            # 使用 'w' 模式创建或覆盖文件
                with open(file, 'wb') as f:
                    # f.write(f"这是为 {file_name} 自动生成的内容。")
                    write_navgrid_from_version(self.parent().current_navgrid_data, target_version, f)
                print(f"文件已成功创建: {file}")
            except IOError as e:
                print(f"创建文件失败: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        sync_window_position(self, 0.5)
