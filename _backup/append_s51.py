import io
P=r"PROGRESS_WEAVE_2026-11-16.md"
s=io.open(P,encoding="utf-8").read()
s+="""

## §51 r46 双击选定、批量撤销与可搜索操作者说明书（2026-11-19）
- 新增独立 r46 模块：双击未选织网单元＝只选它；双击已选单元＝从选择中移除；Shift/Ctrl 双击追加。画外框或已有未收尾草稿时仍保留原生“双击收尾”；双击选定后退出无草稿的形状编辑态。
- `deleteWeaveUnit(a, skipUndo)` 支持批量共用一次 pushUndo；新增 `__weaveHooks.deleteUnits(ids)`，r45 右键批量删除现在 Ctrl+Z 一次恢复整批。
- 性能：识别条用 ResizeObserver 替代 1.5s 布局轮询；缩略图 1.2s→2.5s 且后台不画；图层同步与自动保存后台标签页跳过（visibilitychange/beforeunload 仍保存）。
- 说明书 r46：版本/损坏标签修复；12 节锚点、9 个任务入口、22 个页内链接、关键词搜索（/ 聚焦、Esc 清空）、无结果态、返回目录；补双击与批量撤销口径。
- QA：dbl_select/deselect/shift_add/multi_remove/sole_clear 全 true；batch_delete units 3→1、one_undo_restores_all=true；empty_clears、project_export、project_import_roundtrip、feature_apis 全 true；duplicate_ids=[]、guide_links=2、recbar gap=8、jserrs=[]。说明书 search_double=s03/s04/s11，empty/clear/version 全 true，bad_targets=0。index s1–s8 与 guide JS 均 node --check 通过。
"""
io.open(P,"w",encoding="utf-8").write(s)
print("progress r46")
