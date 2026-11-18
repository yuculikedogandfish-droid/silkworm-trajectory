import io, os
TMP=os.environ["TEMP"]
src=io.open(r"docs\index.html",encoding="utf-8").read()
i=src.find("/* ===== r39 个体与图层合并"); st=src.rfind("<script>",0,i); en=src.find("</script>",i)+len("</script>")
mod=src[st:en]
head=r"""<!doctype html><meta charset="utf-8"><body style="margin:0;padding:10px;background:#0a0f10;width:520px">
<div style="width:270px" id="habRight"><div id="habLayerTree"></div></div><div id="habAgents"></div>
<button id="habLayerGroup"></button><button id="habLayerUngroup"></button><button id="habLayerMerge"></button><button id="habLayerClear"></button>
<div id="habWorldWrap" style="position:relative;width:1px;height:1px"><canvas id="habWorld" width="1" height="1"></canvas><canvas id="habSnapOverlay" width="1" height="1"></canvas></div>
<script>
var AGENTS=[{id:'wv-1',kind:'weave',x:0,y:0,w:240,h:240,worms:8},{id:'wv-2',kind:'weave',x:0,y:0,w:240,h:240,worms:8},{id:'wv-3',kind:'weave',x:0,y:0,w:240,h:240,worms:8}];
window.__studioHabitat={agents:function(){return AGENTS;},view:function(){return{s:1,cx:0,cy:0,w:1,h:1,px:function(x){return x;},py:function(y){return y;}};},weaveEditState:function(){return null;},addWeave:function(){},buildWeave:function(){},drawWeave:function(){}};
window.prompt=function(){return '上排两块';};
</script>"""
tail=r"""<script>
setTimeout(function(){
  var tree=document.getElementById('habLayerTree');
  ['wv-1','wv-2'].forEach(function(id){var cb=tree.querySelector('[data-pick="'+id+'"]');cb.checked=true;cb.dispatchEvent(new Event('change',{bubbles:true}));});
  document.getElementById('habLayerGroup').click();
  tree.querySelector('[data-menu="wv-1"]').click();
}, 40);
</script>"""
io.open(os.path.join(TMP,'g42_menu2.html'),'w',encoding='utf-8').write(head+mod+tail)
print('ok')
