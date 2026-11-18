# -*- coding: utf-8 -*-
import io, base64
ROOT = r"H:\tool\silkworm-trajectory"
h = io.open(ROOT + r"\docs\index.html", encoding="utf-8").read()
h = h.replace("      paintWorld();\n    }\n    renderDrive();", "      const qpt=performance.now(); paintWorld(); if(location.hash==='#visual' && performance.now()-qpt>50) console.log('QA paint_ms='+Math.round(performance.now()-qpt));\n    }\n    renderDrive();", 1)
b64 = base64.b64encode(io.open(r"C:\Users\54364\AppData\Local\Doubao\User Data\ClipboardTemp\6b643051-5cc5-4931-936f-e2e9517b281f.png", "rb").read()).decode("ascii")
h = h.replace("<body>", "<body>\n<script>window.__errs=[];window.addEventListener('error',function(e){window.__errs.push(e.message+' @'+e.lineno);});</script>", 1)
inject = r'''
<script>var IMG="data:image/png;base64,__IMG__";</script>
<div id="qaout" style="position:fixed;left:8px;top:8px;z-index:99999;background:#000;color:#7CFFB2;font:12px monospace;padding:7px;max-width:1200px;white-space:pre-wrap">pending</div>
<script>
window.addEventListener('load', function(){
  var L=[];
  Promise.resolve().then(function(){L.push('reader='+typeof __imgRec.readDataURL);return new Promise(function(res){__imgRec.readDataURL(IMG,res);});}).then(function(){
    window.confirm=function(){return true;};
    var R=__imgRec,H=__studioHabitat;
    R.analyse();
    var st=R.state;
    if(location.hash==='#small') st.boxes=st.boxes.filter(function(b){return b.present;}).slice(0,3);
    var bm=location.hash.match(/^#b(\d)$/);
    if(bm){var bn=Number(bm[1]);st.boxes=st.boxes.filter(function(b){return b.present;}).slice(bn*5,bn*5+5);}
    var present=st.boxes.filter(function(b){return b.present;});
    L.push('preview_boxes='+st.boxes.length+' present='+present.length+' outlines='+present.filter(function(b){return b.outline&&b.outline.length>=3;}).length);
    console.log('QA before apply',present.length);
    var applyStart=performance.now();
    R.apply(true);
    L.push('apply_ms='+Math.round(performance.now()-applyStart));
    console.log('QA after apply');
    var units=function(){return H.agents().filter(function(a){return a.kind==='weave';});};
    var us=units(), sizes={};
    us.forEach(function(u){sizes[u.w+'x'+u.h]=1;});
    L.push('applied='+us.length+' sizes='+Object.keys(sizes).length+' outlines='+us.filter(function(u){return u.outline&&u.outline.length>=3;}).length);
    L.push('narrow_preserved='+us.some(function(u){return u.w<40||u.h<40;}));
    var islands=0,notches=0;
    us.forEach(function(u){var sh=u.custom&&u.custom.shapes&&u.custom.shapes['0,0'];if(sh){islands+=(sh.islands||[]).length;notches+=sh.notchPts?1:0;}});
    L.push('shape_islands='+islands+' curve_notches='+notches);
    var l=Infinity,t=Infinity,r=-Infinity,b=-Infinity;
    us.forEach(function(u){l=Math.min(l,u.x-u.w/2);r=Math.max(r,u.x+u.w/2);t=Math.min(t,u.y-u.h/2);b=Math.max(b,u.y+u.h/2);});
    console.log('QA before export');
    var doc=H.export();
    var outlineInDoc=doc.agents.filter(function(a){return a.kind==='weave'&&a.outline&&a.outline.length>=3;}).length;
    console.log('QA before import');
    H.import(doc);
    console.log('QA after import');
    if(location.hash==='#measure'){
      var mc=document.createElement('canvas');mc.width=1400;mc.height=900;
      var mg=mc.getContext('2d'),mv=H.view(),mt=performance.now();
      units().forEach(function(u){H.drawWeave(mg,u,mv);});
      console.log('QA draw31_ms='+Math.round(performance.now()-mt));
    }
    if(location.hash==='#visual'){
      var vc=document.createElement('canvas');vc.width=1200;vc.height=850;
      vc.style.cssText='position:fixed;left:0;top:0;z-index:9998;background:#070A0C';
      document.body.appendChild(vc);
      var vs=Math.min(1.5,1100/(r-l),760/(b-t)),vcx=(l+r)/2,vcy=(t+b)/2;
      var vv={s:vs,w:vc.width,h:vc.height,px:function(x){return 600+(x-vcx)*vs;},py:function(y){return 425+(y-vcy)*vs;}};
      var vg=vc.getContext('2d'),vt=performance.now();
      units().forEach(function(u){H.drawWeave(vg,u,vv);});
      console.log('QA visual_ms='+Math.round(performance.now()-vt));
    }
    L.push('project_outline_export='+outlineInDoc+' import='+units().filter(function(u){return u.outline&&u.outline.length>=3;}).length);
    L.push('post_import_sizes='+Object.keys(sizes).length);
    setTimeout(function(){L.push('jserrs='+JSON.stringify(window.__errs||[]));document.getElementById('qaout').textContent=L.join('\n');},1200);
  }).catch(function(e){document.getElementById('qaout').textContent='ERR '+e.message+' '+e.stack;});
});
</script>
'''.replace('__IMG__',b64)
j=h.rfind('</body>')
h=h[:j]+inject+'\n'+h[j:]
io.open(ROOT+r'\_backup\rec43\qa_r47.html','w',encoding='utf-8').write(h)
print('qa r47',len(h))
