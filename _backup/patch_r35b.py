# -*- coding: utf-8 -*-
"""r35 剩余：孔洞不限大小 / 右键添加缺口立刻出现 + 重画入口 / 文案"""
import io

P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(P, encoding="utf-8").read()


def rep(old, new, cnt=1):
    global s
    n = s.count(old)
    assert n == cnt, (n, old[:90])
    s = s.replace(old, new)


rep("""      isl.r = Math.max(12, Math.min(Math.min(a.w, a.h) * 0.45, Math.hypot(p.x - ox - isl.cx, p.y - oy - isl.cy)));""",
"""      // 孔洞大小不限：只保证不把整格吃干净（留 1% 边），要多大拉多大
      isl.r = Math.max(6, Math.min(Math.min(a.w, a.h) * 0.99, Math.hypot(p.x - ox - isl.cx, p.y - oy - isl.cy)));""")

rep("""      { label: '添加缺口（在格内点几下围一圈）', run: () => {
          pushUndo();
          const sh = ensureShapeOverride(a, e.ix, e.iy);
          delete sh.notchPts; delete sh.notch;
          if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
          weaveCellContent(a, e.ix, e.iy);
          setWeaveTool('notch');
          e.mode = 'notch'; e.drafts = {};
          syncEditNote();
          hint('在格内连点几下围出形状，双击收尾（至少 3 点）。');
        } },""",
"""      { label: '添加缺口（放在这一点）', run: () => {
          pushUndo();
          const sh = ensureShapeOverride(a, e.ix, e.iy);
          // 立刻给一个看得见的缺口，再让你拖点改形（不是"点了没反应"）
          const rr = Math.max(40, Math.min(a.w, a.h) * 0.2);
          const pts0 = [];
          for (let i = 0; i < 6; i++) {
            const ang = (Math.PI * 2 / 6) * i - Math.PI / 2;
            pts0.push({ x: lx + Math.cos(ang) * rr * 1.08, y: ly + Math.sin(ang) * rr });
          }
          sh.notchPts = pts0;
          if (sh.notch) delete sh.notch;
          if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
          weaveCellContent(a, e.ix, e.iy);
          setWeaveTool('notch');
          syncEditNote();
          toast('缺口已经放在你点的地方：拖白点改形状，点线上就加锚点，右键可删。', 'ok');
        } },
      { label: '重画缺口（点几下围一圈）', run: () => {
          pushUndo();
          const sh = ensureShapeOverride(a, e.ix, e.iy);
          delete sh.notchPts; delete sh.notch;
          if (a.cache && a.cache.delete) a.cache.delete(e.ix + ',' + e.iy);
          weaveCellContent(a, e.ix, e.iy);
          setWeaveTool('notch');
          e.mode = 'notch'; e.drafts = {};
          syncEditNote();
          hint('在格内连点几下围出形状，双击收尾（至少 3 点）。');
        } },""")

rep("""    notch: '点几下围一圈＝缺口（画的时候就是光滑曲线）· 双击收尾 · 拖白点挪锚点 · 点在线上就地加锚点 · 拖边小方点也加锚点 · 右键＝菜单',""",
"""    notch: '拖白点改缺口形状 · 点在线上＝就地加锚点 · 右键＝删点/删整个缺口 · 想重新围一圈：右键菜单「重画缺口」',""")

io.open(P, "w", encoding="utf-8").write(s)
print("r35 rest patched")
