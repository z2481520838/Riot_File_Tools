# coding: utf-8
"""app.core.character.core — LoL 4.20/4.17 角色资产硬化解析核心。

从 skn420_viewer v8.3(经 38 项回归验证)原样移植的纯逻辑层:
  · 哈希: HashStringELF(大小写折叠, 官方 ELFHash.cpp 逐行)/FNV-1a/
    HashStringCaseInsensitiveFNV(4.20 exe 0x530cf0 逐指令)
  · SKN(SkinnedMesh)/SKL(双格式)/Rig(官方关节树+逆绑定+ELF 校验)
  · ANM v3/v4/v5/canm(量化四元数解码)+ 轨道插值(Catmull-Rom)
  · INI/INIBIN(官方 ConfigFile/PropertyReader 语义)+ 材质绑定
    (SkinnedMesh::LoadSkinINI + MaterialOverride 优先级)
  · BLND: 官方指针数组定位 + 边界校验(替代旧实现硬编码 108 偏移的
    脆弱读取 — 见 Riot_File_Tools 旧 read_blnd), EventResource
    帧表({dataID, frame} 按帧升序)+ 哈希表双副本互证;
  · 4.20 模拟器(Sim420 多 pass 关节预算)与判定(run_checks)
零 GUI 依赖: 本模块不 import 任何 Tk/Qt。"""

from ._compat import (io, math, os, re, struct, sys, time,   # noqa: F401
                      _PILImage, _PILDraw, _PILFont, PIL_OK,
                      _np, NP_OK)
import itertools  # noqa: F401


TOOL_VERSION = '8.0 (2026-11-20, 渲染精度/帧率/占用优化 — ltk pose·切片语义)'

# ---------------- 4.20/4.17 引擎常量(出处见文件头) ----------------
NPASS = 4            # mPassJoints[4]
PASS_CAP = 68        # 每 pass 关节容量 (0x962430)
# v8 光栅分块预算: 每块 bbox 像素上限(ltk-manager 后台烘焙限时切片的
# 资源语义 — 限时切片限制每帧烘焙 6ms, 这里限每块瞬时临时量 ≈45MB:
# 块内 ≈16 个像素级 float32/int32 数组 × 512k × 4B)。旧单批无界(最坏
# 40M 像素 ≈ GB 级瞬时分配) = 「占用高」主因之一。
_RASTER_PIX_BUDGET = 512_000
# v8 姿态帧缓存字节上限(ltk preview/animation.rs MAX_POSES 烘焙上限同义):
# 值 = (nv×3 + n×3)×4B/帧, Kayn_Skin20 ≈0.16MB/帧 → ≈400 帧(典型整段
# 动画全部缓存); 旧 dict 缓存 ≈2MB/帧 且仅按条数上限 4096。
_POSE_CACHE_MAX_BYTES = 64 << 20
MIN_TO_ADD_INIT = 13 # 0x9622a1
MAT_CAP = 255        # static float Mat[255*12] / RIG_BONE_LIMIT=255
REG_BASE = 0x18      # SetVertexShaderConstantF 起始寄存器
REG_CAP = 256        # SM2.0 顶点着色器常量寄存器上限
WORD_MAX = 65535     # 索引 WORD / 顶点计数上限
PALETTE_WARN = 250   # palette 余量告警线(255-5)
FREE3_STRUCT = 12    # pass3 空位结构性安全线(任何三角形需求 <= 12 槽)
RIG_BONE_LIMIT = 255 # RigResource.cpp: RIG_BONE_LIMIT

SEV_PASS, SEV_WARN, SEV_FAIL = 'PASS', 'WARN', 'FAIL'
SEV_INFO, SEV_SKIP = 'INFO', 'SKIP'


class SknError(Exception):
    pass


# ============================================================ 数学库 ===
# 约定: 四元数 (x, y, z, w); 仿射矩阵 3x4 = [ [r0,r1,r2,t], x3 行 ] (行主序);
# 姿态分解 pos + quat + scale(先缩放后旋转再平移), 与 Riot::Xform 一致。

def qnorm(q):
    n = math.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3])
    if n == 0.0:
        return (0.0, 0.0, 0.0, 1.0)
    return (q[0] / n, q[1] / n, q[2] / n, q[3] / n)


def qmat(q):
    """四元数 -> 3x3 旋转矩阵(行主序)。"""
    x, y, z, w = qnorm(q)
    return ((1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)),
            (2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)),
            (2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)))


def qconj(q):
    return (-q[0], -q[1], -q[2], q[3])


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qrot(q, v):
    """v' = q * (v, 0) * conj(q)。"""
    qv = qmul(q, (v[0], v[1], v[2], 0.0))
    return qmul(qv, qconj(q))[:3]


def qslerp(a, b, t):
    a, b = qnorm(a), qnorm(b)
    d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]
    if d < 0.0:
        b = (-b[0], -b[1], -b[2], -b[3])
        d = -d
    if d > 0.9995:
        return qnorm(tuple(a[i] + (b[i] - a[i]) * t for i in range(4)))
    th = math.acos(max(-1.0, min(1.0, d)))
    s = math.sin(th)
    if abs(s) < 1e-9:
        return a
    wa = math.sin((1.0 - t) * th) / s
    wb = math.sin(t * th) / s
    return qnorm(tuple(a[i] * wa + b[i] * wb for i in range(4)))


def qdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]


