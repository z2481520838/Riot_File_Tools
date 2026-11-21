# coding: utf-8
"""app.core.character.player — 角色预览控制器(v8.3 播放引擎移植, GUI 无关)。

职责(与 UI 解耦, 状态经回调上抛):
  · 模型链: load_skn/.skl/Rig + 官方一键链(load_config → 皮肤包 →
    .skn+.skl+.blnd+贴图+SubmeshesToHide, CharacterData::Load 语义)
  · 动画: load_anm(多资产)/Sequencer 连播/帧步进播放(墙钟重锚,
    官方整 tick 语义)/姿态帧缓存(有界, ltk MAX_POSES 同义)
  · 蒙皮: numpy 4 槽向量化/纯 Python 兜底; 显示顶点集合全量蒙皮
    (官方 SkinningVertex: 隐藏仅渲染层)
  · 事件: 动画↔事件表自动桥接(anim_key 双通道) + 播放期官方
    SubmeshVisibility 窗口判定(帧起 endFrame 止, 负值=到 clip 末)
  · 材质: 官方 Texture/MaterialOverride%d 优先级 + 旧式多贴图键兜底
回调接口(self.cb_*): status(str) / time(fidx, total, t, dur) /
frames(int) / mask_changed() / anm_changed() / blnd_changed()。"""

from ._compat import os, time  # noqa: F401
from ._compat import _np, NP_OK
from .core import (parse_skn, parse_skl, parse_anm, parse_blnd, parse_config,
                   Rig, elf_hash, anim_key, list_skin_packages,
                   build_material_bindings, resolve_material_overrides,
                   resolve_asset_path, resolve_blnd_anim_ref,
                   decode_dds_texture, _texture_keys_cfg, cfg_get,
                   _CLIP_KIND_NAMES)
from .core import _POSE_CACHE_MAX_BYTES


def _sub_name_tokens(name):
    """子网格名 → 贴图命名匹配用 token 列表(非字母数字切分, 小写)。"""
    out, cur = [], []
    for ch in (name or ''):
        if ch.isalnum():
            cur.append(ch)
        else:
            if cur:
                out.append(''.join(cur).lower())
                cur = []
    if cur:
        out.append(''.join(cur).lower())
    return [t for t in out if len(t) >= 3]


