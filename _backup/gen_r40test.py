import io, os
TMP=os.environ["TEMP"]
src=io.open(r"docs\index.html",encoding="utf-8").read()
i=src.find("/* ===== r39 个体与图层合并"); st=src.rfind("<script>",0,i); en=src.find("</script>",i)+len("</script>")
mod=src[st:en]
head=r"""<!doctype html><meta charset="utf-8"><body style="margin:0;background:#101514">
<div style="width:270px" id="habRight"><div id="habLayerTree"></div></div><div id="habAgents"></div>
<button id="habLayerGroup"></button><button id="habLayerUngroup"></button><button id="habLayerMerge"></button><button id="habLayerClear"></button>
<div id="habWorldWrap" style="position:relative;width:800px;height:400px"><canvas id="habWorld" width="800" height="400" style="display:block"></canvas><canvas id="habSnapOverlay" width="800" height="400"></canvas></div>
<pre id="out"></pre>
<script>
var AGENTS=[{id:'wv-1',kind:'weave',x:-200,y:0,w:200,h:200,worms:8},{id:'wv-2',kind:'weave',x:0,y:0,w:200,h:200,worms:8}];
window.__studioHabitat={agents:function(){return AGENTS;},view:function(){return{s:1,cx:400,cy:200,w:800,h:400,px:function(x){return 400+x;},py:function(y){return 200+y;}};},weaveEditState:function(){return {agentId:'wv-1'};},addWeave:function(){},buildWeave:function(){}};
window.prompt=function(){return 'G';}; window.confirm=function(){return true;};
</script>"""
tail=r"""
<script>
function ev(el,type,x,y){var r=el.getBoundingClientRect();el.dispatchEvent(new PointerEvent(type,{bubbles:true,clientX:r.left+x,clientY:r.top+y,button:0,buttons:(type==='pointerup'?0:1),pointerId:1}));}
setTimeout(function(){
  var tree=document.getElementById('habLayerTree'), world=document.getElementById('habWorld'), res=[];
  ['wv-1','wv-2'].forEach(function(id){var cb=tree.querySelector('[data-pick="'+id+'"]');cb.checked=true;cb.dispatchEvent(new Event('change',{bubbles:true}));});
  document.getElementById('habLayerGroup').click();
  res.push('thumb=' + (tree.querySelector('canvas.lay-thumb') ? 'yes' : 'no'));
  // 编辑态下从块体（避开手柄）拖：整组应一起走
  ev(world,'pointerdown',140,140);
  ev(world,'pointermove',170,150); ev(world,'pointermove',170,150);
  res.push('edit_drag=' + Math.round(AGENTS[0].x) + ',' + Math.round(AGENTS[1].x) + ',' + Math.round(AGENTS[0].y));
  ev(world,'pointerup',170,150);
  var mb=tree.querySelector('[data-menu="wv-1"]'); mb.click();
  res.push('menu_items=' + (document.querySelectorAll('.lay-menu button').length));
  document.querySelector('.lay-menu button').click(); // 锁定
  res.push('locked=' + !!AGENTS[0].locked);
  document.title='R40 ' + res.join(' | ');
}, 900);
</script>
"""
io.open(os.path.join(TMP,'r40_test.html'),'w',encoding='utf-8').write(head+mod+tail)
print('ok')
