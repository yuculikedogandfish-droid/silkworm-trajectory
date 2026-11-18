p = r"_backup\build_guide_r34.py"
s = open(p, encoding="utf-8").read()
s = s.replace("版本：<b>r35</b>", "版本：<b>r36</b>")
s = s.replace("使用说明 r35</title>", "使用说明 r36</title>")
s = s.replace("使用说明 · r35", "使用说明 · r36")
s = s.replace("格内右键菜单：添加孔洞 / 添加缺口 / 添加壁 / 添加丝路 / 重设整块外框 / 清掉形状 / 退出编辑。",
              "格内右键菜单：添加孔洞 / 添加缺口 / 重画缺口 / 添加壁 / 添加丝路 / 重设外框 / 清除形状 / 删除这一块织网单元 / 退出编辑。")
open(p, "w", encoding="utf-8").write(s)
print("r36 caption/version ok")