class Player(object):
    """角色预览控制器: 绑定一个 viewport.Viewport 实例驱动渲染。"""

    def __init__(self, vp):
        self.vp = vp                     # Viewport(QWidget)
        # 资产
        self.m = None                   # skn mesh
        self.skl = None
        self.rig = None
        self.cfg = None                  # IniAsset | InibinAsset
        self.data_root = ''
        self._cfg_active_row = None
        self._skin_pkgs = []
        self._cfg_blnd_pending = None
        # 动画
        self.anm_list = []
        self.anm = None
        # 播放状态
        self.playing = False
        self.play_speed = 1.0
        self.play_t = 0.0
        self._play_t0 = 0.0
        self._play_anchor = 0.0
        self._play_fidx = -1
        self._play_frames = 0
        # Sequencer 连播
        self._seq_playlist = None
        self._seq_bounds = None
        self._seq_total = 0.0
        self._seq_cur = -1
        self._seq_clips = None
        self._seq_label = ''
        # 显示顶点/姿态缓存/蒙皮
        self._display_verts = []
        self._pose_frames = {}
        self._pose_cache_bytes = 0
        self._np_skin = None
        # 双层显隐掩码(引擎层 + 用户层)
        self._engine_mask = {}
        self._initial_sub_mask = {}
        self._user_sub_over = {}
        self._sub_by_hash = None
        # 事件
        self._ev_blnd = None
        self._ev_clip_events = None
        # 回调(UI 注入)
        self.cb_status = None            # (str)
        self.cb_time = None              # (fidx, total_frames, t, dur)
        self.cb_frames = None            # (本周期帧计数)
        self.cb_mask_changed = None      # ()
        self.cb_anm_changed = None       # ()
        self.cb_blnd_changed = None      # ()

    # ------------------------------------------------------------ 回调上抛
    def _status(self, msg):
        if self.cb_status:
            try:
                self.cb_status(msg)
            except Exception:
                pass

    # ------------------------------------------------------------ 模型载入
    def load_skn(self, path, skl_path=None):
        """载入 .skn(+同名/指定 .skl) — 同步(预览链不做 Sim 体检)。"""
        m = parse_skn(path)
        skl = None
        rig = None
        if skl_path is None:
            sib = os.path.splitext(path)[0] + '.skl'
            if os.path.exists(sib):
                skl_path = sib
        if skl_path:
            skl = parse_skl(skl_path)
            rig = Rig(skl)
        self.m, self.skl, self.rig = m, skl, rig
        # v6.1: 掩码随新模型重置(引擎层全显)
        self._engine_mask = {s['name']: True for s in m['subs']}
        self._initial_sub_mask = dict(self._engine_mask)
        self._user_sub_over = {}
        self._display_verts = []
        self._pose_frames = {}
        self._pose_cache_bytes = 0
        self._np_skin = None
        # 抽稀默认(v8: numpy 光栅目标 60000 三角形 — 典型英雄全量)
        ntri = m['ni'] // 3
        target = 60000 if NP_OK else 4000
        K = 1
        for cand in (1, 2, 4, 8, 16):
            if ntri // cand <= target:
                K = cand
                break
        self.vp.set_decimate(K)
        self.vp.set_model(m, self.rig)
        if self.anm_list and self.rig is not None:
            for a in self.anm_list:
                a.map_to_rig(self.rig)
        self._status('已加载 %s — 子网格 %d · 三角形 %d%s'
                     % (os.path.basename(path), len(m['subs']), ntri,
                        (' · 骨架 %d 关节' % self.rig.n)
                        if self.rig else ' · 无骨架(仅网格)'))
        if self.cfg is not None:
            self._apply_submeshes_to_hide()
            self._load_render_textures()
            self._cfg_attach_model()
        return m

    # ------------------------------------------------------- 官方一键链
    def load_config(self, path):
        """导入 .ini/.inibin → 解析 + 皮肤包清单(官方链入口)。"""
        self.cfg = parse_config(path)
        if not self.data_root:
            self.data_root = os.path.dirname(os.path.dirname(path))
        self._cfg_active_row = None
        try:
            self._skin_pkgs = list_skin_packages(self.cfg)
        except Exception:
            self._skin_pkgs = []
        self._status('已载入角色配置: %s — %s · 皮肤包 %d'
                     % (os.path.basename(path), self.cfg.fmt,
                        len(self._skin_pkgs)))
        return self.cfg

    def skin_packages(self):
        return list(self._skin_pkgs or [])

    def load_skin_package(self, pkg):
        """官方链一键载入(CharacterData::Load 语义):
        .skn + .skl + .blnd + 材质贴图 + SubmeshesToHide。"""
        cfg = self.cfg
        if cfg is None or pkg is None:
            return False
        cfg_dir = os.path.dirname(os.path.abspath(cfg.path))
        pkg['data_root'] = self.data_root
        r = pkg.get('resolved') or {}
        skn_p = r.get('skn')
        skl_p = r.get('skl') or None
        blnd_p = r.get('blnd')
        self._cfg_active_row = pkg
        self._cfg_blnd_pending = blnd_p
        if skn_p:
            self.load_skn(skn_p, skl_p)
            self._status('官方链载入: %s — %s%s%s'
                         % (pkg['section'], os.path.basename(skn_p),
                            (' + ' + os.path.basename(skl_p)) if skl_p else '',
                            (' + ' + os.path.basename(blnd_p)) if blnd_p else ''))
        elif blnd_p:
            self._cfg_after_model_load()
            self._status('官方链(部分): [%s] 网格体未找到 — 动画池 %s 已载入'
                         % (pkg['section'], os.path.basename(blnd_p)))
        else:
            self._status('官方链: [%s] 未找到模型文件与动画池' % pkg['section'])
            return False
        return True

    def _cfg_after_model_load(self):
        blnd_p = self._cfg_blnd_pending
        self._cfg_blnd_pending = None
        if not blnd_p:
            return
        try:
            self.load_blnd(blnd_p)
        except Exception as e:
            self._status('动画池(.blnd)载入失败: %s' % e)
            return
        cfg_dir = os.path.dirname(os.path.abspath(self.cfg.path)) \
            if self.cfg else None
        blnd_dir = os.path.dirname(blnd_p) or None
        extra = ()
        if cfg_dir and blnd_dir:
            try:
                if not os.path.samefile(cfg_dir, blnd_dir):
                    extra = (blnd_dir,)
            except OSError:
                extra = (blnd_dir,)
        elif blnd_dir:
            extra = (blnd_dir,)
        loaded, missed = 0, 0
        known = set(getattr(a, 'path', '') for a in self.anm_list)
        for ref in (self._ev_blnd.anim_refs if self._ev_blnd else []):
            name = (ref.get('name') or '').strip()
            if not name:
                continue
            lp = resolve_blnd_anim_ref(cfg_dir, self.data_root, name,
                                        extra_bases=extra)
            if not lp or lp in known:
                continue
            try:
                self.anm_list.append(parse_anm(lp))
                if self.rig is not None:
                    self.anm_list[-1].map_to_rig(self.rig)
                loaded += 1
            except Exception:
                missed += 1
        if self.cb_anm_changed:
            self.cb_anm_changed()
        if loaded or missed:
            self._status('官方动画池: 外置 .anm 载入 %d 个(失败 %d)'
                         % (loaded, missed))
        # 当前动画若已有 → 立即桥接事件表(v8.3)
        if self.anm is not None and self._ev_clip_events is None:
            self._ev_bind_anm_events(self.anm)

    # ------------------------------------------------------------- blnd/事件
    def load_blnd(self, path):
        """载入 .blnd(官方指针链硬化解析) + 事件表绑定(自动桥接)。"""
        ba = parse_blnd(path)
        self._ev_blnd = ba
        self._ev_clip_events = None
        if self.anm is not None:
            bound = self._ev_bind_anm_events(self.anm)
            if bound:
                self._status('动画池: %s — %d 事件表 · 当前动画已桥接 %s'
                             % (os.path.basename(path), len(ba.events), bound))
        if self.cb_blnd_changed:
            self.cb_blnd_changed()
        return ba

    def blnd_clips(self):
        return list((getattr(self._ev_blnd, 'pool_clips', None) or []))

    def _ev_bind_clip_events(self, clip):
        """绑定 clip 名 → 事件表(播放期官方事件应用)。"""
        self._ev_clip_events = None
        self._restore_initial_mask()
        ba = self._ev_blnd
        if ba is None or clip is None:
            return None
        name = clip.get('name') if isinstance(clip, dict) else None
        for t in (getattr(ba, 'events', None) or []):
            if getattr(t, 'owner_clip', None) == name:
                self._ev_clip_events = t
                return name
        return None

    def _ev_bind_anm_events(self, anm):
        """动画资产 → 事件表自动桥接(v8.3 修复: 普通播放路径事件生效)。

        双通道官方语义: 1) blnd AnimNames 引用链(anim_idx → clip → 表);
        2) owner_clip 名 == 动画基名(anim_key 规范化)。"""
        self._ev_clip_events = None
        ba = self._ev_blnd
        if anm is None or ba is None:
            return None
        key = anim_key(getattr(anm, 'path', ''))
        if not key:
            return None
        refs = getattr(ba, 'anim_refs', None) or []
        pool_clips = getattr(ba, 'pool_clips', None) or []
        for i, r in enumerate(refs):
            if anim_key(r.get('name') or '') != key:
                continue
            for c in pool_clips:
                if (c.get('clip_kind') or 'atomic') == 'atomic' \
                        and c.get('anim_idx') == i:
                    self._ev_bind_clip_events({'name': c['name']})
                    if self._ev_clip_events is not None:
                        return c['name']
                    break
        for t in (getattr(ba, 'events', None) or []):
            if anim_key(getattr(t, 'owner_clip', '') or '') == key:
                self._ev_bind_clip_events({'name': t.owner_clip})
                if self._ev_clip_events is not None:
                    return t.owner_clip
        return None

    def _restore_initial_mask(self):
        """引擎层恢复初始掩码(官方 mInitialSubmeshToHideMask 回置)。"""
        if self.m is not None:
            init = self._initial_sub_mask or \
                {s['name']: True for s in self.m['subs']}
            if dict(self._engine_mask) != init:
                self._engine_mask = dict(init)
                self._sub_mask_apply()

    def _apply_clip_events(self, t):
        """播放期官方事件应用: SubmeshVisibility(类型3) → 子网格显隐。

        官方语义(AnimEventSubmeshVisibility + AnimationHelperClient):
        事件帧起 显示/隐藏 至 endFrame(负值=持续到 clip 末),
        窗口外恢复初始掩码。哈希 = HashStringELF(大小写折叠)。"""
        tab = self._ev_clip_events
        if tab is None or self.m is None:
            return
        evs = [e for e in (tab.events or [])
               if e.get('type_id') == 3 and (e.get('show_hash') or
                                             e.get('hide_hash'))]
        if not evs:
            return
        td = getattr(tab, 'owner_tick_duration', 0) or 0
        fps = (1.0 / td) if 0 < td < 1e4 else (
            self.anm.fps if self.anm and 0.5 < self.anm.fps < 240 else 30.0)
        t_f = t * fps
        if self._sub_by_hash is None:
            self._sub_by_hash = {elf_hash(s['name']): s['name']
                                 for s in self.m['subs']}
        init = self._initial_sub_mask or \
            {s['name']: True for s in self.m['subs']}
        eng = dict(self._engine_mask or init)
        changed = False
        for e in evs:
            start = e['frame']
            end = e.get('end_frame')
            if end is None or end < 0:
                end = 1e9            # 持续到 clip 末(官方 -1 语义)
            active = start <= t_f < end
            for h, vis in ((e.get('show_hash') or 0, True),
                           (e.get('hide_hash') or 0, False)):
                if not h:
                    continue
                name = self._sub_by_hash.get(h)
                if not name:
                    continue
                want = vis if active else init.get(name, True)
                if eng.get(name, True) != want:
                    eng[name] = want
                    changed = True
        if changed:
            self._engine_mask = eng
            self._sub_mask_apply()

    def _sub_mask_apply(self):
        """双层显隐掩码落地: 引擎层 ∪ 用户层(覆盖优先) → 视口。"""
        if self.m is None:
            return
        eff = dict(self._engine_mask) if self._engine_mask \
            else {s['name']: True for s in self.m['subs']}
        for k, v in (self._user_sub_over or {}).items():
            eff[k] = v
        self.vp.sub_visible.clear()
        self.vp.sub_visible.update(eff)
        self.vp._cv_items_key = None
        if self.cb_mask_changed:
            self.cb_mask_changed()

    def set_user_sub_visibility(self, name, visible):
        """用户手动层显隐(跨片段保留; v6.1 官方双层语义)。"""
        self._user_sub_over[name] = bool(visible)
        self._sub_mask_apply()

    # --------------------------------------------------- SubmeshesToHide
    def _apply_submeshes_to_hide(self):
        """官方 SubmeshesToHide(SkinnedMesh::LoadSkinINI):
        清单 → ELF 哈希 → 位掩码 → 初始不可见(引擎层)。"""
        if self.m is None or self.cfg is None:
            return
        row = self._cfg_active_row or {}
        sec = row.get('section') if isinstance(row, dict) else None
        sec = (sec or 'MeshSkin') if (sec or 'MeshSkin') else 'MeshSkin'
        raw = cfg_get(self.cfg, sec, 'SubmeshesToHide', '') or ''
        raw = str(raw).strip()
        if not raw:
            return
        import re as _re
        names = [t for t in _re.split(r'[,;\s]+', raw) if t]
        if not names:
            return
        want = set(n.lower() for n in names)
        eng = {}
        hidden = []
        for s in self.m['subs']:
            hide = s['name'].lower() in want
            eng[s['name']] = not hide
            if hide:
                hidden.append(s['name'])
        self._engine_mask = eng
        self._initial_sub_mask = dict(eng)
        self._sub_by_hash = None
        self._sub_mask_apply()
        if hidden:
            self._status('SubmeshesToHide 生效: 隐藏 %d/%d 子网格(%s)'
                         % (len(hidden), len(self.m['subs']),
                            ', '.join(hidden[:4]) +
                            (' …' if len(hidden) > 4 else '')))

    # ------------------------------------------------------------ 贴图装配
    def _load_render_textures(self):
        """v6 贴图渲染装配(官方 LoadSkinINI + MaterialOverride 全链):
        Texture 键 → 默认; MaterialOverride%d 优先级降序逐子网格求值;
        旧式多贴图键/命名 token 兜底; 失败回退均色/分类色。"""
        if self.m is None or self.cfg is None:
            return
        cfg = self.cfg
        cfg_dir = os.path.dirname(os.path.abspath(cfg.path))
        row = self._cfg_active_row or {}
        sec = row.get('section') if isinstance(row, dict) else None
        sec = (sec or 'MeshSkin') if (sec or 'MeshSkin') else 'MeshSkin'
        texmap = {}
        used_paths = []
        bindings, default_ref, overrides = build_material_bindings(cfg, sec)
        sub_names = [s['name'] for s in self.m['subs']]
        official_ref = resolve_material_overrides(sub_names, overrides,
                                                  default_ref)
        refs = {}
        for low, ref in official_ref.items():
            if ref:
                refs.setdefault(ref, low)
        for key, ref in bindings.items():
            if ref and ref not in refs:
                refs[ref] = key
        for ref in list(refs.keys()):
            lp = resolve_asset_path(cfg_dir, self.data_root, ref)
            if not lp:
                continue
            tex, err = decode_dds_texture(lp)
            if tex is None:
                self._status('贴图解码失败 %s: %s'
                             % (os.path.basename(lp), err))
                continue
            tex['path'] = lp
            used_paths.append(lp)
            for low, r2 in official_ref.items():
                if r2 == ref:
                    texmap[low] = tex
            for key, r2 in bindings.items():
                if r2 == ref:
                    texmap.setdefault(key, tex)
        n_over = sum(1 for low, r in official_ref.items()
                     if overrides and r != (default_ref or ''))
        covered = set(texmap.keys())
        extra_paths = []
        for ref in _texture_keys_cfg(cfg, sec):
            lp = resolve_asset_path(cfg_dir, self.data_root, ref)
            if lp and lp not in used_paths:
                extra_paths.append(lp)
        for tp in (row.get('tex_ps') or []):
            if tp and tp not in used_paths and tp not in extra_paths:
                extra_paths.append(tp)
        for lp in extra_paths:
            tex, err = decode_dds_texture(lp)
            if tex is None:
                continue
            tex['path'] = lp
            used_paths.append(lp)
            base = os.path.basename(lp).lower()
            for s in self.m['subs']:
                low = s['name'].lower()
                if low in covered:
                    continue
                if any(t in base for t in _sub_name_tokens(s['name'])):
                    texmap[low] = tex
                    covered.add(low)
        self.vp.set_textures(texmap)
        if texmap:
            hit = sum(1 for s in self.m['subs']
                      if (s['name'].lower() in texmap) or ('' in texmap))
            ov = (' · 材质覆盖生效 %d 子网格' % n_over) if n_over else ''
            self._status('官方材质装配: 贴图 %d 张 — 渲染覆盖 %d/%d 子网格%s'
                         % (len(used_paths), hit, len(self.m['subs']), ov))
        if self.cb_mask_changed:
            self.cb_mask_changed()

    def _cfg_attach_model(self):
        """模型载入后: 官方贴图均色 → 子网格着色(无解码依赖的轻链)。"""
        row = self._cfg_active_row
        if row is None or self.m is None:
            return
        if 'tex_ps' not in row and (row.get('resolved') or {}).get('textures'):
            row['tex_ps'] = [tp for _k, _v, tp in
                             row['resolved']['textures']]
        from .core import load_dds_info
        tint = {}
        used = []
        for tp in (row.get('tex_ps') or []):
            info, _e = load_dds_info(tp)
            if info is None:
                continue
            used.append(tp)
            for s in self.m['subs']:
                low = s['name'].lower()
                if any(t in os.path.basename(tp).lower()
                       for t in _sub_name_tokens(s['name'])):
                    if low not in tint:
                        tint[low] = info['avg']
        if tint:
            self.vp.set_tint_map(tint)
            self.vp.use_tint = True

    # ------------------------------------------------------------ 动画选择
    def load_anm(self, path):
        """载入一个 .anm 资产(追加列表, 不自动切换)。"""
        for a in self.anm_list:
            if getattr(a, 'path', '') == path:
                return a
        a = parse_anm(path)
        if self.rig is not None:
            a.map_to_rig(self.rig)
        self.anm_list.append(a)
        if self.cb_anm_changed:
            self.cb_anm_changed()
        return a

    def select_anm(self, anm):
        """切换当前动画(脱离连播; v8.3 自动桥接事件表)。"""
        if anm is None:
            return
        self._pose_frames = {}
        self._pose_cache_bytes = 0
        self._np_skin = None
        self._play_fidx = -1
        self._seq_clear()
        self.anm = anm
        if self.rig is not None:
            anm.map_to_rig(self.rig)
        self.play_t = 0.0
        self._sample_pose(0.0)
        bound = self._ev_bind_anm_events(anm)
        note = ''
        if bound:
            note = ' · 事件表 %s(播放期事件生效)' % bound
        elif self._ev_blnd is not None:
            note = ' · 无匹配事件表(此动画事件不派发)'
        self._status('动画: %s — 匹配骨架 %d/%d 轨道%s'
                     % (os.path.basename(anm.path), len(anm.rig_map),
                        len(anm.tracks), note))
        if self.cb_anm_changed:
            self.cb_anm_changed()

    # ------------------------------------------------------- Sequencer 连播
    def _seq_clear(self):
        self._seq_playlist = None
        self._seq_bounds = None
        self._seq_total = 0.0
        self._seq_cur = -1
        self._seq_clips = None
        self._seq_label = ''

    def _seq_setup(self, anms, clips=None):
        """装配 Sequencer 顺序连播: 分段边界/总时长 + 事件表绑定。"""
        self._seq_clear()
        if not anms:
            return
        bounds = [0.0]
        for a in anms:
            bounds.append(bounds[-1] + max(a.duration, 1e-4))
        self._seq_playlist = list(anms)
        self._seq_bounds = bounds
        self._seq_total = bounds[-1]
        self._seq_clips = list(clips or [])
        self._seq_cur = -1
        self._seq_label = 'Sequencer'
        self.anm = anms[0]
        if self.rig is not None:
            self.anm.map_to_rig(self.rig)
        self.play_t = 0.0
        self._sample_pose(0.0)
        self._pose_frames = {}
        self._pose_cache_bytes = 0
        self._ev_bind_clip_events(self._seq_clips[0]
                                  if self._seq_clips else None)

    def _ev_representative_child(self, c, depth=0):
        """官方 Pool::GetLongestMainChildRecursive 语义(代表子片段)。"""
        if depth > 16:
            return None
        kind = c.get('clip_kind') or 'atomic'
        if kind == 'atomic':
            return c
        pool_clips = (self._ev_blnd or
                      type('X', (), {'pool_clips': []})).pool_clips or []
        ch = []
        for ci in (c.get('children') or []):
            if 0 <= ci < len(pool_clips):
                ch.append(pool_clips[ci])
        if not ch:
            return None
        if kind == 'parallel':
            mains = [k for k in ch if (k.get('flags') or 0) & 1]
            cand = mains or ch
            best = None
            best_d = -1.0
            for k in cand:
                d = (k.get('end_tick', 0) or 0) * (k.get('tick_duration') or 0)
                if d > best_d:
                    best_d, best = d, k
            if best is not None:
                r = self._ev_representative_child(best, depth + 1)
                if r is not None:
                    return r
            return self._ev_representative_child(ch[0], depth + 1)
        return self._ev_representative_child(ch[0], depth + 1)

    def _ev_atomic_descendants(self, c, depth=0):
        """容器 clip → 有序原子 clip 清单(Sequencer 播放顺序用)。"""
        if depth > 16:
            return []
        kind = c.get('clip_kind') or 'atomic'
        if kind == 'atomic':
            return [c]
        pool_clips = (self._ev_blnd or
                      type('X', (), {'pool_clips': []})).pool_clips or []
        out = []
        for ci in (c.get('children') or []):
            if 0 <= ci < len(pool_clips):
                out.extend(self._ev_atomic_descendants(pool_clips[ci],
                                                       depth + 1))
        return out

    def _ev_load_clip_anm(self, c):
        """原子 clip → 外置 .anm(官方路径解析 + 载入)。"""
        ba = self._ev_blnd
        ai = c.get('anim_idx')
        if ba is None or ai is None or not (0 <= ai < len(ba.anim_refs)):
            return None
        ref = (ba.anim_refs[ai].get('name') or '').strip()
        if not ref:
            return None
        cfg_dir = os.path.dirname(os.path.abspath(self.cfg.path)) \
            if self.cfg else None
        blnd_dir = os.path.dirname(ba.path) or None
        extra = ()
        if cfg_dir and blnd_dir:
            try:
                if not os.path.samefile(cfg_dir, blnd_dir):
                    extra = (blnd_dir,)
            except OSError:
                extra = (blnd_dir,)
        elif blnd_dir:
            extra = (blnd_dir,)
        lp = resolve_blnd_anim_ref(cfg_dir, self.data_root, ref,
                                   extra_bases=extra)
        if not lp:
            return None
        try:
            return self.load_anm(lp)
        except Exception:
            return None

    def play_clip(self, c):
        """官方 clip 语义播放: Atomic 直播; Sequencer 顺序连播;
        其余容器 → 代表子片段(GetLongestMainChildRecursive)。"""
        kind = c.get('clip_kind') or 'atomic'
        if kind == 'atomic':
            a = self._ev_load_clip_anm(c)
            if a is not None:
                self.select_anm(a)
                self._ev_bind_clip_events(c)
                self.start_play()
                return True
            # .anm 缺失也绑事件表(图表可看; 稍后选同名动画自动桥接)
            self._ev_bind_clip_events(c)
            self._status('clip %s — .anm 缺失暂不播放, 事件表已绑(%d 事件)'
                         % (c['name'], len((self._ev_clip_events.events
                                            if self._ev_clip_events else []) or [])))
            return False
        if kind == 'sequencer':
            atoms = self._ev_atomic_descendants(c)
            seq = []
            for ac in atoms:
                a = self._ev_load_clip_anm(ac)
                if a is not None:
                    seq.append((a, ac))
            if seq:
                self._seq_setup([a for a, _c in seq],
                                [cc for _a, cc in seq])
                self.start_play()
                self._status('clip %s — Sequencer 顺序连播 %d 段'
                             % (c['name'], len(seq)))
                return True
            self._status('clip %s — 子片段无可播 .anm' % c['name'])
            return False
        rep = self._ev_representative_child(c)
        if rep is not None:
            a = self._ev_load_clip_anm(rep)
            if a is not None:
                self.select_anm(a)
                self._ev_bind_clip_events(rep)
                self.start_play()
                self._status('clip %s — 代表子片段 %s(%s 官方语义)'
                             % (c['name'], rep['name'],
                                _CLIP_KIND_NAMES.get(kind, kind)))
                return True
        self._status('clip %s — %s 无可解析子片段'
                     % (c['name'], _CLIP_KIND_NAMES.get(kind, kind)))
        return False

    # ------------------------------------------------------------ 播放引擎
    def start_play(self, reset=True):
        if reset:
            self.play_t = 0.0
            self._play_anchor = 0.0
            self._play_fidx = -1
        self.playing = True
        self.vp.set_playing(True)
        self._play_t0 = time.perf_counter()

    def pause_play(self):
        self.playing = False
        self.vp.set_playing(False)

    def toggle_play(self):
        if self.playing:
            self.pause_play()
        else:
            self.start_play(reset=False)
            self._play_t0 = time.perf_counter()

    def seek(self, t):
        """滑杆 seek(暂停态): 采样该帧并重绘。"""
        self._play_anchor = float(t)
        self.play_t = float(t)
        self._sample_pose(float(t))
        self.vp.request_render()

    def set_speed(self, speed):
        if self.playing:
            self._play_anchor = self.play_t
            self._play_t0 = time.perf_counter()
        self.play_speed = max(0.05, float(speed))

    def tick(self):
        """播放步进(由 UI QTimer 驱动, 对齐下一动画帧边界 — v8.3 语义)。"""
        if not self.playing or self.anm is None:
            return None
        now = time.perf_counter()
        wall = now - self._play_t0
        speed = max(0.05, self.play_speed)
        seq = self._seq_playlist
        if seq:
            total = max(self._seq_total, 1e-6)
            t = (self._play_anchor + wall * speed) % total
            bounds = self._seq_bounds or [0.0, total]
            k = 0
            for j in range(len(bounds) - 1):
                if bounds[j] <= t < bounds[j + 1]:
                    k = j
                    break
                if j == len(bounds) - 2:
                    k = j
            a = seq[k]
            if self.anm is not a:
                # 段界切换: 换动画 + 姿态缓存清 + 事件表重绑
                self.anm = a
                if self.rig is not None:
                    a.map_to_rig(self.rig)
                self._pose_frames = {}
                self._pose_cache_bytes = 0
                self._play_fidx = -1
                clips = self._seq_clips
                self._ev_bind_clip_events(clips[k] if clips and
                                          k < len(clips) else None)
            local_t = t - bounds[k]
            fps = a.fps if 0.5 < a.fps < 240 else 30.0
            frame_dt = 1.0 / fps
            fidx = int(local_t * fps)
            if fidx != self._play_fidx:
                self._play_fidx = fidx
                self.play_t = min(fidx * frame_dt, max(a.duration, 1e-6))
                self._sample_pose_f(fidx, fps, local_t)
                self._apply_clip_events(local_t)
                self._play_frames += 1
            to_next = frame_dt - (local_t % frame_dt)
            delay_ms = max(1, min(15.0,
                                  to_next * 1000.0 / max(speed, 1e-6) - 1.0))
            return int(delay_ms)
        dur = max(self.anm.duration, 1e-6)
        t = (self._play_anchor + wall * speed) % dur
        fps = self.anm.fps if 0.5 < self.anm.fps < 240 else 30.0
        frame_dt = 1.0 / fps
        fidx = int(t * fps)
        if fidx != self._play_fidx:
            self._play_fidx = fidx
            self.play_t = min(fidx * frame_dt, dur)
            self._sample_pose_f(fidx, fps, t)
            self._apply_clip_events(t)
            self._play_frames += 1
        to_next = frame_dt - (t % frame_dt)
        delay_ms = max(1, min(15.0, to_next * 1000.0 / max(speed, 1e-6) - 1.0))
        return int(delay_ms)

    # ------------------------------------------------------ 姿态采样/蒙皮
    def _rebuild_display_verts(self):
        """收集显示三角形引用的顶点集合(全子网格蒙皮, 官方 SkinningVertex)。"""
        if self.m is None:
            self._display_verts = []
            return
        self._pose_frames = {}
        self._pose_cache_bytes = 0
        self._np_skin = None
        need = set()
        for si, tris in self.vp.subs_disp:
            for t in tris:
                need.update(self.m['idx'][t * 3:t * 3 + 3])
        self._display_verts = sorted(need)

    def _pose_cache_insert(self, fidx, verts, jp):
        """姿态帧缓存插入(键=帧号; 有界字节上限 FIFO 淘汰)。"""
        cache = self._pose_frames
        if fidx in cache:
            return
        nbytes = int(verts.nbytes) + int(jp.nbytes)
        if nbytes > _POSE_CACHE_MAX_BYTES:
            return
        while cache and self._pose_cache_bytes + nbytes > \
                _POSE_CACHE_MAX_BYTES:
            k0 = next(iter(cache))
            old = cache.pop(k0)
            self._pose_cache_bytes -= int(old[0].nbytes) + int(old[1].nbytes)
        cache[fidx] = (verts, jp)
        self._pose_cache_bytes += nbytes

    def _np_skin_arrays(self):
        """numpy 蒙皮数据(显示顶点)一次构建, 播放期间复用。"""
        if not NP_OK or self.m is None or not self._display_verts:
            return None
        if self._np_skin is not None:
            return self._np_skin
        dv = self._display_verts
        verts = self.m['verts']
        P = _np.asarray([verts[vi][0] for vi in dv], dtype=_np.float32)
        B = _np.asarray([verts[vi][1] for vi in dv], dtype=_np.int32)
        W = _np.asarray([verts[vi][2] for vi in dv], dtype=_np.float32)
        IDX = _np.asarray(dv, dtype=_np.int32)
        self._np_skin = (P, B, W, IDX)
        return self._np_skin

    def _skin_display_verts(self, infl, world):
        """蒙皮当前显示顶点: numpy 向量化(4 权重槽合成先行)或纯 Python。"""
        dv = self._display_verts
        verts = self.m['verts']
        ns = self._np_skin_arrays()
        if ns is not None and infl is not None:
            P, B, W, IDX = ns
            M = _np.asarray(infl, dtype=_np.float32)          # (J,3,4)
            ok = B < M.shape[0]
            Bc = _np.where(ok, B, 0)
            Wc = _np.where(ok, W, 0.0)
            accM = Wc[:, 0, None, None] * M[Bc[:, 0]]
            for k in range(1, 4):
                wk = Wc[:, k]
                if not wk.any():
                    continue
                accM += wk[:, None, None] * M[Bc[:, k]]
            acc = (accM[:, :, :3] * P[:, None, :]).sum(axis=2) + accM[:, :, 3]
            return acc
        skin_pos = {}
        for vi in dv:
            p, bi, bw = verts[vi]
            x = y = z = 0.0
            for k in range(4):
                w = bw[k]
                if w <= 0.0:
                    continue
                M = infl[bi[k]] if bi[k] < len(infl) else None
                if M is None:
                    continue
                x += w * (M[0][0] * p[0] + M[0][1] * p[1] +
                          M[0][2] * p[2] + M[0][3])
                y += w * (M[1][0] * p[0] + M[1][1] * p[1] +
                          M[1][2] * p[2] + M[1][3])
                z += w * (M[2][0] * p[0] + M[2][1] * p[1] +
                          M[2][2] * p[2] + M[2][3])
            skin_pos[vi] = (x, y, z)
        return skin_pos

    def _sample_pose_f(self, fidx, fps, t):
        """整帧采样(缓存键=动画帧号; 官方整 tick 语义)。"""
        t_tick = (fidx / fps) if (fps and fps > 0) else t
        cache = self._pose_frames
        hit = cache.get(fidx)
        if hit is not None:
            self.vp.set_positions_array(hit[0], hit[1])
        else:
            locals_ = self.rig.local_pose_anm(self.anm, t_tick)
            world, skin, infl = self.rig.skinning_from_locals(locals_)
            ns = self._np_skin_arrays()
            bind = self.vp._np_bind_array()
            if ns is not None and bind is not None and infl is not None:
                acc = self._skin_display_verts(infl, world)
                verts = bind.copy()
                verts[ns[3]] = acc
                jp = _np.asarray([(w[0][3], w[1][3], w[2][3])
                                  for w in world], dtype=_np.float32)
                self._pose_cache_insert(fidx, verts, jp)
                self.vp.set_positions_array(verts, jp)
            else:
                skin_pos = self._skin_display_verts(infl, world)
                jp = [(world[i][0][3], world[i][1][3], world[i][2][3])
                      for i in range(self.rig.n)]
                if len(cache) < 4096:
                    cache[fidx] = (skin_pos, jp)
                self.vp.set_positions_sparse(skin_pos, jp)
        if self.cb_time:
            total = int(max(getattr(self.anm, 'duration', 0.0) *
                            fps, 1))
            self.cb_time(fidx, total, t_tick,
                         getattr(self.anm, 'duration', 0.0))

    def _sample_pose(self, t):
        """按 4.17 RigPose 求值链采样一帧并 CPU 蒙皮(帧缓存)。"""
        if self.anm is None or self.m is None:
            return
        if self.rig is None:
            self._status('该模型未配骨架, 无法播放动画')
            return
        if not self._display_verts:
            self._rebuild_display_verts()
        fps = self.anm.fps if 0.5 < self.anm.fps < 240 else 30.0
        self._sample_pose_f(int(t * fps), fps, t)

    def ensure_display_verts(self):
        if self.m is not None and not self._display_verts:
            self._rebuild_display_verts()
