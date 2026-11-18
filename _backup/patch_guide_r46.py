# -*- coding: utf-8 -*-
import io, re, shutil
P = r"H:\tool\silkworm-trajectory\docs\使用说明.html"
s = io.open(P, encoding="utf-8").read()
shutil.copyfile(P, r"H:\tool\silkworm-trajectory\_backup\guide-r45-before-r46.html")
s = s.replace("使用说明 r42", "使用说明 r46").replace("版本：<b>r45</b>", "版本：<b>r46</b>").replace("使用说明 · r45", "使用说明 · r46")
s = s.replace("</</dd>", "</dd>")

css = r"""
.screen-only{ }
.guide-tools{position:sticky;top:0;z-index:20;background:rgba(8,10,9,.97);padding:14px 0 12px;margin:20px 0 6px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.searchrow{display:flex;gap:10px;align-items:center}
#guideSearch{width:100%;min-height:46px;border:1px solid #385149;border-radius:5px;background:#111816;color:var(--ink);font:16px/1.4 inherit;padding:10px 13px;outline:none}
#guideSearch:focus{border-color:var(--acc);box-shadow:0 0 0 2px rgba(121,203,182,.14)}
.searchhint{font-size:12.5px;color:var(--dim);white-space:nowrap}
#searchStat{font-size:13px;color:var(--acc);min-height:22px;padding-top:5px}
.quick-title{font-size:14px;color:var(--warm);margin:22px 0 9px;font-weight:600}
.quick{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.quick a,.toc a{color:var(--ink);text-decoration:none}
.quick a{display:block;border:1px solid var(--line);background:#101614;padding:10px 12px;border-radius:5px;font-size:14px;line-height:1.45}
.quick a:hover,.quick a:focus{border-color:var(--acc);color:var(--acc)}
.toc{margin-top:22px;font-size:14px;color:var(--dim)}
.toc ol{columns:2;margin:10px 0 0;padding-left:24px}
.toc li{margin:4px 0;padding-left:3px}
.toc a:hover{color:var(--acc);text-decoration:underline}
.toc a.dim{opacity:.25}
.keyline{margin-top:16px;font-size:13px;color:var(--dim)}
.keyline b{color:var(--ink);font-weight:500}
#noResult{display:none;border:1px solid var(--line);padding:24px;margin:24px 0;color:var(--dim);text-align:center}
.backtop{position:fixed;right:18px;bottom:18px;z-index:15;background:#18231f;color:var(--acc);border:1px solid #385149;border-radius:5px;padding:8px 12px;font-size:13px;text-decoration:none}
.card[hidden]{display:none}
@media(max-width:640px){.quick{grid-template-columns:repeat(2,minmax(0,1fr))}.toc ol{columns:1}.searchhint{display:none}.wrap{padding:28px 18px 80px}h1{font-size:30px}}
"""
s = s.replace("@media print{", css + "\n@media print{", 1)
s = s.replace("  .card h3{break-after:avoid;page-break-after:avoid}", "  .card h3{break-after:avoid;page-break-after:avoid}\n  .screen-only,.backtop,#noResult{display:none!important}\n  .card[hidden]{display:block!important}", 1)
s = s.replace('<main class="wrap"><header class="cover">', '<main class="wrap"><header class="cover" id="guideTop">', 1)
newnav = r"""<div class="guide-tools screen-only"><div class="searchrow"><input id="guideSearch" type="search" placeholder="搜操作：删除、双击、孔洞、分组、保存、导出…" aria-label="搜索使用说明"><span class="searchhint">按 / 也能搜索</span></div><div id="searchStat" aria-live="polite"></div></div><div class="quick-title">我现在要做什么？</div><nav class="quick screen-only" aria-label="按任务查找"><a href="#s01">第一次做，从哪开始</a><a href="#s12">上传参考图，生成版式</a><a href="#s03">选中、改单元或删除</a><a href="#s04">画孔洞、缺口、壁和丝路</a><a href="#s05">把描好的蚕放进来</a><a href="#s11">框选、分组、对齐排版</a><a href="#s07">中途保存和载入工程</a><a href="#s08">导出图片、视频或母版</a><a href="#s10">遇到问题，先查这里</a></nav><div class="keyline screen-only"><b>最常用的四个动作：</b>双击＝选定 / 再双击取消　·　右键＝添加或删除　·　点空白＝取消选择　·　Ctrl+Z＝撤销</div><div class="toc screen-only"><b>全部目录</b><ol><li><a data-toc href="#s01">三分钟上手</a></li><li><a data-toc href="#s02">界面地图</a></li><li><a data-toc href="#s03">选中、编辑与删除单元</a></li><li><a data-toc href="#s04">改形状的手感</a></li><li><a data-toc href="#s05">把蚕放进来</a></li><li><a data-toc href="#s06">让丝好看、隐藏蚕或丝</a></li><li><a data-toc href="#s07">存盘与恢复</a></li><li><a data-toc href="#s08">导出视频 / 图片 / 母版</a></li><li><a data-toc href="#s09">名词表</a></li><li><a data-toc href="#s10">常见问题</a></li><li><a data-toc href="#s11">图层、分组与排版</a></li><li><a data-toc href="#s12">从参考图识别版式</a></li></ol></div><div id="noResult">没有找到这一节。换个短一点的词试试，比如“删除”“保存”或“导出”。</div>"""
s = re.sub(r'<div class="toc"><b>目录</b><ol>.*?</ol></div>', newnav, s, count=1)

num = 0
def add_id(m):
    global num
    num += 1
    return m.group(1) + ' id="s%02d"' % num + '>'
s = re.sub(r'(<section class="card(?: newpage)?")>', add_id, s)
assert num == 12, num

# 操作文案：双击与画线收尾分开说清楚
s = s.replace("<tr><td>点一个格子</td><td>进入这一格的编辑", "<tr><td><b>双击一个格子</b></td><td>选中这一块；<b>再双击已选中的格子</b>就取消选定。Shift / Ctrl + 双击可以追加选择。只是选定，不会删掉东西。</td></tr><tr><td>点一个格子</td><td>进入这一格的编辑", 1)
s = s.replace("<tr><td>双击</td><td>画线时＝收尾；编辑时＝结束这一轮的造型。</td></tr>", "<tr><td>双击</td><td><b>正在画线时＝收尾</b>；没有画线时＝选中这一块 / 再双击取消选定。</td></tr>", 1)
s = s.replace("<h3>框选：在空地拉一个框</h3>", "<h3>双击、框选：选一块或选多块</h3><p><b>双击格子</b>＝选中它；<b>再双击已选中的格子</b>＝取消选定。Shift / Ctrl + 双击可追加。要一次选多块，就在空地拉框：</p>", 1)
s = s.replace("（r39 之后的新东西）", "").replace("（r43 之后）", "")

js = r"""
<script>
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
</script><a class="backtop screen-only" href="#guideTop">返回目录</a>"""
j = s.rfind("</body>")
s = s[:j] + js + s[j:]
io.open(P, "w", encoding="utf-8").write(s)
print("guide r46", len(s), "sections", num)
