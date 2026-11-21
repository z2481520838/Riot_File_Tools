# coding: utf-8
"""app.core.character.viewport — Qt(PySide6) 软光栅 3D 视口。

自 v8.3 Tk Canvas 视口移植(ltk-manager 视口语义对齐层全量保留):
  · 相机预设 game/orbit/top/front/side(cameraPresets.ts)+ 逐预设记忆
    + 平滑过渡(DRAG_SMOOTHING/PRESET_TRANSITION τ)
  · 视图模式 lit/unshaded/untextured/wireframe(+ 线框叠加透明度)
  · numpy 帧缓冲软光栅: 顶点剔除/排序/分块预算(_RASTER_PIX_BUDGET)/
    交互自适应分辨率(播放下限 0.60)/贴图双线性/8 级平面着色/地面网格
  · 朝向 gizmo(Qt paintEvent 自绘)/HUD 条带缓存/骨架叠加
  · 输入: 左拖旋/中右拖平移/滚轮缩放(Qt 事件 → v8.3 处理器桥)
Tk 耦合已全部替换: canvas → QWidget, after() → QTimer,
PhotoImage blit → QImage + paintEvent, PostScript 导出 → PNG。"""

from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QImage, QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import QWidget, QApplication

from ._compat import (math, os, re, time,      # noqa: F401
                      _PILImage, _PILDraw, _PILFont, PIL_OK,
                      _np, NP_OK)
from .core import _RASTER_PIX_BUDGET   # 引擎常量块(分块光栅预算)

SUB_COLORS = ['#e0564f', '#4f9fe0', '#59b35c', '#d9a33c', '#9a6fd0', '#3fae9b',
              '#e0784f', '#c94f9e', '#7f8ee0', '#a8bd54', '#e05f8a', '#54bdc9',
              '#d0705f', '#8fc46a', '#e0a54f', '#b09be0']

BG_COLOR = '#12151c'
HUD_COLOR = '#9fb3c8'
SKELETON_COLOR = '#39d0ff'
JOINT_COLOR = '#ffd23d'


def _hex_rgb(h):
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


_SUB_RGB = [_hex_rgb(c) for c in SUB_COLORS]
_BG_RGB = _hex_rgb(BG_COLOR)
_HUD_RGB = _hex_rgb(HUD_COLOR)
_SKEL_RGB = _hex_rgb(SKELETON_COLOR)
_JOINT_RGB = _hex_rgb(JOINT_COLOR)
_SEL_RGB = (0xff, 0x40, 0x40)
_NAME_RGB = (0x8f, 0xd8, 0xff)
_NOTE_RGB = (0x6e, 0xe7, 0xa0)
_LAMP = (0.35, 0.5, 0.79)

# ----------------------------------------------------------------------
# v7: ltk-manager 视口常数(https://github.com/LeagueToolkit/ltk-manager
# src/modules/viewport — 逐文件对齐; 注释标注每个常数的来源文件)
# ----------------------------------------------------------------------
UNITS_PER_METRE = 100.0        # shared/utils/space.ts: 引擎单位/米(near=2 far=20000)
CHAMPION_HEIGHT = 200.0        # shared/utils/space.ts: 冠军身高(取景兜底尺度)
_NEAR_PLANE = UNITS_PER_METRE / 50.0      # cameraPresets.ts CAMERA.near = 2
_FAR_PLANE = UNITS_PER_METRE * 200.0      # cameraPresets.ts CAMERA.far = 20000
FIT_MARGIN = 1.15              # framing.ts MARGIN: 取景留白
ORTHO_STAND_OFF = 4.0          # framing.ts STAND_OFF: 正交相机立于 4·radius
GAME_PITCH_DEG = 56.0          # cameraPresets.ts GAME_PITCH: 对局相机俯仰(水平面下)
GAME_FOV_DEG = 40.0            # cameraPresets.ts GAME_FOV = CameraConfig.ZoomFov
GAME_ZOOM = (1000.0, 2250.0)   # cameraPresets.ts GAME_ZOOM(mZoomMin/MaxDistance)
ORBIT_FOV_DEG = 45.0           # cameraPresets.ts CAMERA.fov(环绕透视)
OPENING_REACH = CHAMPION_HEIGHT * 3.0     # SceneCamera.tsx: 无可取景时的开屏立距
DRAG_SMOOTHING_TAU = 0.10       # SceneCamera.tsx DRAG_SMOOTHING=0.06/帧@60fps ≈ τ0.28s;
                                # 软件光栅器像素级拖动取 τ=0.1s(仍「读作直连」)
PRESET_TRANSITION_TAU = 0.25    # 预设/轴吸附切换动画时间常数(≈250ms 到位)
EDGE_OVERLAY_OPACITY = 0.6     # viewMode.ts EDGE_OVERLAY_OPACITY: 线框叠加不透明度
_GIZMO_AXES = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
_GIZMO_RGB = ((0xe0, 0x56, 0x56), (0x56, 0xb3, 0x5c), (0x4f, 0x9f, 0xe0))
_PITCH_MAX = math.pi / 2.0           # v7: 轴向视图需 ±90° 俯仰(ltk 正交预设)
_FREE_ZOOM = (_NEAR_PLANE * 4.0, _FAR_PLANE / 2.0)   # SceneCamera.tsx FREE_ZOOM


def _fov_deg_to_focal(fov_deg):
    """垂直视场(°) → 720 基准像素焦距(本查看器 focal 单位; v6 惯例)。
    focal = (720/2)/tan(fov/2) — cameraPresets.ts fov 语义的像素等价。"""
    return 360.0 / math.tan(math.radians(fov_deg) / 2.0)


# 相机预设表(cameraPresets.ts CAMERA_STANDS 的本查看器映射):
#   look = 相机立于目标的哪一侧(单位向量, target→camera);
#   fov = 垂直视场°(透视预设); zoom = 推拉范围(引擎单位)或 None=自由;
#   ortho = 正交预设(top 的屏幕上向 = 世界 +Z — 与 ltk TOP_UP 一致)。
_CAM_PRESET_INFO = {
    'game': dict(label='游戏相机',
                 look=(0.0, math.sin(math.radians(GAME_PITCH_DEG)),
                       -math.cos(math.radians(GAME_PITCH_DEG))),
                 ortho=False, fov=GAME_FOV_DEG, zoom=GAME_ZOOM),
    'orbit': dict(label='环绕', ortho=False, look=None, fov=ORBIT_FOV_DEG,
                  zoom=None),
    'top': dict(label='顶视图', ortho=True, look=(0.0, 1.0, 0.0)),
    'front': dict(label='前视图', ortho=True, look=(0.0, 0.0, 1.0)),
    'side': dict(label='侧视图', ortho=True, look=(1.0, 0.0, 0.0)),
}
CAMERA_PRESETS = ('game', 'orbit', 'top', 'front', 'side')   # cameraPresets.ts 顺序
CAMERA_LABELS = dict((k, v['label']) for k, v in _CAM_PRESET_INFO.items())

# 视图模式(viewMode.ts VIEW_MODES): lit/unshaded/untextured/wireframe
VIEW_MODES = ('lit', 'unshaded', 'untextured', 'wireframe')
VIEW_MODE_LABELS = {'lit': '材质(贴图+光照)', 'unshaded': '无光照(贴图原色)',
                    'untextured': '纯色+光照', 'wireframe': '线框'}

# PIL HUD 中文回退字体链(Windows/macOS/Linux 各自的内置 CJK 字体)
_HUD_FONT_CANDS = (
    '/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf',
    '/usr/share/fonts/truetype/chinese/NotoSansSC-Bold.ttf',
    '/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf',
    'C:/Windows/Fonts/msyh.ttc',
    'C:/Windows/Fonts/simhei.ttf',
    'C:/Windows/Fonts/simsun.ttc',
    '/System/Library/Fonts/PingFang.ttc',
)
_HUD_FONT = None


def _pil_hud_font():
    """获取支持中文的 PIL 字体(全平台回退链); 失败退回默认位图字体。"""
    global _HUD_FONT
    if _HUD_FONT is not None:
        return _HUD_FONT
    if PIL_OK:
        for cand in _HUD_FONT_CANDS:
            try:
                _HUD_FONT = _PILFont.truetype(cand, 11)
                return _HUD_FONT
            except Exception:
                continue
        try:
            _HUD_FONT = _PILFont.load_default(size=11)
            return _HUD_FONT
        except Exception:
            pass
        try:
            _HUD_FONT = _PILFont.load_default()
            return _HUD_FONT
        except Exception:
            pass
    _HUD_FONT = False
    return False


def _cam_rows(yaw, pitch):
    """帧内复用的旋转量(避免逐顶点重算三角函数 — v1 的主要热点之一)。"""
    return math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)


def _project_view(p, target, cy, sy, cp, sp):
    """世界 -> 视空间(x1, y2, z2); z2 未含 dist。"""
    dx = p[0] - target[0]
    dy = p[1] - target[1]
    dz = p[2] - target[2]
    x1 = cy * dx + sy * dz
    z1 = -sy * dx + cy * dz
    y2 = cp * dy - sp * z1
    z2 = sp * dy + cp * z1
    return (x1, y2, z2)


def _view_to_screen(x1, y2, z2, dist, f, w, h, k=None):
    """视空间 -> 屏幕(v1 兼容式; k 给定 = v7 正交投影: u = w/2 + k·x1,
    免透视除法; 画家深度 zc = z2 + dist 两种投影通用)。"""
    zc = z2 + dist
    if k is not None:
        return (w / 2.0 + k * x1, h / 2.0 - k * y2, zc)
    if zc < 1e-3:
        return None
    return (w / 2.0 + f * x1 / zc, h / 2.0 - f * y2 / zc, zc)


def _look_to_yaw_pitch(look):
    """v7: ltk 相机 look(target→camera 单位向量) → 本查看器 yaw/pitch。
    本查看器相机偏移 = dist·(cp·sy, -sp, -cp·cy) ⇒ sp = -Ly,
    sy = Lx/cp, cy = -Lz/cp(cameraPresets.ts GAME_LOOK 等的等价映射);
    look = +Y 时 yaw=0 → 屏幕上向 = 世界 +Z = ltk TOP_UP 一致。"""
    ly = max(-1.0, min(1.0, look[1]))
    sp = -ly
    cp = math.sqrt(max(0.0, 1.0 - sp * sp))
    if cp < 1e-9:
        return (0.0, math.asin(sp))       # 正顶/正底视图(ltk top)
    yaw = math.atan2(look[0] / cp, -look[2] / cp)
    return (yaw, math.asin(sp))


