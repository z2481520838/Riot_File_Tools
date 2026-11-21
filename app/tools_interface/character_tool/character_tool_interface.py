# coding: utf-8
"""app.tools_interface.character_tool — 角色预览工具(Fluent UI + 官方链)。

v1(测试分支): 单页集成 3D 视口(软光栅) + 官方一键链导入(.ini/.inibin →
皮肤包 → .skn/.skl/.blnd/贴图) + 动画播放/Sequencer + 事件表自动桥接
(SubmeshVisibility 播放期生效) + 相机预设/视图模式/子网格显隐。
目标: ltk-manager 水准的角色可视化(地图网格体可视化预留同层扩展)。"""
import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QSizePolicy,
                               QFileDialog, QListWidgetItem)
from qfluentwidgets import (CardWidget, PushButton, PrimaryPushButton,
                            ComboBox, SwitchButton, Slider, ListWidget,
                            BodyLabel, StrongBodyLabel, TitleLabel, InfoBar,
                            InfoBarPosition, FluentIcon)

from ..tool_interface import ToolInterface
from ...core.character.viewport import (Viewport, CAMERA_LABELS,
                                         CAMERA_PRESETS, VIEW_MODE_LABELS,
                                         VIEW_MODES)

_DECIMATE = [(1, '全部'), (2, '精细 1/2'), (4, '平衡 1/4'),
             (8, '流畅 1/8'), (16, '极简 1/16')]
_SPEEDS = ['0.25x', '0.5x', '1x', '1.5x', '2x', '4x']


