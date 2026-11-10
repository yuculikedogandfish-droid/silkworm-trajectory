# 蚕轨迹工作室 — GPT 交接（工程条件）

把本文件和仓库 `H:\tool\silkworm-trajectory` 交给下一个模型。以包含本文件的那次提交为准。

打开 `editor/蚕轨迹描图器.html`。它已经把预览嵌在右侧，不要再拆成两个要分别打开的页面。

## 必须遵守

- 单文件离线 HTML，原生 JS。不要引入构建、框架或外部图片。
- 三份页面必须保持字节级一致：`editor/蚕轨迹描图器.html`（先改这份的描图部分）、`editor/silkworm-tracer.html`、`docs/index.html`。
- 预览的源文件是 `viewer/motion-preview.html`。改完预览后，要把整份 HTML 转义后写进描图器的 iframe `srcdoc`（`&` → `&amp;`，`"` → `&quot;`），再把描图器复制到另外两份。`srcdoc` 里的 `</script>` 不能拿去当描图器脚本的结尾。
- 不要改运动函数：`joinStrokeGaps`、`stepLaw`、`driftReplay`、`rebuildRoute`、`mulberry32`、`perturbPoints`、`tick`、`scrubU`。不要改 `u`、种子、邻格规则、循环语义。
- 不要改预览投影：`projectPoint`、`worldToScreen`、`screenToWorld`。倾角 0 是真正的俯视。
- 蚕的画法在 `viewer/motion-preview.html` 的 `SILK_LOOK` 到 `drawWormHead()`。蚕室有自己的 `drawHabitatWorm`，不要让它去调用预览的 `drawWormBody`。
- 默认描线是均匀 0.2、白色 `#ffffff`、材质 `line`。新活动框是 1.5×1.5 格，有编号，可拖动，拖白点改大小。点/秒上限是 120。

## 实验条件（这次要保住的功能）

描图器侧栏最上方和预览侧栏最上方都有同一组可填字段：

| 控件 | id | 含义 |
|---|---|---|
| 记录时间 | `condTime` | `datetime-local`，实验当时，不是保存文件的时刻 |
| 填当前时间 | `fillConditionNow()` | 把本机现在的年月日时分写入记录时间 |
| 常用条件 | `condPreset` | 可选项：手填、`25,65`、`22,70`、`28,60`、`30,55`。选中只负责填温度和湿度，之后仍可改数字 |
| 温度 °C | `condTemp` | 数字，可空，步进 0.1 |
| 湿度 % | `condHum` | 数字，可空，0–100 |
| 摘要 | `condStat` | 载入后给人看的一句话 |

任一侧改动都会用 `postMessage` 同步到另一侧，类型是 `silkworm-studio/conditions`，载荷 `{ conditions }`。写入输入框时用 `applyingConditions` 挡住回传，避免两边互相刷。程序设置 `input.value` 不会触发 `input` 事件。

载入工程后，两边的摘要都必须变成文件里的那一句，例如 `2026-11-10 20:19 · 25 °C · 湿度 65%`。旧工程没有 `conditions` 时，描图器清空这三个框，不要沿用上一次手填的值。只载入轨迹 JSON、不是工作室工程时，预览不要清空用户已经填的条件。

## 工程文件

`schema` 固定为 `silkworm-studio/project`，`projectVersion` 仍是 3。条件是新增的可选字段，不要因为旧文件没有它就拒绝载入。

```javascript
{
  schema: 'silkworm-studio/project',
  projectVersion: 3,
  savedAt: '2026-11-10T12:19:00.000Z', // 保存动作的 UTC 时间，机器写
  conditions: {
    recordedAt: '2026-11-10T20:19',    // 用户填的实验当地时间，可 null
    temperatureC: 25,                  // 可 null
    humidity: 65                       // 百分数，可 null
  },
  calibration, worms, activeId, strokeOpts, bridge,
  segments, segmentIndex, maxWormTab, videoFps, videoFileName,
  preview: { /* 播放、视角、轨迹、点亮格、平移 */ },
  habitat: { /* 蚕室演示，见下 */ }
}
```

两边的按钮：

- 描图器：`saveProject` / `loadProject`，文件框 `#fileProject`
- 预览：`saveStudioProject` / `loadStudioProject`，文件框 `#fileStudio`

描图器保存时先读自己的 `conditions`。只有描图器三个框都空、而 iframe 回传的条件有值时，才采用预览的条件。预览保存时用预览框里的值。描图器向 iframe 要数据的消息是 `silkworm-studio/export-request`；iframe 回答 `silkworm-studio/export`，里面带 `preview`、`habitat`、`conditions`。载入时父页发送 `silkworm-studio/import`，可以同时带这三项。

视频字节不进工程，只记录 `videoFileName`。打开后要提示用户重新载入该文件。

## 不要和蚕室温湿度混在一起

蚕室在预览页下半部分 `#habitat`。`#habTemp`、`#habHum` 和 `habitat.tempC`、`habitat.humidity` 只驱动演示模型 `habitat-demo-0.1`。它们不是实验记录。保存时它们留在 `habitat` 对象里。不要在用户没操作的情况下把滑杆抄进 `conditions`，也不要让 `conditions` 去改蚕的速度或停顿。

`window.__studioHabitat.export()` / `import()` 继续只管蚕室。

## 改预览后如何嵌回描图器

在仓库根目录用 Node 处理，不要用会碰到 `srcdoc` 里第一个 `</script>` 的整文件替换。

```javascript
const fs = require('fs');
const path = require('path');
const root = 'H:/tool/silkworm-trajectory';
const preview = fs.readFileSync(root + '/viewer/motion-preview.html', 'utf8').replace(/\r\n/g, '\n');
const srcdoc = preview.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
const file = root + '/editor/蚕轨迹描图器.html';
let html = fs.readFileSync(file, 'utf8').replace(/\r\n/g, '\n');
const start = html.indexOf('srcdoc="');
const end = html.indexOf('"></iframe>');
html = html.slice(0, start + 8) + srcdoc + html.slice(end);
fs.writeFileSync(file, html);
fs.copyFileSync(file, root + '/editor/silkworm-tracer.html');
fs.copyFileSync(file, root + '/docs/index.html');
```

然后对 `viewer/motion-preview.html` 里的两段脚本，以及描图器最后一个 `<script>`（iframe 之后那一段）做 `node --check`。

## 建议的回归

1. 描图器把时间填成一个容易认出的值，温度 22，湿度 70。右侧预览同一组数字跟着变。
2. 从描图器保存，再打开。摘要是这组条件，轨迹和活动框还在。
3. 只打开 `viewer/motion-preview.html`，手填另一组条件并保存。用描图器打开该文件后，侧栏显示预览里的条件。
4. 改蚕室滑杆再保存。重新打开后滑杆恢复，但 `conditions` 仍是用户填的实验条件。
5. 打开一份没有 `conditions` 的旧工程。三个框被清空，蚕和标定仍在。
