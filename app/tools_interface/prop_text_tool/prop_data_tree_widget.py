import sys
from dataclasses import is_dataclass, fields
from ..build import*
from ...components.dialog_widget import DialogWidget
from ...core.objects.prop_text.base_value import*

class PropData_TreeWidget(DialogWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.build()

    def build(self):
        card = CardWidget(self)
        output_layout = QVBoxLayout(card)
        self.outputTree = TreeWidget(self)
        self.outputTree.setHeaderLabels(["Name", "Value"])
        self.outputTree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 自动调整第1列宽度
        self.outputTree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 自动调整第2列宽度
        self.outputTree.header().setHidden(True)
        output_layout.addWidget(self.outputTree)
        card.setLayout(output_layout)
        self.viewLayout.addWidget(card)

    def build_button(self):
        self.button_layout = QVBoxLayout()
        self.exit_button = PushButton(self.tr('Cancel'), self)
        self.button_layout.addWidget(self.exit_button)
        self.exit_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.button_layout.setAlignment(Qt.AlignCenter)  # 居中按钮
        self.viewLayout.addLayout(self.button_layout)  # 将按钮布局添加到主布局中
        self.exit_button.clicked.connect(self._MessageBoxBase__onCancelButtonClicked)

    def showPropAsTree(self, obj):
        """把解析后的对象展示到 Tree（支持 dataclass / dict / list / tuple / 基本类型，跳过 None 值）"""
        self.outputTree.clear()
        self.outputTree.setColumnCount(2)
        # self.outputTree.setHeaderLabels(["Name", "Value"])

        root = QTreeWidgetItem(["PropFile", ""])
        self.outputTree.addTopLevelItem(root)

        def short_repr(v, maxlen=120):
            if v is None:
                return ""
            if isinstance(v, str):
                s = v.strip()
                return s if len(s) <= maxlen else s[:maxlen] + "…"
            if isinstance(v, (int, float, bool)):
                return str(v)
            return f"<{type(v).__name__}>"

        def add_node(parent_item, name, value):
            # 跳过 None
            if value is None:
                return
            
            if is_dataclass(value):
                if isinstance(value, (vec2, vec3, vec4)):  # 对于 Vec2, Vec3, Vec4 类型
                    node = QTreeWidgetItem([str(name), f"{value}"])
                    parent_item.addChild(node)
                else:
                    node = QTreeWidgetItem([str(name), type(value).__name__])
                    parent_item.addChild(node)
                    for f in fields(value):
                        v = getattr(value, f.name)
                        if v is not None:  # ✅ 跳过 None
                            add_node(node, f.name, v)

            elif isinstance(value, dict):
                if not value:  # 空 dict 不展示
                    return
                node = QTreeWidgetItem([str(name), f"dict[{len(value)}]"])
                parent_item.addChild(node)
                for k, v in value.items():
                    if v is not None:  # ✅ 跳过 None
                        add_node(node, str(k), v)

            elif isinstance(value, (list, tuple)):
                if not value:  # 空 list 不展示
                    return
                node = QTreeWidgetItem([str(name), f"list[{len(value)}]"])
                parent_item.addChild(node)
                for i, v in enumerate(value):
                    if v is not None:  # ✅ 跳过 None
                        add_node(node, f"[{i}]", v)
            else:
                leaf = QTreeWidgetItem([str(name), short_repr(value)])
                parent_item.addChild(leaf)

        if is_dataclass(obj):
            for f in fields(obj):
                v = getattr(obj, f.name)
                if v is not None:  # ✅ 跳过 None
                    add_node(root, f.name, v)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if v is not None:
                    add_node(root, k, v)
        elif isinstance(obj, (list, tuple)):
            for i, v in enumerate(obj):
                if v is not None:
                    add_node(root, f"[{i}]", v)
        else:
            if obj is not None:
                add_node(root, "value", obj)

        self.outputTree.expandToDepth(1)
