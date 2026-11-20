# schematic-replication（原理图复刻）

一个 Claude Code skill：把书上、照片或截图里的电路图**照原样**还原到嘉立创EDA专业版（EasyEDA Pro）。

- 默认严格照图：位号、数值、型号、接法、版式照抄；原图笔误也照抄，在图旁加注释说明。
- 先画完再质检：电气修正与逐网核对（`verify.py`）只在用户要求时做。
- 附带脚本：搜库、试放量引脚、按规划自动放置/连线、断点续跑、读回核对引脚。

## 依赖

- 嘉立创EDA专业版（已验证 V4.1.105）及 `easyeda-agent` CLI（`easyeda` 命令，已验证 v1.18.2）
- Python 3.10+
- 可选：ImageMagick（把导出的 SVG 转 PNG 和原图对比）

## 安装

```bash
git clone https://github.com/<你的用户名>/schematic-replication ~/.claude/skills/schematic-replication
```

然后在 Claude Code 里输入 `/schematic-replication`，或直接说"帮我复刻这张原理图"。

## 目录

| 路径 | 说明 |
|---|---|
| `SKILL.md` | skill 主文件：流程、脚本说明、必知的坑 |
| `references/pitfalls.md` | easyeda CLI 踩坑详表 |
| `references/spec-example.py` | 完整示例（图 A-4 TOP221 反激电源） |
| `scripts/` | `libsearch.py` / `probe_pins.py` / `specgen.py` / `build.py` / `verify.py` / `eda.py` |

## 用法简述

```bash
export EASYEDA_PROJECT=<工程 uuid>
python -I scripts/probe_pins.py <页uuid> <device uuid>...   # 量引脚
python -I my-spec.py                                         # 生成 spec.json
python -I scripts/build.py my-spec.json place                # 必须看到 all N expected pins match
python -I scripts/build.py my-spec.json wire
```

## 许可

MIT
