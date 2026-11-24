# -*- coding: utf-8 -*-
"""r49b：说明书 FAQ 补「重叠单元命中 / 拖动瞬移」两条"""
import io

P = r'H:\tool\silkworm-trajectory\docs\使用说明.html'
s = io.open(P, encoding='utf-8').read()
n0 = len(s)

anchor = '</dl></section><section class="card newpage" id="s11">'
assert anchor in s, 'anchor missing'

add = (
    '<dt>两块叠在一起，点上面那块却选中下面那块？</dt>'
    '<dd>旧版是“数组里第一块算命中”，谁先放谁抢点。现在的规则：'
    '<b>点在丝线上更近的那块优先</b>，其次<b>按上层（后放的在上）</b>；'
    '点只落在包围盒里、附近没有丝时，也按上层算。'
    '<b>锁定的层不再参与画布点击</b>——它不会挡住下面的块，要改它就到右侧图层列表点它再解锁。</dd>'
    '<dt>按住一大块拖，块会“跳”到光标下面？</dt>'
    '<dd>以前拖动是把块中心吸到光标，抓边缘就会瞬移半格。现在改成<b>按位移拖动</b>：'
    '抓哪儿就从哪儿平移，松手位置 = 你看到的位移。</dd>'
    '<dt>正在“编辑这一格”，想顺手拖另一块？</dt>'
    '<dd>直接按住拖就行：<b>点一下</b>会切到那一块的编辑，<b>按住拖动</b>就把那一块挪走，不用先退出再选。</dd>'
)

s = s.replace(anchor, add + anchor, 1)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('len', n0, '->', len(s))
