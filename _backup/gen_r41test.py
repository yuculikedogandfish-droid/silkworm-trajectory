import io, os
TMP=os.environ["TEMP"]
src=io.open(r"docs\index.html",encoding="utf-8").read()
i=src.find("/* ===== r39 个体与图层合并"); st=src.rfind("<script>",0,i); en=src.find("</script>",i)+len("</script>")
mod=src[st:en]
head=r"""<!doctype html><meta charset="utf-8"><body style="margin:0;background:#101514">
<div style="width:270px" id="habRight"><div id="habLayerTree"></div></div><div id="habAgents"></div>
<button id="habLayerGroup"></button><button id="habLayerUngroup"></button><button id="habLayerMerge"></button><button id="habLayerClear"></button>
<div id="habWorldWrap" style="position:relative;width:800px;height:400px"><canvas id="habWorld" width="800" height="400" style="display:block"></canvas><canvas id="habSnapOverlay" width="800" height="400"></canvas></div>
<script>
var AGENTS=[
 {id:'wv-1',kind:'weave',x:-400,y:0,w:200,h:200,worms:8},
 {id:'wv-2',kind:'weave',x:0,y:0,w:200,h:200,worms:8},
 {id:'wv-3',kind:'weave',x:600,y:0,w:200,h:200,worms:8}];
window.__studioHabitat={agents:function(){return AGENTS;},view:function(){return{s:1,cx:400,cy:200,w:800,h:400,px:function(x){return 400+x;},py:function(y){return 200+y;}};},weaveEditState:function(){return null;},addWeave:function(){},buildWeave:function(){},
 drawWeave:function(ctx,a,v){ctx.strokeStyle='#cfd8d2';ctx.lineWidth=1;ctx.beginPath();for(var k=0;k<24;k++){ctx.moveTo(v.px(a.x-a.w/2)+((k*37)%a.w*v.s/(v.s||1)),v.py(a.y-a.h/2));ctx.lineTo(v.px(a.x-a.w/2)+((k*37)%a.w),v.py(a.y+((k*13)%a.h)-a.h/2));}ctx.stroke();}};
window.prompt=function(){return 'G';}; window.confirm=function(){return true;};
</script>"""
tail=r"""
<script>
function ev(el,type,x,y,mods){var r=el.getBoundingClientRect();el.dispatchEvent(new PointerEvent(type,{bubbles:true,clientX:r.left+x,clientY:r.top+y,button:0,shiftKey:!!(mods&&mods.shift),buttons:(type==='pointerup'?0:1),pointerId:1}));}
setTimeout(function(){
  var tree=document.getElementById('habLayerTree'), world=document.getElementById('habWorld'), res=[];
  // 1) 框选：从 (40,90) 拉到 (620,320) —— 应选中 wv-1、wv-2
  ev(world,'pointerdown',40,90);
  ev(world,'pointermove',300,200); ev(world,'pointerup',620,320);
  res.push('marquee_sel=' + tree.querySelectorAll('.lay-row.on').length);
  // 2) 等间距吸附：把 wv-3 拖到 B 右侧、与 A-B 同样的缝(200)
  ev(world,'pointerdown',1000,200);
  ev(world,'pointermove',806,200); ev(world,'pointerup',806,200);
  res.push('gap_snap_x=' + Math.round(AGENTS[2].x));
  // 3) 缩略图：应真的画出内容（非全黑）
  var th=tree.querySelector('canvas.lay-thumb'), tc=th.getContext('2d');
  var px=tc.getImageData(0,0,th.width,th.height).data, nz=0;
  for(var k=0;k<px.length;k+=4){ if(px[k]>40||px[k+1]>40||px[k+2]>40) nz++; }
  res.push('thumb_lit=' + nz);
  // 4) 上移一层：真改 agents 顺序
  var before=AGENTS.map(function(a){return a.id;}).join(',');
  tree.querySelector('[data-menu="wv-2"]').click();
  var items=document.querySelectorAll('.lay-menu button');
  items[1].click();  // 上移一层
  res.push('order=' + before + '->' + AGENTS.map(function(a){return a.id;}).join(','));
  document.title='R41 ' + res.join(' | ');
}, 900);
</script>
"""
io.open(os.path.join(TMP,'r41_test.html'),'w',encoding='utf-8').write(head+mod+tail)
print('ok')
