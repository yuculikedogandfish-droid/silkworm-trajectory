# -*- coding: utf-8 -*-
"""蚕室 UI/蚕行为 QA：只显示 #habitat，塞一块织网单元 + 一只格内蚕，跑 400 步后截图"""
import io

src = r'H:\tool\silkworm-trajectory\docs\index.html'
dst = r'C:\Users\54364\AppData\Local\Temp\qa-hab-worm.html'

INJECT = r'''
<style>
body > *:not(#habitat){display:none !important;}
</style>
<script>
window.addEventListener('load', function () {
  try {
    var h = window.__studioHabitat;
    if (!h || !h.addWeave) return;
    h.agents.length = 0;
    h.addWeave();
    var cell = h.agents[0];
    cell.w = cell.h = 240;
    cell.u = 1;
    var route = [];
    // 竖长八字：两个环 + 各自一次自交
    for (var i = 0; i <= 120; i++) {
      var t = i / 120 * Math.PI * 2;
      route.push({ x: Math.sin(t) * 34, y: Math.cos(t) * 46 - 24 });
    }
    for (var j = 0; j <= 120; j++) {
      var t2 = j / 120 * Math.PI * 2;
      route.push({ x: Math.sin(t2) * 40, y: Math.cos(t2) * 52 + 26 });
    }
    var worm = {
      id: 'rt-1', kind: 'route', wormId: 1, color: '#d4c4a8',
      route: route, mode: 'run', bodyVisible: true,
      offX: 0, offY: 0, rot: 0, scale: 1, follow: true,
      u: 0, phase: 0, turnSign: 1, pauseUntil: 0, speedScale: 1,
      silk: [], scope: 'cell', homeUnitId: cell.id,
      x: 0, y: 0, heading: 0, travel: 0,
    };
    h.agents.push(worm);
    for (var k = 0; k < 400; k++) h.step(0.05);
    h.renderList && h.renderList();
    h.syncRoutePanel && h.syncRoutePanel();
  } catch (e) {
    document.title = 'QAERR ' + e.message;
  }
});
</script>
'''

with io.open(src, 'r', encoding='utf-8') as f:
    s = f.read()
if '</body>' not in s:
    raise SystemExit('no </body>')
s = s.replace('</body>', INJECT + '</body>')
with io.open(dst, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print(dst)
