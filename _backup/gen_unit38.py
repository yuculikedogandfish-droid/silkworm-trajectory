import io, os, re
TMP = os.environ["TEMP"]
src = io.open(r"docs\index.html", encoding="utf-8").read()
# 抽出 r38 模块
m = "/* ===== r38 拖拽上传"
i = src.find(m); start = src.rfind("<script>", 0, i); end = src.find("</script>", i)
mod = src[start+len("<script>"):end]

harness = """<!doctype html><html><head><meta charset="utf-8"><style>
body{background:#111;color:#ddd;font:12px sans-serif}
</style></head><body>
<div id="habRecDrop"><input type="file" id="habRecFile" hidden><span id="habRecDropText">drop</span></div>
<div id="habRecImageNote"></div>
<div id="habAgents"></div>
<button id="habLayerGroup">编组所选</button><button id="habLayerUngroup">解散组</button><button id="habLayerClear">全部展开</button>
<div id="habLayerTree"></div>
<pre id="out"></pre>
<script>
window.__studioHabitat = { agents: () => window.__AGENTS };
window.__AGENTS = [
  { id: 'wv-1', kind: 'weave', hideSilk: false },
  { id: 'wv-2', kind: 'weave', hideSilk: false },
  { id: 'wv-3', kind: 'weave', hideSilk: false }
];
</script>
<script>%s</script>
<script>
const log = [];
const tree = document.getElementById('habLayerTree');
log.push('rows=' + tree.querySelectorAll('.lay-row').length);
const boxes = tree.querySelectorAll('input[data-pick]');
boxes[0].checked = true; boxes[0].dispatchEvent(new Event('change', { bubbles: true }));
boxes[1].checked = true; boxes[1].dispatchEvent(new Event('change', { bubbles: true }));
window.prompt = () => '测试组'; window.alert = (m) => log.push('ALERT:' + m);
document.getElementById('habLayerGroup').click();
log.push('groups=' + tree.querySelectorAll('.lay-group[data-group]').length);
log.push('rows2=' + tree.querySelectorAll('.lay-row').length);
log.push('LS=' + (localStorage.getItem('silkworm-habitat-layer-groups/v1') || 'none').slice(0, 80));
// 眼睛：关掉组
document.querySelector('button[data-geye]').click();
log.push('hidden=' + window.__AGENTS.map(a => (a.hideSilk ? 1 : 0)).join(''));
// 点击层名应触发对应卡片点击
log.push('eyeText=' + document.querySelector('button[data-geye]').textContent);
document.getElementById('out').textContent = log.join('\\n');
</script>
</body></html>""" % mod
io.open(os.path.join(TMP, 'r38-unit.html'), 'w', encoding='utf-8').write(harness)
print('harness ok', len(mod))
