# 嘉立创EDA 复刻时的坑（easyeda-agent v1.18.x，EDA 4.1.105）

## 文档与位号
- 同一个 Schematic 下所有页共享位号空间；`--designator R1` 或 modify 成已存在的位号会被自动改成下一个空号（R20、T2）。多张原图要用原图位号 → 每张图 `board new` 建独立原理图（会附带一个空 PCB）。
- 原图的 "Q?" 不能作位号，用最接近的编号并在注释里说明。
- `sch page-rename` 对新建页可能失败，页名留给用户手改即可。

## 放置
- 本 EDA 会话中放过、后来**所有实例都删掉**的器件，再次 `sch place` 会超时（connector did not respond）。工程里仍有实例的器件可以继续放。处理：换同值的另一个 LCSC 料号；试放件留着最后挪用；重画时先挪动旧元件（`sch modify --patch {"x","y","rotation","designator"}`），不要删了再放。
- 超时不代表没放上：先 `sch list` 查坐标/位号，再决定是否重放，避免出现自动编号的重复件（R1 被抢号）。
- 旋转约定：`sch place --rotation 90` 把左引脚转到上方；`sch modify --rotation` 和读回值用相反约定（place 90 = modify 270，0/180 相同）。带镜像时 EDA 先旋转再镜像。
- 不同料号的同类器件引脚定义可能不同（三极管 E/B/C 编号、LED 的 A/K 在哪边、0805 电容是否竖放），换料后必须重新核对引脚偏移。

## 连线
- 几何守卫：与引脚相连的第一段导线必须沿引脚外伸方向；穿过元件本体会被拒。
- 引脚坐标可能是 294.99999 或 401 这类非整网格值，导线端点要用读回的精确值，否则差一点接不上（表现为该脚网络为空）。
- 偶发 "create failed!"：未创建，可安全重试。
- `sch wire --net X` 会在线上显示网络名文字，复刻时不要给导线指定网络名。
- 交叉线没有端点就不连接（与原图"无连接点交叉"一致）；T 形连接要把主线在交点处拆段。
- `sch group-move` 不支持多段导线；整体平移 = 逐个 modify 元件 + 删线重画。

## 标识与端口
- `sch connect --pin ... --kind net_port_in` 生成的输入端口有时箭头朝向导线一侧；输出端口（out/bi）名字默认隐藏。出图检查：方向反的端口删掉（`prim-delete --no-cascade` 保留短线）后用 `sch netflag --kind ... --x --y --rotation` 原位重放（specgen 的 `g.port()`），名字用 `sch text create` 补。
- netflag 的 rotation 也有约定差异：竖直方向的端口，读回 90 对应输入 270；先放一个、出图确认再批量放。
- 电源符号（power）偶尔无法放置，改用 net_label 同名标注。
- 接地符号 `gnd` 可用 connect 放；侧放接地（原图横着画的地）用 `--direction left/right`。

## 共享窗口
- 多个会话/Agent 共用一个 EDA 窗口时，未加 `--doc` 的写入会落到"当前激活页"。所有写入加 `--doc`，读完/写完切回对方的页面；大规模重画前让用户停掉其他会话。
- 若出现多个窗口（网页版打开了同名副本），所有命令加 `--project <工程uuid>` 定向。

## 出图核对
- `sch export-image --format png` 在页面被别人切走时会导出错页；用 svg + `--doc` 更稳，再用 ImageMagick 转 PNG（中文缺字体会显示方块，不影响 EDA 内显示）。
- 部分库器件位号会显示 "R1.1"（多部件符号），网表位号仍是 R1；要去掉只能换料号。