def q_from_mat3(M):
    """3x3 旋转矩阵(行主序) -> 四元数(xyzw)。"""
    m00, m01, m02 = M[0]
    m10, m11, m12 = M[1]
    m20, m21, m22 = M[2]
    tr = m00 + m11 + m22
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (m21 - m12) / s
        y = (m02 - m20) / s
        z = (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        w = (m21 - m12) / s
        x = 0.25 * s
        y = (m01 + m10) / s
        z = (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        w = (m02 - m20) / s
        x = (m01 + m10) / s
        y = 0.25 * s
        z = (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        w = (m10 - m01) / s
        x = (m02 + m20) / s
        y = (m12 + m21) / s
        z = 0.25 * s
    return qnorm((x, y, z, w))


def trs_to_mat(pos, scl, rot):
    """pos + quat + scale -> 3x4 仿射(先缩放, 后旋转, 再平移)。"""
    R = qmat(rot)
    return [[R[0][0] * scl[0], R[0][1] * scl[1], R[0][2] * scl[2], pos[0]],
            [R[1][0] * scl[0], R[1][1] * scl[1], R[1][2] * scl[2], pos[1]],
            [R[2][0] * scl[0], R[2][1] * scl[1], R[2][2] * scl[2], pos[2]]]


def mat_mul(A, B):
    """3x4 仿射乘(父 x 子)。"""
    return [[A[0][0] * B[0][0] + A[0][1] * B[1][0] + A[0][2] * B[2][0],
             A[0][0] * B[0][1] + A[0][1] * B[1][1] + A[0][2] * B[2][1],
             A[0][0] * B[0][2] + A[0][1] * B[1][2] + A[0][2] * B[2][2],
             A[0][0] * B[0][3] + A[0][1] * B[1][3] + A[0][2] * B[2][3] + A[0][3]],
            [A[1][0] * B[0][0] + A[1][1] * B[1][0] + A[1][2] * B[2][0],
             A[1][0] * B[0][1] + A[1][1] * B[1][1] + A[1][2] * B[2][1],
             A[1][0] * B[0][2] + A[1][1] * B[1][2] + A[1][2] * B[2][2],
             A[1][0] * B[0][3] + A[1][1] * B[1][3] + A[1][2] * B[2][3] + A[1][3]],
            [A[2][0] * B[0][0] + A[2][1] * B[1][0] + A[2][2] * B[2][0],
             A[2][0] * B[0][1] + A[2][1] * B[1][1] + A[2][2] * B[2][1],
             A[2][0] * B[0][2] + A[2][1] * B[1][2] + A[2][2] * B[2][2],
             A[2][0] * B[0][3] + A[2][1] * B[1][3] + A[2][2] * B[2][3] + A[2][3]]]


def mat_apply(M, v):
    return (M[0][0] * v[0] + M[0][1] * v[1] + M[0][2] * v[2] + M[0][3],
            M[1][0] * v[0] + M[1][1] * v[1] + M[1][2] * v[2] + M[1][3],
            M[2][0] * v[0] + M[2][1] * v[1] + M[2][2] * v[2] + M[2][3])


def mat_apply3(M, v):
    """仅旋转+缩放部分作用(不含平移)。"""
    return (M[0][0] * v[0] + M[0][1] * v[1] + M[0][2] * v[2],
            M[1][0] * v[0] + M[1][1] * v[1] + M[1][2] * v[2],
            M[2][0] * v[0] + M[2][1] * v[1] + M[2][2] * v[2])


def mat_inverse(M):
    """3x4 仿射逆。"""
    a, b, c = M[0][0], M[0][1], M[0][2]
    d, e, f = M[1][0], M[1][1], M[1][2]
    g, h, i = M[2][0], M[2][1], M[2][2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-12:
        return None
    inv = [[(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
           [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
           [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det]]
    t = (M[0][3], M[1][3], M[2][3])
    return [inv[0] + [-sum(inv[0][k] * t[k] for k in range(3))],
            inv[1] + [-sum(inv[1][k] * t[k] for k in range(3))],
            inv[2] + [-sum(inv[2][k] * t[k] for k in range(3))]]


def mat_to_trs(M):
    """3x4 -> (pos, quat, scale)。"""
    sx = math.sqrt(M[0][0] ** 2 + M[1][0] ** 2 + M[2][0] ** 2)
    sy = math.sqrt(M[0][1] ** 2 + M[1][1] ** 2 + M[2][1] ** 2)
    sz = math.sqrt(M[0][2] ** 2 + M[1][2] ** 2 + M[2][2] ** 2)
    if det3(M) < 0:  # 镜像姿态: 把符号并到一个缩放轴上
        sx = -sx
    R = [[M[r][0] / sx if sx else 0.0, M[r][1] / sy if sy else 0.0,
          M[r][2] / sz if sz else 0.0] for r in range(3)]
    return ((M[0][3], M[1][3], M[2][3]), q_from_mat3(R), (sx, sy, sz))


def det3(M):
    return (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1])
            - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
            + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))


def catmull_rom_factors(t):
    """Riot CatmullRomSplineFactors (Anim_CompressedAnimResource.cpp 原式)。"""
    f0 = ((-0.5 * t + 1.0) * t - 0.5) * t
    f1 = (1.5 * t - 2.5) * (t * t) + 1.0
    f2 = ((-1.5 * t + 2.0) * t + 0.5) * t
    f3 = (t - 1.0) * (0.5 * t * t)
    return f0, f1, f2, f3


def catmull_rom_vec(t, p0, p1, p2, p3):
    f0, f1, f2, f3 = catmull_rom_factors(t)
    return tuple(p0[k] * f0 + p1[k] * f1 + p2[k] * f2 + p3[k] * f3 for k in range(3))


def catmull_rom_quat(t, q0, q1, q2, q3):
    """原实现: 四元数各分量做样条加权后 Normalize。"""
    f0, f1, f2, f3 = catmull_rom_factors(t)
    return qnorm(tuple(q0[k] * f0 + q1[k] * f1 + q2[k] * f2 + q3[k] * f3
                       for k in range(4)))


def elf_hash(s):
    """Riot::HashFunctions::HashStringELF(4.17 ELFHash.cpp 逐行对齐):
    大写折小写(c += 32), h = c + 16h, 高 4 位折叠 h ^= high ^ (high>>24)。
    (v6 修正: 旧实现缺大小写折叠 — 'LeeSin_tree'/'LeeSin_Tree' 官方同哈希
    0x540415; 骨架/子网格哈希匹配由此一致。)"""
    h = 0
    for ch in s.encode('ascii', 'replace'):
        c = ch
        if 0x41 <= c <= 0x5A:          # 'A'..'Z' → 小写(官方)
            c += 32
        h = (c + 16 * h) & 0xFFFFFFFF
        high = h & 0xF0000000
        if high:
            h = (h ^ high ^ (high >> 24)) & 0xFFFFFFFF
    return h


def fnv1a_hash(s):
    """FNV-1a 32bit(新版 ANM 关节哈希兼容)。"""
    h = 0x811C9DC5
    for c in s.encode():
        h = ((h ^ c) * 0x01000193) & 0xFFFFFFFF
    return h


def anim_key(path):
    """v8.3: 动画资产名规范化(动画文件 ↔ blnd clip 名互匹配用)。

    官方引用链: blnd AnimNames 记 'characters/kayn/skins/skin20/
    animations/transform_assassin.pie_c_13_22.anm' ↔ clip 名
    'Transform_Assassin' — 基名(剥 .anm + 剥构建后缀 .pie_c_N_N)
    大小写折叠后相等。v8.2 及之前普通动画下拉/播放按钮路径从不
    绑事件表 → 播放期事件全部静默失效(用户实测 StartFrame>0 的
    Transform 后续事件不在规定帧切换; @0 事件因初始掩码全显示而
    视觉无差异, 被误判为'生效')。"""
    n = os.path.basename(str(path or '')).lower()
    n = re.sub(r'\.pie_c_\d+_\d+\.anm$', '', n)
    n = re.sub(r'\.anm$', '', n)
    return n.strip()


def fnv1_ci_hash(s):
    """HashStringCaseInsensitiveFNV — 4.20 exe 0x530cf0 逐指令还原。

    指令序列(每字符): 大写 A-Z 折叠为小写 → h *= 0x01000193(FNV-1 先乘) →
    h ^= c。与 FNV-1a(先异或后乘)不同, 本函数是 Riot 资源格式令牌
    (skFormatToken)与事件名哈希(EventNameHash)的官方算法。"""
    h = 0x811C9DC5
    for ch in s.encode():
        c = ch
        if 0x41 <= c <= 0x5A:
            c += 0x20
        h = (h * 0x01000193) & 0xFFFFFFFF
        h ^= c
    return h


# ---- 官方资源格式令牌(4.20 exe @0x530cf0..0x530ea7 哨兵字符串的运行时哈希) --
_SENTINEL_EVENT = '__Riot::Animation::EventResource::skFormatToken__'
_SENTINEL_RIG = '__Riot::Animation::RigResource::skFormatToken__'
_SENTINEL_ANIM = '__Riot::Animation::AnimationResource::skFormatToken__'
_SENTINEL_POOL = '__Riot::Animation::AnimationPoolData::skFormatToken__'
_SENTINEL_MASK = '__Riot::Animation::MaskResource::skFormatToken__'
TOKEN_EVENT = fnv1_ci_hash(_SENTINEL_EVENT)      # 0x4C15E8DD
TOKEN_RIG = fnv1_ci_hash(_SENTINEL_RIG)          # 0x22FD4FC3
TOKEN_ANIM = fnv1_ci_hash(_SENTINEL_ANIM)        # 0xBE0794D3
TOKEN_POOL = fnv1_ci_hash(_SENTINEL_POOL)        # 0x5A40C9DD
TOKEN_MASK = fnv1_ci_hash(_SENTINEL_MASK)        # 0x4BBB4577

# ---- BLND/ANM 二进制头(4.20 exe 0x897b2d 三重比较, 0x8972b0 通用读取器) --
BLND_ENGINE_TYPE = 0x32643372      # "r3d2"
BLND_BLOCK_TYPE = 0x646E6C62       # "blnd"
BLND_VERSION = 1
CANM_BLOCK_TOKEN = 0x6D6E6163      # "canm" — CompressedAnimResource 块类型
ANM_V3_VERSION = 3                 # AnimationResource(r3d2anmd)裸版本


def decode_quantized_quat(v0, v1, v2):
    """48bit 量化四元数(ANM v5/r3d2canm; 同 QuantizedQuaternion48):
    bits: [45:47] 最大分量索引, [30:45]/[15:30]/[0:15] 三个 15bit 分量。"""
    bits = (v0 & 0xFFFF) | ((v1 & 0xFFFF) << 16) | ((v2 & 0xFFFF) << 32)
    max_index = (bits >> 45) & 0x3
    a = ((bits >> 30) & 0x7FFF) / 32767.0 * math.sqrt(2.0) - 1.0 / math.sqrt(2.0)
    b = ((bits >> 15) & 0x7FFF) / 32767.0 * math.sqrt(2.0) - 1.0 / math.sqrt(2.0)
    c = (bits & 0x7FFF) / 32767.0 * math.sqrt(2.0) - 1.0 / math.sqrt(2.0)
    d = math.sqrt(max(0.0, 1.0 - a * a - b * b - c * c))
    if max_index == 0:
        return (d, a, b, c)
    if max_index == 1:
        return (a, d, b, c)
    if max_index == 2:
        return (a, b, d, c)
    return (a, b, c, d)


def encode_quantized_quat(q):
    """48bit 量化四元数编码(自检/合成动画用; 与解码互逆, 误差 < 1e-4 量级)。"""
    q = qnorm(q)
    idx = max(range(4), key=lambda k: abs(q[k]))
    comp = [q[k] for k in range(4) if k != idx]
    hi = 1.0 / math.sqrt(2.0)
    vals = [int(round((v + hi) / (2.0 * hi) * 32767.0)) for v in comp]
    vals = [max(0, min(0x7FFF, v)) for v in vals]
    bits = (idx << 45) | (vals[0] << 30) | (vals[1] << 15) | vals[2]
    return (bits & 0xFFFF, (bits >> 16) & 0xFFFF, (bits >> 32) & 0xFFFF)


# ============================================================ SKN 解析 ===

def parse_skn(path):
    """解析 .skn (v0x10001~0x10005), 自动探测子网格四元组字段序, 校验完美分区。
    与 skn420_doctor 的解析逐字同源; 额外抽取法线/UV 供渲染。"""
    d = open(path, 'rb').read()
    if len(d) < 24:
        raise SknError('文件过小(不足文件头)')
    magic, version = struct.unpack_from('<II', d, 0)
    if version < 0x10000 or version > 0x10005:
        raise SknError('不支持的 SKN 版本 0x%x' % version)
    pos = 8
    (cnt,) = struct.unpack_from('<I', d, pos)
    pos += 4
    if cnt == 0 or cnt > 512:
        raise SknError('子网格数异常: %d' % cnt)
    if pos + cnt * 80 > len(d):
        raise SknError('子网格表越界')
    raw = []
    for i in range(cnt):
        name = d[pos:pos + 64].split(b'\0', 1)[0].decode('ascii', 'replace')
        q = struct.unpack_from('<IIII', d, pos + 64)
        raw.append((name, q))
        pos += 80
    if version <= 0x10003:
        if pos + 8 > len(d):
            raise SknError('几何头越界')
        ni, nv = struct.unpack_from('<II', d, pos)
        pos += 8
        vsize, vtype, flags = 0x34, 0, 0
    else:
        if pos + 60 > len(d):
            raise SknError('几何头越界')
        flags, ni, nv, vsize, vtype = struct.unpack_from('<IIIII', d, pos)
        pos += 60
    if vsize < 52:
        raise SknError('顶点流尺寸异常: 0x%x' % vsize)
    idx_off = pos
    if idx_off + ni * 2 + nv * vsize > len(d):
        raise SknError('索引区/顶点区与文件大小不符 (ni=%d nv=%d vsize=0x%x filesize=%d)'
                      % (ni, nv, vsize, len(d)))
    idx = list(struct.unpack_from('<%dH' % ni, d, idx_off))
    vert_off = idx_off + ni * 2
    verts, normals, uvs = [], [], []
    for i in range(nv):
        o = vert_off + i * vsize
        p = struct.unpack_from('<3f', d, o)
        bi = struct.unpack_from('<4B', d, o + 12)
        bw = struct.unpack_from('<4f', d, o + 16)
        verts.append((p, bi, bw))
        if vsize >= 52:
            normals.append(struct.unpack_from('<3f', d, o + 32))
            uvs.append(struct.unpack_from('<2f', d, o + 44))
        else:
            normals.append((0.0, 0.0, 1.0))
            uvs.append((0.0, 0.0))

    # 子网格四元组字段序自动探测: 必须对顶点区与索引区各构成完美分区
    chosen = None
    for perm in itertools.permutations(range(4)):
        subs = []
        for name, q in raw:
            subs.append(dict(name=name, fv=q[perm[0]], vc=q[perm[1]],
                             fi=q[perm[2]], ic=q[perm[3]]))
        sv = sorted((s['fv'], s['vc']) for s in subs)
        si = sorted((s['fi'], s['ic']) for s in subs)
        if sum(x[1] for x in sv) != nv or sum(x[1] for x in si) != ni:
            continue
        cur, okv = 0, True
        for fv, vc in sv:
            if fv != cur:
                okv = False
                break
            cur = fv + vc
        cur, oki = 0, True
        for fi, ic in si:
            if fi != cur:
                oki = False
                break
            cur = fi + ic
        if okv and oki:
            chosen = (perm, subs)
            break
    if chosen is None:
        raise SknError('子网格四元组无法构成完美分区(结构损坏或字段序未知)')
    perm, subs = chosen
    tail = len(d) - (vert_off + nv * vsize)
    return dict(path=path, data=d, magic=magic, version=version, ni=ni, nv=nv,
                vsize=vsize, vtype=vtype, flags=flags, idx=idx, verts=verts,
                normals=normals, uvs=uvs,
                idx_off=idx_off, vert_off=vert_off, subs=subs,
                subperm=perm, tail=tail)

# ============================================================ SKL 解析 ===

def parse_skl(path):
    """解析 .skl 全量(骨架树 / 绑定 / 影响表), 兼容两代格式:
    · 新令牌格式 0x22FD4FC3(RigResource): 64B 头, 关节 100B 全字段(局部 TRS +
      逆绑定 TRS + ELF 名哈希 + 相对名字偏移 @0x60), 影响表 i16[NSB] = 着色器骨
      -> 关节映射(NumShaderBones 即 NSB)。
    · 旧 r3d2-sklt: 8B 魔数 + 版本(1/2) + 关节数; 关节 88B(名 32 + 父 i32 +
      半径 f32 + 全局矩阵 f32x12); v2 关节表后为 u32 NSB + i16 影响表。
    返回 dict 兼容 skn420_doctor 的字段(fmt/num_joints/nsb)并附加全部骨架数据。"""
    d = open(path, 'rb').read()
    if len(d) < 32:
        raise SknError('.skl 文件过小')
    token = struct.unpack_from('<I', d, 4)[0]
    if token == 0x22FD4FC3:
        return _parse_skl_token(d, path)
    r3did, sklt = struct.unpack_from('<II', d, 0)
    if r3did == 0x32643372 and sklt == 0x746c6b73:
        return _parse_skl_legacy(d, path)
    raise SknError('无法识别的 .skl 格式 (token 0x%08x / magic 0x%08x)' % (token, r3did))


def _cstr(d, off):
    end = d.index(b'\0', off)
    return d[off:end].decode('ascii', 'replace')


def _parse_skl_token(d, path):
    nj = struct.unpack_from('<H', d, 14)[0]
    nsb = struct.unpack_from('<I', d, 16)[0]
    joff = struct.unpack_from('<I', d, 20)[0]
    ioff = struct.unpack_from('<I', d, 28)[0]
    bno = struct.unpack_from('<I', d, 40)[0]
    if nj == 0 or nj > RIG_BONE_LIMIT:
        raise SknError('.skl 关节数异常: %d (RIG_BONE_LIMIT=%d)' % (nj, RIG_BONE_LIMIT))
    if joff + nj * 100 > len(d):
        raise SknError('.skl 关节表越界')
    joints = []
    for i in range(nj):
        o = joff + i * 100
        jid = struct.unpack_from('<H', d, o + 2)[0]
        par = struct.unpack_from('<h', d, o + 4)[0]
        nh = struct.unpack_from('<I', d, o + 8)[0]
        radius = struct.unpack_from('<f', d, o + 12)[0]
        pos = struct.unpack_from('<3f', d, o + 16)
        scl = struct.unpack_from('<3f', d, o + 28)
        rot = struct.unpack_from('<4f', d, o + 40)
        ibt = struct.unpack_from('<3f', d, o + 56)
        ibs = struct.unpack_from('<3f', d, o + 68)
        ibq = struct.unpack_from('<4f', d, o + 80)
        nrel = struct.unpack_from('<i', d, o + 96)[0]
        # Joint::Sync: mName = 相对偏移 + 该字段自身地址
        name = _cstr(d, (o + 96 + nrel) if 0 <= o + 96 + nrel < len(d) else bno)
        joints.append(dict(id=jid, parent=par, name=name, hash=nh, radius=radius,
                            pos=pos, scl=scl, rot=qnorm(rot),
                            ib_t=ibt, ib_s=ibs, ib_q=qnorm(ibq)))
    if nsb and ioff + nsb * 2 <= len(d):
        influences = list(struct.unpack_from('<%dh' % nsb, d, ioff))
    else:
        influences = list(range(nj))
    return dict(path=path, fmt='new(v0x22FD4FC3)', num_joints=nj, nsb=nsb,
                joints=joints, influences=influences, names=[j['name'] for j in joints])


def _parse_skl_legacy(d, path):
    ver = struct.unpack_from('<I', d, 8)[0]
    nj = struct.unpack_from('<I', d, 12)[0]
    if ver not in (1, 2):
        raise SknError('旧 .skl 版本不支持: %d' % ver)
    if nj == 0 or nj > RIG_BONE_LIMIT:
        raise SknError('.skl 关节数异常: %d' % nj)
    pos = 16
    JSIZE = 88  # name32 + parent4 + radius4 + 全局矩阵 48
    if pos + nj * JSIZE > len(d):
        raise SknError('旧 .skl 关节表越界(88B 布局)')
    joints = []
    for i in range(nj):
        o = pos + i * JSIZE
        name = d[o:o + 32].split(b'\0', 1)[0].decode('ascii', 'replace')
        par = struct.unpack_from('<i', d, o + 32)[0]
        radius = struct.unpack_from('<f', d, o + 36)[0]
        g = struct.unpack_from('<12f', d, o + 40)
        M = [list(g[0:4]), list(g[4:8]), list(g[8:12])]
        p, q, s = mat_to_trs(M)
        joints.append(dict(id=i, parent=par, name=name, hash=elf_hash(name),
                           radius=radius, pos=p, scl=s, rot=q,
                           ib_t=(0.0, 0.0, 0.0), ib_s=(1.0, 1.0, 1.0),
                           ib_q=(0.0, 0.0, 0.0, 1.0), legacy_global=M))
    pos += nj * JSIZE
    if ver == 2:
        nsb = struct.unpack_from('<I', d, pos)[0]
        pos += 4
        if pos + nsb * 2 > len(d):
            raise SknError('旧 .skl 影响表越界')
        influences = list(struct.unpack_from('<%dh' % nsb, d, pos))
    else:
        nsb = nj
        influences = list(range(nj))
    return dict(path=path, fmt='old-v%d(r3d2-sklt)' % ver, num_joints=nj, nsb=nsb,
                joints=joints, influences=influences,
                names=[j['name'] for j in joints])


# ------------------------------------------------ 关节树 / 绑定求值链 --

class Rig(object):
    """4.17 RigPose 求值链的 Python 复刻:
    局部姿态(绑定 or 动画) --父链级联--> 世界姿态 --x 逆绑定--> 蒙皮矩阵。"""

    def __init__(self, skl):
        self.skl = skl
        self.joints = skl['joints']
        self.n = len(self.joints)
        self.influences = skl.get('influences') or list(range(self.n))
        self.nsb = len(self.influences)
        self.parents = [j['parent'] for j in self.joints]
        self._check_tree()
        # ClearToBindPose: mPoseAry[i] = joints[i].mParentOffset (局部绑定)
        self.bind_local = [trs_to_mat(j['pos'], j['scl'], j['rot'])
                           for j in self.joints]
        self.world_bind = self._concat_world(self.bind_local)
        # 旧格式全局矩阵直接给出世界绑定
        if skl['fmt'].startswith('old-'):
            self.world_bind = [list(j['legacy_global']) for j in self.joints]
            self.bind_local = [self.world_bind[i] if self.parents[i] < 0 else
                               mat_mul(mat_inverse(self.world_bind[self.parents[i]]),
                                       self.world_bind[i])
                               for i in range(self.n)]
        self.inv_bind = self._inv_binds()
        self.inv_bind_err = self._verify_inv_bind()

    def _check_tree(self):
        bad = [(i, p) for i, p in enumerate(self.parents)
               if p != -1 and not (0 <= p < self.n)]
        if bad:
            raise SknError('骨架父索引越界: %s' % bad[:5])
        for i in range(self.n):
            seen, cur, hops = set(), i, 0
            while cur != -1 and hops <= self.n + 2:
                if cur in seen:
                    raise SknError('骨架父链成环(含关节 %d)' % i)
                seen.add(cur)
                cur = self.parents[cur]
                hops += 1

    def _concat_world(self, locals_):
        """ConvertToWorldPose: ConvertJointToWorldPose 父链级联(带已更新位图防重)。"""
        world = [None] * self.n

        def get(i):
            if world[i] is not None:
                return world[i]
            L = locals_[i]
            p = self.parents[i]
            world[i] = L if p < 0 else mat_mul(get(p), L)
            return world[i]

        for i in range(self.n):
            get(i)
        return world

    def _inv_binds(self):
        out = []
        for i in range(self.n):
            M = mat_inverse(self.world_bind[i])
            out.append(M if M is not None else
                       [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]])
        return out

    def _verify_inv_bind(self):
        """新格式自检: 计算的 inverse(世界绑定) 与文件存储的逆绑定比较。"""
        if self.skl['fmt'].startswith('old-'):
            return 0.0
        worst = 0.0
        for i, j in enumerate(self.joints):
            M = mat_mul(self.inv_bind[i], self.world_bind[i])
            worst = max(worst, max(abs(M[r][3]) for r in range(3)))
            for r in range(3):
                for c in range(3):
                    worst = max(worst, abs(M[r][c] - (1.0 if r == c else 0.0)))
        return worst

    def elf_hash_check(self):
        ok = sum(1 for j in self.joints
                 if elf_hash(j['name'].lower()) == j['hash']
                 or elf_hash(j['name']) == j['hash'])
        return ok, self.n

    def depths(self):
        out = [0] * self.n
        for i in range(self.n):
            cur, hops = i, 0
            while self.parents[cur] >= 0 and hops <= self.n:
                cur = self.parents[cur]
                hops += 1
            out[i] = hops
        return out

    def local_pose_bind(self):
        return list(self.bind_local)

    def local_pose_anm(self, anm, t):
        """动画采样局部姿态: 未被动画覆盖的关节用绑定姿态。返回 [3x4] 列表。"""
        sample = anm.sample_pose(t)  # {anm 关节 id: (pos,quat,scale)}
        locals_ = list(self.bind_local)
        for rig_idx, anm_idx in anm.rig_map.items():
            if anm_idx in sample:
                pos, quat, scl = sample[anm_idx]
                locals_[rig_idx] = trs_to_mat(pos, scl, quat)
        return locals_

    def skinning_from_locals(self, locals_):
        """ConvertToSkinningPose: 蒙皮矩阵 = 世界姿态 x 逆绑定(列向量约定,
        v' = W x invBind x v; 反编译 SIMD 展开即此序), 再经影响表映射到着色器骨
        (NSB)域 — 即引擎传给顶点着色器的矩阵调色板。"""
        world = self._concat_world(locals_)
        skin = [mat_mul(world[i], self.inv_bind[i]) for i in range(self.n)]
        infl = [None if j >= self.n else skin[j] for j in self.influences]
        return world, skin, infl

    def world_bind_positions(self):
        return [(self.world_bind[i][0][3], self.world_bind[i][1][3],
                 self.world_bind[i][2][3]) for i in range(self.n)]


# ============================================================ ANM 解析 ===

ANM_MAGIC_UNCOMP = b'r3d2anmd'
ANM_MAGIC_COMP = b'r3d2canm'
ANM_RES_TOKEN = TOKEN_ANIM           # AnimationResource::skFormatToken 0xBE0794D3
CH_ROT, CH_TRA, CH_SCA = 0, 1, 2


def parse_anm(path):
    """解析 .anm 动画(r3d2anmd v3/v4/v5 + r3d2canm 压缩), 归一化为 AnmAsset。
    · v3(4.20 同代): 轨道=32B 关节名 + flags, 帧=(四元数 16B + 位移 12B) 顺序存放;
      fps 以 u32 整数存储; 无缩放轨道(恒 1)。
    · v4: 帧内联关节哈希(u32+3xu16+pad=12B/帧/轨道), 全量四元数调色板(16B)。
    · v5: 哈希独立区, 调色板分离(向量 12B / 量化四元数 6B), 帧仅 3xu16。
    · canm: 128B 头 + 10B 压缩帧(time16 + joint/type 打包 + 3xu16 值),
      Catmull-Rom 样条求值(与 4.17 Evaluate 同式)。"""
    return parse_anm_data(open(path, 'rb').read(), path)


def parse_anm_data(d, path, off=0):
    """字节级解析入口: .anm 文件本体与 .blnd 内嵌动画块共用(off = 块起点)。"""
    if len(d) - off < 32:
        raise SknError('.anm 数据过小(off=0x%x, 剩 %d 字节)' % (off, len(d) - off))
    magic = d[off:off + 8]
    version = struct.unpack_from('<I', d, off + 8)[0]
    if magic == ANM_MAGIC_UNCOMP:
        if version == 3:
            return _parse_anm_v3(d, path, off)
        if version == 4:
            return _parse_anm_v45(d, path, 4, off)
        if version == 5:
            return _parse_anm_v45(d, path, 5, off)
        raise SknError('不支持的 .anm 非压缩版本 %d' % version)
    if magic == ANM_MAGIC_COMP:
        if version in (1, 2, 3):
            return _parse_anm_canm(d, path, version, off)
        raise SknError('不支持的 .anm 压缩版本 %d' % version)
    raise SknError('无法识别的 .anm (magic=%r @0x%x)' % (magic[:8], off))


def _anm_finalize(path, fmt, version, fps, duration, frame_count, tracks):
    """tracks: {关节哈希或名字: 关节数据}; 统一成 AnmAsset。"""
    return AnmAsset(path, fmt, version, fps, duration, frame_count, tracks)


class _TrackUniform(object):
    """v3/v4/v5: 均匀帧网格轨道。values[i] = (pos, quat, scale)。"""

    def __init__(self, frame_count, frame_dt, values, ident):
        self.frame_count = frame_count
        self.frame_dt = frame_dt
        self.values = values
        self.ident = ident

    def sample(self, t):
        n = self.frame_count
        if n <= 0:
            return None
        x = t / self.frame_dt if self.frame_dt > 0 else 0.0
        i = int(x)
        if i >= n - 1:
            return self.values[n - 1]
        u = x - i
        a, b = self.values[i], self.values[i + 1]
        pos = tuple(a[0][k] + (b[0][k] - a[0][k]) * u for k in range(3))
        quat = qslerp(a[1], b[1], u)
        scl = tuple(a[2][k] + (b[2][k] - a[2][k]) * u for k in range(3))
        return (pos, quat, scl)

    def key_times(self):
        return [i * self.frame_dt for i in range(self.frame_count)]


class _TrackKeys(object):
    """canm: 每关节三通道关键帧序列, Catmull-Rom 求值(0x622eb0 同式)。"""

    def __init__(self, duration):
        self.duration = duration
        self.rot = []   # [(time16, quat)]
        self.tra = []   # [(time16, pos)]
        self.sca = []   # [(time16, scale)]

    def sample(self, t):
        if not self.rot and not self.tra and not self.sca:
            return None
        time16 = int((min(t, self.duration) / self.duration if self.duration > 0
                      else 0.0) * 65535.0)

        def pick(keys, slerp=False, default=None):
            if not keys:
                return default
            # 四控制点: P1 = 最后一个 <= time16 的关键帧, P2 = 下一个;
            # 端点越界时钳位复制(与引擎热帧窗口等价的随机访问式实现)。
            ks = keys
            n = len(ks)
            j = 0
            while j < n and ks[j][0] <= time16:
                j += 1
            j = max(1, min(j, n - 1))
            p0 = ks[max(j - 2, 0)]
            p1 = ks[j - 1]
            p2 = ks[j]
            p3 = ks[min(j + 1, n - 1)]
            t0, t1 = p1[0], p2[0]
            span = (t1 - t0) if (t1 - t0) > 0 else 1
            u = (time16 - t0) / span
            u = max(0.0, min(1.0, u))
            if slerp:
                return catmull_rom_quat(u, p0[1], p1[1], p2[1], p3[1])
            return catmull_rom_vec(u, p0[1], p1[1], p2[1], p3[1])

        pos = pick(self.tra, default=(0.0, 0.0, 0.0))
        quat = pick(self.rot, slerp=True, default=(0.0, 0.0, 0.0, 1.0))
        scl = pick(self.sca, default=(1.0, 1.0, 1.0))
        return (pos, quat, scl)

    def key_times(self):
        return [k[0] * self.duration / 65535.0 if self.duration > 0 else 0.0
                for k in (self.rot or self.tra or self.sca)]


class AnmAsset(object):
    """归一化动画资产: 帧率/时长/轨道; rig_map 在 GUI 层由骨架哈希匹配填充。"""

    def __init__(self, path, fmt, version, fps, duration, frame_count, tracks):
        self.path = path
        self.fmt = fmt
        self.version = version
        self.fps = fps
        self.duration = duration
        self.frame_count = frame_count
        self.tracks = tracks          # {ident(哈希或名字): track}
        self.rig_map = {}             # {rig 关节 idx: anm 关节 idx}
        self.joint_idents = list(tracks.keys())

    def sample_pose(self, t):
        """返回 {anm 关节 idx: (pos, quat, scale)}。"""
        out = {}
        for i, ident in enumerate(self.joint_idents):
            s = self.tracks[ident].sample(t)
            if s is not None:
                out[i] = s
        return out

    def map_to_rig(self, rig):
        """GenerateBindData 语义: anm 关节 -> rig 关节(名字 / ELF / FNV-1a)。"""
        self.rig_map = {}
        by_hash = {}
        for i, j in enumerate(rig.joints):
            by_hash[j['hash']] = i
            by_hash[fnv1a_hash(j['name'])] = i
            by_hash[j['name']] = i
        for anm_idx, ident in enumerate(self.joint_idents):
            ri = by_hash.get(ident)
            if ri is None and isinstance(ident, str):
                ri = by_hash.get(elf_hash(ident))
            if ri is None and isinstance(ident, int):
                for j in rig.joints:
                    if j['hash'] == ident or fnv1a_hash(j['name']) == ident:
                        ri = rig.joints.index(j)
                        break
            if ri is not None:
                self.rig_map[ri] = anm_idx
        return self.rig_map


def _parse_anm_v3(d, path, off=0):
    skeleton_id, track_count, frame_count, fps_u = struct.unpack_from(
        '<4I', d, off + 12)
    fps = float(fps_u)
    if fps <= 0:
        fps = 30.0
    duration = frame_count / fps
    pos = off + 28
    tracks = {}
    for ti in range(track_count):
        name = d[pos:pos + 32].split(b'\0', 1)[0].decode('ascii', 'replace')
        pos += 32
        flags = struct.unpack_from('<I', d, pos)[0]
        pos += 4
        values = []
        for fi in range(frame_count):
            quat = qnorm(struct.unpack_from('<4f', d, pos))
            v = struct.unpack_from('<3f', d, pos + 16)
            pos += 28
            values.append((v, quat, (1.0, 1.0, 1.0)))
        tracks[name] = _TrackUniform(frame_count, 1.0 / fps, values, name)
    return _anm_finalize(path, 'r3d2anmd v3(4.20 同代)', 3, fps, duration,
                          frame_count, tracks)


def _parse_anm_v45(d, path, version, off=0):
    """官方 AnimationResource 布局(4.17 反编译 Resource.cpp 构造器 +
    PoolSerializer::ConvertFromOldAnimData/IsValidAnimationFile 交叉验证;
    4.20 实物 spell1_circle.pie_c_13_22.anm 逐字节锚定):

    BinaryHeader 12B{"r3d2","anmd",ver} → AnimationResource 0x40:
      +0x00 mResourceSize      +0x04 formatToken(0 或 skFormatToken)
      +0x08 mVersion           +0x0c mFlags
      +0x10 mNumChannels        +0x14 mNumTicks
      +0x18 mTickDuration(f32)  +0x1c mJointNameHashesOffset
      +0x20 mAssetNameOffset    +0x24 mTimeOffset
      +0x28 mVectorPaletteOffset(=0x40) +0x2c mQuatPaletteOffset
      +0x30 mTickDataOffset     +0x34 mExtBuffer[3]
    所有偏移相对资源起点(= 文件 12 / 嵌入块 off+12)。
    区序(v5): 向量调色板(12B) → 量化四元数(6B) → 关节哈希(u32×N)
    → TickData(6B/tick/channel: pos,scale,quat 索引)。
    v4(inV2 格式, 无哈希区): 四元数调色板 = Quaternion4f(16B),
    TickDataV2 12B(内联 mTargetHash + 3 索引)。"""
    (resource_size, format_token, _ver, _flags, track_count, frame_count) = \
        struct.unpack_from('<6I', d, off + 12)
    frame_duration = struct.unpack_from('<f', d, off + 36)[0]
    (jhash_off, _asset_off, _time_off, vec_off, quat_off,
     tickdata_off) = struct.unpack_from('<6i', d, off + 40)
    BIAS = off + 12
    if frame_duration <= 0 or frame_duration > 30.0:
        raise SknError('.anm v%d 帧时长非法(%g; 官方校验 ∈(0,30])'
                      % (version, frame_duration))
    if track_count > 0x800 or frame_count > 0x40000:
        raise SknError('.anm v%d 通道/tick 超界(ch=%d ticks=%d; 官方上限'
                      ' 0x800/0x40000)' % (version, track_count, frame_count))
    # 官方 IsValidAnimationFile: formatToken 必须为 0 或 skFormatToken
    if format_token not in (0, ANM_RES_TOKEN):
        raise SknError('.anm v%d formatToken 0x%08x 非官方值'
                      % (version, format_token))
    data_end = off + 12 + resource_size
    if data_end > len(d) or data_end <= off + 12:
        data_end = len(d)          # 嵌入块尾随数据 → 钳到块边界
    if data_end <= off + 12:
        raise SknError('.anm v%d 资源尺寸非法(0x%x)' % (version, resource_size))
    def _ok_rel(v):
        return 0 <= v < data_end - off - 12
    fps = 1.0 / frame_duration
    duration = frame_count * frame_duration
    # 段顺序(v5): 向量调色板 → 四元数调色板 → 关节哈希 → tick 数据
    vec_count = (quat_off - vec_off) // 12 if _ok_rel(vec_off) and \
        quat_off > vec_off else 0
    quat_size = 6 if version == 5 else 16
    quat_end = jhash_off if (version == 5 and _ok_rel(jhash_off) and
                             jhash_off > quat_off) else tickdata_off
    quat_count = (quat_end - quat_off) // quat_size if _ok_rel(quat_off) \
        and quat_end > quat_off else 0
    vec_pal = []
    if _ok_rel(vec_off):
        for i in range(max(0, vec_count)):
            vo = vec_off + BIAS + i * 12
            if vo + 12 > len(d):
                raise SknError('.anm v%d 向量调色板越界(%d/%d)'
                              % (version, i, vec_count))
            vec_pal.append(struct.unpack_from('<3f', d, vo))
    quat_pal = []
    if _ok_rel(quat_off):
        for i in range(max(0, quat_count)):
            qo = quat_off + BIAS + i * quat_size
            if qo + quat_size > len(d):
                raise SknError('.anm v%d 四元数调色板越界(%d/%d)'
                              % (version, i, quat_count))
            if version == 5:
                q = decode_quantized_quat(
                    *struct.unpack_from('<3H', d, qo))
            else:
                q = qnorm(struct.unpack_from('<4f', d, qo))
            quat_pal.append(qnorm(q))
    # 哈希表(仅 v5; 官方 GenerateBindData 语义: 哈希表缺失 = v2 内联格式)
    jhashes = []
    if version == 5 and _ok_rel(jhash_off) and tickdata_off > jhash_off:
        n = (tickdata_off - jhash_off) // 4
        if jhash_off + n * 4 <= data_end - off - 12:
            for i in range(max(0, n)):
                jhashes.append(struct.unpack_from(
                    '<I', d, jhash_off + BIAS + i * 4)[0])
        else:
            jhashes = []
    # tick 数据(TickData v5 / TickDataV2 v4) — 官方 mTickDataOffset
    tracks = {}
    if not _ok_rel(tickdata_off):
        raise SknError('.anm v%d tick 数据偏移非法(0x%x)'
                      % (version, tickdata_off))
    if version == 5:
        rows = []
        for fi in range(frame_count):
            row = []
            for ti in range(track_count):
                fo = tickdata_off + BIAS + (fi * track_count + ti) * 6
                if fo + 6 > len(d):
                    raise SknError('.anm v%d tick 数据越界(tick %d ch %d)'
                                  % (version, fi, ti))
                tid, sid, rid = struct.unpack_from('<3H', d, fo)
                row.append((tid, sid, rid))
            rows.append(row)
        for ti in range(track_count):
            ident = jhashes[ti] if ti < len(jhashes) else ('track%d' % ti)
            values = []
            for fi in range(frame_count):
                tid, sid, rid = rows[fi][ti]
                values.append((vec_pal[tid] if tid < len(vec_pal) else (0.0, 0.0, 0.0),
                               quat_pal[rid] if rid < len(quat_pal) else (0.0, 0.0, 0.0, 1.0),
                               vec_pal[sid] if sid < len(vec_pal) else (1.0, 1.0, 1.0)))
            tracks[ident] = _TrackUniform(frame_count, frame_duration, values, ident)
    else:
        # v4: TickDataV2 12B(内联 mTargetHash + 3 索引) — 官方 inV2Format
        per_hash_frames = {}
        stride = track_count * 12
        for fi in range(frame_count):
            base = tickdata_off + BIAS + fi * stride
            if base + stride > len(d):
                raise SknError('.anm v4 tick 数据越界(tick %d)' % fi)
            for ti in range(track_count):
                h = struct.unpack_from('<I', d, base + ti * 12)[0]
                tid, sid, rid = struct.unpack_from('<3H', d, base + ti * 12 + 4)
                fr = per_hash_frames.setdefault(h, [None] * frame_count)
                fr[fi] = (tid, sid, rid)
        for h, rows in per_hash_frames.items():
            values = []
            for fi in range(frame_count):
                fr = rows[fi] or (0, 0, 0)
                tid, sid, rid = fr
                values.append((vec_pal[tid] if tid < len(vec_pal) else (0.0, 0.0, 0.0),
                               quat_pal[rid] if rid < len(quat_pal) else (0.0, 0.0, 0.0, 1.0),
                               vec_pal[sid] if sid < len(vec_pal) else (1.0, 1.0, 1.0)))
            tracks[h] = _TrackUniform(frame_count, frame_duration, values, h)
    return _anm_finalize(path, 'r3d2anmd v%d' % version, version, fps, duration,
                          frame_count, tracks)


def _parse_anm_canm(d, path, version, off=0):
    (resource_size, format_token, flags, joint_count, frame_count,
     jump_cache_count) = struct.unpack_from('<6I', d, off + 12)
    duration, fps = struct.unpack_from('<2f', d, off + 0x24)
    tra_min = struct.unpack_from('<3f', d, off + 0x44)
    tra_max = struct.unpack_from('<3f', d, off + 0x50)
    sca_min = struct.unpack_from('<3f', d, off + 0x5c)
    sca_max = struct.unpack_from('<3f', d, off + 0x68)
    frames_off, jc_off, jh_off = struct.unpack_from('<3i', d, off + 0x74)
    BIAS = off + 12
    if duration <= 0:
        raise SknError('.anm 压缩版时长非法(%f)' % duration)

    def dec_vec(v, mn, mx):
        return tuple(v[k] / 65535.0 * (mx[k] - mn[k]) + mn[k] for k in range(3))

    jhashes = []
    if jh_off > 0:
        for i in range(joint_count):
            jhashes.append(struct.unpack_from('<I', d, jh_off + BIAS + i * 4)[0])
    tracks = {}
    for ji in range(joint_count):
        ident = jhashes[ji] if ji < len(jhashes) else ji
        tracks[ident] = _TrackKeys(duration)
    for fi in range(frame_count):
        o = frames_off + BIAS + fi * 10
        t16, jt = struct.unpack_from('<2H', d, o)
        v0, v1, v2 = struct.unpack_from('<3H', d, o + 4)
        ji = jt & 0x3FFF
        ctype = jt >> 14
        if ji >= joint_count:
            continue
        tr = tracks[jhashes[ji] if ji < len(jhashes) else ji]
        if ctype == CH_ROT:
            tr.rot.append((t16, decode_quantized_quat(v0, v1, v2)))
        elif ctype == CH_TRA:
            tr.tra.append((t16, dec_vec((v0, v1, v2), tra_min, tra_max)))
        elif ctype == CH_SCA:
            tr.sca.append((t16, dec_vec((v0, v1, v2), sca_min, sca_max)))
    for tr in tracks.values():
        tr.rot.sort(key=lambda k: k[0])
        tr.tra.sort(key=lambda k: k[0])
        tr.sca.sort(key=lambda k: k[0])
    return _anm_finalize(path, 'r3d2canm v%d(压缩)' % version, version,
                         fps or 30.0, duration, frame_count, tracks)


# ==================================================== INI / INIBIN / BLND ===
# 角色配置与其编译产物、动画事件容器:
#   · .ini/.cfg 文本与 .inibin(0xBEEF)双入口 — 皮肤表(SimpleSkin/Skeleton/
#     Texture*)、资源清单、贴图;
#   · .blnd — 4.20 同代客户端的「骨架+动画+事件」编译容器(6.20 起被官方
#     淘汰, 4.20 客户端仍在读): 内嵌块全量解析 + 事件表启发式定位;
#   · 键名哈希自校准: inibin 的键只有哈希, 本工具用「节+键组合候选 × 哈希
#     函数候选」按命中数动态甄别, 未识别键保留原始哈希(值不受影响)。
#
# inibin 二进制布局依据: 公开解析器 Pupix/lol-inibin-parser(MIT)逐字段对照 —
#   头部: magic u16(0xBEEF) + version + 字符串表长度 u16 + 类型位图 u16;
#   数据体按位序: 每个类型块 = u16 键数 + 键哈希(u32)xN + 值(N x 宽度);
#   字符串块(0x1000)最后: 键 + 偏移 u16 xN + 字符串表(偏移相对表首)。
# 本工具同时兼容「version 1 字节 / 2 字节」两种头部读法, 以字符串偏移与
# 块边界校验自动甄别。

INI_ASSET_EXTS = ('skn', 'skl', 'anm', 'blnd', 'dds', 'troy', 'part',
                  'inibin', 'cfg', 'ini', 'wav', 'bnk')


def _ini_get(sections, section, key):
    sec = sections.get(section) or {}
    hit = sec.get(key.lower())
    return hit[1] if hit else None


def _texture_keys(sec):
    """按 Texture, Texture2..Texture9 顺序取非空贴图引用。"""
    out = []
    for cand in ['texture'] + ['texture%d' % i for i in range(2, 10)]:
        v = sec.get(cand)
        if v and v[1].strip():
            out.append(v[1].strip())
    return out


def parse_ini_file(path):
    """解析老客户端角色 .ini/.cfg 文本: [节] 键=值; 键名大小写不敏感;
    重复键容忍(记录并保留首个 — 与客户端 WARN 行为一致)。"""
    raw = open(path, 'rb').read()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('latin-1')
    sections = {}
    order = []
    dup = []
    cur = 'Global'
    sections[cur] = {}
    order.append(cur)
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s[0] in ';#':
            continue
        if s[0] == '[' and s.endswith(']'):
            cur = s[1:-1].strip()
            if cur not in sections:
                sections[cur] = {}
                order.append(cur)
            continue
        if '=' in s:
            k, _, v = s.partition('=')
            k, v = k.strip(), v.strip()
            if not k:
                continue
            sec = sections.setdefault(cur, {})
            if cur not in order:
                order.append(cur)
            kl = k.lower()
            if kl in sec:
                dup.append('[%s] %s' % (cur, k))
            else:
                sec[kl] = (k, v)
    return IniAsset(path, sections, order, dup)


class IniAsset(object):
    """ini/cfg 文本角色配置(官方明文形态; 4.20 客户端与 inibin 等价读取)。"""

    def __init__(self, path, sections, order, dup):
        self.path = path
        self.sections = sections
        self.order = order
        self.dup = dup
        self.fmt = 'ini 文本'
        self.calib = None
        self.names = {}

    def items(self):
        for sec in self.order:
            for kl in self.sections[sec]:
                k, v = self.sections[sec][kl]
                yield dict(section=sec, key=k, type='str', value=v)

    def skin_rows(self):
        rows = []
        for sec in self.order:
            low = sec.lower()
            if low not in ('skinnedmesh', 'skeleton') and not low.startswith('skin'):
                continue
            sd = self.sections[sec]
            if not sd:
                continue
            rows.append(dict(section=sec,
                             skn=_ini_get(self.sections, sec, 'SimpleSkin'),
                             skl=_ini_get(self.sections, sec, 'Skeleton'),
                             textures=_texture_keys(sd)))
        return rows

    def asset_paths(self):
        out = []
        for sec in self.order:
            for kl in self.sections[sec]:
                k, v = self.sections[sec][kl]
                v = (v or '').strip()
                ext = v.rsplit('.', 1)[-1].lower() if '.' in v else ''
                if ext in INI_ASSET_EXTS:
                    out.append((ext, v, '[%s] %s' % (sec, k)))
        return out

    def report_lines(self):
        return ['配置: %s (%s)' % (os.path.basename(self.path), self.fmt),
                '区段 %d · 键值 %d · 重复键 %d' % (
                    len(self.order),
                    sum(len(self.sections[s]) for s in self.order),
                    len(self.dup)),
                '皮肤区段: %s' % ', '.join(r['section'] for r in self.skin_rows())]


# ------------------------------------------------------------- inibin -----

# 官方 inibin v2 格式 — 4.20 Windows exe TryToLoadBinaryFileV2(0x8b0380) 反汇编
# + 4.17 Mac 反编译 ConfigFile.cpp/ConfigFileIOFunctions.cpp 双源对照,
# 并以 4.20 客户端真实文件 Skin05.inibin 逐字节验证:
#   [0] u8  version = 2         (读取器仅读取 3 字节并 cmp byte[0], 2)
#   [1] u16 charEntries         (字符串池字节数, 池固定在文件末尾)
#   [3] u16 avaliableSets       (类型节位掩码, 读取于文件偏移 3)
#   [5] 各存在节按官方 ReadList 调用序排列: {u16 count; u32 hash[]; 值[]}
#   末尾 charEntries 字节字符串池; String 节的值为池内 u16 偏移。
# 键哈希 = Riot::HashFunctions::HashStringSDBM(section, '*', name)
#   (SDBMHash.cpp 0x5ab6e0: 节部分 h = 65599*(h+c); +'*'(42); 键部分 c+65599*hv)

INIBIN_MAGIC = 0xA7009202          # = version(02)+charEntries+mask低字节的巧合组合;
                                      # 官方读取器仅校验 byte[0] == 2(0x8b0438)
INIBIN_TYPES = (                    # 官方 TYPE_INDEX 枚举序 = 文件节序
    (0x0001, 'i32', 4), (0x0002, 'f32', 4), (0x0004, 's8/10', 1),
    (0x0008, 'i16', 2), (0x0010, 'i8', 1), (0x0020, 'bool', 0),
    (0x0040, '3xs8/10', 3), (0x0080, '3xf32', 12), (0x0100, '2xu8/10', 2),
    (0x0200, '2xf32', 8), (0x0400, '4xu8/10', 4), (0x0800, '4xf32', 16),
    (0x1000, 'str', 0), (0x2000, 'i64', 8),
)
_INIBIN_KNOWN_MASK = 0x3FFF


def sdbm_key_hash(section, name):
    """官方 HashStringSDBM(section, '*', name) — 大小写不敏感。"""
    h = 0
    for ch in section.encode('ascii', 'replace'):
        c = ch + 32 if 65 <= ch <= 90 else ch
        h = (65599 * (h + c)) & 0xFFFFFFFF
    hv = (h + 42) & 0xFFFFFFFF
    for ch in name.encode('ascii', 'replace'):
        c = ch + 32 if 65 <= ch <= 90 else ch
        hv = (c + 65599 * hv) & 0xFFFFFFFF
    return hv


# 官方键名字典 — 全部取自 4.17 反编译真实调用点:
#   CharacterData::LoadSkinInfo / LoadIdleParticles / LoadAnimationPoolData
#   SkinnedMesh::LoadSkinINI / LoadParticleINI
_MESHSKIN_KEYS = [
    'ChampionSkinName', 'ChampionSkinName2', 'SkinScale', 'AttributeFlags',
    'IconAvatar', 'IconCircle', 'IconSquare', 'Animations', 'SimpleSkin',
    'Skeleton', 'Texture', 'Texture1', 'Texture2', 'Texture3', 'Texture4',
    'Texture5', 'Texture6', 'Texture7', 'Texture8', 'Texture9', 'TextureLow',
    'EmissiveTexture', 'GlossTexture', 'Material', 'MaterialOverridePriority',
    'XOffset', 'YOffset', 'WorldOffset', 'Scale', 'UnitBarKey', 'VOOverride',
    'SkipVOOverride', 'ExtraCharacterPreloads', 'ParticleOverride_DeathParticle',
    'ParticleOverride_ChampionKillDeathParticle', 'selfIllumination',
    'selfIlluminationColor', 'recallTexture', 'RecallTexture', 'OverrideBoundingBox',
    'ChampionKillDeathParticle', 'DeathParticle', 'AmbientParticle',
    'SelectionHeight', 'SelectionRadius', 'HealthBarHeight', 'ParallelParticles',
    'NumParticleOverride', 'Particle', 'skinName', 'SkinNumber', 'Name',
    'Model', 'Path', 'Mesh', 'Animation', 'BlendMultiplier', 'Part', 'Sound',
    'BaseHP', 'BaseMP', 'AttackDamage', 'AttackRange', 'Armor',
    'MoveSpeed', 'HealthRegen', 'ManaRegen', 'AmbientRadius', 'AmbientColor',
    'PerceptionBubbleRadius', 'PathfindingCollisionRadius',
    'PathfindingCollisionHeights', ' GameplayPathfindingCollisionRadius',
    # v6 补全: 官方 SkinnedMesh::LoadSkinINI 读取但旧字典漏掉的键 —
    # SubmeshesToHide 家族(SkinnedMesh.cpp @0x10db2fc) 与
    # MaterialOverride%d{Priority, RenderingMode}(逐槽全键) — 缺名时
    # inibin 的 SDBM 哈希无法还原 → cfg_get 取不到 → 用户实测
    # 「SubmeshesToHide 没有生效」的直接根源。
    'SubmeshesToHide', 'SubmeshShadowsToHide', 'SubmeshMouseOversToHide',
    'BrushAlphaOverride', 'CastShadows', 'UsesSkinVO', 'Fresnel',
    'FresnelRed', 'FresnelGreen', 'FresnelBlue', 'ReflectionMap',
    'ReflectionOpacityDirect', 'ReflectionOpacityGlancing',
    'ReflectionFresnel', 'ReflectionFresnelRed',
    'ReflectionFresnelGreen', 'ReflectionFresnelBlue',
    'BoundingCylinderRadius', 'BoundingCylinderHeight',
    'BoundingSphereRadius', 'TextureLow', 'TransColorTexture',
    'TransitionTexture', 'EmissiveTexture',
]
# v6.1: MaterialOverride 槽位键注册 0..63(官方客户端固定读 4 槽; 用户
# 要求放开上限 → inibin SDBM 键名字典覆盖任意实存槽位, 超出范围的槽
# 在 ini 文本形态下经键扫描自动发现, 不受字典范围限制)。
for _i in range(64):
    _MESHSKIN_KEYS += ['MaterialOverride%dTexture' % _i,
                       'MaterialOverride%dSubmesh' % _i,
                       'MaterialOverride%dGlossTexture' % _i,
                       'MaterialOverride%dPriority' % _i,
                       'MaterialOverride%dRenderingMode' % _i]
for _i in range(16):
    _MESHSKIN_KEYS += ['ParticleOverride%d' % _i]
_INIBIN_NAME_SECTIONS = (['MeshSkin', 'Global', 'Data', 'Info', 'Items',
                           'Attachment', 'Spells'] +
                          ['Skin%d' % _i for _i in range(21)])
_INIBIN_NAME_MAP = {}
for _sec in _INIBIN_NAME_SECTIONS:
    for _k in _MESHSKIN_KEYS:
        _h = sdbm_key_hash(_sec, _k)
        _INIBIN_NAME_MAP.setdefault(_h, '%s.%s' % (_sec, _k))

def inibin_name_of(h):
    return _INIBIN_NAME_MAP.get(h)

def _safe_cstr(d, off, maxlen=512):
    if off is None or off < 0 or off >= len(d):
        return None
    end = d.find(b'\0', off, off + maxlen)
    if end < 0:
        end = min(off + maxlen, len(d))
    return d[off:end].decode('ascii', 'replace')


def _printable_ratio(s):
    if not s:
        return 0.0
    n = sum(1 for c in s if 32 <= ord(c) < 127)
    return n / float(len(s))


def _inibin_read_values(d, pos, tname, n):
    """读取 n 个官方类型值; 返回 (值列表, 新 pos)。越界抛 SknError。"""
    out = []
    for _i in range(n):
        if tname == 'i32':
            out.append(struct.unpack_from('<i', d, pos)[0]); pos += 4
        elif tname == 'i64':
            out.append(struct.unpack_from('<q', d, pos)[0]); pos += 8
        elif tname == 'i16':
            out.append(struct.unpack_from('<h', d, pos)[0]); pos += 2
        elif tname == 'i8':
            out.append(struct.unpack_from('<b', d, pos)[0]); pos += 1
        elif tname == 'f32':
            out.append(struct.unpack_from('<f', d, pos)[0]); pos += 4
        elif tname == 's8/10':
            out.append(struct.unpack_from('<b', d, pos)[0] / 10.0); pos += 1
        elif tname == 'bool':
            out.append(bool(struct.unpack_from('<B', d, pos)[0] & 1)); pos += 1
        elif tname == '3xs8/10':
            out.append(tuple(c / 10.0 for c in
                             struct.unpack_from('<3b', d, pos))); pos += 3
        elif tname == '3xf32':
            out.append(struct.unpack_from('<3f', d, pos)); pos += 12
        elif tname == '2xu8/10':
            out.append(tuple(c / 10.0 for c in
                             struct.unpack_from('<2B', d, pos))); pos += 2
        elif tname == '2xf32':
            out.append(struct.unpack_from('<2f', d, pos)); pos += 8
        elif tname == '4xu8/10':
            out.append(tuple(c / 10.0 for c in
                             struct.unpack_from('<4B', d, pos))); pos += 4
        elif tname == '4xf32':
            out.append(struct.unpack_from('<4f', d, pos)); pos += 16
        else:
            raise SknError('未知 inibin 值类型 %s' % tname)
        if pos > len(d):
            raise SknError('inibin 值区越界(%s @0x%x)' % (tname, pos))
    return out, pos


def _inibin_parse_body(d):
    """官方 inibin v2 数据体解析 → (entries, strings, meta)。

    布局已由 4.20 Windows exe 反汇编(读取器 0x8b0380: 读 3 字节头 +
    cmp byte[0],2 → 读 2 字节 avaliableSets → 14 个 ReadList 调用 →
    按 word[ebp-3] 即 charEntries 读字符串池)与真实文件交叉验证。
    头部无独立魔数 — byte[0] 即版本, 其后 u16 字符串池长度、u16 类型位图。"""
    if len(d) < 5:
        raise SknError('inibin 文件过小')
    version = d[0]
    char_entries, mask = struct.unpack_from('<HH', d, 1)
    if version != 2:
        raise SknError('inibin 版本 %d(官方 4.20 读取器仅接受 v2, 其余报'
                      '"Old version needs to be recompiled")' % version)
    if mask & ~_INIBIN_KNOWN_MASK:
        raise SknError('类型位图含未知位 0x%04x' % mask)
    if char_entries > len(d):
        raise SknError('字符串池声明(%dB)超过文件' % char_entries)
    strtab = len(d) - char_entries
    pos = 5
    entries = []
    strings = []
    for bit, tname, _size in INIBIN_TYPES:
        if tname == 'str':
            continue                      # 字符串节最后处理(池在文件末尾)
        if not (mask & bit):
            continue
        if pos + 2 > len(d):
            raise SknError('inibin 键数越界(位 0x%04x)' % bit)
        (n,) = struct.unpack_from('<H', d, pos)
        pos += 2
        if pos + n * 4 > len(d):
            raise SknError('inibin 键表越界(位 0x%04x, n=%d)' % (bit, n))
        keys = struct.unpack_from('<%dI' % n, d, pos)
        pos += n * 4
        if tname == 'bool':               # 官方 ReadListBitSet: 位打包
            nbytes = (n >> 3) + (1 if n & 7 else 0)
            if pos + nbytes > len(d):
                raise SknError('inibin 位包越界(n=%d)' % n)
            bits = d[pos:pos + nbytes]
            pos += nbytes
            vals = [bool(bits[i >> 3] & (1 << (i & 7))) for i in range(n)]
        else:
            vals, pos = _inibin_read_values(d, pos, tname, n)
        for h, v in zip(keys, vals):
            entries.append(dict(hash=h, type=tname, value=v))
    if mask & 0x1000:
        if pos + 2 > len(d):
            raise SknError('inibin 字符串键数越界')
        (n,) = struct.unpack_from('<H', d, pos)
        pos += 2
        if pos + n * 4 + n * 2 > len(d):
            raise SknError('inibin 字符串键/偏移表越界(n=%d)' % n)
        keys = struct.unpack_from('<%dI' % n, d, pos)
        pos += n * 4
        offs = struct.unpack_from('<%dH' % n, d, pos)
        pos += n * 2
        if pos != strtab:
            raise SknError('字符串池起点不一致(节尾 0x%x, 池 0x%x)'
                           % (pos, strtab))
        for h, o in zip(keys, offs):
            s = _safe_cstr(d, strtab + o)
            if s is None or _printable_ratio(s) < 0.5:
                raise SknError('字符串偏移越界或不可解码(0x%x + 0x%x)'
                               % (strtab, o))
            strings.append((h, s))
        pos = strtab
    elif pos != strtab:
        raise SknError('节区与字符串池边界不一致(节尾 0x%x, 池 0x%x)'
                       % (pos, strtab))
    meta = dict(version=version, strtab_len=char_entries, mask=mask, end=pos,
                hdr_variant='官方v2(5字节头)', char_entries=char_entries)
    return entries, strings, meta


_CFG_SECTIONS = ['MeshSkin'] + ['Skin%d' % i for i in range(0, 21)]
_CFG_KEYS = ['SimpleSkin', 'Skeleton', 'Texture', 'Animations']


def parse_inibin(path):
    """解析官方 .inibin v2 → InibinAsset(哈希键名经 SDBM 字典还原)。"""
    d = open(path, 'rb').read()
    entries, strings, meta = _inibin_parse_body(d)
    notes = ['官方 inibin v2: 5 字节头(version/charEntries/avaliableSets 0x%04x)' % meta['mask']]
    asset = InibinAsset(path, entries, strings, meta, notes)
    asset.calibrate()
    return asset


class InibinAsset(object):
    """官方 inibin v2 角色配置: SDBM 哈希键 + 类型化值 + 字符串池。

    键名还原依据官方 HashStringSDBM(section,'*',name); 与 4.20 客户端
    ReadCFG_* 同语义提供 get()/get_int()/get_float()/get_bool()。"""

    def __init__(self, path, entries, strings, meta, notes):
        self.path = path
        self.entries = entries
        self.strings = strings
        self.meta = meta
        self.notes = notes
        self.fmt = 'inibin 官方v2'
        self.calib = None
        self.names = dict(_INIBIN_NAME_MAP)
        self._by_hash = {}
        for h, s in self.strings:
            self._by_hash.setdefault(h, s)
        for e in self.entries:
            self._by_hash.setdefault(e['hash'], e['value'])

    def name_of(self, h):
        nm = self.names.get(h)
        return nm if nm else '0x%08x' % h

    def calibrate(self):
        """官方哈希已知度统计(展示用; 键名还原不再依赖猜测)。"""
        have = set(self._by_hash)
        hits = sum(1 for h in have if h in _INIBIN_NAME_MAP)
        self.calib = {'fn': 'SDBM(官方)', 'form': 'Section*Key', 'hits': hits,
                      'total': len(have)}
        return self.calib

    # ---- 官方 ReadCFG_* 同语义取值 ----
    def get(self, section, key, default=None):
        """ReadCFG_S 同义: 字符串值, 数值可回退字符串(GetValueFromBinary)。"""
        h = sdbm_key_hash(section, key)
        v = self._by_hash.get(h)
        if v is None:
            return default
        if isinstance(v, str):
            return v
        if isinstance(v, bool):
            return '1' if v else '0'
        if isinstance(v, tuple):
            return ' '.join('%g' % x for x in v)
        return ('%g' % v) if isinstance(v, float) else str(v)

    def get_int(self, section, key, default=0):
        v = self.get(section, key)
        if v is None:
            return default
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return default

    def get_float(self, section, key, default=0.0):
        v = self.get(section, key)
        if v is None:
            return default
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    def get_bool(self, section, key, default=False):
        v = self.get(section, key)
        if v is None:
            return default
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in ('1', 'true')

    def items(self):
        for h, s in self.strings:
            nm = self.names.get(h) or '0x%08x' % h
            sec, _, key = nm.partition('.')
            yield dict(section=sec, key=key, type='str', value=s)
        for e in self.entries:
            nm = self.names.get(e['hash']) or '0x%08x' % e['hash']
            sec, _, key = nm.partition('.')
            yield dict(section=sec, key=key, type=e['type'], value=e['value'])

    def skin_rows(self):
        """官方 [MeshSkin] 字段行(SkinnedMesh::LoadSkinINI + CharacterData::LoadSkinInfo)。"""
        row = dict(section='MeshSkin', skn=self.get('MeshSkin', 'SimpleSkin'),
                   skl=self.get('MeshSkin', 'Skeleton'),
                   blnd=self.get('MeshSkin', 'Animations'),
                   textures=_texture_keys_cfg(self))
        return [row] if (row['skn'] or row['skl'] or row['textures']) else []

    def asset_paths(self):
        out = []
        for h, s in self.strings:
            v = (s or '').strip()
            ext = v.rsplit('.', 1)[-1].lower() if '.' in v else ''
            if ext in INI_ASSET_EXTS:
                out.append((ext, v, self.names.get(h) or '0x%08x' % h))
        return out

    def report_lines(self):
        c = self.calib or {}
        lines = ['配置: %s (%s)' % (os.path.basename(self.path), self.fmt),
                 '键 %d (数值 %d · 字符串 %d)' % (
                     len(self.entries) + len(self.strings),
                     len(self.entries), len(self.strings))]
        if c.get('hits') is not None:
            lines.append('键名还原: 官方 SDBM(section,*,name) · 命中 %d/%d'
                         % (c['hits'], c['total']))
        lines += ['· ' + n for n in self.notes]
        return lines


def parse_config(path):
    """按官方规则自动分派: 扩展名 .inibin → 二进制 v2; 否则 .ini/.cfg 文本。
    扩展名缺失时以 byte[0]==2 且不可文本化各半识别(官方判定即版本字节)。"""
    ext = os.path.splitext(path)[1].lower()
    with open(path, 'rb') as fp:
        head = fp.read(8)
    if ext == '.inibin':
        return parse_inibin(path)
    if ext in ('.ini', '.cfg'):
        return parse_ini_file(path)
    if head and head[0] == 2 and not all(
            9 <= b < 127 for b in head[:4]):
        return parse_inibin(path)
    return parse_ini_file(path)


def cfg_report(asset):
    """角色配置统一报表(CLI --inibin / GUI 概览共用)。"""
    lines = asset.report_lines()
    rows = asset.skin_rows()
    if rows:
        lines.append('')
        lines.append('皮肤表(官方字段):')
        for r in rows:
            lines.append('  [%s] skn=%s skl=%s 贴图=%s'
                          % (r['section'], r['skn'] or '-', r['skl'] or '-',
                             ','.join(r['textures']) or '-'))
    aps = asset.asset_paths()
    if aps:
        lines.append('')
        lines.append('资源引用 %d 条:' % len(aps))
        for ext, v, where in aps[:40]:
            lines.append('  .%-5s %-44s %s' % (ext, v[:44], where))
        if len(aps) > 40:
            lines.append('  … 其余 %d 条' % (len(aps) - 40))
    return lines


# --------------------------------------------------------- 路径 / 贴图 ----

def _existing_ci(paths):
    for p in paths:
        if not p:
            continue
        if os.path.exists(p):
            return os.path.abspath(p)
        d, b = os.path.split(p)
        try:
            if d and os.path.isdir(d):
                for fn in os.listdir(d):
                    if fn.lower() == b.lower():
                        return os.path.abspath(os.path.join(d, fn))
        except OSError:
            pass
    return None


def resolve_asset_path(cfg_dir, data_root, ref):
    """角色配置引用解析: 依次试 配置目录 / DATA 根 / DATA 根拼 DATA 前缀 /
    各基目录下取文件名(大小写不敏感)。"""
    ref = (ref or '').replace('\\', '/').strip()
    if not ref:
        return None
    bases = [cfg_dir, data_root]
    if data_root:
        bases.append(os.path.join(data_root, 'DATA'))
        bases.append(os.path.join(data_root, 'DATA', 'Characters'))
    cands = []
    for b in bases:
        if not b:
            continue
        cands.append(os.path.join(b, ref))
        cands.append(os.path.join(b, os.path.basename(ref)))
    return _existing_ci(cands)


def _match_child_ci(d, name):
    """目录 d 下大小写不敏感地查找名字为 name 的文件/子目录。"""
    try:
        low = name.lower()
        for fn in os.listdir(d):
            if fn.lower() == low:
                return os.path.join(d, fn)
    except OSError:
        pass
    return None


def resolve_level_ci(base, rel):
    """base + rel 逐级(大小写不敏感)解析; 任一级缺失/非文件 → None。"""
    if not base or not rel:
        return None
    cur = base
    for comp in rel.split('/'):
        if not comp:
            continue
        cur = _match_child_ci(cur, comp)
        if cur is None:
            return None
    return cur if os.path.isfile(cur) else None


def resolve_blnd_anim_ref(cfg_dir, data_root, ref, extra_bases=()):
    """blnd 外置 .anm 引用解析(v5.2, 用户实测官方语义对齐)。

    官方语义: 资源路径以 Game/Data(DATA 根)为根逐级挂接, blnd 保留完整
    路径(如 characters/leesin/skins/skin05/animations/x.anm)。本地视图:
    ini 所在目录通常即 .../skin05/, 故忽略存储路径中的上层目录, 逐级丢弃
    前缀直到在 ini 目录下命中(如 animations/x.anm)。

    解析次序:
      1. 完整路径直挂 DATA 根 / ini 目录(官方根语义);
      2. 从 ini 所在目录逐级丢弃上层目录前缀直到命中(主修复);
      3. DATA 根下同样逐级丢弃(用户把 DATA 根指到 Game/Data 时适用);
      4. 兜底: 各基目录下仅按文件名(大小写不敏感)。
    全程逐级大小写不敏感(游戏目录大小写与引用不一致是常态)。"""
    ref = (ref or '').replace('\\', '/').strip()
    if not ref:
        return None
    comps = [c for c in ref.split('/') if c]
    if not comps:
        return None
    bases = [b for b in ([cfg_dir] + list(extra_bases) + [data_root]) if b]
    # 1) 完整路径直挂(官方 DATA 根语义)
    for b in bases:
        p = resolve_level_ci(b, ref)
        if p:
            return p
    # 2/3) 逐级丢弃上层目录前缀(保留最长可命中后缀)
    for k in range(1, len(comps)):
        rel = '/'.join(comps[k:])
        for b in bases:
            p = resolve_level_ci(b, rel)
            if p:
                return p
    # 4) 兜底: 仅文件名(旧 resolve_asset_path 行为)
    last = comps[-1]
    for b in bases:
        p = _match_child_ci(b, last)
        if p and os.path.isfile(p):
            return p
    return None


def load_dds_info(path):
    """读取 .dds 贴图(Pillow 原生支持 DXT1/3/5 与未压缩位图)。
    返回 {image, thumb, avg, size} 或 (None, 原因)。"""
    if not PIL_OK:
        return None, '未安装 Pillow(pip install pillow) — 无法预览贴图'
    try:
        img = _PILImage.open(path)
        img.load()
        rgb = img.convert('RGB')
    except Exception as e:
        return None, '%s: %s' % (type(e).__name__, e)
    thumb = rgb.copy()
    thumb.thumbnail((96, 96))
    px = list(thumb.getdata())
    if px:
        n = float(len(px))
        avg = tuple(int(sum(c[i] for c in px) / n + 0.5) for i in range(3))
    else:
        avg = (128, 128, 128)
    return dict(image=rgb, thumb=thumb, avg=avg, size=img.size), None


def decode_dds_texture(path):
    """解码 .dds → numpy (H, W, 3) uint8 RGB 与 (H, W) uint8 alpha。
    Pillow 原生解码 DXT1/3/5 与未压缩 DDS(4.20 客户端 r3dRenderer::
    LoadTexture 的格式域)。失败 → (None, 原因)。"""
    if not PIL_OK:
        return None, '未安装 Pillow(pip install pillow) — 无法解码贴图'
    if not NP_OK:
        return None, '未安装 numpy(pip install numpy) — 贴图渲染需 numpy'
    try:
        img = _PILImage.open(path)
        img.load()
        if img.mode in ('RGBA', 'LA', 'PA'):
            rgba = img.convert('RGBA')
            arr = _np.asarray(rgba, dtype=_np.uint8)
            rgb = _np.ascontiguousarray(arr[:, :, :3])
            alpha = _np.ascontiguousarray(arr[:, :, 3])
        else:
            rgb = _np.asarray(img.convert('RGB'), dtype=_np.uint8)
            alpha = _np.full(rgb.shape[:2], 255, dtype=_np.uint8)
        return dict(rgb=rgb, alpha=alpha, size=(img.width, img.height)), None
    except Exception as e:
        return None, '%s: %s' % (type(e).__name__, e)


# ------------------------------------------- 官方材质键(SkinnedMesh::LoadSkinINI) --
# 4.17 反编译 Skinning/SkinnedMesh.cpp LoadSkinINI 逐键对齐:
#   Texture            → mDiffuseTextureHigh(缺省回退 "checker.dds")
#   TextureLow         → mDiffuseTextureLow
#   EmissiveTexture    → mEmissiveTexture(缺省 DefaultEmissive.dds)
#   GlossTexture       → mGlossMap(缺省 = Texture)
#   MaterialOverride%dTexture/Submesh/GlossTexture → 4 槽逐子网格覆盖
#   (GetSubmeshMaterialOverride: 子网格名 std_stricmp 相等即命中)。

_MATERIAL_OVERRIDE_KEYS = [
    ('MaterialOverride%dTexture', 'MaterialOverride%dSubmesh',
     'MaterialOverride%dGlossTexture')]


def build_material_bindings(cfg, section='MeshSkin'):
    """官方材质装配(SkinnedMesh::LoadSkinINI + SkinnedMeshMaterial::
    SetupSubmesh + GetSubmeshMaterialOverride 三段语义):

    · 默认 Texture → mDiffuseTextureHigh(未覆盖子网格的 stage0 贴图);
    · MaterialOverride%d{Texture, Submesh, GlossTexture, Priority,
      RenderingMode} → 材质覆盖表;
      官方客户端固定读 4 槽(LoadMaterialOverrides i=0..3) — v6.1 按用户
      要求放开上限: 扫描配置中实际存在的全部槽位(0..任意; inibin 键名
      字典注册 0..63, ini 文本形态无上限);
    · 覆盖命中规则(官方 GetSubmeshMaterialOverride + multimap<int, MO*,
      greater<int>>): 按优先级降序遍历, 首个「空子网格名(匹配全部)或
      std_stricmp 相等」命中; flags&1(有 Texture)才替换 stage0 贴图。

    返回 (bindings, default_ref, overrides):
      bindings = {子网格名lower: 贴图引用} + ''=默认(旧形态兼容, 名字直配
      仅在无更高优先级无名槽覆盖时生效);
      overrides = 逐槽结构化记录(优先级降序), 供调用方按网格子网格名单
      官方逐个求值(网格在盘后才知名字)。"""
    default = cfg_get(cfg, section, 'Texture', '') or ''
    default = str(default).strip()
    # —— 槽位发现: 官方键族 MaterialOverride%d{Texture,Submesh,
    # GlossTexture,Priority,RenderingMode} — 不预设 4 槽上限, 扫描实存槽号。
    slots = set()
    if cfg is not None:
        sec_l = (section or '').lower()
        for it in cfg.items():
            if (it['section'] or '').lower() != sec_l:
                continue
            m = re.match(r'^MaterialOverride(\d+)(Texture|Submesh|'
                         r'GlossTexture|Priority|RenderingMode)$',
                         str(it['key']), re.I)
            if m:
                slots.add(int(m.group(1)))
    overrides = []
    for i in sorted(slots):
        tex = str(cfg_get(cfg, section,
                         'MaterialOverride%dTexture' % i, '') or '').strip()
        sub = str(cfg_get(cfg, section,
                         'MaterialOverride%dSubmesh' % i, '') or '').strip()
        gloss = str(cfg_get(cfg, section,
                            'MaterialOverride%dGlossTexture' % i,
                            '') or '').strip()
        try:
            pri = int(float(cfg_get(cfg, section,
                                   'MaterialOverride%dPriority' % i, 0) or 0))
        except (TypeError, ValueError):
            pri = 0
        try:
            mode = int(float(cfg_get(cfg, section,
                                     'MaterialOverride%dRenderingMode' % i,
                                     0) or 0))
        except (TypeError, ValueError):
            mode = 0
        if tex or gloss or mode:
            overrides.append(dict(slot=i, tex=tex, sub=sub, gloss=gloss,
                                  pri=pri, mode=mode))
    # 官方 multimap<int, MaterialOverride*, greater<int>>: 优先级降序,
    # 等优先级保持插入序(槽号升序)
    overrides.sort(key=lambda o: -o['pri'])
    # 旧形态 bindings(名字直配): 仅记录「未被更高优先级无名槽抢走」的槽
    blanket = None                 # 最高优先级的无名覆盖(匹全部子网格)
    for o in overrides:
        if o['tex'] and not o['sub']:
            blanket = o
            break
    bindings = {}
    if default:
        bindings[''] = default
    for o in overrides:
        if o['tex'] and o['sub'] and (blanket is None or
                                      o['pri'] > blanket['pri']):
            bindings[o['sub'].lower()] = o['tex']
    if blanket is not None and blanket['tex']:
        # 无名高优先级覆盖接管默认(官方: 对任意子网格先于默认命中)
        bindings[''] = blanket['tex']
    return bindings, default, overrides


def resolve_material_overrides(sub_names, overrides, default_ref):
    """官方 GetSubmeshMaterialOverride 逐子网格求值。

    对每个子网格名: 按优先级降序遍历覆盖槽, 首个「空名或 stricmp 相等」
    且有 Texture 的槽命中; 无命中 → 默认 Texture。返回
    {子网格名lower: 贴图引用}(不含默认 '')。"""
    out = {}
    for nm in sub_names:
        low = str(nm).lower()
        hit = None
        for o in overrides or []:
            if not o.get('tex'):
                continue
            sub = o.get('sub') or ''
            if not sub or sub.lower() == low:
                hit = o['tex']
                break
        out[low] = hit if hit else (default_ref or '')
    return out


# ------------------------------------------------- 官方角色包(CharacterData) --
# 4.20 exe 取证锚点:
#   CharacterData::Load        @0x568e20  载入 <角色>.inibin/.ini → 配置对象;
#   LoadSkinDescription       @0x56e0d0  "Skin%02d.ini"(skin>0) / "Base.ini"
#                                        兜底, 存在性经配置对象 +0x28 槽检查;
#   皮肤字段读取              @0x963cd0  SimpleSkin(+".skn") / Skeleton /
#                                        MaxNumBlendWeights(1..4) /
#                                        OverrideBoundingBox;
#   LoadAnimationPoolData      @0x56d5c0  "Animations" 键 → .blnd → 0x897a60;
#   材质键族                   @0x10db0f8 Material / EmissiveTexture /
#                                        TextureLow / GlossTexture /
#                                        MaterialOverride%d{Submesh,Material…};
#   子网格显隐键               @0x10db2fc SubmeshesToHide / SubmeshShadowsToHide
#                                        / SubmeshMouseOversToHide。

def _texture_keys_cfg(cfg, section='MeshSkin'):
    """按官方键序取贴图引用(Texture / Texture1..9 / Emissive / Gloss...)。
    section = 当前活动皮肤节(Skin%02d / MeshSkin)。"""
    out = []
    for key in ['Texture'] + ['Texture%d' % i for i in range(1, 10)] + \
            ['EmissiveTexture', 'GlossTexture', 'TextureLow', 'recallTexture']:
        v = cfg_get(cfg, section, key)
        if v and str(v).strip():
            out.append(str(v).strip())
    return out


_OFFICIAL_EXT_FIX = {               # 键名以小写比较(kl)
    'simpleskin': '.skn',          # 0x963f44: 值后强制拼 .skn(若未带后缀)
    'skeleton': '',                # 0x964032: 缺省拼 "_skeleton"
    'animations': '.blnd',          # 0x56d71e: "Animations" → blnd 加载器
}
_OFFICIAL_EXT_KIND = {
    'simpleskin': 'skn', 'skeleton': 'skl', 'animations': 'blnd',
}

_TEX_KEY_SET = {
    'material', 'emissivetexture', 'texturelow', 'glosstexture',
    'reflectionmap', 'transcolortexture', 'transitiontexture',
}


def cfg_get(cfg, section, key, default=None):
    """ini/inibin 统一读键(大小写不敏感; 0x8b0630 GetString 语义)。"""
    if cfg is None:
        return default
    sec_l = (section or '').lower()
    key_l = (key or '').lower()
    for it in cfg.items():
        if (it['section'] or '').lower() == sec_l and \
                str(it['key']).lower() == key_l:
            v = it['value']
            if isinstance(v, str):
                v = v.strip()
                return v if v else default
            return v
    return default


def cfg_sections(cfg):
    secs = []
    for it in cfg.items():
        s = it['section']
        if s and s not in secs:
            secs.append(s)
    return secs


def cfg_section_items(cfg, section):
    out = {}
    sec_l = (section or '').lower()
    for it in cfg.items():
        if (it['section'] or '').lower() == sec_l:
            k = str(it['key'])
            if k not in out:
                out[k] = it['value']
    return out


def list_skin_packages(cfg):
    """列出配置中的可选皮肤 — 官方节名 MeshSkin / MeshSkin%d
    (4.17 反编译 CharacterData::LoadSkinInfo: meshSkin = "MeshSkin", 
    skinID != 0 且非重构数据时拼 "MeshSkin" + itoa(skinID))。
    兼容旧 "Skin%02d"/Base/SkinnedMesh 写法。"""
    pkgs = []
    seen = set()
    for sec in cfg_sections(cfg):
        low = sec.lower()
        sid = None
        if low == 'meshskin':
            sid = 0
        elif low.startswith('meshskin') and low[8:].isdigit():
            sid = int(low[8:])
        elif low == 'skinnedmesh':
            sid = 0
        elif low.startswith('skin') and low[4:].isdigit():
            sid = int(low[4:])
        elif low == 'base':
            sid = 0
        if sid is None:
            continue
        if sid in seen:
            continue
        seen.add(sid)
        pkgs.append(build_skin_package(cfg, sid, sec))
    return [p for p in pkgs if p is not None]


def build_skin_package(cfg, skin_id, section=None):
    """按官方链装配一个皮肤的全部资产引用并做磁盘解析。

    返回 SkinPackage(section=Skin%02d / Base, 模型/骨架/动画池/贴图引用,
    每项含 resolved 本地路径或 None)。"""
    if cfg is None:
        return None
    sid = int(skin_id)
    # 官方节名双形态: MeshSkin / MeshSkin%d(4.17 CharacterData::LoadSkinInfo)
    # 兼容旧 "Skin%02d"/Base/SkinnedMesh 写法
    section = 'MeshSkin' if sid == 0 else 'MeshSkin%d' % sid
    items = cfg_section_items(cfg, section)
    if not items and sid > 0:
        for alt in ('MeshSkin%d' % sid, 'Skin%02d' % sid, 'Skin%d' % sid):
            items = cfg_section_items(cfg, alt)
            if items:
                section = alt
                break
    if not items:
        for alt in ('MeshSkin', 'SkinnedMesh', 'Skin0', 'Skin00', 'Base'):
            items = cfg_section_items(cfg, alt)
            if items:
                section = alt
                break
    if not items:
        return None
    cfg_dir = os.path.dirname(os.path.abspath(cfg.path))
    data_root = ''                      # 由调用方注入(GUI 的 DATA 根)
    pkg = dict(skin_id=sid, section=section, cfg_dir=cfg_dir,
               data_root='', raw={}, resolved={})

    def _resolve(ref, ext_fix):
        ref = (ref or '').replace('\\', '/').strip()
        if not ref:
            return None
        # 官方后缀补全: SimpleSkin → .skn / Animations → .blnd
        ext = ref.rsplit('.', 1)[-1].lower() if '.' in ref else ''
        if ext_fix and ext != ext_fix.lstrip('.') and '.' not in ref:
            ref2 = ref + ext_fix
        elif ext_fix and ext != ext_fix.lstrip('.') and \
                ref.lower().endswith(ext_fix.lstrip('.') + '_skeleton'):
            ref2 = ref                       # Skeleton 缺省 "_skeleton" 形态
        else:
            ref2 = ref
        bases = [cfg_dir, data_root]
        if data_root:
            bases.append(os.path.join(data_root, 'DATA'))
            bases.append(os.path.join(data_root, 'DATA', 'Characters'))
            bases.append(os.path.dirname(cfg_dir))
        cands = []
        for b in bases:
            if not b:
                continue
            cands.append(os.path.join(b, ref2))
            cands.append(os.path.join(b, ref))
            cands.append(os.path.join(b, os.path.basename(ref2)))
            cands.append(os.path.join(b, os.path.basename(ref)))
        # 官方回退: "data/%s"(0x897de4)
        cands.append(os.path.join(cfg_dir, 'data', ref2))
        cands.append(os.path.join(cfg_dir, 'data', ref))
        return _existing_ci(cands)

    for key, val in items.items():
        kl = key.lower()
        v = val.strip() if isinstance(val, str) else val
        if kl in _OFFICIAL_EXT_FIX and v:
            pkg['raw'][key] = v
            pkg['resolved'][_OFFICIAL_EXT_KIND[kl]] = _resolve(
                v, _OFFICIAL_EXT_FIX[kl])
        elif kl in _TEX_KEY_SET and v:
            pkg['raw'][key] = v
            r = _resolve(v, '')
            if r:
                pkg['resolved'].setdefault('textures', []).append(
                    (key, v, r))
        elif kl.startswith('materialoverride') and v:
            pkg['raw'][key] = v
            r = _resolve(v, '')
            if r:
                pkg['resolved'].setdefault('textures', []).append(
                    (key, v, r))
        elif kl in ('submeshestohide', 'submeshshadowstohide',
                    'submeshmouseoverstohide') and v:
            pkg['raw'][key] = v          # 官方子网格显隐键(清单, 不解析路径)
    return pkg


def skin_package_report(pkg):
    """SkinPackage 一行式摘要(资产关联页/状态栏用)。"""
    r = pkg['resolved']
    got = []
    if r.get('skn'):
        got.append('模型√')
    if r.get('skl'):
        got.append('骨架√')
    if r.get('blnd'):
        got.append('动画池√')
    if r.get('textures'):
        got.append('贴图%d' % len(r['textures']))
    return '%s: %s' % (pkg['section'], ' · '.join(got) if got else
                       '引用未解析(检查文件位置/DATA 根)')


# ------------------------------------------------------------- blnd -------
# 官方 blnd 布局(v5 全链定案 — 与 4.20 客户端逐字节对齐)
# 双源: 4.17 Mac 反编译 PoolBuilder.cpp / PoolSerializer.cpp /
#   ResourceBuilders.cpp / Anim_EventResource.cpp / Pool.cpp;
#   4.20 Windows exe 反汇编(0x897a60 头三重比较 / 0x897ca0 池加载器:
#   [edi+0x4c]=引用数, [edi+0x50]=名字表, 名字 = 记录字段地址+存值 —
#   0x894d90 Riot::Sync 字段相对定基)。
# 实物锚定: LeeSinSkin05.blnd(4772B) 全部字段逐字节验证(含 2 张事件表、
#   23 blend、23 clip、23 外置 .anm 引用、骨架路径哈希)。
#
# 文件 = BinaryHeader 12 字节 {u32 "r3d2", u32 "blnd", u32 version=1}
#      + PoolData 定长头 0x60 @ 文件 0x0C(池基址; PoolSerializer::Load
#        直接把 fread 起点当 PoolData — sizeof(BinaryHeader)=12):
#   +0x00 mResourceSize(文件内 0)   +0x04 mFormatToken = 0x5A40C9DD
#   +0x08 mVersion                  +0x0C mNumClasses(clip 数)
#   +0x10 mNumBlends                +0x14 mNumTransitionData
#   +0x18 mNumTracks                +0x1C mNumAnimData
#   +0x20 mNumMaskData              +0x24 mNumEventData
#   +0x28 mUseCascadeBlend          +0x2C mCascadeBlendValue(f32)
#   +0x30 mBlendDataAry    +0x34 mTransitionData   +0x38 mBlendTrackAry
#   +0x3C mClassAry        +0x40 mMaskDataAry      +0x44 mEventDataAry
#   +0x48 mAnimDataAry(均为 OffsetPtr: 目标 = 字段地址 + 存值, 可为负)
#   +0x4C mAnimNameCount            +0x50 mAnimNames(OffsetPtr)
#   +0x54 mSkeleton.pathHash(FNV-1a)+0x58 mSkeleton.path(OffsetPtr)
# 数组区(按 BuildPoolData 写出序, 池基+0x60 起):
#   BlendData[numBlends] 16B {u32 mFromAnimId, u32 mToAnimId,
#                             u32 mBlendFlags, f32 mBlendTime}
#   [TransitionClipData[numTrans] + 尾随 transition-to 数组]
#   TrackResource[numTracks] 0x30 {u32 size=0x30, f32 mBlendWeight,
#       u32 mIndex, u32 mBlendMode, char mName[32]}
#   类指针数组 u32[numClasses]   ← 条目相对数组基(Riot::RelativeArray)
#   掩码指针数组 u32[numMask]    ← 条目相对数组基
#   事件指针数组 u32[numEvent]   ← 条目相对数组基(→ EventResource)
#   动画指针数组 u32[numAnim]    ← 文件内为 0(外置 .anm, Load 后 Sync 补指针)
#   clip 资源链(每 clip: ClipResource 头+名+AtomicClip+[syncgroup][updater]
#   [+EventResource 紧随其后]) … 动画名记录+字符串池 … 骨架路径字符串。
# ClipResource: {u32 mResourceSize, u32 mFlags, u32 mUniqueID,
#   u32 mNameOffset, u32 mClipDataOffset}(名字/数据偏移相对 clip 起点起算)
#   + 名字串(4 对齐) + ClipData:
# AtomicClip {u32 mClipTypeID=1, u32 mStartTick, u32 mEndTick,
#   f32 mTickDuration, u32 mAnimData(动画槽索引 — 文件内为索引, Sync 后
#   才是指针), u32 mEventData(OffsetPtr 字段相对), u32 mMaskData,
#   u32 mTrackData(OffsetPtr 字段相对), u32 mUpdaterDataOffset, …}
# EventResource(0x34 头, 全部偏移相对资源起点):
#   {u32 mResourceSize(整个资源含表与字符串), u32 mFormatToken(本时代为 0),
#    u32 mFlags, {u16 pad, u16 mNumEvents}, u32 mUniqueID,
#    u32 mEventOffsetArrayOffset, u32 mEventDataOffset,
#    u32 mEventNameHashOffset, u32 mEventFrameOffset, u32 mNameOffset,
#    u32 mExtBuffer[0]=0xFFFFFFFF, u32 mExtBuffer[1]=0xFFFFFFFF}
#   + EventDataOffset_t[n] {u32 mDataOffset}(资源相对)
#   + BaseEventData[n](类型相关; 字符串偏移相对各事件数据自身起点)
#   + EventNameHash_t[n] {u32 mDataID, u32 mNameHash}(按哈希排序)
#   + EventFrame_t[n] {u32 mDataID, f32 mFrame}(按帧排序 — GetEvent 二分前提)
#   + 名字串(= 所属 clip 名)
# BaseEventData 公共头: {u32 pad, u32 mEventTypeId, u32 mFlags,
#   f32 mFrame, u32 mNameOffset, …类型相关…}:
#   1 Sound      : +soundOff                                  (步长 0x18)
#   2 Particle   : +effectOff, boneOff, targetOff, f32 mEndFrame (0x24)
#   3 SubmeshVis : +f32 mEndFrame, u32 mShowSubmeshHash, u32 mHideSubmeshHash (0x20)
#   4 Fade       : +f32 mTimeToFade, f32 mEndFrame, f32 mTargetAlpha (0x1c→0x20)
#   5 JointSnap  : +f32 mEndFrame, u32 mJointToOverrideIdx, u32 mJointToSnapToIdx
#   6 EnableLookAt: +f32 mEndFrame, u32 mEnable, u32 mLockCurrentValues

BLND_CLIP_MAGICS = (b'r3d2anmd', b'r3d2canm')
RIG_TOKEN_NEW = TOKEN_RIG
_EV_TOKEN_INVALID = 0xFFFFFFFF
_EV_TYPE_NAMES = {0: 'Invalid', 1: 'Sound', 2: 'Particle',
                  3: 'SubmeshVisibility', 4: 'Fade', 5: 'JointSnap',
                  6: 'EnableLookAt'}   # ResourceBuilders switch 官方 typeid 序
BLND_ENGINE_TYPE = 0x32643372          # "r3d2" (PoolSerializer::Load 三重比较)
BLND_BLOCK_TYPE = 0x646E6C62           # "blnd"
BLND_VERSION = 1
BLND_POOL_TOKEN = 0x5A40C9DD
BLND_POOL_BASE = 0x0C                   # PoolData 基 = BinaryHeader(12B) 之后
BLND_POOL_HDR = 0x60                    # sizeof(PoolData)


def _blnd_offptr(field_addr, stored):
    """官方 OffsetPtr: 目标 = 字段地址 + 存值(可为负); 无效值 → None。
    语义源: 4.17 反编译 Riot::Sync 0x894d90 / PoolSerializer::OffsetToPtr。"""
    if stored == _EV_TOKEN_INVALID or stored == 0:
        return None
    sv = stored - 0x100000000 if stored >= 0x80000000 else stored
    return field_addr + sv


def _res_off(base, stored):
    """资源相对偏移(EventResource/ClipResource 内部表): 目标 = 资源起点+存值。"""
    if stored == _EV_TOKEN_INVALID:
        return None
    return base + stored


class BlndEventTable(object):
    """EventResource 事件表(官方指针链定位, 无启发式)。

    events[i]: frame(引擎帧值), data_id, name, type_id, name_hash(官方
    HashStringCaseInsensitiveFNV 复算值) + 就地补丁槽位(frame_abs_off =
    帧表 f32 / frame2_abs_off = BaseEventData.mFrame / name_abs_off /
    name_max_len) + 类型相关字段(sound/particle/bone/target/end_frame/
    show_hash/hide_hash/time_to_fade/target_alpha/…)。"""

    def __init__(self):
        self.off = 0
        self.num = 0
        self.frame_off = 0
        self.data_off = 0
        self.hash_off = None
        self.name_off = None
        self.stride = 0x24
        self.offset_mode = '官方指针链(事件指针数组 → EventResource)'
        self.frame_table_sorted = True
        self.num_field_off = 0x0e
        self.events = []
        self.score = 1.5
        self.confidence = '高'
        self.resource_name = ''

    def describe(self):
        order = '按帧升序' if self.frame_table_sorted else 'dataID 序(现代布局)'
        return ('事件表 @0x%06x · %d 事件 · %s · 帧表@+0x%02x(%s)'
                % (self.off, self.num, self.offset_mode,
                   self.frame_off - self.off if self.frame_off else 0, order))


def _safe_str_at(d, a, maxlen=128):
    if a is None or not (0 <= a < len(d)):
        return '', 0
    s = _safe_cstr(d, a, maxlen)
    if not s or _printable_ratio(s) < 0.75:
        return '', 0
    end = d.find(b'\0', a, a + maxlen)
    ln = (end if end >= 0 else min(a + maxlen, len(d))) - a
    return s, max(ln, 1)


def _decode_base_event(d, ev_a, data_id, frame_slot):
    """BaseEventData(类型相关布局) → 事件 dict。字符串偏移相对 ev_a 起点起算
    (EventResourceBuilder::_Build 的 CopyStringIntoMem 目标)。"""
    if ev_a is None or ev_a + 0x18 > len(d):
        return None
    pad, type_id, flags = struct.unpack_from('<3I', d, ev_a)
    frame = struct.unpack_from('<f', d, ev_a + 0x0c)[0]
    name_rel = struct.unpack_from('<I', d, ev_a + 0x10)[0]
    ev = dict(frame=frame, data_id=data_id, name='', type_id=type_id,
              name_hash=0, flags=flags,
              frame_abs_off=frame_slot, frame2_abs_off=ev_a + 0x0c,
              name_abs_off=None, name_max_len=0)
    na = ev_a + name_rel if name_rel not in (0, _EV_TOKEN_INVALID) else None
    ev['name'], ev['name_max_len'] = _safe_str_at(d, na, 96)
    if na is not None and ev['name']:
        ev['name_abs_off'] = na
    if ev['name']:
        ev['name_hash'] = fnv1_ci_hash(ev['name'])
    # —— 类型相关字段(偏移同样相对 ev_a) ——
    def _off(i):
        v = struct.unpack_from('<I', d, ev_a + 0x14 + i * 4)[0] \
            if ev_a + 0x18 + i * 4 <= len(d) - 4 else _EV_TOKEN_INVALID
        return v
    if type_id == 1:                       # SoundEventData
        so = _off(0)
        ev['sound'] = _safe_str_at(d, ev_a + so, 160)[0] if so not in (0, _EV_TOKEN_INVALID) else ''
    elif type_id == 2:                     # ParticleEventData
        eo, bo, to = _off(0), _off(1), _off(2)
        ev['particle'] = _safe_str_at(d, ev_a + eo, 160)[0] \
            if eo not in (0, _EV_TOKEN_INVALID) else ''
        ev['bone'] = _safe_str_at(d, ev_a + bo, 64)[0] \
            if bo not in (0, _EV_TOKEN_INVALID) else ''
        ev['target'] = _safe_str_at(d, ev_a + to, 64)[0] \
            if to not in (0, _EV_TOKEN_INVALID) else ''
        if ev_a + 0x24 <= len(d) - 4:
            ev['end_frame'] = struct.unpack_from('<f', d, ev_a + 0x20)[0]
    elif type_id == 3:                     # SubmeshVisibilityEventData
        if ev_a + 0x20 <= len(d) - 4:
            ev['end_frame'] = struct.unpack_from('<f', d, ev_a + 0x14)[0]
            ev['show_hash'] = struct.unpack_from('<I', d, ev_a + 0x18)[0]
            ev['hide_hash'] = struct.unpack_from('<I', d, ev_a + 0x1c)[0]
    elif type_id == 4:                     # FadeEventData
        if ev_a + 0x20 <= len(d) - 4:
            ev['time_to_fade'] = struct.unpack_from('<f', d, ev_a + 0x14)[0]
            ev['end_frame'] = struct.unpack_from('<f', d, ev_a + 0x18)[0]
            ev['target_alpha'] = struct.unpack_from('<f', d, ev_a + 0x1c)[0]
    elif type_id == 5:                     # JointSnapEventData
        if ev_a + 0x20 <= len(d) - 4:
            ev['end_frame'] = struct.unpack_from('<f', d, ev_a + 0x14)[0]
            ev['joint_to_override'] = struct.unpack_from('<I', d, ev_a + 0x18)[0]
            ev['joint_to_snap_to'] = struct.unpack_from('<I', d, ev_a + 0x1c)[0]
    elif type_id == 6:                     # EnableLookAtEventData
        if ev_a + 0x20 <= len(d) - 4:
            ev['end_frame'] = struct.unpack_from('<f', d, ev_a + 0x14)[0]
            ev['enable_look_at'] = struct.unpack_from('<I', d, ev_a + 0x18)[0]
            ev['lock_current_values'] = struct.unpack_from('<I', d, ev_a + 0x1c)[0]
    return ev


def _parse_event_resource(d, res, owner_clip=None, tick_duration=0.0):
    """按官方 EventResource 布局解码一张事件表(全偏移资源相对; 帧表/
    哈希表/偏移数组按 _Build 序), 并做哈希交叉校验。失败 → None。"""
    n = len(d)
    if not (0 <= res < n) or res + 0x34 > n:
        return None
    (size, tok, flags, packed, uid, arr_off, data_off, hash_off, frame_off,
     name_off, ext0, ext1, hdr_size) = struct.unpack_from('<13I', d, res)
    num = (packed >> 16) & 0xFFFF
    if not (1 <= num <= 4096):
        return None
    arr_a = _res_off(res, arr_off)
    data_a = _res_off(res, data_off)
    hash_a = _res_off(res, hash_off)
    frame_a = _res_off(res, frame_off)
    name_a = _res_off(res, name_off)
    if arr_a is None or data_a is None or frame_a is None:
        return None
    if arr_a + num * 4 > n or frame_a + num * 8 > n or data_a >= n:
        return None
    t = BlndEventTable()
    t.off = res
    t.num = num
    t.data_off = data_a
    t.frame_off = frame_a
    t.hash_off = hash_a
    t.name_off = name_a
    if name_a is not None:
        t.resource_name = _safe_str_at(d, name_a, 64)[0]
    # —— 帧表 EventFrame_t{u32 mDataID, f32 mFrame} ——
    # 4.17/4.20 官方 _Build 产物按帧升序(AddEventsToEventResource 的 std::sort);
    # 2017+ 现代 blnd(如 Kayn Skin20)按 dataID 序追加, 不再重排 — 实测两代文件
    # 并存。引擎派发链(EventController::Update → BaseEvent::GetStartFrame →
    # BaseEventData.mFrame)全程不读帧表, 帧表仅服务 GetEvent(frame,tol) 二分
    # 查找(反编译无任何调用方); 排序缺失只影响该二分, 不影响播放派发 —
    # 故按帧升序降级为「告警不拒收」, 与引擎 LoadData 行为一致。
    frames = []
    for i in range(num):
        did, f = struct.unpack_from('<If', d, frame_a + i * 8)
        if not (-1e4 <= f <= 1e6) or not (0 <= did < num):
            return None
        frames.append((did, f))
    frame_table_sorted = num <= 1 or all(
        frames[i][1] <= frames[i + 1][1] + 1e-4 for i in range(num - 1))
    slot_of = {}
    for i, (did, f) in enumerate(frames):
        slot_of[did] = frame_a + i * 8 + 4
    # —— 偏移数组 → BaseEventData ——
    evs = []
    for i in range(num):
        mo = struct.unpack_from('<I', d, arr_a + i * 4)[0]
        ev_a = _res_off(res, mo)
        ev = _decode_base_event(d, ev_a, i, slot_of.get(i))
        if ev is None:
            return None
        if abs(ev['frame'] - dict((did, f) for did, f in frames)[i]) > 1e-3:
            return None                  # 帧表 ↔ BaseEventData 双副本互证
        evs.append(ev)
    # —— 哈希表 EventNameHash_t{u32 mDataID, u32 mNameHash} 交叉校验 ——
    if hash_a is not None and hash_a + num * 8 <= n:
        for i in range(num):
            did, h = struct.unpack_from('<2I', d, hash_a + i * 8)
            if 0 <= did < num:
                evs[did]['hash_abs_off'] = hash_a + i * 8 + 4
                if evs[did].get('name') and h != fnv1_ci_hash(evs[did]['name']):
                    return None      # 官方 GetEvent(name) 语义
    evs.sort(key=lambda e: e['frame'])
    t.events = evs
    t.frame_table_sorted = frame_table_sorted
    if not frame_table_sorted:
        # 现代 blnd 布局: 帧表保持 dataID 序(追加不重排)。不影响引擎派发
        # (派发只读 BaseEventData.mFrame), 仅 GetEvent(frame,tol) 二分失真。
        t.offset_mode += ' · 帧表 dataID 序(现代布局, 派发不受影响)'
    if owner_clip:
        t.resource_name = t.resource_name or owner_clip
        t.owner_clip = owner_clip
    t.owner_tick_duration = tick_duration
    return t


def _scan_blnd_events(d, notes):
    """非官方池容器回退: 0x4C15E8DD(EventResource::skFormatToken,
    HashStringCaseInsensitiveFNV)4 字节对齐锚定 + 官方布局校验。"""
    tables, seen = [], set()
    tok = struct.pack('<I', TOKEN_EVENT)
    start = 0
    while True:
        o = d.find(tok, start)
        if o < 0:
            break
        start = o + 1
        if o in seen or o % 4:
            continue
        t = _parse_event_resource(d, o)
        if t is not None:
            seen.add(o)
            tables.append(t)
            notes.append('%s — 可写回: 帧值(帧表+BaseEventData 双副本) + '
                         '不长于原位的名字' % t.describe())
    return tables


def _parse_skl_token_at(d, path, res, jbias):
    """新令牌骨架块(res=资源起点; jbias=表偏移解释 0/资源起点)。"""
    nj = struct.unpack_from('<H', d, res + 14)[0]
    nsb = struct.unpack_from('<I', d, res + 16)[0]
    joff = struct.unpack_from('<I', d, res + 20)[0]
    ioff = struct.unpack_from('<I', d, res + 28)[0]
    bno = struct.unpack_from('<I', d, res + 40)[0]
    if nj == 0 or nj > RIG_BONE_LIMIT:
        raise SknError('骨架块关节数异常 %d' % nj)
    jbase = joff + jbias
    if jbase < 0 or jbase + nj * 100 > len(d):
        raise SknError('骨架块关节表越界')
    joints = []
    for i in range(nj):
        o = jbase + i * 100
        jid = struct.unpack_from('<H', d, o + 2)[0]
        par = struct.unpack_from('<h', d, o + 4)[0]
        nh = struct.unpack_from('<I', d, o + 8)[0]
        radius = struct.unpack_from('<f', d, o + 12)[0]
        pos = struct.unpack_from('<3f', d, o + 16)
        scl = struct.unpack_from('<3f', d, o + 28)
        rot = struct.unpack_from('<4f', d, o + 40)
        ibt = struct.unpack_from('<3f', d, o + 56)
        ibs = struct.unpack_from('<3f', d, o + 68)
        ibq = struct.unpack_from('<4f', d, o + 80)
        nrel = struct.unpack_from('<i', d, o + 96)[0]
        naddr = (o + 96 + nrel) if 0 <= o + 96 + nrel < len(d) else (bno + jbias)
        name = _safe_cstr(d, naddr) or 'joint%d' % i
        joints.append(dict(id=jid, parent=par, name=name, hash=nh,
                            radius=radius, pos=pos, scl=scl, rot=qnorm(rot),
                            ib_t=ibt, ib_s=ibs, ib_q=qnorm(ibq)))
    influences = []
    if nsb:
        ibase = ioff + jbias
        if 0 <= ibase and ibase + nsb * 2 <= len(d):
            influences = list(struct.unpack_from('<%dh' % nsb, d, ibase))
    if not influences:
        influences = list(range(nj))
    return dict(path=path, fmt='new(v0x22FD4FC3)@0x%x' % res, num_joints=nj,
                nsb=nsb, joints=joints, influences=influences,
                names=[j['name'] for j in joints])


def _parse_skl_legacy_at(d, path, res):
    """旧 r3d2-sklt 骨架块(res=资源起点)。"""
    ver = struct.unpack_from('<I', d, res + 8)[0]
    nj = struct.unpack_from('<I', d, res + 12)[0]
    if ver not in (1, 2):
        raise SknError('旧骨架块版本不支持: %d' % ver)
    if nj == 0 or nj > RIG_BONE_LIMIT:
        raise SknError('骨架块关节数异常 %d' % nj)
    pos = res + 16
    JSIZE = 88
    if pos + nj * JSIZE > len(d):
        raise SknError('旧骨架块关节表越界')
    joints = []
    for i in range(nj):
        o = pos + i * JSIZE
        name = d[o:o + 32].split(b'\0', 1)[0].decode('ascii', 'replace')
        par = struct.unpack_from('<i', d, o + 32)[0]
        radius = struct.unpack_from('<f', d, o + 36)[0]
        g = struct.unpack_from('<12f', d, o + 40)
        M = [list(g[0:4]), list(g[4:8]), list(g[8:12])]
        p, q, s = mat_to_trs(M)
        joints.append(dict(id=i, parent=par, name=name, hash=elf_hash(name),
                           radius=radius, pos=p, scl=s, rot=q,
                           ib_t=(0.0, 0.0, 0.0), ib_s=(1.0, 1.0, 1.0),
                           ib_q=(0.0, 0.0, 0.0, 1.0)))
    pos += nj * JSIZE
    if ver == 2:
        nsb = struct.unpack_from('<I', d, pos)[0]
        pos += 4
        if pos + nsb * 2 > len(d):
            raise SknError('旧骨架块影响表越界')
        influences = list(struct.unpack_from('<%dh' % nsb, d, pos))
    else:
        nsb = nj
        influences = list(range(nj))
    return dict(path=path, fmt='old-v%d(r3d2-sklt)@0x%x' % (ver, res),
                num_joints=nj, nsb=nsb, joints=joints, influences=influences,
                names=[j['name'] for j in joints])


def _scan_blnd_rigs(d, path, notes):
    rigs = []
    tok = struct.pack('<I', RIG_TOKEN_NEW)
    start, tried = 0, set()
    while True:
        o = d.find(tok, start)
        if o < 0:
            break
        start = o + 1
        got = None
        for res in (o - 4, o):
            if res < 0 or res in tried:
                continue
            for label, jbias in (('绝对', 0), ('资源相对', res)):
                try:
                    got = _parse_skl_token_at(d, path, res, jbias)
                    notes.append('骨架块 @0x%06x(%s 表偏移): %d 关节 NSB=%d'
                                 % (res, label, got['num_joints'], got['nsb']))
                    break
                except Exception:
                    continue
            if got:
                tried.add(res)
                break
        if got:
            rigs.append(got)
    magic = b'r3d2sklt'
    start = 0
    while True:
        o = d.find(magic, start)
        if o < 0:
            break
        start = o + 8
        try:
            rigs.append(_parse_skl_legacy_at(d, path, o))
            notes.append('骨架块 @0x%06x(旧 r3d2-sklt): %d 关节'
                         % (o, rigs[-1]['num_joints']))
        except Exception as e:
            notes.append('骨架块 @0x%06x 解析失败: %s' % (o, e))
    return rigs


class BlndAsset(object):
    """blnd 官方 AnimationPoolData 解析结果(官方指针链, 无启发式)。

    双源: 4.17 Mac 反编译 PoolBuilder/PoolSerializer/ResourceBuilders/
    Anim_EventResource + 4.20 exe 反汇编; LeeSinSkin05.blnd 逐字节锚定:
    pool_clips(ClipResource/AtomicTick), pool_blends(BlendData), pool_tracks
    (TrackResource), events(EventResource — 官方事件指针数组定位, 帧表/哈希
    表/偏移数组齐备), anim_refs(外置 .anm 路径+哈希), skeleton_ref(路径+哈希)。"""

    def __init__(self, path, d, clips, rigs, events, notes, pool=None,
                 anim_refs=None):
        self.path = path
        self.d = d
        self.size = len(d)
        self.clips = clips
        self.rigs = rigs
        self.events = events
        self.notes = notes
        self.pool = pool or {}
        self.anim_refs = anim_refs or []
        self.official = bool(pool and pool.get('official'))
        self.pool_clips = pool.get('pool_clips') or [] if self.official else []
        self.pool_blends = pool.get('blends') or []
        self.pool_tracks = pool.get('tracks') or []
        self.skeleton_ref = pool.get('skeleton') or ''
        bits = []
        if self.official:
            bits.append('官方池 r3d2/blnd · clip %d · blend %d · 事件表 %d'
                        % (len(self.pool_clips), len(self.pool_blends),
                           len(events)))
            bits.append('动画引用 %d' % (pool.get('count', 0)))
        if clips and not self.official:
            bits.append('%d 内嵌动画块' % len(clips))
        if rigs:
            bits.append('%d 骨架块' % len(rigs))
        if not bits:
            bits.append('无子资源')
        self.fmt = 'blnd 官方 AnimationPoolData(%s)' % ' · '.join(bits)

    def chart_from_events(self, idx=0):
        """把第 idx 张事件表转成可编辑 EventChart; 帧率优先取所属 clip 的
        官方 mTickDuration(1/fps), 其次池 fps, 否则 30。"""
        if not self.events:
            return None
        t = self.events[idx]
        fps = 30.0
        owner = getattr(t, 'owner_clip', None)
        for c in self.pool_clips:
            if c['name'] == owner and c.get('tick_duration', 0) > 0:
                fps = 1.0 / c['tick_duration']
                break
        if not (0.1 < fps < 1000):
            fps = 30.0
        dur = 1.0
        if self.pool_clips and owner:
            for c in self.pool_clips:
                if c['name'] == owner:
                    dur = max(c.get('end_tick', 0) *
                              c.get('tick_duration', 1 / 30.0), 0.1)
                    break
        elif self.clips:
            dur = self.clips[0].duration
        else:
            dur = max((max(e['frame'] for e in t.events) / fps), 0.1) \
                if t.events else 1.0
        evs = [dict(frame=float(e['frame']), name=e['name'],
                    type_id=int(e['type_id'])) for e in t.events]
        return EventChart(self.path, dur, fps, evs)


_CLIP_KIND_NAMES = {
    'atomic': 'Atomic', 'sequencer': 'Sequencer', 'parallel': 'Parallel',
    'selector': 'Selector', 'condition_bool': 'ConditionBool',
    'condition_float': 'ConditionFloat', 'parametric': 'Parametric',
    'container': '容器', 'invalid': '无效',
}


def _parse_blnd_container(d, ac, cds, tid, num_classes, num_anim):
    """官方多 clip 容器 ClipData 解析(全部按官方序列化布局 + 尺寸自洽)。

    官方结构(ResourceBuilders.cpp 各 *_Build 的字段写序 +
    PoolSerializer::DumpToTextFile switch 全景; ClipData 首字段 mClipTypeID,
    以 AtomicClip 实物 {1,startTick,endTick,tickDur,animSlot} 逐字节锚定):
      AtomicClip     {1, u32 mStartTick, u32 mEndTick, f32 mTickDuration,
                      u32 mAnimData, ...}                       cds=0x34
      ParallelClip   {4, u32 mNumClips, u32 mClipIndices[]}     cds=8+4n
      SequencerClip  {tid, u32 mTrackIndex, u32 mNumClips,
                      u32 mClipIndices[]}                        cds=12+4n
      SelectorClip   {tid, u32 mTrackIndex, u32 mNumPairs,
                      SelectorClipPair{mClipID, f32 mProbability}[]} cds=12+8n
      ConditionBool/Float 同 Selector 形(pair 第二字为 bool/float 值)
      ParametricClip {6, u32 mNumPairs, u32 mUpdaterType, mMaskData,
                      mTrackData, ParametricPair{mClipID, f32 mValue}[]}
                                                                cds=0x14+8n
    类型 ID 数值证据(4.17 反汇编双处交叉): 1=Atomic / 4=Parallel /
    6=Parametric(Anim_ClipResource.cpp ClipResource::Sync case 1/4/6 +
    Pool.cpp GetAnimationTrack clipType==1/==6); 其余四类数值未知 →
    按「计数字段 == (cds-布局基)/步长」精确自洽判别(官方 _Build 的
    mResourceSize 精确含 count×步长, 真实布局必然严格相等; 各候选布局
    的等式互斥, 不会同时成立)。
    子引用为子 clip 的 mUniqueID(官方 mClipIdPtrMap); 兼容数组下标回退。
    返回 (kind, children[原始引用值...], pairs) — 解析成池索引由调用方
    在池构建完成后统一执行(uid_map + 下标回退)。"""
    n = len(d)

    def _u32(o):
        return struct.unpack_from('<I', d, ac + o)[0] \
            if ac + o + 4 <= n else None

    def _f32(o):
        return struct.unpack_from('<f', d, ac + o)[0] \
            if ac + o + 4 <= n else None

    refs = []
    pairs = []
    kind = 'container'
    track_idx = None

    def _plausible(v):
        return v is not None and v <= 0x7FFFFFFF

    # —— 已知类型 ID(4.17 反汇编数值证据, 双处交叉一致) ——
    if tid == 4:                       # ParallelClip(官方 case 4)
        kind = 'parallel'
        cnt = _u32(4)
        N = (cds - 8) // 4 if cds >= 8 and (cds - 8) % 4 == 0 else -1
        m = cnt if (cnt is not None and cnt == N and 1 <= cnt <= num_classes) \
            else max(0, N)
        for i in range(max(0, m)):
            v = _u32(8 + i * 4)
            if v is None or not _plausible(v):
                break
            refs.append(v)
        return kind, refs, pairs
    if tid == 6:                       # ParametricClip(官方 case 6)
        kind = 'parametric'
        cnt = _u32(4)
        N = (cds - 0x14) // 8 if cds >= 0x14 and (cds - 0x14) % 8 == 0 else -1
        m = cnt if (cnt is not None and cnt == N and 1 <= cnt <= num_classes) \
            else max(0, N)
        for i in range(max(0, m)):
            v = _u32(0x14 + i * 8)
            f = _f32(0x18 + i * 8)
            if v is None or not _plausible(v):
                break
            refs.append(v)
            pairs.append((v, f if f is not None else 0.0))
        return kind, refs, pairs

    # —— 未知类型 ID: 官方尺寸自洽判别。
    # 真实序列化布局的计数字段必等于 (cds - 布局基)/步长 的精确推导值
    # (mResourceSize 由官方 _Build 精确写定); 四种候选布局互斥:
    #   Sequencer {trackIndex@4, numClips@8, ids@12}  cds = 12+4N
    #   Parallel  {numClips@4, ids@8}                 cds = 8+4N
    #   Selector/Condition {trackIndex@4, numPairs@8,
    #            pair{clipID,f32}@12}                 cds = 12+8N
    #   Parametric {numPairs@4, updater@8, mask@0xc,
    #            track@0x10, pair@0x14}               cds = 0x14+8N
    # 官方 SequencerClip 含 mTrackIndex 字段(SequencerClipResourceBuilder
    # ::_Build: mTrackIndex=0xFFFFFFFF 初置 + Patch 填充 track 池索引) —
    # 旧实现把它当 Parallel 形的 numClips 读 → 首个子引用实为计数字段 →
    # 解析到池内无关 clip(用户实测「Sequencer 首个片段为无关动作」)。
    def _seq_try():
        if cds >= 12 and (cds - 12) % 4 == 0:
            N = (cds - 12) // 4
            cnt = _u32(8)
            tr = _u32(4)
            if cnt == N and 1 <= N <= num_classes and tr is not None:
                out = []
                for i in range(N):
                    v = _u32(12 + i * 4)
                    if v is None or not _plausible(v):
                        return None
                    out.append(v)
                return tr, out
        return None

    def _par_try():
        if cds >= 8 and (cds - 8) % 4 == 0:
            N = (cds - 8) // 4
            cnt = _u32(4)
            if cnt == N and 1 <= N <= num_classes:
                out = []
                for i in range(N):
                    v = _u32(8 + i * 4)
                    if v is None or not _plausible(v):
                        return None
                    out.append(v)
                return out
        return None

    def _cond_try():
        if cds >= 12 and (cds - 12) % 8 == 0:
            N = (cds - 12) // 8
            cnt = _u32(8)
            tr = _u32(4)
            if cnt == N and 1 <= N <= num_classes and tr is not None:
                out, prs = [], []
                for i in range(N):
                    v = _u32(12 + i * 8)
                    f = _f32(16 + i * 8)
                    if v is None or not _plausible(v):
                        return None
                    out.append(v)
                    prs.append((v, f if f is not None else 0.0))
                return tr, out, prs
        return None

    def _pmc_try():
        if cds >= 0x14 and (cds - 0x14) % 8 == 0:
            N = (cds - 0x14) // 8
            cnt = _u32(4)
            if cnt == N and 1 <= N <= num_classes:
                out, prs = [], []
                for i in range(N):
                    v = _u32(0x14 + i * 8)
                    f = _f32(0x18 + i * 8)
                    if v is None or not _plausible(v):
                        return None
                    out.append(v)
                    prs.append((v, f if f is not None else 0.0))
                return out, prs
        return None

    r = _seq_try()
    if r is not None:
        track_idx, refs = r
        return 'sequencer', refs, pairs
    r = _par_try()
    if r is not None:
        return 'parallel', r, pairs
    r = _cond_try()
    if r is not None:
        track_idx, refs, pairs = r
        # 布尔槽(pair 值 ∈ {0,1}) → ConditionBool; 值域 0..1 →
        # Selector(概率); 其余 → ConditionFloat(官方语义区分)
        vals = [p[1] for p in pairs]
        if vals and all(float(v).is_integer() and v in (0.0, 1.0)
                        for v in vals):
            kind = 'condition_bool'
        elif vals and all(0.0 <= v <= 1.0 for v in vals):
            kind = 'selector'
        else:
            kind = 'condition_float'
        return kind, refs, pairs
    r = _pmc_try()
    if r is not None:
        refs, pairs = r
        return 'parametric', refs, pairs
    # 全部不自洽 → 宽松兜底(旧形态; 仅记录原始引用供人工核对)
    if cds >= 8 and (cds - 8) % 4 == 0:
        m = (cds - 8) // 4
        for i in range(max(0, m)):
            v = _u32(8 + i * 4)
            if v is None or not _plausible(v):
                break
            refs.append(v)
    return 'container', refs, pairs


def _parse_blnd_pool_official(d, notes):
    """官方 AnimationPoolData 全链解析(4.20 实物逐字节锚定) → (pool, anim_refs)。

    链序(= PoolSerializer::Load 语义): 12 字节 BinaryHeader → PoolData@0x0C
    (0x60 头) → mBlendDataAry/mTransitionData/mBlendTrackAry/mClassAry/
    mMaskDataAry/mEventDataAry/mAnimDataAry(均字段相对 OffsetPtr) →
    类指针数组(条目相对数组基) → clip 资源链(ClipResource+AtomicClip, 其
    mEventData 指向所属 EventResource) → 事件指针数组 → 动画名记录+字符串池
    → 骨架路径。任何一处失败即返回非官方(调用方回退旧扫描)。"""
    n = len(d)
    pool = {'body_off': BLND_POOL_BASE, 'official': False}
    if n < BLND_POOL_BASE + BLND_POOL_HDR:
        return pool, []
    et, bt, ver = struct.unpack_from('<3I', d, 0)
    if et != BLND_ENGINE_TYPE or bt != BLND_BLOCK_TYPE or ver != BLND_VERSION:
        notes.append('非官方 blnd 头(EngineType=0x%08x BlockType=0x%08x '
                     'Version=%d; 官方为 r3d2/blnd/1) — 回退旧扫描'
                     % (et, bt, ver))
        return pool, []
    base = BLND_POOL_BASE
    token = struct.unpack_from('<I', d, base + 0x04)[0]
    if token != BLND_POOL_TOKEN:
        notes.append('池 token 0x%08x ≠ 0x%08X(AnimationPoolData'
                     '::skFormatToken) — 回退旧扫描' % (token, BLND_POOL_TOKEN))
        return pool, []
    pool['official'] = True
    (res_size, _tok, version, num_classes, num_blends, num_trans, num_tracks,
     num_anim, num_mask, num_event, use_cascade, cascade_f) = \
        struct.unpack_from('<12I', d, base)
    anim_name_cnt = struct.unpack_from('<I', d, base + 0x4c)[0]
    pool.update(version=version, num_classes=num_classes,
                num_blends=num_blends, num_trans=num_trans,
                num_tracks=num_tracks, num_anim=num_anim,
                num_mask=num_mask, num_event=num_event,
                use_cascade=use_cascade, cascade_value=cascade_f,
                anim_name_cnt=anim_name_cnt,
                mResourceSize=res_size)
    if num_classes > 4096 or num_blends > 4096 or num_anim > 4096 \
            or num_event > 4096 or num_tracks > 256 or num_trans > 4096:
        notes.append('池计数超界 — 回退旧扫描')
        pool['official'] = False
        return pool, []

    def _ptr(off):
        return _blnd_offptr(base + off,
                            struct.unpack_from('<I', d, base + off)[0])

    blend_a = _ptr(0x30)
    trans_a = _ptr(0x34)
    track_a = _ptr(0x38)
    class_a = _ptr(0x3c)
    mask_a = _ptr(0x40)
    event_a = _ptr(0x44)
    anim_a = _ptr(0x48)
    names_a = _ptr(0x50)
    skel_hash = struct.unpack_from('<I', d, base + 0x54)[0]
    skel_a = _ptr(0x58)
    pool.update(blend_off=blend_a, track_off=track_a, class_off=class_a,
                event_off=event_a, anim_off=anim_a, names_off=names_a,
                skeleton_off=skel_a)
    if class_a is None or class_a + num_classes * 4 > n:
        notes.append('类指针数组缺失/越界 — 回退旧扫描')
        pool['official'] = False
        return pool, []

    # —— BlendData[numBlends] {from, to, flags, time} ——
    blends = []
    if blend_a is not None and blend_a + num_blends * 16 <= n:
        for i in range(num_blends):
            f_, t_, fl, tm = struct.unpack_from('<3If', d, blend_a + i * 16)
            blends.append(dict(off=blend_a + i * 16, idx=i, frm=f_, to=t_,
                               flags=fl, time=tm))
        pool['blends'] = blends
    # —— TransitionClipData(尽力; 本时代常见 0) ——
    if trans_a is not None and num_trans and trans_a + num_trans * 16 <= n:
        pool['transitions'] = [
            struct.unpack_from('<4I', d, trans_a + i * 16)
            for i in range(num_trans)]
    # —— TrackResource[numTracks] 0x30 ——
    tracks = []
    if track_a is not None and track_a + num_tracks * 0x30 <= n:
        for i in range(num_tracks):
            o = track_a + i * 0x30
            sz, wgt = struct.unpack_from('<If', d, o)
            idx_, mode = struct.unpack_from('<2I', d, o + 8)
            nm = _safe_str_at(d, o + 0x10, 32)[0] or ''
            if sz != 0x30:
                notes.append('轨道 %d 资源尺寸 0x%x(非 0x30) — 跳过' % (i, sz))
                continue
            tracks.append(dict(off=o, name=nm, weight=wgt, index=idx_,
                              mode=mode))
        pool['tracks'] = tracks
        for tr in tracks:
            notes.append('官方混合轨道 @0x%06x: %s · 权重 %g · 模式 %d'
                         % (tr['off'], tr['name'], tr['weight'], tr['mode']))
    # —— 掩码/事件/动画指针数组(条目相对数组基) ——
    def _rel_ary(ary_a, cnt):
        out = []
        if ary_a is not None and cnt and ary_a + cnt * 4 <= n:
            for i in range(cnt):
                v = struct.unpack_from('<I', d, ary_a + i * 4)[0]
                sv = v - 0x100000000 if v >= 0x80000000 else v
                out.append(ary_a + sv)
        return out

    event_bases = _rel_ary(event_a, num_event)
    anim_bases = _rel_ary(anim_a, num_anim)
    mask_bases = _rel_ary(mask_a, num_mask)
    pool['event_bases'] = event_bases
    pool['anim_bases'] = anim_bases
    # —— 类指针数组 → clip 资源链 ——
    pool_clips = []
    class_entries = []
    for i in range(num_classes):
        o = struct.unpack_from('<I', d, class_a + i * 4)[0]
        ca = class_a + o
        class_entries.append(ca)
        if not (0 < o < n) or ca + 0x14 > n:
            pool_clips.append(dict(name='clip%d' % i, start_tick=0,
                                    end_tick=0, tick_duration=0,
                                    anim_idx=None, flags=0, id=i,
                                    off=ca, atomic_off=0, event_off=None,
                                    track_off=None, clip_kind='invalid',
                                    type_id=0, children=[], child_pairs=[]))
            continue
        sz, flags, uid, name_off, data_off = struct.unpack_from('<5I', d, ca)
        name_a = ca + name_off
        name = _safe_str_at(d, name_a, 64)[0] or ('clip%d' % i)
        ac = ca + data_off
        start_tick = end_tick = 0
        tick_dur = 0.0
        anim_idx = None
        ev_off = None
        track_off = None
        kind = 'atomic'
        children = []
        child_pairs = []
        # ClipData 尺寸 = mResourceSize - mClipDataOffset(官方链整资源含名字)
        cds = sz - data_off if (sz > data_off >= 0) else 0
        if not (0 <= ac and ac + 8 <= n and cds >= 8):
            pool_clips.append(dict(name=name, flags=flags, id=uid,
                                    start_tick=0, end_tick=0, tick_duration=0,
                                    anim_idx=None, off=ca, size=sz,
                                    atomic_off=ac, event_off=None,
                                    track_off=None, clip_kind='invalid',
                                    children=[], child_pairs=[]))
            continue
        tid = struct.unpack_from('<I', d, ac)[0]
        if tid == 1:
            # AtomicClip(官方 0x34): tick 范围/时长/动画槽/事件/掩码/轨道
            if ac + 0x34 <= n:
                (t1_, start_tick, end_tick) = struct.unpack_from('<3I', d, ac)
                tick_dur = struct.unpack_from('<f', d, ac + 0x0c)[0]
                anim_idx = struct.unpack_from('<I', d, ac + 0x10)[0]
            # mEventData / mTrackData = OffsetPtr(字段相对)
            # AtomicClip 字段序: +0x10 mAnimData(动画槽索引) +0x14 mEventData
            # +0x18 mMaskData +0x1c mTrackData +0x20 mUpdaterDataOffset
            if ac + 0x20 <= n:
                ev_rel = struct.unpack_from('<I', d, ac + 0x14)[0]
                ev_off = _blnd_offptr(ac + 0x14, ev_rel)
                track_off = _blnd_offptr(
                    ac + 0x1c,
                    struct.unpack_from('<I', d, ac + 0x1c)[0])
            kind = 'atomic'
        else:
            # 官方多 clip 容器(SequencerClip/ParallelClip/SelectorClip/
            # ConditionBoolClip/ConditionFloatClip/ParametricClip —
            # PoolSerializer::DumpToTextFile switch + PoolBuilder::LoadData
            # 结构驱动解析: 已知型号 4=Parallel/6=Parametric(4.17
            # ClipResource::Sync switch); 其余按 ClipData 尺寸判形状:
            #   S形 {tid, u32 count, u32 indices[]}: cdss = 8+4n
            #   C形 {tid, u32 trackIdx, u32 numPairs, pair8B[]}: cdsc = 12+8n
            #   P形(Parametric) {tid, numPairs, updater, mask, track,
            #      pair8B[]}: cdsp = 0x14+8n
            kind, children, child_pairs = _parse_blnd_container(
                d, ac, cds, tid, num_classes, num_anim)
            notes.append('clip %s 类型号 %d(%s) — 子引用 %d 个'
                         % (name, tid, _CLIP_KIND_NAMES.get(kind, kind),
                            len(children)))
        pool_clips.append(dict(name=name, flags=flags, id=uid,
                                start_tick=start_tick, end_tick=end_tick,
                                tick_duration=tick_dur, anim_idx=anim_idx,
                                off=ca, size=sz, atomic_off=ac,
                                event_off=ev_off, track_off=track_off,
                                clip_kind=kind, type_id=tid,
                                children=children, child_pairs=child_pairs))
    pool['class_entries'] = class_entries
    pool['pool_clips'] = pool_clips
    # —— 子引用解析(官方 mClipIdPtrMap: 引用 = 子 clip mUniqueID;
    # 无 uid 命中时回退数组下标 — 双兼容) → children = 池索引列表 ——
    uid_map = {}
    for ci, c in enumerate(pool_clips):
        uid_map.setdefault(c.get('id'), ci)
    for self_ci, c in enumerate(pool_clips):
        if c.get('clip_kind') in (None, 'atomic', 'invalid'):
            continue
        raw_refs = c.get('children') or []
        resolved = []
        for v in raw_refs:
            ci = uid_map.get(v)
            if ci is None and 0 <= v < len(pool_clips):
                ci = v
            if ci is not None and ci != self_ci:
                resolved.append(ci)
        c['children'] = resolved
        c['child_pairs'] = [(uid_map.get(v, v if 0 <= v < len(pool_clips)
                                          else None), f)
                            for v, f in (c.get('child_pairs') or [])]
        c['child_pairs'] = [(v, f) for v, f in c['child_pairs'] if v is not None]
    notes.append('clip 资源 %d 个: %s'
                 % (len(pool_clips),
                    ', '.join(c['name'] for c in pool_clips[:14])
                    + (' …' if len(pool_clips) > 14 else '')))
    if blends:
        pairs = ', '.join('#%d→#%d@%gs' % (b['frm'], b['to'], b['time'])
                          for b in blends[:6])
        notes.append('混合表 %d 条@0x%06x(from/to=clip 索引, 官方语义: '
                     'GetBlendData(from,to) → 混合时长/标志) — %s%s'
                     % (len(blends), blend_a, pairs,
                        ' …' if len(blends) > 6 else ''))
    # —— 事件指针数组 → EventResource(官方链) ——
    events = []
    owner_of = {}
    for c in pool_clips:
        if c.get('event_off') is not None:
            owner_of[c['event_off']] = c
    used_bases = set()
    for eb in event_bases:
        if eb in used_bases or not (0 <= eb < n):
            continue
        used_bases.add(eb)
        owner = owner_of.get(eb)
        t = _parse_event_resource(
            d, eb, owner_clip=(owner['name'] if owner else None),
            tick_duration=(owner.get('tick_duration') if owner else 0) or 0)
        if t is not None:
            events.append(t)
            evn = len(t.events)
            names = ', '.join(e['name'] for e in t.events[:3])
            notes.append('事件表 @0x%06x(%s): %d 事件 — %s%s'
                          % (eb, getattr(t, 'owner_clip', '?'), evn, names,
                             ' …' if evn > 3 else ''))
        else:
            notes.append('事件资源 @0x%06x 官方布局校验失败' % eb)
    # 未入指针数组但被 clip 引用的事件资源(防御性兜底)
    if owner_of:
        for c in pool_clips:
            eo = c.get('event_off')
            if eo is not None and eo not in used_bases and 0 <= eo < n:
                t = _parse_event_resource(
                    d, eo, owner_clip=c['name'],
                    tick_duration=c.get('tick_duration') or 0)
                if t is not None:
                    events.append(t)
                    used_bases.add(eo)
                    notes.append('事件表 @0x%06x(%s, clip 直连): %d 事件'
                                 % (eo, c['name'], len(t.events)))
    pool['event_count'] = len(events)
    # —— 外置动画引用 PathRecord{hash, nameOff(字段相对)} ——
    refs = []
    if anim_name_cnt and 0 < anim_name_cnt <= 4096 and names_a is not None \
            and names_a + anim_name_cnt * 8 <= n:
        for i in range(anim_name_cnt):
            h, noff = struct.unpack_from('<2I', d, names_a + i * 8)
            na = _blnd_offptr(names_a + i * 8 + 4, noff)
            nm = _safe_str_at(d, na, 192)[0] if na is not None else ''
            refs.append(dict(hash=h, name=nm or '', name_off=na,
                             hash_ok=(nm and fnv1a_hash(nm) == h)))
        pool['count'] = anim_name_cnt
        pool['names'] = [r['name'] for r in refs]
        bad = sum(1 for r in refs if not r['hash_ok'])
        notes.append('官方动画池: %d 引用 — %s%s'
                     % (anim_name_cnt,
                        ', '.join(r['name'].rsplit('/', 1)[-1]
                                  for r in refs[:12]),
                        ' …' if anim_name_cnt > 12 else ''))
        notes.append('动画名哈希校验(FNV-1a): %d/%d 通过%s'
                     % (anim_name_cnt - bad, anim_name_cnt,
                        '' if not bad else '(%d 未对齐!)' % bad))
    if anim_a is not None:
        pool['anim_slots'] = [None if v == 0 else v for v in
                             (struct.unpack_from('<I', d, anim_a + i * 4)[0]
                              for i in range(num_anim))] \
            if anim_a + num_anim * 4 <= n else []
    # —— 骨架路径 ——
    if skel_a is not None and 0 <= skel_a < n:
        spath = _safe_str_at(d, skel_a, 192)[0] or ''
        pool['skeleton'] = spath
        if spath and fnv1a_hash(spath) == skel_hash:
            notes.append('骨架引用: %s(哈希 FNV-1a 校验√)' % spath)
        elif spath:
            notes.append('骨架引用: %s(哈希 0x%08x 未匹配, 备用)'
                         % (spath, skel_hash))
    else:
        pool['skeleton'] = ''
    pool['_events'] = events
    return pool, refs


def parse_blnd(path):
    """解析 .blnd — 官方链(4.20 客户端 PoolSerializer::Load 逐字节对齐):
      1) 12 字节 BinaryHeader {"r3d2" "blnd" version=1};
      2) PoolData@0x0C: 头 0x60(计数 + 字段相对 OffsetPtr 数组指针);
      3) 数组区: BlendData(混合表) → [Transition] → TrackResource →
         类指针数组 → clip 资源链(ClipResource + AtomicTick, 其 mEventData
         指向所属 EventResource) → 事件指针数组 → 动画指针数组(外置, 文件内
         0) → 动画名记录+字符串池 → 骨架路径;
      4) 事件表: 官方指针链定位, 帧表({dataID, frame} 按帧排序)/哈希表
         ({dataID, fnv1_ci})/偏移数组齐备, 哈希逐条交叉校验;
      5) 回退: 非官方容器 → 旧式内嵌子资源全扫描(r3d2anmd/canm 动画块、
         骨架块、0x4C15E8DD 令牌锚定)。"""
    d = open(path, 'rb').read()
    notes = ['文件 %d 字节; 头 12 字节 %s' % (len(d), d[:12].hex())]
    pool, anim_refs = _parse_blnd_pool_official(d, notes)
    clips = []
    events = []
    if pool.get('official'):
        events = pool.pop('_events', [])
    else:
        for magic in BLND_CLIP_MAGICS:
            start = 0
            while True:
                o = d.find(magic, start)
                if o < 0:
                    break
                start = o + 1
                try:
                    a = parse_anm_data(d, path, o)
                    clips.append(a)
                    notes.append('动画块 @0x%06x: %s · %.2fs · %d 轨道'
                                 % (o, a.fmt, a.duration, len(a.tracks)))
                except Exception as e:
                    notes.append('动画块 @0x%06x 解析失败: %s' % (o, e))
        events = _scan_blnd_events(d, notes)
    rigs = _scan_blnd_rigs(d, path, notes)
    if not clips and not rigs and not events and not pool.get('count'):
        notes.append('未发现可识别子资源 — 可用「BLND 取证」导出头 256 字节'
                     '十六进制协助定位')
    return BlndAsset(path, d, clips, rigs, events, notes, pool=pool,
                     anim_refs=anim_refs)


def blnd_report(asset):
    lines = ['BLND 官方池报告 — %s (%d 字节)'
             % (os.path.basename(asset.path), asset.size),
             '格式: %s' % asset.fmt, '']
    lines += ['· ' + n for n in asset.notes]
    if asset.official and asset.pool_clips:
        lines.append('')
        lines.append('clip 明细(官方 AtomicTick):')
        for c in asset.pool_clips:
            dur = c['end_tick'] * c['tick_duration'] if c['tick_duration'] else 0
            lines.append('  %-16s 帧 %d..%d · %.3fs/tick · 动画#%s%s'
                         % (c['name'], c['start_tick'], c['end_tick'],
                            c['tick_duration'] or 0,
                            c['anim_idx'] if c['anim_idx'] is not None else '-',
                            ' · 带事件表' if c.get('event_off') is not None
                            else ''))
        if asset.pool_blends:
            lines.append('')
            lines.append('混合表(BlendData 官方语义 from/to=clip 索引):')
            for b in asset.pool_blends[:30]:
                fr = asset.pool_clips[b['frm']]['name'] \
                    if 0 <= b['frm'] < len(asset.pool_clips) else '#%d' % b['frm']
                to = asset.pool_clips[b['to']]['name'] \
                    if 0 <= b['to'] < len(asset.pool_clips) else '#%d' % b['to']
                lines.append('  %s → %s · 时长 %gs · 标志 %d'
                             % (fr, to, b['time'], b['flags']))
            if len(asset.pool_blends) > 30:
                lines.append('  … 其余 %d 条' % (len(asset.pool_blends) - 30))
        if asset.pool_tracks:
            lines.append('')
            lines.append('混合轨道(TrackResource):')
            for tr in asset.pool_tracks:
                lines.append('  %s · 权重 %g · 模式 %d' %
                             (tr['name'], tr['weight'], tr['mode']))
    if asset.skeleton_ref:
        lines.append('')
        lines.append('骨架引用: %s' % asset.skeleton_ref)
    if asset.anim_refs:
        lines.append('')
        lines.append('外置 .anm 引用 %d:' % len(asset.anim_refs))
        for r in asset.anim_refs[:40]:
            lines.append('  %s%s' % (r['name'],
                                     '' if r.get('hash_ok') else '(哈希未对齐)'))
        if len(asset.anim_refs) > 40:
            lines.append('  … 其余 %d 条' % (len(asset.anim_refs) - 40))
    if asset.clips:
        lines.append('')
        lines.append('内嵌动画块明细:')
        for i, a in enumerate(asset.clips):
            lines.append('  [%d] %.2fs · %.0f fps · %d 轨道 · %s'
                         % (i, a.duration, a.fps, len(a.tracks), a.fmt))
    for t in asset.events:
        lines.append('')
        lines.append('  ' + t.describe())
        for e in t.events[:30]:
            extra = ''
            if e.get('sound'):
                extra += ' 声音 %s' % e['sound']
            if e.get('particle'):
                extra += ' 粒子 %s' % e['particle']
            if e.get('bone'):
                extra += ' 挂接 %s' % e['bone']
            if e.get('show_hash'):
                extra += ' 显示子网格哈希 0x%08x' % e['show_hash']
            if e.get('end_frame') is not None and e.get('end_frame', 0) < 0:
                extra += ' 末帧 %g' % e['end_frame']
            lines.append('    帧 %-10g 名 %-24s 类型 %s%s'
                         % (e['frame'], e['name'][:24],
                            _EV_TYPE_NAMES.get(e['type_id'],
                            '0x%x' % e['type_id']), extra))
        if len(t.events) > 30:
            lines.append('    … 其余 %d 条' % (len(t.events) - 30))
    lines.append('')
    lines.append('写回能力: 事件帧值(帧表+BaseEventData 双副本原位 f32)与'
                 '「不长于原名字」的就地改名; 增删事件请用 .events.json 工作流。')
    return lines


def blnd_patch_events(d, table, edits):
    """安全就地补丁: edits = [{'idx', 'frame' or None, 'name' or None}]。
    仅改 4 字节帧值与「不长于原位」的名字(\\0 填充); 任何约束不满足则整体
    拒绝(返回 (None, 原因列表)), 绝不产出半写状态。
    帧值写回后按官方不变量把 EventFrame_t 帧表重排为按帧升序
    (GetEvent(frame,tol) 二分前提 — 引擎播放本身只读 BaseEventData.mFrame,
    重排仅为保持文件与官方 _Build 产物逐字节同构)。"""
    reasons = []
    out = bytearray(d)
    frame_changed = False
    for ed in edits:
        idx = ed.get('idx')
        if not (isinstance(idx, int) and 0 <= idx < len(table.events)):
            reasons.append('事件索引非法: %r' % (idx,))
            continue
        ev = table.events[idx]
        nf = ed.get('frame')
        if nf is not None:
            try:
                nf = float(nf)
            except (TypeError, ValueError):
                reasons.append('事件 %d 帧值非法: %r' % (idx, ed.get('frame')))
                nf = None
            if nf is not None:
                if -1e4 <= nf <= 1e6:
                    if ev.get('frame_abs_off') is not None:
                        struct.pack_into('<f', out, ev['frame_abs_off'], nf)
                        frame_changed = True
                    if ev.get('frame2_abs_off') is not None:
                        # BaseEventData.mFrame 与帧表双副本同步写回
                        # (官方 GetStartFrame 读 BaseEventData.mFrame)
                        struct.pack_into('<f', out, ev['frame2_abs_off'], nf)
                    if (ev.get('frame_abs_off') is None
                            and ev.get('frame2_abs_off') is None):
                        reasons.append('事件 %d 无可写回的帧值槽' % idx)
                else:
                    reasons.append('事件 %d 帧值超界: %r' % (idx, nf))
        nn = ed.get('name')
        if nn is not None:
            nn = str(nn)
            if ev['name_abs_off'] is None or not ev['name_max_len']:
                reasons.append('事件 %d 无可写回的名字槽' % idx)
            else:
                try:
                    b = nn.encode('ascii')
                except UnicodeEncodeError:
                    reasons.append('事件 %d 名字含非 ASCII 字符' % idx)
                    b = None
                if b is not None:
                    if len(b) > ev['name_max_len']:
                        reasons.append('事件 %d 名字 %d 字节超出原位 %d 字节'
                                       % (idx, len(b), ev['name_max_len']))
                    else:
                        seg = b + b'\0' * (ev['name_max_len'] - len(b))
                        out[ev['name_abs_off']:ev['name_abs_off'] +
                            ev['name_max_len']] = seg
                        # 同步更新哈希表条目(GetEvent(name) 官方查找语义;
                        # 名字变了哈希必须同步, 否则重读校验/客户端查找失配)
                        if ev.get('hash_abs_off') is not None:
                            try:
                                struct.pack_into('<I', out, ev['hash_abs_off'],
                                                 fnv1_ci_hash(nn))
                            except Exception:
                                pass
    if reasons:
        return None, reasons
    if frame_changed:
        # 官方不变量: EventFrame_t[n] 按帧升序(_Build 产物)。帧值被改后原地重排
        # 该条目集(8B 条目 {u32 mDataID, f32 mFrame}, mFrame 槽 = frame_abs_off,
        # 条目基 = frame_abs_off - 4)。
        entries = []
        ok = True
        for ev in table.events:
            fa = ev.get('frame_abs_off')
            if fa is None:
                continue
            if not (4 <= fa <= len(out) - 4):
                ok = False
                break
            entries.append((fa - 4,
                            struct.unpack_from('<I', out, fa - 4)[0],
                            struct.unpack_from('<f', out, fa)[0]))
        if ok and entries:
            # entries[j] = 帧表槽位(基 fa-4, 读回的 did/frame)。注意必须按
            # 「物理槽位升序」收集后再与排序序列 zip — table.events 是按帧
            # 排序的事件序, 对现代布局(dataID 序帧表)两序不同, 直接 zip 会把
            # 排序对写进错误槽位(v8.2 修复)。srt = 同一组 (did, frame) 按帧
            # 升序 — 物理槽位 j 写入排序后第 j 对。
            entries.sort(key=lambda x: x[0])
            srt = sorted(entries, key=lambda x: (x[2], x[1]))
            for (base, _did, _fr), (_sbase, did, fr) in zip(entries, srt):
                struct.pack_into('<I', out, base, did)
                struct.pack_into('<f', out, base + 4, fr)
    if len(out) != len(d):
        return None, ['内部错误: 补丁后文件大小改变']
    return bytes(out), []


# ------------------------------------------------------ 事件图表模型 ------

class EventChart(object):
    """动画事件图表模型(源: .blnd 事件表 / .events.json / 新建)。"""

    def __init__(self, source='', duration=1.0, fps=30.0, events=None):
        self.source = source
        self.duration = max(float(duration), 1e-3)
        self.fps = max(float(fps), 0.1)
        self.events = list(events or [])
        self.dirty = False

    @staticmethod
    def _norm(ev):
        return dict(frame=float(ev.get('frame', 0.0)),
                    name=str(ev.get('name', '')),
                    type_id=int(ev.get('type_id', 0)))

    def add(self, frame, name='新事件', type_id=0):
        ev = self._norm(dict(frame=max(0.0, min(float(frame),
                                                self.duration * self.fps)),
                             name=name, type_id=type_id))
        self.events.append(ev)
        self.events.sort(key=lambda e: e['frame'])
        self.dirty = True
        return ev

    def remove(self, i):
        if 0 <= i < len(self.events):
            self.events.pop(i)
            self.dirty = True

    def move(self, i, frame):
        if 0 <= i < len(self.events):
            self.events[i]['frame'] = max(0.0, min(float(frame),
                                                   self.duration * self.fps))
            self.events.sort(key=lambda e: e['frame'])
            self.dirty = True

    def time_of(self, frame):
        return frame / self.fps


def events_to_json(chart, path):
    obj = {'version': 1, 'source': chart.source, 'duration': chart.duration,
           'fps': chart.fps,
           'events': [{'frame': e['frame'], 'time': e['frame'] / chart.fps,
                       'name': e['name'], 'type_id': e['type_id']}
                      for e in chart.events]}
    with open(path, 'w', encoding='utf-8') as fp:
        json.dump(obj, fp, ensure_ascii=False, indent=2)
    return obj


def events_from_json(path):
    with open(path, 'r', encoding='utf-8') as fp:
        obj = json.load(fp)
    fps = float(obj.get('fps', 30.0))
    evs = []
    for e in obj.get('events', []):
        frame = e.get('frame')
        if frame is None:
            frame = float(e.get('time', 0.0)) * fps
        evs.append(EventChart._norm(dict(frame=frame, name=e.get('name', ''),
                                         type_id=e.get('type_id', 0))))
    chart = EventChart(obj.get('source', path), obj.get('duration', 1.0),
                       fps, evs)
    chart.dirty = False
    return chart


def events_to_csv(chart, path):
    with open(path, 'w', encoding='utf-8-sig', newline='') as fp:
        fp.write('frame,time,name,type_id\r\n')
        for e in chart.events:
            fp.write('%g,%.4f,%s,%d\r\n' % (e['frame'], e['frame'] / chart.fps,
                                            e['name'], e['type_id']))


# ------------------------------------------------------ 合成回环素材 ------

def _build_synthetic_inibin(path):
    """合成官方 inibin v2(4.20 exe TryToLoadBinaryFileV2 反汇编布局):
    5 字节头 {u8 version=2, u16 charEntries, u16 avaliableSets} + 官方
    14 类型节序 + 尾部字符串池; 键哈希 = SDBM(section,'*',name)。"""
    strtab = bytearray()
    strings = []          # (hash, value)
    for sec, key, val in (
            ('MeshSkin', 'SimpleSkin', 'kayn.skn'),
            ('MeshSkin', 'Skeleton', 'kayn.skl'),
            ('MeshSkin', 'Texture', 'kayn_base_tx_cm.dds'),
            ('MeshSkin', 'Animations', 'KaynTest.blnd'),
            ('MeshSkin', 'ChampionSkinName', 'KaynTest'),
            ('Skin1', 'SimpleSkin', 'kayn_skin1.skn'),
            ('Skin1', 'Texture', 'kayn_skin1_tx_cm.dds')):
        strings.append((sdbm_key_hash(sec, key), val))
    offs = []
    for _h, s in strings:
        offs.append(len(strtab))
        strtab += s.encode('ascii') + b'\0'
    # 官方节序: Int32 → Float32 → FixedPoint → Int16 → Int8 → Bit →
    # FPVec3 → F32Vec3 → FPVec2 → F32Vec2 → FPVec4 → F32Vec4 → Str → Int64
    body = bytearray()
    entries_i32 = [(sdbm_key_hash('Global', 'BaseHP'), 540)]
    body += struct.pack('<H', len(entries_i32))
    for h, v in entries_i32:
        body += struct.pack('<Ii', h, v)
    entries_f32 = [(sdbm_key_hash('MeshSkin', 'SkinScale'), 1.25)]
    body += struct.pack('<H', len(entries_f32))
    for h, v in entries_f32:
        body += struct.pack('<If', h, v)
    entries_fp = [(sdbm_key_hash('MeshSkin', 'selfIllumination'), 0.9)]
    body += struct.pack('<H', len(entries_fp))
    for h, v in entries_fp:
        body += struct.pack('<Ib', h, int(round(v * 10)))
    entries_bit = [(sdbm_key_hash('MeshSkin', 'AttributeFlags'), True)]
    body += struct.pack('<H', len(entries_bit))
    for h, v in entries_bit:
        body += struct.pack('<I', h)
    body += bytes([1 if entries_bit[0][1] else 0])
    entries_v3 = [(sdbm_key_hash('MeshSkin', 'OverrideBoundingBox'),
                   (75.0, 120.0, 75.0))]
    body += struct.pack('<H', len(entries_v3))
    for h, v in entries_v3:
        body += struct.pack('<I3f', h, *v)
    body += struct.pack('<H', len(strings))
    for h, _s in strings:
        body += struct.pack('<I', h)
    for o in offs:
        body += struct.pack('<H', o)
    buf = (bytes([2]) + struct.pack('<HH', len(strtab), 0x10A7) +
           bytes(body) + bytes(strtab))
    open(path, 'wb').write(buf)
    return strings


def _build_synthetic_blnd(path, anm_path, anm_name=b'KaynTestAttack.anm',
                           clip_name=b'Idle1', ev_name=b'testevent',
                           ev_particle=b'kayn_test.troy',
                           skel_ref=b'characters/kayn/kayn.skl'):
    """合成「官方 AnimationPoolData」blnd — 自检黄金基准(v5 布局, 与
    LeeSinSkin05.blnd 逐字段一致, 全部偏移按官方定基):

      · BinaryHeader 12 字节 {r3d2, blnd, 1}(sizeof=12, 无第 4 字);
      · PoolData @文件 0x0C: 0x60 头{mResourceSize=0, token 0x5A40C9DD,
        计数, OffsetPtr(字段相对) 数组指针, 动画名计数/表, 骨架哈希/路径};
      · 数组区(池基+0x60): BlendData {from,to,flags,time} →
        TrackResource 0x30{'Default', 权重 1.0} → 类指针数组(条目相对
        数组基) → clip 资源链(ClipResource 0x14 + 名 + AtomicClip 0x34
        {typeId=1, ticks, tickDur, animIdx, mEventData=字段相对 → 所属
        EventResource, mTrackData=字段相对}) → EventResource(0x30 头 +
        偏移数组 + BaseEventData + {id,hash} + {id,frame} + 资源名=clip 名)
        → 事件指针数组(条目相对数组基) → 动画指针数组(0=外置) →
        动画名记录{hash, nameOff(字段相对)} + 字符串 → 骨架路径。"""
    anm = open(anm_path, 'rb').read()
    buf = bytearray(struct.pack('<3I', BLND_ENGINE_TYPE, BLND_BLOCK_TYPE,
                                BLND_VERSION))
    pool = BLND_POOL_BASE                   # PoolData 基 = 文件 0x0C
    buf += b'\0' * 0x60                     # 池头占位(后回填)
    # ---- BlendData[1]: {from=0, to=0, flags=0, time=0.2} ----
    blends_off = len(buf)
    buf += struct.pack('<3If', 0, 0, 0, 0.2)
    # ---- TrackResource 0x30: {size, weight(f), mode, index, name[32]} ----
    track_off = len(buf)
    tr = struct.pack('<IfII', 0x30, 1.0, 0, 0) + b'Default\0'
    buf += tr + b'\0' * (0x30 - len(tr))
    # ---- 类指针数组(1×4, 条目相对数组基) ----
    ary_off = len(buf)
    clip_off = ary_off + 4
    buf += struct.pack('<I', 0)             # 占位
    # ---- clip: ClipResource 0x14 + 名字 + AtomicClip 0x34 ----
    name_area = len(clip_name) + 1
    name_area += (-name_area) % 4
    clip_size = 0x14 + name_area + 0x34
    buf += struct.pack('<5I', clip_size, 0, 0, 0x14, 0x14 + name_area)
    buf += clip_name + b'\0' * (name_area - len(clip_name))
    atomic_off = len(buf)
    ev_off = atomic_off + 0x34               # EventResource 紧随 clip
    # AtomicClip 13×u32: {typeId=1, startTick, endTick, tickDur(f32),
    # animIdx, mEventData(字段相对→ev_off), mMaskData=0,
    # mTrackData(字段相对→track_off), updater=0, ext×4}
    buf += struct.pack('<III', 1, 0, 6)
    buf += struct.pack('<f', 1.0 / 30.0)
    buf += struct.pack('<2I', 0, (ev_off - (atomic_off + 0x14)) & 0xFFFFFFFF)
    buf += struct.pack('<2I', 0,
                       (track_off - (atomic_off + 0x1c)) & 0xFFFFFFFF)
    buf += struct.pack('<5I', 0, 0, 0, 0, 0)   # updaterOff + mExtBuffer×4 → 13×u32 = 0x34
    # ---- EventResource(官方布局, 资源相对偏移) ----
    nm = ev_name + b'\0'
    pt = ev_particle + b'\0'
    bn = b'root\0'
    ev_frame = 3.0
    # 布局: 0x30 头 + 偏移数组(4) + BaseEventData 0x24 + 字符串
    #        + {id,hash}(8) + {id,frame}(8) + 资源名(clip 名)
    data_off = 0x34                          # 偏移数组 @+0x30 × 1 条目
    name_off = 0x24                          # 相对 BaseEventData 起点
    part_off = name_off + len(nm)
    bone_off = part_off + len(pt)
    targ_off = bone_off + len(bn)
    hash_off = data_off + 0x24 + len(nm) + len(pt) + len(bn)
    frame_off = hash_off + 8
    resname_off = frame_off + 8
    ev_size = resname_off + len(clip_name) + 1
    ev_size += (-ev_size) % 4
    buf += struct.pack('<12I', ev_size, 0, 0, 0x00010000, 0,
                       0x30, data_off, hash_off, frame_off, resname_off,
                       0xFFFFFFFF, 0xFFFFFFFF)
    buf += struct.pack('<I', data_off)       # 偏移数组[0]
    # BaseEventData(Particle): {pad, typeId=2, flags=2, frame(f),
    # nameOff, effOff, boneOff, targOff, endFrame(f)=-1}
    buf += struct.pack('<3I', 0, 2, 2)
    buf += struct.pack('<f', ev_frame)
    buf += struct.pack('<4I', name_off, part_off, bone_off, targ_off)
    buf += struct.pack('<f', -1.0)
    buf += nm + pt + bn
    buf += struct.pack('<2I', 0, fnv1_ci_hash(ev_name.decode()))
    buf += struct.pack('<If', 0, ev_frame)
    buf += clip_name + b'\0'
    while len(buf) % 4:
        buf += b'\0'
    # ---- 事件指针数组(1×4, 条目相对数组基) ----
    ev_ary = len(buf)
    buf += struct.pack('<I', (ev_off - ev_ary) & 0xFFFFFFFF)
    # ---- 动画指针数组(1×4 = 0, 外置引用) ----
    anim_ary = len(buf)
    buf += struct.pack('<I', 0)
    # ---- 动画名记录 {hash, nameOff(字段相对)} + 字符串 ----
    names_off = len(buf)
    anm_str = names_off + 8
    buf += struct.pack('<2I', fnv1a_hash(anm_name.decode('ascii')),
                       anm_str - (names_off + 4))
    buf += anm_name + b'\0'
    while len(buf) % 4:
        buf += b'\0'
    # ---- 骨架路径字符串 ----
    skel_str = len(buf)
    buf += skel_ref + b'\0'
    while len(buf) % 4:
        buf += b'\0'
    # ---- 回填池头(全部字段相对定基) ----
    struct.pack_into('<I', buf, pool + 0x00, 0)                 # mResourceSize
    struct.pack_into('<I', buf, pool + 0x04, BLND_POOL_TOKEN)
    struct.pack_into('<I', buf, pool + 0x08, 0)                 # mVersion
    struct.pack_into('<I', buf, pool + 0x0c, 1)                 # mNumClasses
    struct.pack_into('<I', buf, pool + 0x10, 1)                 # mNumBlends
    struct.pack_into('<I', buf, pool + 0x14, 0)                 # mNumTrans
    struct.pack_into('<I', buf, pool + 0x18, 1)                 # mNumTracks
    struct.pack_into('<I', buf, pool + 0x1c, 1)                 # mNumAnim
    struct.pack_into('<I', buf, pool + 0x20, 0)                 # mNumMask
    struct.pack_into('<I', buf, pool + 0x24, 1)                 # mNumEvent
    struct.pack_into('<If', buf, pool + 0x28, 0, 0.0)
    struct.pack_into('<I', buf, pool + 0x30, blends_off - (pool + 0x30))
    struct.pack_into('<I', buf, pool + 0x34, 0)                 # mTransitionData
    struct.pack_into('<I', buf, pool + 0x38, track_off - (pool + 0x38))
    struct.pack_into('<I', buf, pool + 0x3c, ary_off - (pool + 0x3c))
    struct.pack_into('<I', buf, pool + 0x40, 0)                 # mMaskDataAry
    struct.pack_into('<I', buf, pool + 0x44, ev_ary - (pool + 0x44))
    struct.pack_into('<I', buf, pool + 0x48, anim_ary - (pool + 0x48))
    struct.pack_into('<I', buf, pool + 0x4c, 1)                 # mAnimNameCount
    struct.pack_into('<I', buf, pool + 0x50, names_off - (pool + 0x50))
    struct.pack_into('<I', buf, pool + 0x54,
                     fnv1a_hash(skel_ref.decode('ascii')))
    struct.pack_into('<I', buf, pool + 0x58, skel_str - (pool + 0x58))
    struct.pack_into('<I', buf, ary_off, clip_off - ary_off)
    open(path, 'wb').write(bytes(buf))
    return dict(anm_off=None, ev_off=ev_off,
                names=[ev_name.decode('ascii')], num=1,
                pool_count=1, pool_names=[anm_name.decode('ascii')],
                clip=dict(name=clip_name.decode(), start_tick=0,
                          end_tick=6, tick_duration=1.0 / 30.0,
                          anim_idx=0, ev_frame=ev_frame),
                skeleton=skel_ref.decode('ascii'))


def _hexdump_head(d, n=256):
    lines = []
    for off in range(0, min(n, len(d)), 16):
        chunk = d[off:off + 16]
        hexs = ' '.join('%02x' % b for b in chunk)
        text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append('%08x  %-47s  %s' % (off, hexs, text))
    return lines



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


