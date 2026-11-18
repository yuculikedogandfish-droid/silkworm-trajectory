# -*- coding: utf-8 -*-
"""QA r37：两张参考图分别识别 + 预览叠加 + 生成验收"""
import base64, json, os

HTML = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = os.environ.get('TEMP', r'C:\Users\54364\AppData\Local\Temp')
IMGS = {
    'p': r"H:\tool\silkworm-trajectory\data\projects\参考图.png",
    'h': r"H:\tool\silkworm-trajectory\data\projects\参考图横.jpeg",
}

JS = r"""
(async () => {
  const st = document.createElement('style');
  st.textContent = 'body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}';
  document.head.appendChild(st);
  await new Promise(r => setTimeout(r, 800));
  const H = window.__studioHabitat;
  const R = window.__imgRec;
  const out = document.createElement('div');
  out.style.cssText = 'position:fixed;left:12px;bottom:12px;z-index:99999;color:#ffd76a;font:12px monospace;background:#000d;padding:6px 8px;max-width:1100px;white-space:pre-wrap';
  (document.getElementById('habitat') || document.body).appendChild(out);
  const log = []; const say = t => { log.push(t); out.textContent = log.join(String.fromCharCode(10)); };
  const img = new Image();
  await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = window.__QA_IMG; });
  const maxSide = 1400;
  const k = Math.min(1, maxSide / Math.max(img.width, img.height));
  const w = Math.round(img.width * k), h = Math.round(img.height * k);
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  const cx = cv.getContext('2d'); cx.drawImage(img, 0, 0, w, h);
  const d = cx.getImageData(0, 0, w, h).data;
  const g = new Uint8Array(w * h);
  for (let i = 0, p = 0; i < g.length; i++, p += 4) g[i] = (d[p] * 0.299 + d[p + 1] * 0.587 + d[p + 2] * 0.114) | 0;
  R.state.img = { w, h, g };
  try {
    R.analyse();
    const bs = R.state.boxes, gd = R.state.grid;
    say('图 ' + img.width + 'x' + img.height + ' → 缩放 ' + w + 'x' + h);
    say('格网 ' + gd.cols + ' 列 x ' + gd.rows + ' 排 · 有丝 ' + gd.present + ' · 空位 ' + (bs.length - gd.present));
    say('格距 px ' + gd.pitchX + ' x ' + gd.pitchY + ' · 孔/咬口 ' + R.state.holes.length);
    say('岛数分布: ' + bs.filter(b => b.islands.length).map(b => b.ci + ',' + b.ri + '=' + b.islands.length).slice(0, 24).join(' '));
    if (window.__QA_APPLY) {
      R.apply(false);
      const us = H.agents().filter(a => a.kind === 'weave');
      say('生成块数=' + us.length + ' 尺寸样例=' + us.slice(0, 3).map(u => Math.round(u.w) + 'x' + Math.round(u.h)).join(' ') + ' 位置样例=' + us.slice(0, 3).map(u => Math.round(u.x) + ',' + Math.round(u.y)).join(' '));
      H.seekTo(6);
    }
  } catch (e) { say('ERR ' + e.message + ' @' + (e.stack || '').split('\n')[1]); }
})();
"""

src = open(HTML, 'r', encoding='utf-8').read()
VARIANT = [(k, v, False) for k, v in IMGS.items()] + [('p', IMGS['p'], True)]
for tag, path, doapply in VARIANT:
    b64 = base64.b64encode(open(path, 'rb').read()).decode()
    mime = 'image/png' if path.lower().endswith('png') else 'image/jpeg'
    data = 'data:%s;base64,%s' % (mime, b64)
    page = src + '<script>window.__QA_IMG=%s;window.__QA_APPLY=%s;</script><script>%s</script>' % (
        json.dumps(data), 'true' if doapply else 'false', JS)
    name = 'r37-%s%s.html' % (tag, '' if doapply else '-pv')
    open(os.path.join(TMP, name), 'w', encoding='utf-8').write(page)
    print(name)
