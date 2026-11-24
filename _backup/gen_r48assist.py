import io, base64
ROOT = r'H:\tool\silkworm-trajectory'
h = io.open(ROOT + r'\docs\index.html', encoding='utf-8').read()
b64 = base64.b64encode(io.open(r'C:\Users\54364\AppData\Local\Doubao\User Data\ClipboardTemp\6b643051-5cc5-4931-936f-e2e9517b281f.png','rb').read()).decode('ascii')
h = h.replace('<body>', '<body>\n<script>window.__errs=[];window.addEventListener("error",function(e){__errs.push(e.message);});</script>', 1)
inject = r'''<script>var IMG="data:image/png;base64,__IMG__";</script>
<div id="qaout" style="position:fixed;left:8px;top:8px;z-index:99999;background:#000;color:#7CFFB2;font:13px monospace;padding:8px;white-space:pre-wrap">pending</div>
<script>
window.addEventListener('load',function(){
  var L=[];
  function ev(el,type,x,y,id){el.dispatchEvent(new PointerEvent(type,{bubbles:true,cancelable:true,clientX:x,clientY:y,pointerId:id||1,button:0,buttons:type==='pointerup'?0:1}));}
  __imgRec.readDataURL(IMG,function(){
    try{
      var R=__imgRec,H=__studioHabitat,st=R.state;
      R.analyse();
      var base=st.boxes.length;
      var target=st.boxes.filter(function(b){return b.present;})[0];
      document.getElementById('habRecRect').click();
      var ov=document.getElementById('habRecOverlay43'),r=ov.getBoundingClientRect(),v=H.view();
      function pt(wx,wy){return [r.left+v.cx+wx*v.s,r.top+v.cy+wy*v.s];}
      var a=pt(target.wx-target.w*0.3,target.wy-target.h*0.3),b=pt(target.wx+target.w*0.3,target.wy+target.h*0.3);
      ev(ov,'pointerdown',a[0],a[1]);ev(ov,'pointermove',b[0],b[1]);ev(ov,'pointerup',b[0],b[1]);
      var manual=st.selectedBox;
      L.push('rect_added='+(st.boxes.length===base+1)+' auto_layer='+(manual&&manual.layer));
      document.getElementById('habRecLayerUp').click();
      L.push('layer_up='+(manual&&manual.layer));
      document.getElementById('habRecLayerDown').click();
      L.push('layer_down='+(manual&&manual.layer));
      document.getElementById('habRecSelect').click();
      var c=pt(manual.wx,manual.wy);ev(ov,'pointerdown',c[0],c[1],2);
      L.push('select_layer_mode='+(st.selectedBox===manual));
      st.boxes=[manual];R.apply(true);
      var us=H.agents().filter(function(u){return u.kind==='weave';});
      L.push('applied='+us.length+' recLayer='+(us[0]&&us[0].recLayer)+' outline='+((us[0]&&us[0].outline)||[]).length);
      L.push('jserrs='+JSON.stringify(window.__errs));
      document.getElementById('qaout').textContent=L.join('\n');
    }catch(e){document.getElementById('qaout').textContent='ERR '+e.message+'\n'+e.stack;}
  });
});
</script>'''.replace('__IMG__',b64)
j=h.rfind('</body>')
h=h[:j]+inject+'\n'+h[j:]
io.open(ROOT+r'\_backup\rec43\qa_r48assist.html','w',encoding='utf-8').write(h)
print('assist qa',len(h))
