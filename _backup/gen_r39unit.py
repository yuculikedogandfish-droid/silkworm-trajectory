# -*- coding: utf-8 -*-
import io, os, re

P = r"H:\tool\silkworm-trajectory\docs\index.html"
s = io.open(P, encoding="utf-8").read()
i = s.find("/* ===== r39 个体与图层合并")
start = s.rfind("<script>", 0, i)
end = s.find("</script>", i) + len("</script>")
mod = s[start:end]

stub = r"""
<!doctype html><meta charset="utf-8"><body style="background:#111;color:#ddd;font:13px monospace">
<div id="habLayerTree"></div>
<div id="habAgents"></div>
<button id="habLayerGroup"></button><button id="habLayerUngroup"></button><button id="habLayerMerge"></button><button id="habLayerClear"></button>
<button data-align="l"></button><button data-align="cx"></button><button data-align="r"></button>
<button data-align="t"></button><button data-align="cy"></button><button data-align="b"></button>
<button data-align="dx"></button><button data-align="dy"></button>
<input id="habArrayN" value="3"><input id="habArrayM" value="1"><input id="habArrayGap" value="12"><button id="habArrayGo"></button>
<div id="habWorldWrap" style="position:relative;width:800px;height:400px"><canvas id="habWorld" width="800" height="400"></canvas><canvas id="habSnapOverlay" width="800" height="400"></canvas></div>
<pre id="out"></pre>
<script>
var AGENTS=[];
for (var i=0;i<3;i++) AGENTS.push({id:'wv-'+i,kind:'weave',x:i*250,y:0,w:200,h:200,seed:i,coverage:0.5,shape:'plain',custom:{walls:{},paths:{},shapes:{}}});
AGENTS.push({id:'rme',kind:'route',wormId:1,x:0,y:0});
window.__studioHabitat = {
  agents: function(){ return AGENTS; },
  view: function(){ return {s:1,cx:400,cy:200,w:800,h:400,px:function(x){return 400+x;},py:function(y){return 200+y;}}; },
  weaveEditState: function(){ return null; },
  addWeave: function(){ AGENTS.push({id:'wv-n'+(AGENTS.length),kind:'weave',x:0,y:0,w:200,h:200,seed:1,custom:{walls:{},paths:{},shapes:{}},cache:new Map()}); },
  buildWeave: function(){},
  seekTo: function(){},
};
window.__weaveHooks = { deleteUnit: function(id){ AGENTS = AGENTS.filter(function(a){return a.id!==id;}); } };
var TMPLRESULT = [];
function log(k,v){ TMPLRESULT.push(k+'='+v); }
window.prompt = function(msg,def){ return '组甲'; };
window.confirm = function(){ return true; };
</script>
"""

tail = r"""
<script>
setTimeout(function(){
  var tree=document.getElementById('habLayerTree');
  log('rows', tree.querySelectorAll('.lay-row').length);
  log('groups', tree.querySelectorAll('.lay-group').length);
  // 勾选三块织网单元
  ['wv-0','wv-1','wv-2'].forEach(function(id){
    var cb=tree.querySelector('[data-pick="'+id+'"]'); cb.checked=true; cb.dispatchEvent(new Event('change',{bubbles:true}));
  });
  document.getElementById('habLayerGroup').click();
  log('rows_after_group', tree.querySelectorAll('.lay-row').length);
  log('group_headers', tree.querySelectorAll('.lay-group[data-group]').length);
  log('stored_members', JSON.stringify((window.__layerStore.dump()||{}).member));
  // 点组名 → 全选
  var gname=tree.querySelector('[data-gsel]'); gname.click();
  log('sel_hint', (tree.querySelector('.lay-row.on')?1:0));
  // 组眼睛
  tree.querySelector('[data-geye]').click();
  log('hidden0', !!AGENTS[0].hideSilk+'/'+!!AGENTS[1].hideSilk);
  tree.querySelector('[data-geye]').click();
  // 对齐左
  ['wv-0','wv-1','wv-2'].forEach(function(id){ var cb=tree.querySelector('[data-pick="'+id+'"]'); cb.checked=true; cb.dispatchEvent(new Event('change',{bubbles:true})); });
  document.querySelector('[data-align="l"]').click();
  log('left_edges', AGENTS.slice(0,3).map(function(a){return Math.round(a.x-a.w/2);}).join(','));
  // 水平等距
  AGENTS[0].x=-200; AGENTS[1].x=0; AGENTS[2].x=200;
  document.querySelector('[data-align="dx"]').click();
  log('dx_gaps', (Math.round(AGENTS[1].x-AGENTS[0].x)+'/'+Math.round(AGENTS[2].x-AGENTS[1].x)));
  // 键盘微调
  window.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight'}));
  log('after_arrow', Math.round(AGENTS[0].x));
  // 阵列复制：只选一块
  tree.querySelector('[data-pick="wv-0"]').checked=true; tree.querySelector('[data-pick="wv-0"]').dispatchEvent(new Event('change',{bubbles:true}));
  ['wv-1','wv-2'].forEach(function(id){ var cb=tree.querySelector('[data-pick="'+id+'"]'); cb.checked=false; cb.dispatchEvent(new Event('change',{bubbles:true})); });
  var before=AGENTS.filter(function(a){return a.kind==='weave';}).length;
  document.getElementById('habArrayGo').click();
  var after=AGENTS.filter(function(a){return a.kind==='weave';}).length;
  log('array_added', after-before);
  log('array_pos', AGENTS.slice(-2).map(function(a){return Math.round(a.x)+':'+Math.round(a.y);}).join(' '));
  // 锁定后键盘不动
  var lk=tree.querySelector('[data-lock="wv-0"]'); lk.click();
  var bx=AGENTS[0].x; window.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight'}));
  log('locked_moved', Math.round(AGENTS[0].x-bx));
  // 删除一层
  var d=tree.querySelector('[data-del="wv-0"]'); var n0=AGENTS.length; d.click();
  log('delete_delta', AGENTS.length-n0);
  document.title='RESULT ' + TMPLRESULT.join(' | ');
  document.getElementById('out').textContent=TMPLRESULT.join('\n');
}, 900);
</script>
"""

html = "<!doctype html><meta charset='utf-8'><body>"
html += stub.split("<body", 1)[1].split(">", 1)[1] if False else stub
html += mod
html += tail

TMP = os.environ["TEMP"]
open(os.path.join(TMP, "r39_unit.html"), "w", encoding="utf-8").write(html)
print("harness ok")
