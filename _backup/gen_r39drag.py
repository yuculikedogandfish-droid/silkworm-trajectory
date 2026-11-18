import io, os
TMP=os.environ["TEMP"]
src=io.open(r"docs\index.html",encoding="utf-8").read()
i=src.find("/* ===== r39 个体与图层合并"); st=src.rfind("<script>",0,i); en=src.find("</script>",i)+len("</script>")
mod=src[st:en]
head=r"""<!doctype html><meta charset="utf-8"><body style="margin:0">
<div id="habLayerTree"></div><div id="habAgents"></div>
<button id="habLayerGroup"></button><button id="habLayerUngroup"></button><button id="habLayerMerge"></button><button id="habLayerClear"></button>
<div id="habWorldWrap" style="position:relative;width:800px;height:400px"><canvas id="habWorld" width="800" height="400" style="display:block"></canvas><canvas id="habSnapOverlay" width="800" height="400"></canvas></div>
<pre id="out"></pre>
<script>
var AGENTS=[{id:'wv-1',kind:'weave',x:-200,y:0,w:200,h:200},{id:'wv-2',kind:'weave',x:0,y:0,w:200,h:200}];
window.__studioHabitat={agents:function(){return AGENTS;},view:function(){return{s:1,cx:400,cy:200,w:800,h:400,px:function(x){return 400+x;},py:function(y){return 200+y;}};},weaveEditState:function(){return null;},addWeave:function(){},buildWeave:function(){}};
window.prompt=function(){return 'G';};
</script>"""
tail=r"""
<script>
function ev(el,type,x,y){var r=el.getBoundingClientRect();el.dispatchEvent(new PointerEvent(type,{bubbles:true,clientX:r.left+x,clientY:r.top+y,button:0,buttons:(type==='pointerup'?0:1),pointerId:1}));}
setTimeout(function(){
  var tree=document.getElementById('habLayerTree'), world=document.getElementById('habWorld');
  var res=[];
  ['wv-1','wv-2'].forEach(function(id){var cb=tree.querySelector('[data-pick="'+id+'"]');cb.checked=true;cb.dispatchEvent(new Event('change',{bubbles:true}));});
  document.getElementById('habLayerGroup').click();
  // 在 wv-1 中心按下，向右拖 30 / 下 10
  ev(world,'pointerdown',200,200);
  ev(world,'pointermove',230,210); ev(world,'pointermove',230,210);
  res.push('drag=' + Math.round(AGENTS[0].x) + ',' + Math.round(AGENTS[1].x) + ',' + Math.round(AGENTS[0].y));
  ev(world,'pointerup',230,210);
  // 再拖到让左缘贴到另一块中心（0）：左缘应吸附到 0
  ev(world,'pointerdown',230,210);
  ev(world,'pointermove',495,210);
  ev(world,'pointerup',520,210);
  res.push('snap_left=' + Math.round(AGENTS[0].x-AGENTS[0].w/2));
  document.title='DRAG ' + res.join(' | ');
}, 900);
</script>
"""
io.open(os.path.join(TMP,'r39_drag.html'),'w',encoding='utf-8').write(head+mod+tail)
print('ok')



