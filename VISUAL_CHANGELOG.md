# 视觉改动记录

只改了 `viewer/motion-preview.html` 的绘制。运动函数与备份逐字相同。

回退文件：`viewer/motion-preview.before-visual.html`。

## 蚕丝

- 新增 `SILK_LOOK`、`clamp01`、`safeUnit`、`buildRibbonVertices`、`getRibbonVertices`、`traceRibbonShape`。
- `drawRibbon()` 改为半透明暖象牙丝带：主体填充、细暗边、沿局部法线的暗侧和高光、极细次级反光。
- 半宽下限从 `2.2` 改为 `0.32`，宽度系数仍是 `0.32`。
- 去掉 `shadowBlur`。
- `line` / `silk` / `ribbon` 仍由材质下拉框切换。细线走同一投影中心线。

## 蚕体

- `drawWormBody(ctx, head, style, alpha, angle)` 接口不变。
- 身体改为贝塞尔轮廓、线性体积色、顶部柔光、七段节线（裁在身体路径内）、背部高光、头部和双眼。
- 当前蚕与残留蚕共用这个函数。残留透明度 `0.38`。
- 朝向改用投影后相邻点的屏幕切线，使俯仰和旋转时头部顺着画面上的丝。轨迹坐标没有改。

## 空间

- 网格、点亮格、活动框改为 `projectPoint()` 的四角，经 `traceProjectedRect()` 描边和填充。不再对旋转后的格子使用 `strokeRect()`。
- `screenToWorld()` 按 yaw、tilt 和透视的逆变换回到世界坐标，再做平移和缩放的逆变换。
- 画布底色改为 `#1a1c21`。格子和活动框改为低饱和暖灰，去掉高饱和青橙描边。

## 性能

- 同一相机签名下，整条 `state.route` 的投影顶点只算一次，播放中的前缀直接切片。
- 签名包含画布尺寸、平移、yaw、tilt、bounds 和头/中/尾宽度。路线对象换掉时缓存失效。
- 材质下拉框每条丝读一次，不在每个点上读 DOM。
