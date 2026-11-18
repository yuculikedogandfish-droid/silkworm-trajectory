# -*- coding: utf-8 -*-
"""r42 说明书配图：同步注入版（避免虚拟时间与异步等待互卡）"""
import io, os, tempfile

SRC = r"H:\tool\silkworm-trajectory\docs\index.html"
TMP = tempfile.gettempdir()

BASE = r"""
window.addEventListener('load', function(){
  var st=document.createElement('style');
  st.textContent='body > *:not(#habitat):not(#habCtxMenu):not(script):not(style){display:none}';
  document.head.appendChild(st);
  var H=window.__studioHabitat;
  var mk=function(x,y){H.addWeave({}); var l=H.agents().filter(function(a){return a.kind==='weave';}); var u=l[l.length-1];
    u.w=240;u.h=240;u.tileField=false;u.x=x;u.y=y;u.worms=8;u.coverage=0.6;
    u.custom={walls:{},paths:{},shapes:{'0,0':{notch:null,islands:[{cx:0,cy:0,r:62}]}}};
    if(u.cache&&u.cache.clear)u.cache.clear(); H.buildWeave(u); return u;};
  window.__A=mk(-250,-60); window.__B=mk(20,-60); window.__C=mk(290,-60);
  window.__layerStore.load({groups:[{id:'g1',name:'上排两块',open:true}],member:{'wv-1':'g1','wv-2':'g1'},order:[]});
  H.seekTo(6);
  window.__scr=function(wx,wy){var v=H.view(), w=document.getElementById('habWorld'), r=w.getBoundingClientRect();
    return {x:r.left+v.px(wx)*(r.width/w.width), y:r.top+v.py(wy)*(r.height/w.height)};};
  window.__pe=function(type,wx,wy){var p=window.__scr(wx,wy), el=document.getElementById('habWorld');
    el.dispatchEvent(new PointerEvent(type,{bubbles:true,clientX:p.x,clientY:p.y,button:0,buttons:(type==='pointerup'?0:1),pointerId:1}));};
  setTimeout(function(){ try{ if(window.__more) window.__more(); }catch(e){ document.title='ERR '+e.message; } }, 80);
});
"""

def page(name, more):
    html = io.open(SRC, encoding="utf-8").read()
    js = "<script>\nwindow.__more=function(){\n" + more + "\n};\n" + BASE + "\n</script>"
    io.open(os.path.join(TMP, name), "w", encoding="utf-8").write(html + js)

page("g42_layers.html", "")
page("g42_menu.html", "var b=document.querySelector('#habLayerTree [data-menu=\"wv-1\"]'); if(b) b.click();")
page("g42_marquee.html", "window.__pe('pointerdown',-420,-210); window.__pe('pointermove',-120,-40); window.__pe('pointermove',160,150);")
page("g42_snap.html", "window.__pe('pointerdown',window.__C.x,window.__C.y); window.__pe('pointermove',window.__C.x+6,-54);")
print("sync pages ok")
