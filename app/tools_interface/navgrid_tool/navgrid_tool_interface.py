# coding:utf-8
from ..build import*
from ...core.manager.logger.logger_manager import LOGGERMANAGER
from ...core.function.navgrid.read_navgrid import ReadWorker
from ...core.function.navgrid.draw_navgrid import render_all_map_layout, RendererWorker, convert_to_image
from ...core.function.general import start_worker_flow, make_circle, make_rectangle
from .navgrid_export_options import NavGrid_ExportOptions
from .navgrid_drawobjects_options import NavGrid_DrawObjects_Options
from ...core.function.navgrid.write_bmp import write_bmp_file

def cerate_tabel(name, info, layout):
    label = QLabel(info)
    layout.addRow(name, label)
    return label

class Layout_Interface(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("layout_Interface")
        self.layout = QVBoxLayout(self)

class Object_Interface(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("object_Interface")
        self.layout = QVBoxLayout(self)

class DataType_Navigation(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)
        self.layout = QVBoxLayout(self)
        self.layout_interface = Layout_Interface(self.parent())
        self.object_interface = Object_Interface(self.parent())

        # 页面切换时,更新属性面板
        # 当前页面为"图层"时,属性面板展示导航信息
        # 当前页面为"对象"时,属性面板展示当前选中对象的信息
        self.addSubInterface(self.layout_interface, 'layout_interface', '图层')
        self.addSubInterface(self.object_interface, 'object_interface', '对象')

        self.layout.addWidget(self.pivot)
        self.layout.addWidget(self.stackedWidget)
        self.stackedWidget.setCurrentWidget(self.layout_interface)
        self.pivot.setCurrentItem(self.layout_interface.objectName())
        self.pivot.currentItemChanged.connect(self.setCurrentWidget)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def setCurrentWidget(self, key):
        widget = self.findChild(QWidget, key)
        self.stackedWidget.setCurrentWidget(widget)

    def addSubInterface(self, widget, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)

class DataType_Navigation_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.layout = QVBoxLayout(self)
        self.navigation = DataType_Navigation(self.parent())
        self.layout.addWidget(self.navigation)
        self.setFixedWidth(300)

class NavGrid_Info_Card(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.layout = QVBoxLayout(self)
        self.blank_info_group = self.build_blank_info_group(self.layout)
        self.info_group = self.build_info_group(self.layout)
        self.setFixedHeight(350)
        self.setFixedWidth(300)

    def build_blank_info_group(self, layout):
        group = QGroupBox(self)
        group.setTitle("属性")
        form_layout = QFormLayout(group)
        self.tips = cerate_tabel("提示:", "暂无数据,请先导入一个文件", form_layout)
        layout.addWidget(group)
        return group

    def build_info_group(self, layout):
        group = QGroupBox(self)
        group.setTitle("属性")
        form_layout = QFormLayout(group)
        self.file_name_info = cerate_tabel("FileName:", "", form_layout)
        self.version_info = cerate_tabel("Version:", "", form_layout)
        self.map_origin_info = cerate_tabel("MapOrigin:", "", form_layout)
        self.map_size_info = cerate_tabel("MapSize:", "", form_layout)
        self.cell_size_info = cerate_tabel("CellSize:", "", form_layout)
        self.cell_count_info = cerate_tabel("CellCount:", "", form_layout)
        self.cell_total_info = cerate_tabel("CellTotal:", "", form_layout)
        self.height_sample_count_info = cerate_tabel("HSCount:", "", form_layout)
        self.height_sample_offset_info = cerate_tabel("HSOffset:", "", form_layout)
        self.min_sample_height_info = cerate_tabel("MinHS:", "", form_layout)
        self.max_sample_height_info = cerate_tabel("MaxHS:", "", form_layout)
        self.height_samples_total_info = cerate_tabel("HSTotal:", "", form_layout)
        self.hint_nodes_count_info = cerate_tabel("HNCount:", "", form_layout)
        group.setVisible(False)
        layout.addWidget(group)
        return group

    def on_set(self, item):
        if item is None:
            if self.info_group.isVisible():
                self.info_group.setVisible(False)
                self.blank_info_group.setVisible(True)
            else:
                InfoBar.error("错误", "无效数据", parent=self.parent())
        else:
            if self.info_group.isVisible():
                self.sync_groupp_data(item)
            else:
                self.info_group.setVisible(True)
                self.blank_info_group.setVisible(False)
                self.sync_groupp_data(item)

    def sync_groupp_data(self, item):
        header = item.header
        data = item.data
        self.file_name_info.setText(item.filename)
        self.version_info.setText(f"{header.major}, {header.minor}")
        self.map_origin_info.setText(f"{round(data.minBounds.x, 3)}, {round(data.minBounds.y, 3)}, {round(data.minBounds.z, 3)}")
        self.map_size_info.setText(f"{round(data.maxBounds.x, 3)}, {round(data.maxBounds.y, 3)}, {round(data.maxBounds.z, 3)}")
        self.cell_size_info.setText(f"{data.cellSize}")
        self.cell_count_info.setText(f"{data.cellCountX}, {data.cellCountZ}")
        self.cell_total_info.setText(f"{len(data.cellsmap.cells)}")
        self.height_sample_count_info.setText(f"{data.height_samples.vector.count.x}, {data.height_samples.vector.count.y}")
        self.height_sample_offset_info.setText(f"{round(data.height_samples.vector.offset.x)}, {round(data.height_samples.vector.offset.y)}")
        self.min_sample_height_info.setText(f"{round(data.height_samples.min_height_sample)}")
        self.max_sample_height_info.setText(f"{round(data.height_samples.max_height_sample)}")
        self.height_samples_total_info.setText(f"{len(data.height_samples.height_samples)}")
        self.hint_nodes_count_info.setText(f"{len(data.hint_nodes)}")

class ColorMapCanvas(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.layout = QVBoxLayout(self)
        self.image_label = QLabel("预览", self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        self.pixmap = QPixmap(self.image_label.size())
        self.pixmap.fill(Qt.transparent)

    def set_view(self, pixmap, data):
        image_label = self.image_label
        self.fix_image_label_scale(data)
        self.current_pixmap = pixmap.scaled(image_label.width(), image_label.height(), Qt.AspectRatioMode.KeepAspectRatio)
        image_label.setPixmap(self.current_pixmap)

    def draw_ellipse(self, pos, radius, outline_color, fill_color, is_point = False):
        # 需要将current_pixmap的左下角视为坐标原点进行绘制，或者将current_pixmap使用左下对齐的方式强制归零
        painter = QPainter(self.current_pixmap)
        painter.setPen(outline_color)  # 描边
        painter.setBrush(fill_color)  # 填充
        painter.drawEllipse(pos.x-radius/20, pos.y-radius/20, radius/10, radius/10)  # 绘制点
        painter.end()
        self.image_label.setPixmap(self.current_pixmap)
        circle = QListWidgetItem(f"Circle {round(pos.x, 3), round(pos.y, 3)}")
        if is_point == True:
            circle = QListWidgetItem(f"Point {round(pos.x, 3), round(pos.y, 3)}")
        circle.setData(Qt.UserRole, make_circle(pos, radius))
        circle.setCheckState(Qt.Checked)
        self.parent().object_list.addItem(circle)

    def draw_line(self, point_list, outline_color):
        # 需要将current_pixmap的左下角视为坐标原点进行绘制，或者将current_pixmap使用左下对齐的方式强制归零
        if not self.current_pixmap or not point_list or len(point_list) < 2:
            return
        q_points = [QPointF(pt.fixed_value.x, pt.fixed_value.y) for pt in point_list]
        painter = QPainter(self.current_pixmap)
        painter.setPen(outline_color)  # 描边
        painter.setBrush(Qt.transparent)  # 填充
        painter.drawPolyline(q_points)
        painter.end()
        self.image_label.setPixmap(self.current_pixmap)
        line = QListWidgetItem(f"Line {len(q_points)}")
        line.setCheckState(Qt.Checked)
        self.parent().object_list.addItem(line)

    def draw_rect(self, origin, size, outline_color):
        # 需要将current_pixmap的左下角视为坐标原点进行绘制，或者将current_pixmap使用左下对齐的方式强制归零
        painter = QPainter(self.current_pixmap)
        painter.setPen(outline_color)  # 描边
        painter.setBrush(Qt.transparent)  # 填充
        painter.drawRect(origin.x, origin.y, size.x - origin.x, size.y - origin.y)
        painter.end()
        self.image_label.setPixmap(self.current_pixmap)
        rect = QListWidgetItem(f"Rectangle {round(origin.x, 3), round(origin.y, 3)}")
        rect.setData(Qt.UserRole, make_rectangle(origin, size))
        rect.setCheckState(Qt.Checked)
        self.parent().object_list.addItem(rect)

    def fix_image_label_scale(self, current_navgrid_data):
        c = current_navgrid_data.data.cellCountZ/current_navgrid_data.data.cellCountX
        new_size = self.height()*0.95
        self.image_label.setFixedSize(new_size, new_size*c)

    def resizeEvent(self, event):
        max_height = self.parent().height()*0.95
        self.setFixedHeight(min(self.width(), max_height))
        current_navgrid_data = getattr(self.parent(), 'current_navgrid_data', None)
        if current_navgrid_data is not None:
            self.fix_image_label_scale(current_navgrid_data)

class NavGrid_Tool_Interface(ToolInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(parent=parent)
        self.setObjectName('ngrid_Tool_Interface')
        self.build()

    def build(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(12)
        self.build_button(self.layout)
        self.build_view_box(self.layout)
        self.build_data_area(self.layout)

    def build_button(self, layout):
        button_layout = QVBoxLayout(self)
        self.load_btn = create_button(self, "导入文件", self.load_file_from_dialog, button_layout, True, 1)# 导入文件
        self.export_f_btn = create_button(self, "导出文件", self.export_file, button_layout, True, 1)# 导出文件
        self.draw_objects_btn = create_button(self, "绘制对象", self.draw_objects, button_layout, True, 1)# 绘制图形
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def build_view_box(self, layout):
        self.view_box_card = ColorMapCanvas(self)
        layout.addWidget(self.view_box_card)

    def build_data_area(self, layout):
        self.layer_list = ListWidget(self)
        self.layer_list.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义右键菜单
        self.layer_list.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键菜单事件
        self.object_list = ListWidget(self)
        self.object_list.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义右键菜单
        self.object_list.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键菜单事件
        self.data_area_layout = QVBoxLayout(self)
        self.navigation_card = DataType_Navigation_Card(self)
        self.navigation_card.navigation.layout_interface.layout.addWidget(self.layer_list)
        self.navigation_card.navigation.object_interface.layout.addWidget(self.object_list)
        self.info_card = NavGrid_Info_Card(self)
        self.data_area_layout.addWidget(self.navigation_card)
        self.data_area_layout.addWidget(self.info_card)
        layout.addLayout(self.data_area_layout)

    def render_navgrid_data(self, navgrid_data):
        @Slot(object)
        def finalize_render(map_layouts):
            self.map_layout_list = map_layouts
            self.update_layout_navigation_bar()
            self.progress_loop.update_data(InfoBarIcon.SUCCESS, "成功:", "导航数据已加载完毕!", 2000)
        @Slot(str)
        def handle_render_failure(error_message):
            self.progress_loop.update_data(InfoBarIcon.ERROR, "错误:", error_message, 2000)
        self.render_worker = start_worker_flow(RendererWorker(navgrid_data), finalize_render, handle_render_failure)

    def load_file_from_dialog(self):
        last_aimesh_ngrid_file = LOGGERMANAGER.get("aimesh_ngrid_file")
        default_directory = "" if last_aimesh_ngrid_file is None else last_aimesh_ngrid_file
        file, _ = QFileDialog.getOpenFileName(self, "选择文件", default_directory, "Aimesh NGrid Files (*.aimesh_ngrid)")
        if not file:
            return
        self.load_file(file)

    def load_file(self, file):
        @Slot(object)
        def finalize_load(navgrid_data):
            self.current_navgrid_data = navgrid_data
            self.info_card.on_set(self.current_navgrid_data)
            self.render_navgrid_data(self.current_navgrid_data.data)
            self.progress_loop.update_text("等待", "正在渲染数据,稍安勿躁......")
        @Slot(str)
        def handle_load_failure(error_message):
            print(error_message)
            self.progress_loop.update_data(InfoBarIcon.ERROR, "错误:", error_message, 2000)
        LOGGERMANAGER.save("aimesh_ngrid_file", file)
        self.read_worker = start_worker_flow(ReadWorker(file), finalize_load, handle_load_failure)
        self.progress_loop = WaitBar("等待", "正在加载文件,稍安勿躁......", self)
        self.progress_loop.show()

    def export_layer(self, item):
        # 这里选择导出的路径
        last_aimesh_ngrid_filepath, last_aimesh_ngrid_filename = LOGGERMANAGER.split_path("aimesh_ngrid_file")
        basename = os.path.splitext(last_aimesh_ngrid_filename)[0] + f".{item.text().replace(' ', '')}"
        filepath, _ = QFileDialog.getSaveFileName(self, "保存 BMP 文件", last_aimesh_ngrid_filepath + "/" + basename, "BMP Files (*.bmp)")
        if not filepath:
            return
        try:
            with open(filepath, 'wb') as f:
                write_bmp_file(f, item, self.current_navgrid_data.data)
            InfoBar.success("导出文件成功", f"{filepath}", parent=self)
        except Exception as e:
            InfoBar.error("错误", f"文件导出失败: {e}", parent=self)
            print("错误", f"文件导出失败: {e}")

    def export_file(self):
        current_navgrid_data = getattr(self, 'current_navgrid_data', None)
        if current_navgrid_data is not None:
            self.export_options = NavGrid_ExportOptions(self)
            self.export_options.show()
        else:
            InfoBar.warning("Tips:", f"Please import the file first.", parent=self)

    def draw_objects(self):
        current_navgrid_data = getattr(self, 'current_navgrid_data', None)
        if current_navgrid_data is not None:
            self.drawobjects_options = NavGrid_DrawObjects_Options(self)
            self.drawobjects_options.show()
        else:
            InfoBar.warning("Tips:", f"Please import the file first.", parent=self)

    def show_context_menu(self, pos):
        item = self.layer_list.itemAt(pos)  # 获取当前点击的项目
        if item:
            menu = RoundMenu(parent=self)  # 创建菜单
            selected_action = Action(FIF.CHECKBOX, 'Selected Layer', self)  # 创建菜单项
            selected_action.triggered.connect(lambda: self.selected_layer(item))  # 点击时触发
            menu.addAction(selected_action)  # 添加菜单项
            export_action = Action(FIF.SAVE, 'Export Layer', self)  # 创建菜单项
            export_action.triggered.connect(lambda: self.export_layer(item))  # 点击时触发
            menu.addAction(export_action)  # 添加菜单项
            replace_action = Action(FIF.UPDATE, 'Replace Layer', self)  # 创建菜单项
            replace_action.triggered.connect(lambda: self.replace_layer(item))  # 点击删除时触发
            menu.addAction(replace_action)  # 添加菜单项
            delete_action = Action(FIF.DELETE, 'Delete Layer', self)  # 创建菜单项
            delete_action.triggered.connect(lambda: self.delete_layer(item))  # 点击删除时触发
            menu.addAction(delete_action)  # 添加菜单项
            menu.exec_(self.layer_list.mapToGlobal(pos))  # 显示菜单

    def update_layout_navigation_bar(self):
        self.layer_list.clear()
        # 向 ListWidget 中添加视图条目
        # 图层名称和对应的 pixmap
        layers = [
            ("Vision Pathing", self.map_layout_list[0]),
            ("Height Samples", self.map_layout_list[1]),
            ("River Regions", self.map_layout_list[2]),
            ("Jungle Quadrants", self.map_layout_list[3]),
            ("Main Region", self.map_layout_list[4]),
            ("Nearest Lane", self.map_layout_list[5]),
            ("POI Flags", self.map_layout_list[6]),
            ("Ring Flags", self.map_layout_list[7]),
            ("SRX Flags", self.map_layout_list[8])
        ]
        for layer_name, color_data in layers:
            item = QListWidgetItem(layer_name)
            # 设置每个图层的pixmap作为item的额外数据
            flipped_image = convert_to_image(color_data).mirrored(False, True)
            pixmap = QPixmap.fromImage(flipped_image)
            item.setData(Qt.UserRole, pixmap)
            self.layer_list.addItem(item)
        self.selected_layer(self.layer_list.item(0))
        self.layer_list.itemClicked.connect(self.update_map_layers)

    def update_map_layers(self, item):
        layer_name = item.text()
        pixmap = item.data(Qt.UserRole)
        self.view_box_card.set_view(pixmap, self.current_navgrid_data)

    def selected_layer(self, item):
        self.layer_list.setCurrentItem(item)
        self.update_map_layers(item)

    def replace_layer(self, item):
        pass

    def delete_layer(self, item):
        print(f"Deleting Layer: {item.text()}")
        row = self.layer_list.row(item)  # 获取当前项的索引
        self.layer_list.takeItem(row)  # 从列表中移除该项