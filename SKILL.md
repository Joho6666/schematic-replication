---
name: schematic-replication
description: Use when the user asks to 原理图复刻 / 照着图片画原理图 / 把书上或照片里的电路图还原到嘉立创EDA (EasyEDA Pro), including photos of textbook figures, screenshots of circuit diagrams, or requests to make an existing EasyEDA page "look like the picture".
---

# 原理图复刻（图片 → 嘉立创EDA）

## 概述

把照片/截图里的原理图还原成嘉立创EDA专业版里可编辑的原理图。**默认目标是"像原图"**：位号、数值、接法、版式照抄，原图笔误也照抄并在图旁注释。电气修正和质检是用户要求后才做的独立步骤。

**REQUIRED SUB-SKILL:** `easyeda-agent`（CLI 用法、数据契约）。本 skill 只补"照图复刻"的流程、脚本和踩过的坑。

## 何时使用 / 不使用

- 用：给了电路图图片，要在嘉立创EDA里画出来；"复刻""还原""照书画""跟图一样"。
- 不用：只要电气正确不在乎外观（直接 `easyeda-agent`）；原理图审查（`design-and-review-circuit`）；整理已有图的可读性（`schematic-humanizer`）。

## 先问清（一次问完）

1. 忠实度：**严格照图**（默认，含原图笔误+注释）还是**外观照图、电路修正**？
2. 多张图是否各建独立原理图（要用原图位号就必须独立，见坑表第 1 行）。
3. 照片缺角/遮挡：等补图，还是先画看得清的部分。
4. 是否有别的会话/Agent 正在用同一个 EDA 窗口：有的话请用户先停掉它；停不了就把它的页面 uuid 填进 spec 的 `home`。

## 流程

1. **读图**：用 Python PIL 把照片旋转、放大 3–5 倍、分区裁剪后再看；模型不能看图时改用 vision MCP（`analyze_technical_diagram`）。逐元件列网表，另列"歧义清单"：无连接点的交叉、未标值、与芯片手册矛盾的标注（如 10mH 这类可疑值）。严格照图时歧义按原图画，在图旁注释说明。
2. **建文档**：每张图 `easyeda board new --project <uuid>` 建独立原理图（附带一个空 PCB）。`export EASYEDA_PROJECT=<uuid>`，脚本的所有调用都会带 `--project`，写入都带 `--doc <页uuid>`。
3. **选料**：`scripts/libsearch.py` 按值/型号/C 编号搜。原图只写符号名（Res2、Cap Pol1、D Zener）就选同值常用料；运放三角符号用通用库"运算放大器_AMP"（3 脚）或"AMP 5 Pin"。库里没有的芯片/型号：先找同系列、引脚功能相同的型号，按引脚名连接并注明替代；都没有再按 `easyeda-agent` 的建库流程自建符号。
4. **量引脚**：`scripts/probe_pins.py <页uuid> <device uuid>...` 在图纸外试放，打印旋转 0° 时的引脚偏移和脚名，粘进 `specgen.DEV`。`DEV` 里写 `None` 表示假定两脚各 ±20，只是占位，没实测过不要信。试放件会记进 `probes.json`，`build.py` 会把它挪进图里复用，不要删除。
5. **写规划**：复制 `references/spec-example.py` 改写。坐标框架：A4 图纸 raw 坐标约 0–1170 × 0–825，Y 向上，5 raw 网格；内框约 15–1155 × 15–810；右下明细表约 x≥460、y≤195，要避开。映射用 `X = x0 + (px - px0)·k`、`Y = y0 − (py - py0)·k`，k 取让整图落在内框里的值（通常 0.4–1.0）。**全部用实线直连**；地按原图画（底部地线或接地符号）；端子放在原图端子的位置。
6. **执行**：`build.py spec.json place`，必须看到 `all N expected pins match`；不对就改 `DEV` 偏移或旋转后重跑。然后 `build.py spec.json wire`（导线 → 标识 → 端口 → NC → 文字）。脚本能断点续跑。
7. **看像不像**：`easyeda sch export-image --format svg --doc <页uuid> --out x.svg`，再用 ImageMagick `magick -density 220 x.svg x.png` 转图（中文缺字体会显示成方块，EDA 里正常），和原图并排看。只调图面，不改电气。
8. **保存**：每张图 `sch save` 必须返回 `saved:true`。交付时说清楚：引脚已核对，但网表没有逐网对账。质检（`verify.py` 逐网比对、`sch check`、`bridge-check`）等用户要求再做。

## 脚本（`scripts/`）

| 文件 | 用途 |
|---|---|
| `libsearch.py <limit> "查询"...` | 批量搜库，输出 C 编号、封装、device uuid |
| `probe_pins.py <页uuid> <uuid>...` | 图纸外试放，打印引脚偏移和脚名，记入 `probes.json` |
| `specgen.py` | `Page` 类：`part / wire / flag / port / text`，按旋转和镜像自动算出各引脚期望坐标 |
| `build.py spec.json place\|wire` | 锁页写入、复用试放件、放置超时后自动核查、读回核对引脚、断点续跑 |
| `verify.py nets.json` | 质检阶段逐网比对（复刻阶段不用） |
| `references/spec-example.py` | 图 A-4 TOP221 的完整示例 |

flag 的 `kind`：`gnd`、`power`、`net_label`、`net_port_in/out/bi`（`connect` 生成）；端口优先用 `port()`（`netflag`）。

## 必知的坑（详见 `references/pitfalls.md`）

| 现象 | 处理 |
|---|---|
| 位号被改成 T2、R20 | 同一原理图内位号跨页唯一：每张图建独立原理图 |
| `sch place` 超时 "connector did not respond" | 本会话放过又删光的器件会卡死：用试放件复用，或换同值的另一个料号；不要先删后放 |
| `modify --rotation` 结果反了 | place 的 90° 等于 modify/读回的 270°；有镜像时先旋转再镜像 |
| 导线被拒（pin-exit-direction）或 create failed | 第一段必须沿引脚朝外；端点用读回的精确浮点坐标；create failed 可以重试 |
| 端口箭头朝向导线、输出端口名字不显示 | 出图检查；方向反的用 `port()` 重放，隐藏的名字补自由文字 |
| 电源符号放不上 | 改用 `net_label` 标同名 |
| 别的会话同时操作 EDA | 写入一律带 `--doc`，spec 的 `home` 填对方页面；大改前请用户停掉对方 |

## 常见错误

- 为省事用网络标签代替导线，画出来不像原图。
- 质检时顺手改数值或型号，违背"照图"；要改先问用户。
- 删旧内容时按位号决定保留哪些，但位号可能已被自动改名；删除前先按坐标和器件名核对保留项。
