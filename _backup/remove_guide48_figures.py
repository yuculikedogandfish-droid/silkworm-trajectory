from pathlib import Path
import re
p=Path(r'H:\tool\silkworm-trajectory\docs\使用说明.html')
s=p.read_text(encoding='utf-8')
a=s.index('<section class="card newpage" id="s12">')
b=s.index('</section>',a)
seg=s[a:b]
seg,n=re.subn(r'<figure\b[^>]*>.*?</figure>','<div class="tip"><b>预览图例：</b>青绿实线＝将生成的光滑外轮廓；淡虚框＝位置参考；黄色＝当前选中或低置信；红色＝不生成；金圈＝圆孔；蓝色虚线＝圆弧缺口。旧版像素描边示例已移除。</div>',seg,flags=re.S)
s=s[:a]+seg+s[b:]
p.write_text(s,encoding='utf-8',newline='')
print('removed figures',n)
