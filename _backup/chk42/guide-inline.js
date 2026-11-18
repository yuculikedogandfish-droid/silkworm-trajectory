
(function(){
  var input=document.getElementById('guideSearch');
  var stat=document.getElementById('searchStat');
  var empty=document.getElementById('noResult');
  var cards=Array.prototype.slice.call(document.querySelectorAll('.card'));
  var links=Array.prototype.slice.call(document.querySelectorAll('[data-toc]'));
  function norm(x){return (x||'').toLowerCase().replace(/\s+/g,'');}
  function apply(){
    var q=norm(input.value),n=0;
    cards.forEach(function(c){var show=!q||norm(c.textContent).indexOf(q)>=0;c.hidden=!show;if(show)n++;});
    links.forEach(function(a){var target=document.querySelector(a.getAttribute('href'));a.classList.toggle('dim',!!q&&!!target&&target.hidden);});
    stat.textContent=q?('找到 '+n+' 节；点下面目录可直达。按 Esc 清空。'):'';
    empty.style.display=(q&&n===0)?'block':'none';
  }
  input.addEventListener('input',apply);
  document.addEventListener('keydown',function(e){
    var tag=(e.target&&e.target.tagName)||'';
    if(e.key==='/'&&!/INPUT|TEXTAREA|SELECT/.test(tag)){e.preventDefault();input.focus();}
    if(e.key==='Escape'&&document.activeElement===input){input.value='';apply();input.blur();}
  });
})();