class Character_Tool_Interface(ToolInterface):
    """角色预览工具页。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('character_Tool_Interface')
        self._timer = None
        self._dragging_slider = False
        self._build()
        self._wire()

    # ------------------------------------------------------------- UI 构建
    def _build(self):
        head = QHBoxLayout()
        t = TitleLabel('角色预览器', self)
        st = BodyLabel('LoL 4.20/4.17 官方链: .ini/.inibin → 皮肤包 → '
                       '模型+骨架+动画池+材质 → 软光栅 3D 预览(动画事件 '
                       'SubmeshVisibility 播放期生效)', self)
        t.setFixedHeight(34)
        head.addWidget(t)
        head.addSpacing(10)
        head.addWidget(st, 1, Qt.AlignBottom)
        self.vBoxLayout.insertLayout(0, head)

        # —— 控制卡片(导入行) ——
        import_card = CardWidget(self)
        il = QHBoxLayout(import_card)
        il.setContentsMargins(16, 12, 16, 12)
        il.setSpacing(10)
        self.import_pkg_btn = PrimaryPushButton(FluentIcon.FOLDER, '导入角色包', import_card)
        self.import_pkg_btn.setToolTip('.ini/.inibin → 官方皮肤链一键装配')
        self.import_skn_btn = PushButton(FluentIcon.TILES, '导入 .skn', import_card)
        self.import_anm_btn = PushButton(FluentIcon.VIDEO, '导入 .anm', import_card)
        self.import_blnd_btn = PushButton(FluentIcon.ALBUM, '导入 .blnd', import_card)
        self.skin_combo = ComboBox(import_card)
        self.skin_combo.setFixedWidth(210)
        self.skin_combo.setToolTip('皮肤包(Skin%02d/Base 节) — 选择后一键载入')
        for w in (self.import_pkg_btn, self.import_skn_btn,
                  self.import_anm_btn, self.import_blnd_btn):
            il.addWidget(w)
        il.addWidget(self.skin_combo)
        il.addStretch(1)
        self.vBoxLayout.addWidget(import_card)

        # —— 主区: 视口 + 右栏 ——
        main = QHBoxLayout()
        main.setSpacing(12)

        # 视口卡片
        self.vp_card = CardWidget(self)
        vl = QVBoxLayout(self.vp_card)
        vl.setContentsMargins(6, 6, 6, 6)
        self.vp = Viewport(self.vp_card)
        self.vp.setMinimumSize(640, 480)
        self.vp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vl.addWidget(self.vp, 1)
        main.addWidget(self.vp_card, 5)

        # 右栏
        right = QVBoxLayout()
        right.setSpacing(10)

        # 动画列表卡片
        anm_card = CardWidget(self)
        al = QVBoxLayout(anm_card)
        al.setContentsMargins(12, 10, 12, 12)
        al.setSpacing(6)
        al.addWidget(StrongBodyLabel('动画资产(事件表自动桥接)', anm_card))
        self.anm_list = ListWidget(anm_card)
        self.anm_list.setFixedHeight(168)
        self.anm_list.setToolTip('双击切换动画; blnd 在池时按官方引用链自动绑定事件表')
        al.addWidget(self.anm_list)
        play_row = QHBoxLayout()
        self.play_btn = PrimaryPushButton(FluentIcon.PLAY, '播放', anm_card)
        self.play_btn.setFixedWidth(96)
        self.speed_combo = ComboBox(anm_card)
        self.speed_combo.addItems(_SPEEDS)
        self.speed_combo.setCurrentIndex(2)
        self.speed_combo.setFixedWidth(84)
        self.time_lbl = BodyLabel('帧 -/- · t 0.00s', anm_card)
        play_row.addWidget(self.play_btn)
        play_row.addWidget(self.speed_combo)
        play_row.addStretch(1)
        play_row.addWidget(self.time_lbl)
        al.addLayout(play_row)
        self.time_slider = Slider(Qt.Horizontal, anm_card)
        self.time_slider.setRange(0, 1000)
        self.time_slider.setEnabled(False)
        al.addWidget(self.time_slider)
        right.addWidget(anm_card)

        # 视图控制卡片
        view_card = CardWidget(self)
        wl = QVBoxLayout(view_card)
        wl.setContentsMargins(12, 10, 12, 12)
        wl.setSpacing(8)
        wl.addWidget(StrongBodyLabel('视图 / 相机', view_card))
        row1 = QHBoxLayout()
        self.cam_combo = ComboBox(view_card)
        self.cam_combo.addItems([CAMERA_LABELS[k] for k in CAMERA_PRESETS])
        self.cam_combo.setCurrentIndex(1)
        self.cam_combo.setFixedWidth(118)
        self.mode_combo = ComboBox(view_card)
        self.mode_combo.addItems([VIEW_MODE_LABELS[m] for m in VIEW_MODES])
        self.mode_combo.setFixedWidth(150)
        self.dec_combo = ComboBox(view_card)
        self.dec_combo.addItems([t for _k, t in _DECIMATE])
        self.dec_combo.setCurrentIndex(0)
        self.dec_combo.setFixedWidth(96)
        self.dec_combo.setToolTip('渲染精度(三角形抽稀; 默认全量)')
        row1.addWidget(self.cam_combo)
        row1.addWidget(self.mode_combo)
        row1.addWidget(self.dec_combo)
        row1.addStretch(1)
        wl.addLayout(row1)
        row2 = QHBoxLayout()
        self.fluid_sw = SwitchButton('交互流畅模式', view_card)
        self.skel_sw = SwitchButton('骨架', view_card)
        self.grid_sw = SwitchButton('地面网格', view_card)
        self.grid_sw.setChecked(True)
        self.tex_sw = SwitchButton('贴图插值', view_card)
        self.tex_sw.setChecked(True)
        row2.addWidget(self.fluid_sw)
        row2.addWidget(self.skel_sw)
        row2.addWidget(self.grid_sw)
        row2.addWidget(self.tex_sw)
        row2.addStretch(1)
        wl.addLayout(row2)
        right.addWidget(view_card)

        # 子网格卡片
        sub_card = CardWidget(self)
        sl = QVBoxLayout(sub_card)
        sl.setContentsMargins(12, 10, 12, 12)
        sl.setSpacing(6)
        sl.addWidget(StrongBodyLabel('子网格(双层显隐: 引擎事件层 ∪ 用户层)', sub_card))
        self.sub_list = ListWidget(sub_card)
        self.sub_list.setFixedHeight(148)
        sl.addWidget(self.sub_list)
        right.addWidget(sub_card)

        # 状态
        self.status_lbl = BodyLabel('未加载 — 导入角色包(.ini/.inibin)官方链一键装配', self)
        self.status_lbl.setWordWrap(True)
        right.addWidget(self.status_lbl)

        main.addLayout(right, 3)
        self.vBoxLayout.addLayout(main, 1)
        self.vBoxLayout.addStretch(0)

        # 播放器(视口就绪后)
        from ...core.character.player import Player
        self.player = Player(self.vp)
        self.player.cb_status = self._on_status
        self.player.cb_time = self._on_time
        self.player.cb_mask_changed = self._refresh_submeshes
        self.player.cb_anm_changed = self._refresh_anm_list
        self.player.cb_blnd_changed = self._refresh_blnd_clips

    # ------------------------------------------------------------- 信号接线
    def _wire(self):
        self.import_pkg_btn.clicked.connect(self._open_config)
        self.import_skn_btn.clicked.connect(self._open_skn)
        self.import_anm_btn.clicked.connect(self._open_anm)
        self.import_blnd_btn.clicked.connect(self._open_blnd)
        self.skin_combo.currentIndexChanged.connect(self._pick_skin)
        self.play_btn.clicked.connect(self._toggle_play)
        self.speed_combo.currentIndexChanged.connect(self._pick_speed)
        self.time_slider.sliderPressed.connect(self._slider_pressed)
        self.time_slider.sliderReleased.connect(self._slider_released)
        self.time_slider.valueChanged.connect(self._slider_moved)
        self.anm_list.itemDoubleClicked.connect(
            lambda item: self._pick_anm(self.anm_list.row(item)))
        self.cam_combo.currentIndexChanged.connect(self._pick_cam)
        self.mode_combo.currentIndexChanged.connect(self._pick_mode)
        self.dec_combo.currentIndexChanged.connect(self._pick_decimate)
        self.fluid_sw.checkedChanged.connect(
            lambda on: setattr(self.vp, 'fluid_mode', bool(on)))
        self.skel_sw.checkedChanged.connect(self._pick_skeleton)
        self.grid_sw.checkedChanged.connect(
            lambda on: setattr(self.vp, 'show_grid', bool(on)))
        self.tex_sw.checkedChanged.connect(
            lambda on: setattr(self.vp, 'tex_filter', bool(on)))
        self.sub_list.itemChanged.connect(self._sub_toggled)
        self.setAcceptDrops(True)

    # ----------------------------------------------------------- 回调接收
    def _on_status(self, msg):
        self.status_lbl.setText(msg)

    def _on_time(self, fidx, total, t, dur):
        self.time_lbl.setText('帧 %d/%d · t %.2fs / %.2fs'
                              % (fidx, total, t, dur))
        if not self._dragging_slider:
            self.time_slider.setValue(int(min(t / max(dur, 1e-6), 1.0) * 1000))

    # ------------------------------------------------------------- 导入链
    def _open_config(self):
        p, _ = QFileDialog.getOpenFileName(
            self, '导入角色配置(官方链一键装配)', '',
            '角色配置 (*.ini *.inibin *.cfg);;所有文件 (*.*)')
        if not p:
            return
        try:
            self.player.load_config(os.path.abspath(p))
        except Exception as e:
            InfoBar.error('解析失败', str(e), parent=self,
                          position=InfoBarPosition.TOP_RIGHT, duration=3000)
            return
        self._refresh_skins()
        InfoBar.success('已载入角色配置', '%s · 皮肤包 %d 个'
                        % (os.path.basename(p), len(self.player._skin_pkgs)),
                        parent=self, position=InfoBarPosition.TOP_RIGHT,
                        duration=2200)
        if self.player._skin_pkgs:
            self.skin_combo.setCurrentIndex(1)
            self._pick_skin(1)

    def _open_skn(self):
        p, _ = QFileDialog.getOpenFileName(self, '导入 .skn', '',
                                           '模型 (*.skn);;所有文件 (*.*)')
        if not p:
            return
        try:
            self.player.load_skn(os.path.abspath(p))
            self.vp.fit_camera(animate=False)
            self.vp.request_render()
            self._refresh_submeshes()
        except Exception as e:
            InfoBar.error('加载失败', str(e), parent=self,
                          position=InfoBarPosition.TOP_RIGHT, duration=3000)

    def _open_anm(self):
        p, _ = QFileDialog.getOpenFileName(self, '导入 .anm', '',
                                           '动画 (*.anm);;所有文件 (*.*)')
        if not p:
            return
        try:
            self.player.load_anm(os.path.abspath(p))
            self._refresh_anm_list()
            self._pick_anm(len(self.player.anm_list) - 1)
        except Exception as e:
            InfoBar.error('解析失败', str(e), parent=self,
                          position=InfoBarPosition.TOP_RIGHT, duration=3000)

    def _open_blnd(self):
        p, _ = QFileDialog.getOpenFileName(self, '导入 .blnd(动画池+事件表)', '',
                                           '动画池 (*.blnd);;所有文件 (*.*)')
        if not p:
            return
        try:
            ba = self.player.load_blnd(os.path.abspath(p))
            InfoBar.success('动画池已载入', '%d 事件表 · %d clip · %d .anm 引用'
                            % (len(ba.events), len(ba.pool_clips),
                               len(ba.anim_refs)),
                            parent=self, position=InfoBarPosition.TOP_RIGHT,
                            duration=2200)
            self._refresh_blnd_clips()
        except Exception as e:
            InfoBar.error('解析失败', str(e), parent=self,
                          position=InfoBarPosition.TOP_RIGHT, duration=3000)

    # ------------------------------------------------------------ 皮肤包
    def _refresh_skins(self):
        self.skin_combo.blockSignals(True)
        self.skin_combo.clear()
        self.skin_combo.addItem('(选择皮肤包)')
        for pkg in self.player.skin_packages():
            r = pkg.get('resolved') or {}
            tags = '·'.join(k for k in ('skn', 'skl', 'blnd')
                           if r.get(k)) or '无模型'
            self.skin_combo.addItem('%s — %s' % (pkg['section'], tags))
        self.skin_combo.blockSignals(False)

    def _pick_skin(self, idx):
        pkgs = self.player.skin_packages()
        if not (1 <= idx <= len(pkgs)):
            return
        ok = self.player.load_skin_package(pkgs[idx - 1])
        if ok:
            self.vp.fit_camera(animate=False)
            self.vp.request_render()
            self._refresh_submeshes()
            self._refresh_anm_list()

    # ------------------------------------------------------------- 动画播放
    def _refresh_anm_list(self):
        self.anm_list.blockSignals(True)
        self.anm_list.clear()
        for a in self.player.anm_list:
            self.anm_list.addItem('%s  [%.2fs]' % (os.path.basename(a.path),
                                                   a.duration))
        self.anm_list.blockSignals(False)
        self.time_slider.setEnabled(bool(self.player.anm_list))
        if self.player.anm_list:
            cur = self.player.anm_list.index(self.player.anm) \
                if self.player.anm in self.player.anm_list else 0
            self.anm_list.setCurrentRow(cur)

    def _refresh_blnd_clips(self):
        ba = getattr(self.player, '_ev_blnd', None)
        if ba is None:
            return
        self._on_status('动画池: %d 事件表 · clip %d · 外置 .anm %d'
                         % (len(ba.events), len(ba.pool_clips),
                            len(ba.anim_refs)))

    def _pick_anm(self, idx):
        if not (0 <= idx < len(self.player.anm_list)):
            return
        self.player.select_anm(self.player.anm_list[idx])
        self._ensure_timer()
        if self.player.playing:
            self.player.start_play()

    def _toggle_play(self):
        if self.player.anm is None:
            InfoBar.warning('无动画', '先导入 .anm 或角色包(blnd 官方池引用)',
                            parent=self, position=InfoBarPosition.TOP_RIGHT,
                            duration=2500)
            return
        self._ensure_timer()
        self.player.toggle_play()
        self.play_btn.setText('暂停' if self.player.playing else '播放')

    def _ensure_timer(self):
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._on_tick)
            self._timer.start(15)

    def _on_tick(self):
        if not self.player.playing:
            return
        delay = self.player.tick()
        if delay is not None:
            self._timer.setInterval(int(delay))

    def _pick_speed(self, idx):
        self.player.set_speed(float(_SPEEDS[idx].rstrip('x')))

    # ------------------------------------------------------------- 时间轴
    def _slider_pressed(self):
        self._dragging_slider = True
        if self.player.playing:
            self.player.pause_play()
            self.play_btn.setText('播放')

    def _slider_released(self):
        self._dragging_slider = False

    def _slider_moved(self, v):
        anm = self.player.anm
        if anm is None:
            return
        t = v / 1000.0 * anm.duration
        self.player.seek(t)
        fps = anm.fps if 0.5 < anm.fps < 240 else 30.0
        self._on_time(int(t * fps), int(anm.duration * fps), t, anm.duration)

    # ------------------------------------------------------------- 视图控制
    def _pick_cam(self, idx):
        key = CAMERA_PRESETS[idx] if 0 <= idx < len(CAMERA_PRESETS) else 'orbit'
        self.vp.set_preset(key, animate=True, refit=False, restore=True)

    def _pick_mode(self, idx):
        mode = VIEW_MODES[idx] if 0 <= idx < len(VIEW_MODES) else 'lit'
        self.vp.set_view_mode(mode)

    def _pick_decimate(self, idx):
        self.vp.set_decimate(_DECIMATE[idx][0] if 0 <= idx < len(_DECIMATE)
                             else 1)
        self.vp.request_render()

    def _pick_skeleton(self, on):
        self.vp.show_skeleton = bool(on)
        self.vp.request_render()

    # ------------------------------------------------------------- 子网格
    def _refresh_submeshes(self):
        self.sub_list.blockSignals(True)
        self.sub_list.clear()
        m = self.player.m
        if m is not None:
            vis = self.vp.sub_visible
            for s in m['subs']:
                it = QListWidgetItem('%s  ·  %d 三角形'
                                     % (s['name'][:26], s['ic'] // 3))
                it.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                it.setCheckState(Qt.Checked if vis.get(s['name'], True)
                                 else Qt.Unchecked)
                self.sub_list.addItem(it)
        self.sub_list.blockSignals(False)

    def _sub_toggled(self, item):
        idx = self.sub_list.row(item)
        m = self.player.m
        if m is None or not (0 <= idx < len(m['subs'])):
            return
        name = m['subs'][idx]['name']
        self.player.set_user_sub_visibility(name,
                                            item.checkState() == Qt.Checked)

    # ------------------------------------------------------------- 拖放导入
    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            ext = os.path.splitext(p)[1].lower()
            try:
                if ext in ('.ini', '.inibin', '.cfg'):
                    self.player.load_config(p)
                    self._refresh_skins()
                    if self.player._skin_pkgs:
                        self.skin_combo.setCurrentIndex(1)
                        self._pick_skin(1)
                elif ext == '.skn':
                    self.player.load_skn(p)
                    self._refresh_submeshes()
                elif ext == '.anm':
                    self.player.load_anm(p)
                    self._refresh_anm_list()
                elif ext == '.blnd':
                    self.player.load_blnd(p)
                elif ext == '.skl' and self.player.m is not None:
                    from ...core.character import parse_skl, Rig
                    self.player.rig = Rig(parse_skl(p))
            except Exception as ex:
                InfoBar.error('导入失败', '%s: %s' % (os.path.basename(p), ex),
                              parent=self, position=InfoBarPosition.TOP_RIGHT,
                              duration=3000)
        e.acceptProposedAction()
        self.vp.fit_camera(animate=False)
        self.vp.request_render()
