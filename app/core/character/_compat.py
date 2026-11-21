# coding: utf-8
"""app.core.character._compat — 共享依赖保护头(v8.3 提取)。

Riot_File_Tools 角色预览核心包的公共依赖: Pillow(位图/DDS 解码/
HUD 字体)与 numpy(投影/光栅/蒙皮向量化)缺失任一自动降级,
不影响解析与体检功能(与原 v8.3 单文件版语义一致)。"""
import io          # noqa: F401
import math        # noqa: F401
import os          # noqa: F401
import re          # noqa: F401
import struct      # noqa: F401
import sys         # noqa: F401
import time        # noqa: F401

# ------------- 可选加速依赖(缺失任一自动降级) ------------------------
try:                                     # Pillow: 位图后缓冲渲染(推荐)
    from PIL import Image as _PILImage
    from PIL import ImageDraw as _PILDraw
    from PIL import ImageFont as _PILFont
    PIL_OK = True
except Exception:                        # pragma: no cover — 环境缺 Pillow
    _PILImage = _PILDraw = _PILFont = None
    PIL_OK = False

try:                                     # numpy: 投影/剔除/排序向量化(推荐)
    import numpy as _np
    NP_OK = True
except Exception:                        # pragma: no cover — 环境缺 numpy
    _np = None
    NP_OK = False
