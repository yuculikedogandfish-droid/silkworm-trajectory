p = r"docs\index.html"
s = open(p, encoding="utf-8").read()
anchor = '.hab-tools[aria-disabled="true"] { opacity: .45; pointer-events: none; }'
i = s.index(anchor)
j = s.index('</style>', i)
# 第一处 </style> 就是被误插进去的那个：删掉它（后面真正的 </style> 保留）
assert j - i < 900, j - i
s = s[:j] + s[j + len('</style>'):]
open(p, "w", encoding="utf-8").write(s)
print('removed stray </style> at', j)
