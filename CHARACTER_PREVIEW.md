# Character Preview 模块(测试分支说明)

本分支以专业分层重构引入**角色可视化预览器**, 达到 ltk-manager 水准的
视口渲染/动画/事件链, 并为后续 Riot 地图网格体(aimesh_ngrid)可视化
预留同一层扩展点。

## 架构

```
app/core/character/            ← 核心层(纯逻辑, 无 UI 依赖)
    _compat.py    共享依赖保护头(Pillow/numpy 缺失自动降级)
    core.py       硬化解析: SKN/SKL(双格式)/ANM(v3/v4/v5/canm)/
                  INI/INIBIN(官方 ConfigFile 语义)/材质绑定
                  (LoadSkinINI + MaterialOverride 优先级)/BLND(官方
                  指针数组定位+边界校验, 替代旧硬编码 108 偏移的脆弱
                  读取)/EventResource 帧表+哈希表双副本互证/Sim420
    viewport.py   Qt(PySide6) 软光栅 3D 视口: 相机预设(game/orbit/
                  top/front/side)+逐预设记忆+平滑过渡; 视图模式
                  (lit/unshaded/untextured/wireframe); numpy 帧缓冲
                  光栅(分块预算/交互自适应分辨率/贴图双线性/地面
                  网格/朝向 gizmo/HUD 条带缓存/骨架叠加)
    player.py     预览控制器(播放墙钟重锚+整 tick 步进+姿态帧缓存
                  有界淘汰/Sequencer 连播/官方 clip 语义播放/
                  SubmeshVisibility 事件窗口派发/双层显隐掩码/
                  官方一键链 .ini→皮肤包→模型+动画池+材质)

app/tools_interface/character_tool/
    character_tool_interface.py  Fluent UI 工具页(PyQt-Fluent-Widgets)
```

## 相对旧实现的硬化点

| 旧实现问题 | 本分支处理 |
| --- | --- |
| blnd 读取顺序依赖固定 108 起始偏移, 无边界校验 | 官方指针数组定位 + 全偏移边界校验, 坏块优雅跳过 |
| elf_hash 缺大小写折叠(与官方 HashStringELF 不一致) | 官方 ELFHash.cpp 逐行对齐(含折叠) |
| BinaryReader 无越界保护 | 全部解析走 bytes 切片 + 长度断言 |
| 事件只在专用编辑页生效 | 动画↔事件表自动桥接(anim_key 双通道: 官方引用链 + owner_clip 基名), 任意播放路径事件生效 |
| 无 3D 预览 | 软光栅视口全量(相机/材质/动画/事件/LOD) |
| main 分支 navgrid_drawobjects_options.py 缺失导致整个应用无法启动 | 按同构模式重建(层选择→渲染→导出) |

## 使用

运行 `python3 demo.py` → 左侧导航 **Character Preview**:
1. 「导入角色包」选 .ini/.inibin → 皮肤包下拉选择 → 一键装配
   (.skn/.skl/.blnd/贴图/SubmeshesToHide 官方链);
2. 动画列表双击切换(事件表自动桥接, 状态栏提示绑定结果);
3. 播放/暂停/变速/时间轴; 视口: 左拖旋转 / 中右拖平移 / 滚轮缩放 /
   左上 gizmo 点击轴向吸附; 右栏: 相机预设/视图模式/精度档/骨架/
   地面网格/贴图插值/子网格双层显隐;
4. 也支持直接拖放 .skn/.skl/.anm/.blnd 到窗口。

## 验收

`scripts/test_character_tool.py`(独立仓库外测试脚本): 21 项全过 —
BLND 59 事件表/105 clip 解析, 46k 三角形渲染出图(多模式非空),
Transform_Assassin 114 帧形态切换事件派发(用户实测 bug 场景),
Fluent 工具页/主窗口全量实例化。