class Viewport(QWidget):
    """3D 视口: mesh + 可选骨架叠加; 支持蒙皮后顶点位置(动画)。

    公共 API 与 v1 兼容(set_model / set_decimate / set_positions /
    request_render / fit_camera / dump_postscript); v2 新增:
      · set_tint_map({子网格名: (r,g,b)}) + use_tint — 官方贴图均色着色;
      · force_canvas — 冒烟测试强制 Canvas 路径(矢量 PostScript 导出);
      · 交互 LOD + 停手全量(见文件头性能提示)。"""

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setMinimumSize(280, 240)
        self.setMouseTracking(True)
        self._qimg = None
        self._qimg_data = None
        self._gizmo_heads = None
        self._note_text = None
        self.yaw = 0.6
        self.pitch = 0.35
        self.dist = 260.0
        self.target = (0.0, 0.0, 0.0)
        self.focal = 900.0
        # ---- v7 ltk-manager 视口(src/modules/viewport)对齐状态 ----
        self.preset = 'orbit'      # cameraPresets.ts: game|orbit|top|front|side
        self.ortho = False         # 当前投影(正交 = top/front/side 预设)
        self.ortho_k = 1.0         # 正交缩放 px/引擎单位(framing.ts ortho zoom)
        self.view_mode = 'lit'     # viewMode.ts: lit|unshaded|untextured|wireframe
        self.wire_overlay = False  # viewMode.ts edges='over': 线框叠于着色表面
        self.show_grid = True       # Viewport.ts stage: 地面网格(ltk stage prop)
        self._pose_memory = {}     # cameraMemory.ts: 逐预设记忆姿态
        self._goal = None          # SceneCamera.tsx 平滑目标姿态
        self._goal_tau = DRAG_SMOOTHING_TAU
        self._smooth_id = None
        self._smooth_t = 0.0
        self._gizmo = None         # OrientationGizmo.tsx: 朝向控件画布
        self._gizmo_items = None
        self._wire_spacing = None  # 模型平均边长(线框叠加拥挤淡出)
        self.on_preset_changed = None   # GUI 回调(组合框同步)
        self.mesh = None
        self.rig = None
        self.subs_disp = []          # [(si, [全局三角形号, ...])]
        self.sub_visible = {}
        self.cull = True
        self.show_skeleton = False
        self.show_names = False
        self.decimate = 1
        self.positions = None        # 蒙皮后顶点位置(None=绑定姿态原坐标)
        self.joint_positions = None  # 世界关节位置(None=绑定)
        self.pose_animated = False   # 当前顶点是否来自动画采样(HUD)
        self.selected_joint = None
        self._winding = 1
        self._dirty = False
        self._pending = False
        self._hud = ''
        # ---- v2 快速渲染状态
        self.tint_map = {}
        self.use_tint = False
        self.force_canvas = False
        self._interacting = False
        self._idle_id = None
        self._fps = 0.0
        # v5.2: 交互自适应分辨率 — 拖动/播放期间全量三角形, 仅按帧时反馈
        # 降低光栅化分辨率(0.30..1.0; 静止 idle 全量重绘恒 1.0); 三角形
        # 永不抽稀(用户精度设置全程生效 = 本轮反馈 #3 的修复)。
        self._drag_scale = 1.0
        self._drag_dt_ema = 0.0
        self._last_scale = 1.0
        self._hud_fps_i = 0          # v5.2 性能: HUD fps 显示值(量化, 缓存友好)
        self._hud_fps_t = 0.0
        self.fluid_mode = True       # 交互流畅模式开关(工具栏复选框)
        self._img = None
        self._draw = None
        self._fb = None           # v5: numpy 帧缓冲(h,w,3 uint8)光栅化目标
        self._photo = None
        self._img_item = None
        self._img_wh = (0, 0)
        self._pil_font = None
        self._frame = None           # 本帧投影参数(骨架/名字层共用)
        self._last_proj = None       # 本帧批量投影结果
        self._np_verts = None
        self._np_bind = None
        self._bind_pos_list = None   # v5.2 性能: 绑定姿态列表缓存(免每帧重建 46k 元素列表)
        self._hud_cache = {}        # v5.2 性能: HUD 文本条带缓存(字体光栅化 8ms/帧 → mask paste 0.2ms)
        self._np_sub_tri = []
        self._cv_items = []
        self._cv_items_key = None
        self._cv_lod = 1
        self._cv_tris = 0
        # ---- v5 贴图渲染状态(官方 SkinnedMeshMaterial::SetupSubmesh 语义)
        self.tex_on = True            # 贴图渲染开关(缺贴图自动回退均色/分类色;
                                     # v7 起由视图模式驱动: lit/unshaded 用贴图)
        self.tex_filter = True        # v8: 贴图双线性插值(官方 D3D9 线性过滤
                                     # 语义; 工具栏「贴图插值」开关)
        self._filter_lod = None       # v8: 运动帧过滤 LOD(None=跟随用户
                                     # 设置; False=缩放<1 帧强制最近邻)
        self.tex_map = {}             # 子网格名(lower) → {rgb, alpha, size, path}
        self._np_uvs = None           # (nv, 2) float32
        self._np_norm = None          # (nv, 3) float32(顶点法线, 贴图路径用)
        self._tex_stats = ''          # HUD: 贴图命中信息

    # ------------------------------------------------ v7 wireframe 属性
    @property
    def wireframe(self):
        """v7: wireframe = 视图模式之一(viewMode.ts); 兼容 v6 直接赋值。"""
        return self.view_mode == 'wireframe'

    @wireframe.setter
    def wireframe(self, val):
        if val:
            self.view_mode = 'wireframe'
        elif self.view_mode == 'wireframe':
            self.view_mode = 'lit'

    # ------------------------------------------------ v7 姿态存取/平滑
    def _size(self):
        """视口尺寸(main 线程缓存 + 工作线程安全读 — v7 修复:
        set_model→fit_camera 在加载工作线程里调用, 跨线程取尺寸不安全
        且会间歇性吞掉加载结果; 取景/换算一律走缓存, render 时刷新)。"""
        s = getattr(self, '_size_cached', None)
        if s is not None:
            return s
        try:
            w = self.width()
            h = self.height()
            if w > 2 and h > 2:
                self._size_cached = (w, h)
                return (w, h)
        except Exception:
            pass
        return (560, 440)

    def _pose_now(self):
        """当前完整姿态(cameraMemory.ts recordCameraPose 的字段集)。"""
        return dict(yaw=self.yaw, pitch=self.pitch, dist=self.dist,
                   k=self.ortho_k, target=tuple(self.target),
                   ortho=self.ortho, focal=self.focal)

    def _remember_pose(self):
        """ltk cameraMemory.recordCameraPose: 记住当前预设的姿态(切回时恢复)。"""
        if self.preset:
            self._pose_memory[self.preset] = self._pose_now()

    def _apply_pose(self, p):
        for key, val in p.items():
            if key == 'target':
                self.target = tuple(val)
            elif key == 'ortho':
                self.ortho = bool(val)
            elif key == 'k':
                self.ortho_k = float(val)
            else:
                setattr(self, key, val)

    def _set_goal(self, g, tau):
        """写入目标姿态并平滑逼近(ltk SceneCamera.tsx DRAG_SMOOTHING):
        tau=0 → 立即生效(v6 直改语义兼容); 否则指数逼近(α=1-exp(-dt/τ))。
        目标字段与现有姿态合并(可分批指定 dist/target 等)。"""
        if not tau or getattr(self, '_no_smooth', False):
            self._apply_pose(g)
            self.request_render()
            return
        if self._goal is None:
            self._goal = self._pose_now()
        self._goal.update(g)
        self._goal_tau = float(tau)
        self._interacting = True
        self._start_smooth()
        self.request_render()

    def _start_smooth(self):
        if self._smooth_id is None:
            self._smooth_t = time.time()
            self._smooth_id = self._after(16, self._smooth_tick)

    def _smooth_tick(self):
        self._smooth_id = None
        g = self._goal
        if g is None:
            return
        now = time.time()
        dt = max(0.001, min(0.1, now - self._smooth_t))
        self._smooth_t = now
        alpha = 1.0 - math.exp(-dt / max(1e-4, self._goal_tau))
        cur = self._pose_now()
        step = {}
        done = True
        for key, gv in g.items():
            if key == 'ortho':
                continue            # 投影切换即时生效, 不参与插值
            if key == 'focal':
                step['focal'] = gv  # 焦距即时到位(镜头切换), 不插值
                continue
            if key == 'target':
                ct = cur['target']
                nt = tuple(ct[i] + (gv[i] - ct[i]) * alpha for i in range(3))
                if any(abs(gv[i] - nt[i]) > 1e-3 for i in range(3)):
                    done = False
                step['target'] = nt
            else:
                cv_ = cur[key] if key in cur else getattr(self, key)
                nv = cv_ + (gv - cv_) * alpha
                if abs(gv - nv) > (1e-3 if key in ('k', 'focal') else 1e-4):
                    done = False
                step[key] = nv
        self._apply_pose(step)
        if done:
            self._apply_pose(g)          # 精确到位
            self._goal = None
            self._interacting = False
            self.request_render()
            self._schedule_idle_full()
        else:
            self._interacting = True
            self.request_render()
            self._smooth_id = self._after(16, self._smooth_tick)

    def snap_goal(self):
        """测试/脚本: 立即取目标姿态(跳过平滑动画)。"""
        if self._smooth_id is not None:
            try:
                self._after_cancel(self._smooth_id)
            except Exception:
                pass
            self._smooth_id = None
        if self._goal is not None:
            self._apply_pose(self._goal)
            self._goal = None
        self._interacting = False

    def _goal_of(self, key, default=None):
        if self._goal is not None and key in self._goal:
            return self._goal[key]
        return getattr(self, key, default)

    def settle(self, timeout=3.0):
        """测试/脚本: 快进事件循环直到平滑收敛(真实动画路径验证用)。"""
        t0 = time.time()
        last = None
        while time.time() - t0 < timeout:
            _process_events()
            if self._goal is None and self._smooth_id is None and \
                    not self._dirty and not self._pending:
                return True
            time.sleep(0.002)
        return False

    # ------------------------------------------------ 模型与显示数据
    def set_model(self, m, rig=None):
        self.mesh = m
        self.rig = rig
        self.positions = None
        self.joint_positions = None
        self.sub_visible = {s['name']: True for s in m['subs']}
        self._winding = self._detect_winding()
        self._build_display()
        self._np_verts = None
        self._np_bind = None
        self._bind_pos_list = None
        self._np_sub_tri = []
        self._np_uvs = None
        self._np_norm = None
        if NP_OK:
            self._np_verts = _np.asarray([v[0] for v in m['verts']],
                                         dtype=_np.float32)
            self._np_sub_tri = [
                _np.asarray(m['idx'][s['fi']:s['fi'] + s['ic']],
                            dtype=_np.int32).reshape((-1, 3))
                for s in m['subs']]
            self._np_uvs = _np.asarray(m['uvs'], dtype=_np.float32)
            self._np_norm = _np.asarray(m['normals'], dtype=_np.float32)
            # v7: 模型平均边长(viewMode.ts edgeSpacing — 线框叠加拥挤淡出)
            try:
                tris = _np.concatenate(self._np_sub_tri)[:4096]
                a_, b_ = self._np_verts[tris[:, 0]], self._np_verts[tris[:, 1]]
                self._wire_spacing = float(
                    _np.mean(_np.linalg.norm(b_ - a_, axis=1)))
            except Exception:
                self._wire_spacing = None
        # 模型更换后按子网格名重新匹配已解码贴图
        if self.tex_map:
            self._match_textures_to_submeshes()
        self._cv_items = []
        self._cv_items_key = None
        self._photo = None
        self._img_item = None
        self.fit_camera()

    def set_textures(self, tex_map):
        """设置贴图集(子网格名 lower → 解码后的 numpy 贴图)。

        官方语义: 子网格 → 材质覆盖(GetSubmeshMaterialOverride, 名字
        std_stricmp) → 覆盖贴图, 否则默认贴图。未命中任何贴图的子网格
        自动回退均色/分类色。"""
        self.tex_map = dict(tex_map or {})
        self._match_textures_to_submeshes()
        self.request_render()

    def _match_textures_to_submeshes(self):
        """把贴图集按当前模型子网格名(大小写不敏感)对齐, 统计命中。"""
        if self.mesh is None:
            return
        hit = 0
        for s in self.mesh['subs']:
            if s['name'].lower() in self.tex_map:
                hit += 1
        self._tex_stats = '%d/%d 子网格命中' % (hit, len(self.mesh['subs']))

    def tex_of(self, name):
        """子网格的贴图(官方覆盖→默认); 无 → None。"""
        t = self.tex_map.get(name.lower())
        if t is not None:
            return t
        return self.tex_map.get('')

    def _current_positions(self):
        if self.positions is not None:
            return self.positions
        if self._bind_pos_list is None:
            self._bind_pos_list = [v[0] for v in self.mesh['verts']]
        return self._bind_pos_list

    def _detect_winding(self):
        """v5.1: 全量有向体积法判定正面朝向(与三角形排列顺序无关)。

        旧法 = XY 投影有向面积对「索引区前 ~3000 个三角形」抽样多数表决 —
        4.20 兼容修复件(skn_420_compat_fix)只重排索引区内的三角形顺序,
        多重集不变, 但抽样样本翻转 → 背面剔除方向判反 → 开启背面剔除时
        整个网格体被全部剔除, 视口只剩 HUD 文本(=「网格体无法正常渲染」)。
        修复: 散度定理 Σ dot(a, b×c)/6 的总体积符号与三角形顺序完全无关
        (右手系: 正体积 = 法线朝外 = 正面 CCW → winding +1); 开放网格
        (|体积| ≤ 包围盒尺度 1e-6)退化为全量 XY 投影面积求和(同为顺序
        无关的多重集统计, 不再抽样)。"""
        m = self.mesh
        tri_n = m['ni'] // 3
        if tri_n == 0:
            return 1
        idx = m['idx']
        pos = [v[0] for v in m['verts']]
        if NP_OK:
            P = _np.asarray(pos, dtype=_np.float64)
            I = _np.asarray(idx[:tri_n * 3], dtype=_np.int64)
            I = I.reshape((-1, 3))
            a, b, c = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]
            tri6 = _np.einsum('ij,ij->i', a, _np.cross(b, c))   # 6×体积贡献
            vol = float(tri6.sum()) / 6.0
            lo, hi = P.min(axis=0), P.max(axis=0)
            scale = float(_np.prod(hi - lo + 1e-9))
            if abs(vol) > 1e-6 * scale:
                return 1 if vol > 0 else -1
            s2 = ((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) -
                  (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0]))
            return 1 if float(s2.sum()) >= 0 else -1
        vol = 0.0
        s2 = 0.0
        for t in range(tri_n):
            i0, i1, i2 = idx[t * 3], idx[t * 3 + 1], idx[t * 3 + 2]
            ax_, ay_, az_ = pos[i0]
            bx_, by_, bz_ = pos[i1]
            cx_, cy_, cz_ = pos[i2]
            vol += (ax_ * (by_ * cz_ - bz_ * cy_) +
                    ay_ * (bz_ * cx_ - bx_ * cz_) +
                    az_ * (bx_ * cy_ - by_ * cx_))
            s2 += (bx_ - ax_) * (cy_ - ay_) - (by_ - ay_) * (cx_ - ax_)
        vol /= 6.0
        xs = [p[0] for p in pos]
        ys = [p[1] for p in pos]
        zs = [p[2] for p in pos]
        scale = ((max(xs) - min(xs) + 1e-9) * (max(ys) - min(ys) + 1e-9) *
                 (max(zs) - min(zs) + 1e-9))
        if abs(vol) > 1e-6 * scale:
            return 1 if vol > 0 else -1
        return 1 if s2 >= 0 else -1

    def _build_display(self):
        m = self.mesh
        K = max(1, self.decimate)
        self.subs_disp = []
        for si, s in enumerate(m['subs']):
            tris = [(s['fi'] // 3 + i) for i in range(0, s['ic'] // 3, K)]
            self.subs_disp.append((si, tris))

    def set_decimate(self, K):
        if self.mesh is None or K == self.decimate:
            self.decimate = K
            return
        self.decimate = K
        self._build_display()
        self._cv_items_key = None
        self.request_render()

    def set_tint_map(self, tint):
        """子网格名 -> (r,g,b) 贴图均色映射(角色配置页调用)。"""
        self.tint_map = dict(tint or {})
        self._cv_items_key = None
        self.request_render()

    def set_positions(self, positions, joint_positions=None):
        self.positions = positions
        self.joint_positions = joint_positions
        self.pose_animated = positions is not None
        if NP_OK and positions is not None and self.mesh is not None and \
                len(positions) == self.mesh['nv']:
            flat = []
            for p in positions:
                flat.append(p[0]); flat.append(p[1]); flat.append(p[2])
            self._np_verts = _np.asarray(flat, dtype=_np.float32).reshape((-1, 3))
        self.request_render()

    def set_positions_sparse(self, skin_pos, joint_positions=None):
        """稀疏提交(纯 Python 兜底路径): {顶点号: (x,y,z)}, 未含顶点用绑定姿态。"""
        m = self.mesh
        if m is None:
            return
        if not skin_pos:
            self.clear_positions()
            return
        self.joint_positions = joint_positions
        self.pose_animated = True
        if NP_OK:
            if self._np_bind is None or self._np_bind.shape[0] != m['nv']:
                self._np_bind = _np.asarray(
                    [v[0] for v in m['verts']], dtype=_np.float32)
            arr = self._np_bind.copy()
            idx = _np.fromiter(skin_pos.keys(), dtype=_np.int32,
                               count=len(skin_pos))
            val = _np.fromiter(
                (c for vi in skin_pos.values() for c in vi),
                dtype=_np.float32, count=len(skin_pos) * 3).reshape((-1, 3))
            arr[idx] = val
            self._np_verts = arr
            self.positions = None               # 以 _np_verts 为准
        else:
            base = [v[0] for v in m['verts']]
            self.positions = [skin_pos.get(i, base[i]) for i in range(m['nv'])]
        self.request_render()

    def _np_bind_array(self):
        """v8: 绑定姿态顶点数组(懒建缓存; 姿态管线数组化路径用)。"""
        if not NP_OK or self.mesh is None:
            return None
        if self._np_bind is None or self._np_bind.shape[0] != self.mesh['nv']:
            self._np_bind = _np.asarray(
                [v[0] for v in self.mesh['verts']], dtype=_np.float32)
        return self._np_bind

    def set_positions_array(self, verts, joint_positions=None):
        """v8 数组直通提交(ltk pose.ts localsInto 语义 — 每帧只写预分配
        缓冲, 零 dict/元组编组): verts = (nv,3) float32 连续数组(未动画
        顶点已回绑定行), joint_positions = (n,3) 数组或 None。
        缓存命中路径专用 — 提交 = 一次浅拷贝引用(渲染/投影均只读该数组,
        不做原地写, 故免 160KB memcpy 也安全)。"""
        if self.mesh is None or verts is None:
            return
        self._np_verts = verts
        self.positions = None
        self.joint_positions = joint_positions
        self.pose_animated = True
        self.request_render()

    def clear_positions(self):
        self.positions = None
        self.joint_positions = None
        self.pose_animated = False
        if NP_OK and self.mesh is not None:
            self._np_verts = _np.asarray([v[0] for v in self.mesh['verts']],
                                         dtype=_np.float32)
        self.request_render()

    # ------------------------------------------------ v7 ltk 相机系统
    def _visible_bounds(self):
        """ltk framing.ts meshBounds: 只统计「可见子网格」引用的顶点范围
        (drawnRanges hidden 语义 — 隐藏子网格不参与取景; 静态绑定几何)。"""
        m = self.mesh
        if m is None:
            return None
        lo = [float('inf')] * 3
        hi = [float('-inf')] * 3
        drawn = False
        if NP_OK:
            P = _np.asarray([v[0] for v in m['verts']], dtype=_np.float64)
            for s in m['subs']:
                if not self.sub_visible.get(s['name'], True):
                    continue
                n = s['ic']
                if n <= 0:
                    continue
                idx = _np.asarray(m['idx'][s['fi']:s['fi'] + n],
                                  dtype=_np.int64)
                if len(idx) == 0:
                    continue
                V = P[idx]
                l, u = V.min(axis=0), V.max(axis=0)
                for ax in range(3):
                    lo[ax] = min(lo[ax], float(l[ax]))
                    hi[ax] = max(hi[ax], float(u[ax]))
                drawn = True
        else:
            pos = [v[0] for v in m['verts']]
            idx = m['idx']
            for s in m['subs']:
                if not self.sub_visible.get(s['name'], True):
                    continue
                for k2 in range(s['fi'], s['fi'] + s['ic']):
                    vi = idx[k2]
                    px, py, pz = pos[vi]
                    if px < lo[0]: lo[0] = px
                    if px > hi[0]: hi[0] = px
                    if py < lo[1]: lo[1] = py
                    if py > hi[1]: hi[1] = py
                    if pz < lo[2]: lo[2] = pz
                    if pz > hi[2]: hi[2] = pz
                if s['ic']:
                    drawn = True
        if not drawn:
            return None
        return (tuple(lo), tuple(hi))

    @staticmethod
    def _ground_point(b):
        """ltk FitCamera ground: 主体的落脚点 = 包围盒底面中心。"""
        (mnx, mny, mnz), (mxx, mxy, mxz) = b
        return ((mnx + mxx) / 2.0, mny, (mnz + mxz) / 2.0)

    def fit_camera(self, animate=False):
        """v7 = ltk-manager framing.ts 取景(替换 v6 的 ext·2.1 粗略式):
        - 边界 = 可见子网格顶点范围(meshBounds drawnRanges 语义);
        - 透视: 包围球取景 dist = (radius / sin(min(vfov,hfov)/2))·1.15,
          方向保持读者当前 yaw/pitch(FitCamera: 方向是相机的);
        - 正交: k = min(w,h)/(2·radius·1.15), 立距 = 4·radius(STAND_OFF);
        - game 预设不取景: 立于地面(脚点)最远距(GAME_ZOOM[1] = 2250)。
        animate=False → 立即生效(v6 兼容); True → 平滑过渡。"""
        b = self._visible_bounds()
        if b is None:
            return
        w, h = self._size()
        (mnx, mny, mnz), (mxx, mxy, mxz) = b
        mid = ((mnx + mxx) / 2.0, (mny + mxy) / 2.0, (mnz + mxz) / 2.0)
        radius = 0.5 * math.sqrt((mxx - mnx) ** 2 + (mxy - mny) ** 2 +
                                 (mxz - mnz) ** 2) or 1.0
        if self.preset == 'game':
            # ltk FitCamera: 自带 zoom 范围的预设(对局相机)不取景 —
            # 立于 ground 的最远距, 如对局站在英雄脚边
            g = dict(target=self._ground_point(b), dist=GAME_ZOOM[1])
            self._set_goal(g, PRESET_TRANSITION_TAU if animate else 0)
            return
        if self.ortho:
            # framing.ts orthographicFraming: zoom = across/(2·radius·MARGIN)
            k = min(w, h) / (2.0 * radius * FIT_MARGIN)
            g = dict(target=mid,
                     dist=min(radius * ORTHO_STAND_OFF, _FAR_PLANE / 2.0),
                     k=k)
        else:
            f = self.focal * (h / 720.0)
            vfov = 2.0 * math.atan((h / 2.0) / f) if f > 1e-6 else 0.8
            hfov = 2.0 * math.atan((w / 2.0) / f) if f > 1e-6 else 1.2
            dist = (radius / math.sin(min(vfov, hfov) / 2.0)) * FIT_MARGIN
            g = dict(target=mid, dist=max(dist, _NEAR_PLANE * 4.0))
        self._set_goal(g, PRESET_TRANSITION_TAU if animate else 0)

    def reset_view(self, animate=True):
        """复位视角 = 环绕预设全新立位 + 取景(v6「复位视角」语义的 v7 等价:
        方向复位到默认 0.6/0.35, 再按 ltk 取景数学框住模型)。"""
        self._remember_pose()
        self.preset = 'orbit'
        self.ortho = False
        self.focal = _fov_deg_to_focal(ORBIT_FOV_DEG)
        g = dict(yaw=0.6, pitch=0.35)
        self._set_goal(g, PRESET_TRANSITION_TAU if animate else 0)
        self.fit_camera(animate=animate)
        if self.on_preset_changed:
            self.on_preset_changed('orbit')

    def set_preset(self, name, animate=True, refit=True, restore=True):
        """v7: ltk SceneCamera 预设立位(cameraPresets.ts CAMERA_STANDS):
        - 有该预设的姿态记忆 → 恢复(cameraMemory lastCameraPose, 逐字段原样);
        - game: 立于 look 方向(对局相机 56° 俯仰)·焦距换算 40° 视场·
          dist = GAME_ZOOM[1](最远), 目标 = 地面脚点, 不取景;
        - orbit: 自由相机 — 保留读者当前方向, 只校正焦距(45°), 取景;
        - top/front/side: 正交投影立于轴 look(±90° 俯仰可达), 随后取景
          (k/立距/目标由 fit 的正交分支决定)。
        切换前记住当前预设的姿态(切回时恢复)。"""
        if name not in _CAM_PRESET_INFO:
            return
        info = _CAM_PRESET_INFO[name]
        if name == self.preset:
            if refit:
                self.fit_camera(animate=animate)
            return
        self._remember_pose()
        self.preset = name
        self.ortho = bool(info['ortho'])
        if info.get('fov'):
            self.focal = _fov_deg_to_focal(info['fov'])
        pose = self._pose_memory.get(name) if restore else None
        if pose is not None:
            # ltk cameraMemory: 恢复的 position/target/zoom 原样应用(exact)
            self.ortho = bool(pose['ortho'])
            self.focal = pose['focal']
            g = dict((key, pose[key]) for key in
                     ('yaw', 'pitch', 'dist', 'k', 'target'))
            self._goal = None
            self._set_goal(g, PRESET_TRANSITION_TAU if animate else 0)
            if self.on_preset_changed:
                self.on_preset_changed(name)
            return
        look = info.get('look')
        if name == 'orbit':
            # 环绕 = 读者的自由相机: 保留方向, 只校正镜头(45°)
            if refit:
                self.fit_camera(animate=animate)
            else:
                self.request_render()
            if self.on_preset_changed:
                self.on_preset_changed('orbit')
            return
        yaw, pitch = _look_to_yaw_pitch(look)
        if name == 'game':
            b = self._visible_bounds()
            g = dict(yaw=yaw, pitch=pitch, dist=GAME_ZOOM[1])
            if b is not None:
                g['target'] = self._ground_point(b)
            self._set_goal(g, PRESET_TRANSITION_TAU if animate else 0)
            if self.on_preset_changed:
                self.on_preset_changed(name)
            return
        # 正交预设: 立于轴向, 目标/缩放/立距交给取景(正交分支)
        self._set_goal(dict(yaw=yaw, pitch=pitch),
                       PRESET_TRANSITION_TAU if animate else 0)
        if refit:
            self.fit_camera(animate=animate)
        else:
            self.request_render()
        if self.on_preset_changed:
            self.on_preset_changed(name)

    def set_view_mode(self, mode):
        """v7: ltk viewMode.ts VIEW_MODES — lit/unshaded/untextured/wireframe。"""
        if mode not in VIEW_MODES:
            return
        self.view_mode = mode
        self._cv_items_key = None      # Canvas 兜底路径重建图元
        self.request_render()

    def _camera_dir(self):
        """相机偏移方向(target→camera 单位向量; 本查看器相机模型推导)。"""
        cy, sy, cp, sp = _cam_rows(self.yaw, self.pitch)
        return (cp * sy, -sp, -cp * cy)

    def _stands_on(self, axis):
        """ltk SceneCamera.standsOn: 相机已立于该轴(点积 > 0.999)。"""
        d = self._camera_dir()
        return (d[0] * axis[0] + d[1] * axis[1] + d[2] * axis[2]) > 0.999

    def _demote_to_orbit(self):
        """ltk SceneCamera: 读者拖动 → 相机脱离预设, 切环绕(保留所见大小:
        正交→透视按 zoomOfReach 换算立距; 透视→透视保立距只换镜头)。"""
        if self.preset == 'orbit':
            return
        self._remember_pose()
        was_ortho = self.ortho
        self.preset = 'orbit'
        self.ortho = False
        if was_ortho:
            # framing.ts zoomOfReach: 视高 h/k 单位 → 立距 = (h/k)/(2·tan(fov/2))
            h = self._size()[1]
            reach = (h / max(self.ortho_k, 1e-9)) / \
                (2.0 * math.tan(math.radians(ORBIT_FOV_DEG) / 2.0))
            lo, hi = _FREE_ZOOM
            self.dist = max(lo, min(hi, reach))
        self.focal = _fov_deg_to_focal(ORBIT_FOV_DEG)
        if self.on_preset_changed:
            self.on_preset_changed('orbit')

    def _zoom_range(self):
        """ltk ZoomRange: 预设自带推拉范围; 自由预设 = near·4..far/2。"""
        info = _CAM_PRESET_INFO.get(self.preset) or {}
        z = info.get('zoom')
        if z:
            return float(z[0]), float(z[1])
        return _FREE_ZOOM

    def _zoom_by(self, factor):
        """v7: 滚轮推拉 — 透视缩立距(预设 zoom 区间钳制), 正交缩 px/单位
        (cameraPresets.ts ZoomRange + SceneCamera 自由 dollies 语义)。"""
        if self.ortho:
            k = self._goal_of('k', 1.0) / factor
            self._set_goal(dict(k=max(0.05, min(60.0, k))),
                           DRAG_SMOOTHING_TAU)
        else:
            d = self._goal_of('dist', self.dist) * factor
            lo, hi = self._zoom_range()
            self._set_goal(dict(dist=max(lo, min(hi, d))),
                           DRAG_SMOOTHING_TAU)
        self._interacting = True
        self.request_render()
        self._schedule_idle_full()

    # ------------------------------------------------ v7 朝向 Gizmo
    def attach_gizmo(self, gizmo_canvas):
        """Qt 版: gizmo 由视口 paintEvent 自绘(参数仅保持 API 兼容)。"""
        self._gizmo = gizmo_canvas
        self._gizmo_items = None

    def _gizmo_look(self, axis):
        """点轴头: 未立于该轴 → 立到它(±X→侧视/±Y→顶视/±Z→前视);
        已立于该轴(standsOn) → 翻到另一端(negated);
        负轴/无平面对应 → 环绕预设但保持该观察方向(ltk presetFacing)。"""
        look = axis if not self._stands_on(axis) else \
            tuple(-c for c in axis)
        if all(c >= 0.0 for c in look):
            preset = {0: 'side', 1: 'top', 2: 'front'}[
                _GIZMO_AXES.index(axis)]
            self.set_preset(preset, animate=True)
        else:
            # 负向轴 → 环绕(ltk: presetFacing 无平面对应 → orbit), 方向 = look
            self._remember_pose()
            self.preset = 'orbit'
            self.ortho = False
            self.focal = _fov_deg_to_focal(ORBIT_FOV_DEG)
            yaw, pitch = _look_to_yaw_pitch(look)
            self._set_goal(dict(yaw=yaw, pitch=pitch),
                           PRESET_TRANSITION_TAU)
            self.fit_camera(animate=True)
            if self.on_preset_changed:
                self.on_preset_changed('orbit')

    def _gizmo_update(self):
        """每帧按相机旋转算三轴头坐标(视口左上 84px 盘, paintEvent 自绘)。"""
        heads = []
        cx = cy = 41.0
        r = 26.0
        cyr, syr, cpr, spr = _cam_rows(self.yaw, self.pitch)
        for ai, ax in enumerate(_GIZMO_AXES):
            x1 = cyr * ax[0] + syr * ax[2]
            z1 = -syr * ax[0] + cyr * ax[2]
            y2 = cpr * ax[1] - spr * z1
            z2 = spr * ax[1] + cpr * z1
            heads.append((ai, cx + x1 * r, cy - y2 * r, z2))
        heads.sort(key=lambda t: -t[3])       # 远端先画(球面排序近似)
        self._gizmo_heads = heads

    # ------------------------------------------------ 投影
    def _project(self, p):
        """单点投影(v1 兼容保留; 帧渲染走 _frame_projection 批量路径)。"""
        cy, sy, cp, sp = _cam_rows(self.yaw, self.pitch)
        x1, y2, z2 = _project_view(p, self.target, cy, sy, cp, sp)
        w = max(self.width(), 2)
        h = max(self.height(), 2)
        f = self.focal * (h / 720.0)
        if self.ortho:
            return _view_to_screen(x1, y2, z2, self.dist, f, w, h,
                                   k=self.ortho_k)
        return _view_to_screen(x1, y2, z2, self.dist, f, w, h)

    def _frame_projection(self, w, h):
        """批量投影(numpy 或纯 Python); 参数存 self._frame 供骨架/名字层。
        v5.2 性能: numpy 路径不再经由 _current_positions() 构建 46k 元素
        Python 列表(旧仅为此调用即 ~1.4ms/帧)。"""
        f = self.focal * (h / 720.0)
        cy, sy, cp, sp = _cam_rows(self.yaw, self.pitch)
        self._frame = dict(w=w, h=h, f=f, cy=cy, sy=sy, cp=cp, sp=sp,
                           k=self.ortho_k if self.ortho else None)
        self._size_cached = (w, h)     # v7: 尺寸缓存(工作线程取景用)
        tx, ty, tz = self.target
        dist = self.dist
        if NP_OK and self.mesh is not None and self._np_verts is not None \
                and self._np_verts.shape[0] == self.mesh['nv']:
            P = self._np_verts
            X = P[:, 0] - tx
            Y = P[:, 1] - ty
            Z = P[:, 2] - tz
            x1 = cy * X + sy * Z
            z1 = -sy * X + cy * Z
            y2 = cp * Y - sp * z1
            z2 = sp * Y + cp * z1
            zc = z2 + dist
            if self.ortho:
                # v7 正交(ltk top/front/side): 免透视除法;
                # 画家序深度仍用 zc
                u = w / 2.0 + self.ortho_k * x1
                v = h / 2.0 - self.ortho_k * y2
            else:
                zsafe = _np.maximum(zc, 1e-3)
                u = w / 2.0 + f * x1 / zsafe
                v = h / 2.0 - f * y2 / zsafe
            self._last_proj = ('np', u, v, zc, x1, y2, z2, w, h, f,
                               (cy, sy, cp, sp))
            return self._last_proj
        pos = self._current_positions()
        proj = [None] * len(pos)
        zcs = [0.0] * len(pos)
        vx = [0.0] * len(pos)
        vy = [0.0] * len(pos)
        vz = [0.0] * len(pos)
        for i, p in enumerate(pos):
            x1, y2v, z2 = _project_view(p, self.target, cy, sy, cp, sp)
            zc = z2 + dist
            vx[i] = x1
            vy[i] = y2v
            vz[i] = z2
            zcs[i] = zc
            if self.ortho:
                proj[i] = (w / 2.0 + self.ortho_k * x1,
                           h / 2.0 - self.ortho_k * y2v)
            elif zc > 1e-3:
                proj[i] = (w / 2.0 + f * x1 / zc, h / 2.0 - f * y2v / zc)
        self._last_proj = ('py', proj, zcs, vx, vy, vz, w, h, f, (cy, sy, cp, sp))
        return self._last_proj

    def _screen_of(self, p):
        """用本帧投影参数把单点投到屏幕(骨架/名字层复用)。"""
        fr = self._frame
        if fr is None:
            return self._project(p)
        x1, y2, z2 = _project_view(p, self.target, fr['cy'], fr['sy'],
                                   fr['cp'], fr['sp'])
        return _view_to_screen(x1, y2, z2, self.dist, fr['f'], fr['w'],
                               fr['h'], k=fr.get('k'))

    # ------------------------------------------------ 调度
    def request_render(self):
        self._dirty = True
        if not self._pending:
            self._pending = True
            self._after(16, self._flush_render)

    def _flush_render(self):
        self._pending = False
        if self._dirty:
            self._dirty = False
            self.render()

    def _schedule_idle_full(self):
        if self._idle_id is not None:
            try:
                self._after_cancel(self._idle_id)
            except Exception:
                pass
        self._idle_id = self._after(250, self._idle_full)

    def _idle_full(self):
        self._idle_id = None
        # v7: 平滑未收敛时顺延全分辨率重绘(避免中途闪全分辨率)
        if self._goal is not None or self._smooth_id is not None:
            self._schedule_idle_full()
            return
        self._interacting = False
        self._dirty = False
        self.render()

    # ------------------------------------------------ 渲染
    def _render_mode(self):
        if not PIL_OK:
            return 'canvas'
        return 'pil'

    def _sub_color(self, si, name):
        if self.use_tint and name in self.tint_map:
            return tuple(self.tint_map[name])
        return _SUB_RGB[si % len(_SUB_RGB)]

    def _shade_palette(self, base):
        """8 级平面着色调色板(避免逐三角形拼颜色)。"""
        pal = []
        for k in range(8):
            s = 0.38 + 0.62 * (k / 7.0)
            pal.append((int(base[0] * s), int(base[1] * s), int(base[2] * s)))
        return pal

    def _interactive_stride(self, mode):
        """交互/播放期间的额外 LOD 预算 — v5.2 起仅限「无 numpy」兜底路径
        (纯 PIL / Canvas; 这些路径无自适应分辨率机制, 不抽稀则拖不动)。
        numpy 光栅路径(render/_render_pil)已不再调用本函数: 交互期间
        三角形全量, 改用 _interactive_scale 分辨率缩放换流畅度。"""
        if not (self._interacting or getattr(self, '_playing_flag', False)):
            return 1
        if mode != 'pil' or not NP_OK:
            budget = 1500
        elif self._interacting:
            budget = 15000
        else:                          # 仅播放(非交互): 保 30fps 的预算
            budget = 8000
        ntri = 0
        for s in self.mesh['subs']:
            if self.sub_visible.get(s['name'], True):
                ntri += s['ic'] // 3
        need = ntri // max(1, self.decimate)
        if need <= budget:
            return 1
        return int(math.ceil(need / float(budget)))

    def _interactive_scale(self):
        """v5.2: numpy 光栅路径的交互分辨率缩放(三角形永不抽稀)。

        拖动/播放期间按帧时反馈自适应(_drag_feedback), 分辨率线性等比缩放
        (投影 = 全尺寸参数 × s, 无畸变); 静止与「交互流畅模式」关闭时恒
        1.0(全分辨率全量)。
        v8: 播放态下限 0.30 → 0.60(用户实测「渲染精度低」的直接修复 —
        播放不再降到 30% 清晰度; 光栅重写后全分辨率已预算内, 绝大多数
        播放帧恒 1.0, 下限仅作卡顿兜底); 拖动仍 0.30 保响应优先。"""
        if not self.fluid_mode:
            return 1.0
        if not (self._interacting or getattr(self, '_playing_flag', False)):
            return 1.0
        floor = 0.60 if getattr(self, '_playing_flag', False) else 0.30
        return float(min(1.0, max(floor, getattr(self, '_drag_scale', 1.0))))

    def _drag_feedback(self, t0):
        """v5.2: 交互/播放期间按上一帧耗时反馈调节 _drag_scale。

        v8: 帧率预算 30→60fps(降档阈值 34→17ms, 升档阈值 20→12ms;
        ltk-manager 视口默认 60fps 帧预算对齐 — 光栅重写后全分辨率帧
        时已入预算, 仅真实掉帧才降分辨率); 静止期复位 1.0 不变。"""
        active = self._interacting or getattr(self, '_playing_flag', False)
        if not active or not self.fluid_mode:
            self._drag_scale = 1.0
            self._drag_dt_ema = 0.0
            return
        dt = time.time() - t0
        if dt <= 0:
            return
        self._drag_dt_ema = (0.6 * self._drag_dt_ema + 0.4 * dt) \
            if self._drag_dt_ema else dt
        s = self._drag_scale
        if self._drag_dt_ema > 0.017:           # > ~59fps 预算 → 降分辨率
            s = max(0.30, s * 0.88)
        elif self._drag_dt_ema < 0.012:           # < ~83fps → 升分辨率
            s = min(1.0, s * 1.06)
        self._drag_scale = s

    def set_playing(self, flag):
        """播放状态标记(LOD 预算用; 不触发重绘)。"""
        self._playing_flag = bool(flag)

    def render(self):
        t0 = time.time()
        mode = self._render_mode()
        if self.mesh is None:
            self._note_img('未加载模型 — 左侧「导入角色包」官方链一键装配')
            return
        w = max(self.width(), 2)
        h = max(self.height(), 2)
        # v5.2: 抽稀预算仅对无 numpy 兜底路径生效; numpy 光栅路径在
        # _render_pil 内部改用 _interactive_scale(三角形全量, 精度设置生效)。
        numpy_path = mode == 'pil' and NP_OK and bool(self._np_sub_tri) and \
            self._last_proj is not None and self._last_proj[0] == 'np'
        extra = 1 if numpy_path else self._interactive_stride(mode)
        if mode == 'pil':
            n_draw, n_kept = self._render_pil(w, h, extra)
            self._draw_skeleton()
            self._draw_hud(w, h, n_draw, n_kept, extra, mode)
            self._blit(w, h)
        else:
            self._last_scale = 1.0
            self._note_img('本环境缺 Pillow — 无法软光栅(安装 Pillow 后可用)')
        self._gizmo_update()      # v7: 朝向控件随帧刷新(ltk Gizmo 跟随相机)
        self._fps_tick(t0)
        self._drag_feedback(t0)

    def _fps_tick(self, t0):
        dt = time.time() - t0
        if dt > 1e-4:
            inst = 1.0 / dt
            self._fps = inst if self._fps <= 0 else (0.85 * self._fps +
                                                     0.15 * inst)

    def _ensure_backbuffer(self, w, h):
        if self._img is None or self._img_wh != (w, h):
            self._img = _PILImage.new('RGB', (w, h), _BG_RGB)
            self._draw = _PILDraw.Draw(self._img)
            self._img_wh = (w, h)
            self._photo = None          # 尺寸变化 → 重建 PhotoImage
            self._img_item = None
        if NP_OK and (self._fb is None or self._fb.shape != (h, w, 3)):
            self._fb = _np.empty((h, w, 3), dtype=_np.uint8)

    def _ensure_fb(self, w, h):
        """v5.2: numpy 帧缓冲按「渲染分辨率」分配(交互期可为缩放尺寸);
        显示位图 _img 恒为视口全尺寸(_render_pil 内 fromarray+resize)。"""
        if not NP_OK:
            return
        if self._fb is None or self._fb.shape != (h, w, 3):
            self._fb = _np.empty((h, w, 3), dtype=_np.uint8)
        if self._pil_font is None:
            self._pil_font = _pil_hud_font() or None   # False → None(默认字体)

    def _blit(self, w, h):
        """Qt 输出: PIL 后缓冲 → QImage(保数据引用) → update() 上屏。"""
        try:
            img = self._img
            if img is None:
                return
            if img.mode != 'RGB':
                img = img.convert('RGB')
            data = img.tobytes()
            self._qimg_data = data      # QImage 不复制缓冲, 保 Python 引用
            self._qimg = QImage(data, img.width, img.height,
                                img.width * 3, QImage.Format.Format_RGB888)
            self.update()
        except Exception:
            pass

    def _raster_sub(self, tri_k, u, v, zc, x1, y2v, z2v, w, h, zavg,
                   tex=None, base_rgb=(180, 180, 180)):
        """numpy 向量化三角形光栅化(v8 分块 + covered-only; 贴图采样或平色)。

        - 画家序(远→近平铺写入, 后写覆盖前写 = 同既有画家算法质量);
        - tex 给定: 重心坐标插值 UV → 纹理采样(小数取 frac, 官方 UV 平铺
          语义) + alpha 测试; 否则平色;
        - 采样行 = v·th 直接寻址(官方 D3D9: DDS 首行 = 上行; 旧 (1-v)
          翻转 = 贴图整体上下颠倒, v5.2 已修);
        - v8 三项重构(算法/语义逐项不变, 组织方式改变):
          1) 分块: 三角形沿深度序切「bbox 像素预算」块(_RASTER_PIX_BUDGET
             ≈ 512k/块, ltk-manager 后台烘焙限时切片的资源语义) — 大临时
             量峰值受控(旧单批最坏 40M 像素 × ~20 个 float32/int32 数组
             ≈ GB 级瞬时分配 = 「占用高」主因之一); 块沿已排序序列切,
             画家序逐块保持;
          2) covered-only: 先算 inside(重心 + 0.5px Minkowski 边缘膨胀)
             再做纹理采样/着色(旧序先在整个 bbox 上采样后掩码 — bbox 浪费
             2-4× 的贴图 gather(int64/int32/uint8 大操作)全白做);
          3) 像素索引 int32 + 每像素三角形号 tid 单次 repeat(替代 6 个
             bbox 级 UV/着色 repeat);
        - v8 贴图双线性插值(tex_filter, 默认开; 官方 D3D9 线性过滤语义):
          像素中心对齐 texel 网格(x = u·tw - 0.5), 4 邻域权重插值, alpha
          测试取「过滤后 alpha」阈值(≈128 — 官方 cutout 在线性过滤下的
          行为); 最近邻路径保留 uint16 移位着色快路径(与 v7 位级一致);
        - 平面朗伯着色(视空间法线 × 灯向), 与旧路径同一光照模型;
        - 直接写 numpy 帧缓冲 self._fb, 每帧一次 fromarray 上屏。"""
        if not NP_OK or len(tri_k) == 0 or self._fb is None:
            return
        np_ = _np
        order = np_.argsort(-zavg)          # 远→近
        tri_s = tri_k[order]
        X = u[tri_s]                        # (T,3) 屏幕坐标(float32)
        Y = v[tri_s]
        # —— 每三角形视空间法线 → 朗伯系数(→ uint8 量化色调, 供移位着色) ——
        # v7: unshaded 视图模式(viewMode.ts 'unshaded')不经光照 — shade ≡ 1
        if self.view_mode == 'unshaded':
            shq = np_.full(len(tri_s), 255, dtype=np_.uint8)
        else:
            axv = x1[tri_s]
            ayv = y2v[tri_s]
            azv = z2v[tri_s]
            e1x = axv[:, 1] - axv[:, 0]
            e1y = ayv[:, 1] - ayv[:, 0]
            e1z = azv[:, 1] - azv[:, 0]
            e2x = axv[:, 2] - axv[:, 0]
            e2y = ayv[:, 2] - ayv[:, 0]
            e2z = azv[:, 2] - azv[:, 0]
            nx = e1y * e2z - e1z * e2y
            ny = e1z * e2x - e1x * e2z
            nz = e1x * e2y - e1y * e2x
            nl = np_.sqrt(nx * nx + ny * ny + nz * nz) + np_.float32(1e-9)
            lx, ly, lz = _LAMP
            shade = 0.38 + 0.62 * np_.abs(
                nx * lx + ny * ly + nz * lz) / nl     # (T,) float32
            shq = np_.clip(shade * 255.0, 0.0, 255.0).astype(np_.uint8)
        # —— 包围盒(裁到视口; 像素中心采样: 中心 k+0.5 ∈ [min,max]) ——
        xmn = np_.ceil(X.min(axis=1) - 0.5).astype(np_.int32)
        xmx = np_.floor(X.max(axis=1) - 0.5).astype(np_.int32)
        ymn = np_.ceil(Y.min(axis=1) - 0.5).astype(np_.int32)
        ymx = np_.floor(Y.max(axis=1) - 0.5).astype(np_.int32)
        np_.clip(xmn, 0, w - 1, out=xmn)
        np_.clip(xmx, 0, w - 1, out=xmx)
        np_.clip(ymn, 0, h - 1, out=ymn)
        np_.clip(ymx, 0, h - 1, out=ymx)
        wpx = xmx - xmn + 1
        hpx = ymx - ymn + 1
        ok = (wpx > 0) & (hpx > 0)          # 退化/近平裁剪三角形丢弃
        if not ok.all():
            tri_s = tri_s[ok]
            X = X[ok]
            Y = Y[ok]
            shq = shq[ok]
            xmn, ymn, wpx, hpx = xmn[ok], ymn[ok], wpx[ok], hpx[ok]
        T = len(tri_s)
        if T == 0:
            return
        # —— 自适应边缘膨胀(0.5px Minkowski): 与 PIL polygon 边界含入等效 ——
        # dist_to_edge_i = |l_i| * 2A/|edge_i|; 计入 dist ≤ 0.5px 的像素 →
        # eps_i = 0.5*|edge_i|/|den|(den = 2×有向面积), 细三角形自动放大,
        # 大三角形趋近纯中心采样(不过度膨胀)。
        den_t = (Y[:, 1] - Y[:, 2]) * (X[:, 0] - X[:, 2]) + \
            (X[:, 2] - X[:, 1]) * (Y[:, 0] - Y[:, 2])
        ad = np_.abs(den_t) + np_.float32(1e-12)
        # v8: 边长/eps 三通道一次算(列序 [1,2],[2,0],[0,1] = eps0/1/2
        # 对应边 12/20/01; 旧逐边标量式 ~3× numpy 派发开销, 46k 三角形
        # ≈6ms → ≈2ms; 逐元素算式相同 = 数值位级一致)。
        Ex = X[:, [1, 2, 0]] - X[:, [2, 0, 1]]
        Ey = Y[:, [1, 2, 0]] - Y[:, [2, 0, 1]]
        elen = np_.sqrt(Ex * Ex + Ey * Ey)
        eps = np_.clip(0.5 * elen / ad[:, None], 0.0, 0.5).astype(np_.float32)
        # 列拷贝转连续(repeat 快路径; strided 视图会内建缓冲拷贝)
        eps0, eps1, eps2 = eps[:, 0].copy(), eps[:, 1].copy(), eps[:, 2].copy()
        area_px = wpx * hpx                     # int32
        total = int(area_px.sum())
        if total <= 0 or total > 40_000_000:
            return
        # —— v8 分块(沿深度序; 块内 bbox 像素 ≤ _RASTER_PIX_BUDGET) ——
        # 块边界 = 累积像素跨过 k·预算 的三角形位置(单三角形超过预算无法
        # 再分 — 其 bbox 已裁到视口, 自然有界)。
        if total > _RASTER_PIX_BUDGET:
            cum = np_.cumsum(area_px.astype(np_.int64))
            cid = cum // _RASTER_PIX_BUDGET
            cuts = np_.flatnonzero(cid[1:] != cid[:-1]) + 1
            bounds = [0] + cuts.tolist() + [T]
        else:
            bounds = [0, T]
        # 贴图逐三角形 UV 坐标(整批取一次; 块内按 tid gather)
        if tex is not None:
            TUV = self._np_uvs[tri_s]           # (T,3,2) float32
            u0t, u1t, u2t = TUV[:, 0, 0], TUV[:, 1, 0], TUV[:, 2, 0]
            v0t, v1t, v2t = TUV[:, 0, 1], TUV[:, 1, 1], TUV[:, 2, 1]
            tex_rgb = tex['rgb']
            tex_alpha = tex['alpha']
            th, tw = tex_rgb.shape[0], tex_rgb.shape[1]
            # v8 过滤 LOD: 用户设置开启双线性 且 本帧非缩放运动帧
            # (缩放<1 的帧自动降最近邻 — 双线性 gather 约 +40% 帧时,
            # 运动中不可感知; _render_pil 在 scale<0.999 时置 False)。
            bilinear = bool(getattr(self, 'tex_filter', True)) and \
                getattr(self, '_filter_lod', None) is not False
        fb = self._fb
        for bi in range(len(bounds) - 1):
            a, b = bounds[bi], bounds[bi + 1]
            if a >= b:
                continue
            area_c = area_px[a:b]
            tot_c = int(area_c.sum())
            if tot_c <= 0 or tot_c > 16_000_000:
                continue                        # 病态单块兜底(与 v7 上限同义)
            wpx_r = np_.repeat(wpx[a:b], area_c)
            xmn_r = np_.repeat(xmn[a:b], area_c)
            ymn_r = np_.repeat(ymn[a:b], area_c)
            starts = np_.repeat(
                (np_.cumsum(area_c) - area_c), area_c).astype(np_.int32)
            offs = np_.arange(tot_c, dtype=np_.int32) - starts
            px = (xmn_r + offs % wpx_r).astype(np_.float32)
            px += np_.float32(0.5)              # 像素中心
            py = (ymn_r + offs // wpx_r).astype(np_.float32)
            py += np_.float32(0.5)
            # —— 重心坐标(float32) ——
            Xc = X[a:b]
            Yc = Y[a:b]
            x0r = np_.repeat(Xc[:, 0], area_c)
            x1r = np_.repeat(Xc[:, 1], area_c)
            x2r = np_.repeat(Xc[:, 2], area_c)
            y0r = np_.repeat(Yc[:, 0], area_c)
            y1r = np_.repeat(Yc[:, 1], area_c)
            y2r = np_.repeat(Yc[:, 2], area_c)
            den = (y1r - y2r) * (x0r - x2r) + (x2r - x1r) * (y0r - y2r)
            with np_.errstate(divide='ignore', invalid='ignore'):
                l0 = ((y1r - y2r) * (px - x2r) +
                      (x2r - x1r) * (py - y2r)) / den
                l1 = ((y2r - y0r) * (px - x2r) +
                      (x0r - x2r) * (py - y2r)) / den
                l2 = 1.0 - l0 - l1
            sd = np_.sign(den)
            eps0_r = np_.repeat(eps0[a:b], area_c)
            eps1_r = np_.repeat(eps1[a:b], area_c)
            eps2_r = np_.repeat(eps2[a:b], area_c)
            inside = (l0 * sd >= -eps0_r) & (l1 * sd >= -eps1_r) & \
                (l2 * sd >= -eps2_r) & (den != 0)
            sel = np_.flatnonzero(inside)
            if sel.size == 0:
                continue
            # —— v8 covered-only: 此后所有每像素工作只作用于 sel ——
            pxi = (px[sel] - np_.float32(0.5)).astype(np_.int32)
            pyi = (py[sel] - np_.float32(0.5)).astype(np_.int32)
            tid = np_.repeat(
                np_.arange(b - a, dtype=np_.int32), area_c)[sel]
            sh_i = shq[a:b][tid]                # uint8 朗伯档
            if tex is not None:
                l0s, l1s, l2s = l0[sel], l1[sel], l2[sel]
                uvx = l0s * u0t[a:b][tid] + l1s * u1t[a:b][tid] + \
                    l2s * u2t[a:b][tid]
                uvy = l0s * v0t[a:b][tid] + l1s * v1t[a:b][tid] + \
                    l2s * v2t[a:b][tid]
                # UV 平铺: 取小数部分(官方纹理寻址 wrap)。
                fx = uvx - np_.floor(uvx)
                fy = uvy - np_.floor(uvy)
                if bilinear:
                    # v8 双线性(官方 D3D9 线性过滤语义): 像素中心对齐
                    # texel 网格 x = u·tw - 0.5, 4 邻域权重插值; alpha
                    # 测试取过滤后 alpha(官方 cutout 在线性过滤下的行为,
                    # 阈值取 8bit 域 128 的连续域中点 127.5)。
                    qx = fx * tw - np_.float32(0.5)
                    qy = fy * th - np_.float32(0.5)
                    xi = np_.floor(qx).astype(np_.int32)
                    yi = np_.floor(qy).astype(np_.int32)
                    tx = qx - xi.astype(np_.float32)
                    ty = qy - yi.astype(np_.float32)
                    xi0 = np_.clip(xi, 0, tw - 1)
                    xi1 = np_.clip(xi + 1, 0, tw - 1)
                    yi0 = np_.clip(yi, 0, th - 1)
                    yi1 = np_.clip(yi + 1, 0, th - 1)
                    w00 = (1.0 - tx) * (1.0 - ty)
                    w01 = tx * (1.0 - ty)
                    w10 = (1.0 - tx) * ty
                    w11 = tx * ty
                    al = (w00 * tex_alpha[yi0, xi0] +
                          w01 * tex_alpha[yi0, xi1] +
                          w10 * tex_alpha[yi1, xi0] +
                          w11 * tex_alpha[yi1, xi1])
                    keep = al >= np_.float32(127.5)
                    if not keep.any():
                        continue
                    c00 = tex_rgb[yi0, xi0]
                    c01 = tex_rgb[yi0, xi1]
                    c10 = tex_rgb[yi1, xi0]
                    c11 = tex_rgb[yi1, xi1]
                    colf = (w00[:, None] * c00 + w01[:, None] * c01 +
                            w10[:, None] * c10 + w11[:, None] * c11)
                    col = np_.clip(colf, 0.0, 255.0).astype(np_.uint8)
                else:
                    # 最近邻(v7 语义, 位级一致)
                    txc = np_.clip((fx * tw).astype(np_.int32), 0, tw - 1)
                    tyc = np_.clip((fy * th).astype(np_.int32), 0, th - 1)
                    keep = tex_alpha[tyc, txc] >= 128   # alpha 测试(cutout)
                    if not keep.any():
                        continue
                    col = tex_rgb[tyc, txc]            # (n,3) uint8
                if not keep.all():
                    pxi = pxi[keep]
                    pyi = pyi[keep]
                    sh_i = sh_i[keep]
                    col = col[keep]
            else:
                n = sel.size
                col = np_.empty((n, 3), dtype=np_.uint8)
                col[:, 0] = base_rgb[0]
                col[:, 1] = base_rgb[1]
                col[:, 2] = base_rgb[2]
            # uint16 整数着色: (col×shade)>>8 — 等价 col*shade/255, 避免两次
            # 浮点转换大临时量(255×255>>8=254, 上限差 1/255 不可见)。
            out_col = (col.astype(np_.uint16) * sh_i[:, None]) >> 8
            # 画家序扁平写入(行序 = 三角形远→近序; 后写覆盖前写)
            fb[pyi, pxi] = out_col

    def _wire_fade(self):
        """v7: viewMode.ts OVERLAY_VERTEX 的全局近似 —
        vEdgeFade = mix(0.2, 1.0, smoothstep(2, 10, edgePixels))。
        edgePixels = 模型平均边长 × 当前像素/单位(透视 f/dist, 正交 k;
        ltk 逐顶点按深度变化, 软件光栅器取每帧单一值)。"""
        sp = self._wire_spacing
        if not sp or sp <= 0:
            return 1.0
        if self.ortho:
            px_per_unit = self.ortho_k
        else:
            h = self._size()[1]
            px_per_unit = (self.focal * (h / 720.0)) / max(self.dist, 1e-6)
        ep = sp * px_per_unit
        t = max(0.0, min(1.0, (ep - 2.0) / 8.0))
        t = t * t * (3.0 - 2.0 * t)             # smoothstep(2, 10)
        return 0.2 + 0.8 * t

    def _stage_extent(self):
        """v7: 地面网格的参照范围(可见子网格包围盒; 键控缓存 — 显隐变更时重算)。"""
        key = (id(self.mesh), tuple(
            s['name'] for s in self.mesh['subs']
            if self.sub_visible.get(s['name'], True)))
        if key != getattr(self, '_stage_key', None):
            self._stage_key = key
            self._stage_bounds = self._visible_bounds()
        return self._stage_bounds

    def _raster_stage_grid(self, scale=1.0, target_img=None):
        """v7: ltk Viewport.ts stage — 地面网格:
        - 地平面 = 模型落脚面(space.ts GROUND_LEVEL 语义 → 可见包围盒 minY);
        - 画家序先于三角形写入帧缓冲 → 主体覆盖网格 = 网格在脚下延伸;
        - 网格间距自适应(每轴 8..16 格), 中心十字轴稍亮作方向参照;
        - numpy 路径逐点写 _fb(免 fromarray 往返), 其余路径 PIL 画线。"""
        if not self.show_grid or self.mesh is None:
            return
        b = self._stage_extent()
        if b is None:
            return
        (mnx, mny, mnz), (mxx, mxy, mxz) = b
        gy = mny
        span = max(mxx - mnx, mxz - mnz, mxy - mny, 50.0) * 1.3
        cx = (mnx + mxx) / 2.0
        cz = (mnz + mxz) / 2.0
        pitch = 1000.0
        for p in (5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0):
            pitch = p
            if span / p <= 16.0:
                break
        segs = []
        x = math.floor((cx - span) / pitch) * pitch
        while x <= cx + span:
            segs.append(((x, gy, cz - span), (x, gy, cz + span), False))
            x += pitch
        z = math.floor((cz - span) / pitch) * pitch
        while z <= cz + span:
            segs.append(((cx - span, gy, z), (cx + span, gy, z), False))
            z += pitch
        segs.append(((cx - span, gy, cz), (cx + span, gy, cz), True))
        segs.append(((cx, gy, cz - span), (cx, gy, cz + span), True))
        pts = []
        for a, c, axis in segs:
            pa = self._screen_of(a)
            pc = self._screen_of(c)
            if pa is None or pc is None:
                continue
            pts.append((pa, pc, axis))
        if not pts:
            return
        if target_img is not None:
            d = _PILDraw.Draw(target_img)
            for pa, pc, axis in pts:
                d.line((pa[0] * scale, pa[1] * scale,
                        pc[0] * scale, pc[1] * scale),
                       fill=(52, 68, 84) if axis else (33, 43, 56), width=1)
            return
        fb = self._fb
        if fb is None or not NP_OK:
            return
        H, W = fb.shape[:2]
        grid_col = _np.array((52, 68, 84), dtype=_np.uint8)
        line_col = _np.array((33, 43, 56), dtype=_np.uint8)
        for pa, pc, axis in pts:
            x0, y0 = pa[0] * scale, pa[1] * scale
            x1, y1 = pc[0] * scale, pc[1] * scale
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            if n > 4000 or n < 2:
                continue
            t = _np.arange(n, dtype=_np.float32) / float(n - 1)
            xs = (x0 + (x1 - x0) * t).astype(_np.int32)
            ys = (y0 + (y1 - y0) * t).astype(_np.int32)
            m = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
            fb[ys[m], xs[m]] = grid_col if axis else line_col

    def _draw_wire_overlay(self, u, v, passes, inv):
        """v7: 线框叠于着色表面(viewMode.ts edges='over'):
        - EDGE_OVERLAY_OPACITY = 0.6 透明度 + 上面 _wire_fade 的拥挤淡出;
        - ltk 把边拉向眼睛(z·0.999)过深度测试且不写深度; 本软件光栅器无
          z-buffer, 叠加线统一画在着色结果之上(近似, 不遮挡判别);
        - inv = 交互缩放坐标 → 全尺寸回映射因子。"""
        if self._img is None or not passes:
            return
        fade = self._wire_fade()
        alpha = int(round(255.0 * EDGE_OVERLAY_OPACITY * fade))
        if alpha <= 10:
            return
        draw = _PILDraw.Draw(self._img, 'RGBA')   # RGB 图上 α 混合绘制
        edge = (0xd0, 0xe0, 0xf0, alpha)
        K = max(1, self.decimate)
        for _zm, si, s, tri_k, zavg, tex in passes:
            if NP_OK and len(tri_k):
                order = _np.argsort(-zavg)
                tri_o = tri_k[order][::K] if K > 1 else tri_k[order]
                Uk = (u[tri_o] * inv).tolist()
                Vk = (v[tri_o] * inv).tolist()
            else:
                Uk = None
            if not Uk:
                continue
            for j in range(len(Uk)):
                draw.line((Uk[j][0], Vk[j][0], Uk[j][1], Vk[j][1],
                           Uk[j][2], Vk[j][2], Uk[j][0], Vk[j][0]),
                          fill=edge, width=1)

    def _render_pil(self, w, h, extra):
        """PIL 位图后缓冲渲染(可选 numpy 向量化)。返回 (绘制数, 保留数)。

        v5.2 numpy 路径:
        - 交互/播放期间自适应分辨率(_interactive_scale 0.30..1.0, 帧时
          反馈): 三角形永不抽稀(精度设置全程生效), 仅降低光栅化分辨率,
          投影线性等比缩放(无畸变), 停手 idle 全分辨率重绘;
        - 同材质(同贴图)子网格合并为单次光栅调用(减少每调固定开销与
          索引排序次数; 无贴图平色回退仍逐子网格保留各自基色)。
        """
        self._frame_projection(w, h)
        m = self.mesh
        n_draw = n_kept = 0
        if NP_OK and self._np_sub_tri and self._last_proj and \
                self._last_proj[0] == 'np':
            (_, u, v, zc, x1, y2v, z2v, _w, _h, _f, _c) = self._last_proj
            # v5.2: 交互自适应分辨率(线性等比缩放, 三角形全量)
            scale = self._interactive_scale()
            ws = max(2, int(round(w * scale)))
            hs = max(2, int(round(h * scale)))
            self._last_scale = scale
            self._ensure_fb(ws, hs)
            if scale != 1.0:
                u = u * scale
                v = v * scale
            # v8 贴图过滤 LOD(标准引擎「运动期降过滤」策略): 缩放 <1
            # 的运动帧自动用最近邻(双线性 gather 约 +40% 帧时; 运动中
            # 过滤差异不可感知), 静止/全分辨率帧用双线性(精度优先)。
            # 停手 idle 全分辨率重绘(v5.2)自动回到双线性清晰度。
            if scale < 0.999:
                self._filter_lod = False
            else:
                self._filter_lod = None          # None = 跟随用户设置
            # v5: numpy 帧缓冲光栅化(贴图 + 平色统一路径)
            # v7 视图模式(viewMode.ts surfaceOf): lit/unshaded 用材质贴图,
            # untextured 平色+光照(官方回退链), wireframe 线框(不走光栅)
            tex_mode = self.view_mode in ('lit', 'unshaded') and \
                self.tex_on and self.tex_map and \
                self._np_uvs is not None and not self.wireframe
            # —— 预过滤 + 子网格级画家序(远→近绘制) ——
            passes = []
            for si, s in enumerate(m['subs']):
                if not self.sub_visible.get(s['name'], True):
                    continue
                tri = self._np_sub_tri[si]
                K = max(1, self.decimate)      # v5.2: 交互不再叠加抽稀(extra≡1)
                if K > 1:
                    tri = tri[::K]
                if len(tri) == 0:
                    continue
                n_kept += int(len(tri))
                U = u[tri]
                V = v[tri]
                Z = zc[tri]
                vis = (Z > 1e-3).all(axis=1)
                if self.cull and int(vis.sum()):
                    ax_, ay_ = U[:, 0], V[:, 0]
                    bx_, by_ = U[:, 1], V[:, 1]
                    cx_, cy_ = U[:, 2], V[:, 2]
                    area = (bx_ - ax_) * (cy_ - ay_) - (by_ - ay_) * (cx_ - ax_)
                    if self._winding < 0:
                        area = -area
                    vis &= area > 0
                tri_k = tri[vis]
                if len(tri_k) == 0:
                    continue
                zavg = Z[vis].mean(axis=1)
                n_draw += int(len(tri_k))
                tex = self.tex_of(s['name']) if tex_mode else None
                passes.append((float(zavg.mean()), si, s, tri_k, zavg, tex))
            passes.sort(key=lambda p: -p[0])
            # 清屏 → 地面网格(ltk stage: 先于主体写入 = 脚下延伸) → 光栅化(远→近)
            self._fb[:, :] = _BG_RGB
            if self.show_grid:
                self._raster_stage_grid(scale)
            if not self.wireframe:
                if tex_mode:
                    # v5.2: 同贴图子网格合并单次光栅调用(默认贴图覆盖大多
                    # 数子网格 → 大模型 13 调 → ~2 调); 平色回退子网格保留
                    # 各自基色不合并。组间仍按平均深度画家序。
                    groups = {}          # id(tex) → {zsum, cnt, items, tex}
                    flats = []           # [(zm, si, tri_k, zavg)] 无贴图子网格
                    for _zm, si, s, tri_k, zavg, tex in passes:
                        if tex is not None:
                            g = groups.get(id(tex))
                            if g is None:
                                g = groups[id(tex)] = dict(
                                    zsum=0.0, cnt=0, items=[], tex=tex)
                            g['zsum'] += float(zavg.sum())
                            g['cnt'] += int(len(tri_k))
                            g['items'].append((tri_k, zavg))
                        else:
                            flats.append((_zm, si, tri_k, zavg))
                    batches = []
                    for g in groups.values():
                        if g['cnt'] == 0:
                            continue
                        zm = g['zsum'] / g['cnt']
                        if len(g['items']) > 1:
                            tri_cat = _np.concatenate(
                                [it[0] for it in g['items']], axis=0)
                            zavg_cat = _np.concatenate(
                                [it[1] for it in g['items']], axis=0)
                        else:
                            tri_cat, zavg_cat = g['items'][0]
                        batches.append((zm, tri_cat, zavg_cat, g['tex'], None))
                    for zm, si, tri_k, zavg in flats:
                        s = m['subs'][si]
                        batches.append((zm, tri_k, zavg, None,
                                        self._sub_color(si, s['name'])))
                    # 组间按平均深度远→近; 组内 _raster_sub 再按 zavg 精排序
                    batches.sort(key=lambda b: -b[0])
                    for _zm, tri_cat, zavg_cat, tex, base_rgb in batches:
                        self._raster_sub(tri_cat, u, v, zc, x1, y2v, z2v,
                                         ws, hs, zavg_cat, tex=tex,
                                         base_rgb=base_rgb or (180, 180, 180))
                else:
                    for _zm, si, s, tri_k, zavg, tex in passes:
                        self._raster_sub(tri_k, u, v, zc, x1, y2v, z2v, ws, hs,
                                         zavg, tex=None,
                                         base_rgb=self._sub_color(si, s['name']))
            # v5.1 关键修复: _fb → _img(fromarray 上屏)。v5 光栅化结果只写
            # 入 numpy 帧缓冲 _fb, 却从未转换回显示位图 _img(_blit 上屏的
            # 是 _img) → 屏幕上只有 HUD 文本, 网格体/贴图全部不可见
            # (=「网格体无法正常渲染」的第二根源; 线框模式画线直写 _img
            # 故不受影响, 造成「线框可见/着色不可见」的假象)。
            # v5.2: _fb 为缩放尺寸时 fromarray 后 NEAREST 放大回全尺寸上屏。
            if self._fb is not None:
                self._img = _PILImage.fromarray(self._fb)
            if self.wireframe:
                draw = _PILDraw.Draw(self._img)
                for _zm, si, s, tri_k, zavg, tex in passes:
                    base = self._sub_color(si, s['name'])
                    order = _np.argsort(-zavg)
                    tri_o = tri_k[order]
                    Uk = u[tri_o]
                    Vk = v[tri_o]
                    for j in range(len(tri_o)):
                        draw.line((float(Uk[j, 0]), float(Vk[j, 0]),
                                   float(Uk[j, 1]), float(Vk[j, 1]),
                                   float(Uk[j, 2]), float(Vk[j, 2]),
                                   float(Uk[j, 0]), float(Vk[j, 0])),
                                  fill=base, width=1)
            if (self._img.width, self._img.height) != (w, h):
                # v8: 缩放帧放大用双线性(旧 NEAREST 在 0.6 档呈可见块状
                # 像素; 双线性放大平滑过渡, 停手全分辨率重绘仍保原生清晰)。
                self._img = self._img.resize((w, h), _PILImage.BILINEAR)
                # v7: 交互缩放坐标 → 全尺寸回映射(叠加线画在全分辨率)
                inv = w / float(max(2, self._fb.shape[1])) \
                    if self._fb is not None else 1.0
            else:
                inv = 1.0
            # v7 线框叠加(viewMode.ts edges='over'): lit/untextured 表面上
            # 叠 EDGE_OVERLAY_OPACITY 透明度边线; 边拥挤时按 smoothstep 淡出
            if self.wire_overlay and self.view_mode in ('lit', 'untextured'):
                self._draw_wire_overlay(u, v, passes, inv)
            # 骨架/HUD 叠加层的画笔(每帧 fromarray/resize 后重建)
            self._draw = _PILDraw.Draw(self._img)
            return n_draw, n_kept
        # 纯 Python + PIL 路径(无 numpy)
        self._ensure_backbuffer(w, h)
        draw = self._draw
        draw.rectangle((0, 0, w - 1, h - 1), fill=_BG_RGB)
        if self.show_grid:
            self._raster_stage_grid(1.0, target_img=self._img)
        proj = self._last_proj[1]
        zcs = self._last_proj[2]
        vx = self._last_proj[3]
        vy = self._last_proj[4]
        vz = self._last_proj[5]
        lx, ly, lz = _LAMP
        polys = []
        for si, tris in self.subs_disp:
            s = m['subs'][si]
            if not self.sub_visible.get(s['name'], True):
                continue
            base = self._sub_color(si, s['name'])
            pal = self._shade_palette(base)
            for t in tris[::max(1, extra)]:
                i0 = m['idx'][t * 3]
                i1 = m['idx'][t * 3 + 1]
                i2 = m['idx'][t * 3 + 2]
                a, b, c = proj[i0], proj[i1], proj[i2]
                if a is None or b is None or c is None:
                    continue
                n_kept += 1
                area = ((b[0] - a[0]) * (c[1] - a[1]) -
                        (b[1] - a[1]) * (c[0] - a[0]))
                if self.cull and (area > 0 if self._winding > 0 else area < 0):
                    continue
                zavg = (zcs[i0] + zcs[i1] + zcs[i2]) / 3.0
                # v7: unshaded 视图模式不经光照 — sh ≡ 1(色阶满档)
                if self.view_mode == 'unshaded':
                    sh = 1.0
                else:
                    ux, uy, uz = vx[i1] - vx[i0], vy[i1] - vy[i0], vz[i1] - vz[i0]
                    wx, wy, wz = vx[i2] - vx[i0], vy[i2] - vy[i0], vz[i2] - vz[i0]
                    nx = uy * wz - uz * wy
                    ny = uz * wx - ux * wz
                    nz = ux * wy - uy * wx
                    nl = math.sqrt(nx * nx + ny * ny + nz * nz)
                    if nl > 1e-9:
                        sh = abs((nx * lx + ny * ly + nz * lz) / nl)
                    else:
                        sh = 0.5
                polys.append((zavg, a, b, c, pal[min(7, int((0.38 + 0.62 * sh)
                                                           * 7.999))]))
        polys.sort(key=lambda k: -k[0])
        n_draw = len(polys)
        if self.wireframe:
            for zavg, a, b, c, _pal in polys:
                draw.line((a[0], a[1], b[0], b[1], c[0], c[1], a[0], a[1]),
                         fill=(200, 200, 200), width=1)
        else:
            for zavg, a, b, c, pal in polys:
                draw.polygon(((a[0], a[1]), (b[0], b[1]), (c[0], c[1])),
                             fill=pal)
        return n_draw, n_kept

    # ------------------------------------------------ Canvas 兜底路径
    def _draw_skeleton(self):
        if not self.show_skeleton or self.rig is None:
            return
        jp = self.joint_positions
        if jp is None:
            jp = self.rig.world_bind_positions()
        pts = [self._screen_of(p) for p in jp]
        mode = self._render_mode()
        if mode == 'pil':
            draw = self._draw
            for i, j in enumerate(self.rig.joints):
                p = self.rig.parents[i]
                if p < 0 or pts[i] is None or pts[p] is None:
                    continue
                draw.line((pts[p][0], pts[p][1], pts[i][0], pts[i][1]),
                         fill=_SKEL_RGB, width=2)
            for i, r in enumerate(pts):
                if r is None:
                    continue
                sel = (i == self.selected_joint)
                rad = 6.0 if sel else 3.5
                color = _SEL_RGB if sel else _JOINT_RGB
                draw.ellipse((r[0] - rad, r[1] - rad, r[0] + rad, r[1] + rad),
                             fill=color,
                             outline=(255, 255, 255) if sel else None)
                if self.show_names and r[2] < self.dist * 1.35:
                    draw.text((r[0] + 7, r[1] - 7),
                             self.rig.joints[i]['name'],
                             font=self._pil_font, fill=_NAME_RGB)
            return
    def _hud_paste(self, lines, rgb):
        """v5.2 性能: HUD 文本条带缓存(贴条, 一次性字体光栅化)。

        旧路径每帧 7 行 PIL 字体渲染 ≈8ms(拖动期纯开销, 大部分行内容
        恒定); 现按「行元组+颜色」缓存 (mask 条带, 纯色层), 命中 = 1 次
        C 级 mask paste(≈0.2ms)。fps/分辨率行变化时仅该次重光栅化。"""
        key = (tuple(lines), rgb)
        ent = self._hud_cache.get(key)
        if ent is None:
            if not lines:
                ent = (None, None, 0)
            else:
                lh = 16
                d0 = _PILDraw.Draw(_PILImage.new('L', (4, 4)))
                ws = []
                for ln in lines:
                    try:
                        ws.append(int(d0.textlength(ln, font=self._pil_font)))
                    except Exception:
                        ws.append(16 * len(ln))
                W = max(ws) + 4 if ws else 4
                strip = _PILImage.new('L', (max(W, 8), lh * len(lines) + 2), 0)
                d = _PILDraw.Draw(strip)
                y = 2
                for ln in lines:
                    if ln:
                        d.text((0, y), ln, font=self._pil_font, fill=255)
                    y += lh
                solid = _PILImage.new('RGB', strip.size, rgb)
                ent = (strip, solid, strip.size[1])
            if len(self._hud_cache) > 96:   # 简单防膨胀
                self._hud_cache.clear()
            self._hud_cache[key] = ent
        return ent

    def _draw_hud(self, w, h, n_draw, n_kept, extra, mode):
        m = self.mesh
        lines = []
        if m:
            lines.append('顶点 %d · 三角形 %d · 子网格 %d'
                         % (m['nv'], m['ni'] // 3, len(m['subs'])))
            lod = self._cv_lod if mode == 'canvas' else \
                max(1, self.decimate * extra)
            # v5.2 性能: 交互/播放期 n_draw 随视角逐帧微变(背面剔除计数),
            # 量化到百位 → 行内容稳定 → HUD 贴条缓存命中; 静止期精确值。
            if self._interacting or getattr(self, '_playing_flag', False):
                nd_show = (n_draw + 50) // 100 * 100
            else:
                nd_show = n_draw
            lines.append('显示 %d/%d 三角形(有效抽稀 1/%d%s)'
                         % (nd_show, m['ni'] // 3, lod,
                            '' if lod > 1 else ', 全量'))
            # v5.2: 交互自适应分辨率状态(三角形全量, 仅运动中降分辨率;
            # 量化到 5% 档位 → 行内容稳定 → HUD 贴条缓存能命中)
            if mode == 'pil' and NP_OK and \
                    getattr(self, '_last_scale', 1.0) < 0.999:
                lines.append('交互分辨率 %d%%(三角形全量 · 停手全分辨率)'
                             % (round(self._last_scale * 20) * 5))
            mode_txt = ('PIL 位图' + ('+numpy' if NP_OK else '')) \
                if mode == 'pil' else 'Canvas 兜底(无剔除/排序, 建议装 Pillow)'
            # v5.2: fps 显示量化(≥2fps 差或 ≥1s 才刷) → 行内容稳定,
            # 避免拖动期 HUD 每帧重光栅化(EMA 浮点逐帧变化会击穿缓存)
            now = time.time()
            if abs(self._fps - getattr(self, '_hud_fps_i', 0.0)) >= 2 or \
                    now - getattr(self, '_hud_fps_t', 0.0) >= 1.0 or \
                    getattr(self, '_hud_fps_i', 0) <= 0:
                self._hud_fps_i = int(max(0, round(self._fps)))
                self._hud_fps_t = now
            lines.append('渲染 %s · %.0f fps' % (mode_txt,
                                                getattr(self, '_hud_fps_i', 0)))
            # v7: 相机预设/视图模式/正交缩放(ltk 相机菜单的 HUD 呈现)
            preset_txt = CAMERA_LABELS.get(self.preset, self.preset)
            if self.ortho:
                preset_txt += ' · 正交 %.2f px/u' % self.ortho_k
            elif self.preset == 'game':
                preset_txt += ' · %d-%d' % GAME_ZOOM
            lines.append('相机 %s · 模式 %s%s' % (
                preset_txt, VIEW_MODE_LABELS.get(self.view_mode, '?'),
                ' · 线框叠加' if self.wire_overlay else ''))
            if self.tex_map and self.view_mode in ('lit', 'unshaded') \
                    and self.tex_on:
                flt = '双线性' if getattr(self, 'tex_filter', True) \
                    else '最近邻'
                if flt == '双线性' and \
                        getattr(self, '_last_scale', 1.0) < 0.999:
                    flt += '(运动帧LOD)'      # v8 过滤 LOD 标注
                lines.append('贴图: 开 · %s · %s' % (
                    self._tex_stats or '%d 张' % len(self.tex_map), flt))
        if self.rig is not None:
            lines.append('骨架 %d 关节 · NSB %d · %s' % (self.rig.n, self.rig.nsb,
                                                          self.rig.skl['fmt']))
        if self.pose_animated:
            lines.append('姿态: 动画采样(CPU 蒙皮)')
        else:
            lines.append('姿态: 绑定')
        if mode == 'pil':
            # v5.2 性能: 缓存贴条替换逐行 draw.text(8ms/帧 → 命中 ~0.2ms)
            shown = [x for x in lines if x]
            strip, solid, hh = self._hud_paste(shown, _HUD_RGB)
            if strip is not None:
                self._img.paste(solid, (12, 10), strip)
                y = 10 + hh
            else:
                y = 10
            if self._hud:
                strip2, solid2, _h2 = self._hud_paste([self._hud],
                                                      _NOTE_RGB)
                if strip2 is not None:
                    self._img.paste(solid2, (12, max(y + 4, h - 26)),
                                    strip2)
                    y += _h2
    # ------------------------------------------------ 交互
    def _on_b1(self, e):
        self._drag = ('rot', e.x, e.y)

    def _on_b2(self, e):
        self._drag = ('pan', e.x, e.y)

    def _on_drag(self, e):
        if getattr(self, '_drag', None) and self._drag[0] == 'rot':
            dx, dy = e.x - self._drag[1], e.y - self._drag[2]
            self._drag = ('rot', e.x, e.y)
            # v7: 拖动脱离预设 → 切环绕(ltk SceneCamera 拖动语义)
            self._demote_to_orbit()
            yaw = self._goal_of('yaw', 0.6) - dx * 0.008
            # v5.2: 俯仰拖拽方向 — 「贴面跟手」(鼠标下拉 → 相机升高俯视);
            # v7: 限幅 ±90°(轴向视图可达, ltk 正交预设)
            pitch = max(-_PITCH_MAX, min(_PITCH_MAX,
                                         self._goal_of('pitch', 0.35) - dy * 0.008))
            self._set_goal(dict(yaw=yaw, pitch=pitch),
                           DRAG_SMOOTHING_TAU)
            self._interacting = True

    def _on_pan(self, e):
        if getattr(self, '_drag', None) and self._drag[0] == 'pan':
            dx, dy = e.x - self._drag[1], e.y - self._drag[2]
            self._drag = ('pan', e.x, e.y)
            h = self._size()[1]
            # 屏幕像素 → 世界单位换算: 透视按立距/焦距, 正交按 1/k
            if self.ortho:
                s = 1.0 / max(self.ortho_k, 1e-9)
            else:
                s = self.dist / (self.focal * (h / 720.0))
            cy, sy = math.cos(self.yaw), math.sin(self.yaw)
            cp, sp = math.cos(self.pitch), math.sin(self.pitch)
            mx, my = -dx * s, dy * s
            gt = self._goal.get('target', self.target) if self._goal \
                else self.target
            nt = (gt[0] + cy * mx,
                  gt[1] + cp * my - sp * (sy * mx),
                  gt[2] - sy * mx + sp * (cp * my))
            self._set_goal(dict(target=nt), DRAG_SMOOTHING_TAU)
            self._interacting = True

    def _on_release(self, e):
        self._drag = None
        self._interacting = False
        self._schedule_idle_full()

    def _on_wheel(self, e):
        self._zoom_by(0.9 if e.delta > 0 else 1.1)

    def _on_wheel_l(self, e):
        self._zoom_by(0.9)

    def _on_wheel_d(self, e):
        self._zoom_by(1.1)


    # -------------------------------------------- Qt 事件与输出层(PySide6)
    def _after(self, ms, fn):
        t = QTimer(self)
        t.setSingleShot(True)
        t.timeout.connect(fn)
        t.start(int(ms))
        return t

    def _after_cancel(self, tid):
        try:
            if tid is not None:
                tid.stop()
                tid.deleteLater()
        except Exception:
            pass

    def _note_img(self, text):
        """无模型/无 Pillow 时的提示画面(PIL 可用则烤进后缓冲)。"""
        self._note_text = text
        if PIL_OK:
            w, h = self._size()
            img = _PILImage.new('RGB', (w, h), _BG_RGB)
            d = _PILDraw.Draw(img)
            try:
                d.text((20, 20), text, fill=_HUD_RGB)
            except Exception:
                pass
            self._img = img
            self._draw = d
            self._blit(w, h)
        else:
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        try:
            if self._qimg is not None and not self._qimg.isNull():
                p.drawImage(0, 0, self._qimg)
            else:
                p.fillRect(self.rect(), QColor(_BG_RGB[0], _BG_RGB[1],
                                               _BG_RGB[2]))
                if getattr(self, '_note_text', None):
                    p.setPen(QColor(_HUD_RGB[0], _HUD_RGB[1], _HUD_RGB[2]))
                    p.drawText(self.rect(),
                              Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                              self._note_text)
            self._paint_gizmo(p)
        finally:
            p.end()

    def _paint_gizmo(self, p):
        """左上朝向控件(ltk OrientationGizmo 观感): 深色盘 + 三轴头。"""
        heads = getattr(self, '_gizmo_heads', None)
        if not heads:
            return
        cx = cy = 41.0
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor(0x31, 0x40, 0x4f), 1)
        p.setPen(pen)
        p.setBrush(QColor(0x1a, 0x21, 0x2c))
        p.drawEllipse(2, 2, 80, 80)
        font = self._gizmo_font()
        for ai, px, py, z2 in heads:
            col = QColor(_GIZMO_RGB[ai][0], _GIZMO_RGB[ai][1],
                         _GIZMO_RGB[ai][2])
            p.setPen(QPen(col, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(QPointF(cx, cy), QPointF(px, py))
            p.setBrush(col)
            p.drawEllipse(QPointF(px, py), 7.0, 7.0)
            p.setPen(QPen(QColor(0x10, 0x14, 0x1a)))
            p.setFont(font)
            p.drawText(QPointF(px - 4.0, py + 4.0), 'XYZ'[ai])

    @staticmethod
    def _gizmo_font():
        global _GIZMO_FONT_CACHE
        f = globals().get('_GIZMO_FONT_CACHE')
        if f is None:
            f = QFont('Segoe UI,Arial', 8, QFont.Weight.Bold)
            _GIZMO_FONT_CACHE = f
        return f

    def _gizmo_pick(self, x, y):
        """点击命中 gizmo 轴头 → 返回轴(供 look 翻转)。"""
        heads = getattr(self, '_gizmo_heads', None)
        if not heads:
            return None
        for ai, px, py, z2 in heads:
            if (x - px) ** 2 + (y - py) ** 2 <= 10.0 ** 2:
                return _GIZMO_AXES[ai]
        return None

    def mousePressEvent(self, e):
        pos = e.position()
        ax = self._gizmo_pick(pos.x(), pos.y())
        if ax is not None:
            self._gizmo_look(ax)
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self._on_b1(_Ev(e))
        elif e.button() in (Qt.MouseButton.MiddleButton,
                            Qt.MouseButton.RightButton):
            self._on_b2(_Ev(e))

    def mouseMoveEvent(self, e):
        drag = getattr(self, '_drag', None)
        if drag and drag[0] == 'rot':
            self._on_drag(_Ev(e))
        elif drag and drag[0] == 'pan':
            self._on_pan(_Ev(e))

    def mouseReleaseEvent(self, e):
        self._on_release(_Ev(e))

    def wheelEvent(self, e):
        d = e.angleDelta().y()
        self._zoom_by(0.9 if d > 0 else 1.1)

    def dump_png(self, path):
        """测试/导出: 当前后缓冲图像 1:1 存 PNG(替代旧 PostScript 导出)。"""
        img = getattr(self, '_img', None)
        if img is None:
            return False
        try:
            img.save(path, 'PNG')
            return True
        except Exception:
            return False

    def dump_postscript(self, path):
        """兼容旧名: 等价 dump_png(.png 路径)。"""
        return self.dump_png(path)


class _Ev(object):
    """Qt 鼠标事件 → 旧处理器(x/y/delta)桥(处理器本体保持 v8.3 原样)。"""

    __slots__ = ('x', 'y', 'delta')

    def __init__(self, e):
        pos = e.position() if hasattr(e, 'position') else e.pos()
        self.x = pos.x()
        self.y = pos.y()
        self.delta = 0


def _process_events():
    app = QApplication.instance()
    if app is not None:
        app.processEvents()


_GIZMO_FONT_CACHE = None
