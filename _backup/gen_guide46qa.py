# -*- coding: utf-8 -*-
import io
ROOT = r"H:\tool\silkworm-trajectory"
s = io.open(ROOT + r"\docs\使用说明.html", encoding="utf-8").read()
qa = r"""
<div id="gqa" style="position:fixed;left:8px;bottom:8px;z-index:9999;background:#000;color:#7CFFB2;font:12px monospace;padding:6px;white-space:pre-wrap">pending</div>
<script>
window.addEventListener('load',function(){
  var L=[];
  var cards=Array.prototype.slice.call(document.querySelectorAll('.card'));
  var links=Array.prototype.slice.call(document.querySelectorAll('a[href^="#"]'));
  var bad=links.filter(function(a){return !document.querySelector(a.getAttribute('href'));});
  L.push('sections='+cards.length+' anchors='+links.length+' bad_targets='+bad.length);
  var inp=document.getElementById('guideSearch');
  inp.value='双击';inp.dispatchEvent(new Event('input',{bubbles:true}));
  var vis=cards.filter(function(c){return !c.hidden;}).map(function(c){return c.id;});
  L.push('search_double='+vis.join(','));
  inp.value='不存在的词xyz';inp.dispatchEvent(new Event('input',{bubbles:true}));
  L.push('empty_state='+((cards.filter(function(c){return !c.hidden;}).length===0)&&document.getElementById('noResult').style.display==='block'));
  inp.value='';inp.dispatchEvent(new Event('input',{bubbles:true}));
  L.push('clear_restores='+(cards.filter(function(c){return !c.hidden;}).length===12));
  L.push('version_r47='+document.title.includes('r47'));
  inp.value='外轮廓';inp.dispatchEvent(new Event('input',{bubbles:true}));
  L.push('search_outline='+cards.filter(function(c){return !c.hidden;}).map(function(c){return c.id;}).join(','));
  document.getElementById('gqa').textContent=L.join('\n');
});
</script>
"""
j=s.rfind("</body>")
s=s[:j]+qa+s[j:]
io.open(ROOT+r"\_backup\rec43\guide_qa47.html","w",encoding="utf-8").write(s)
print("guide qa")
