p = r"_backup\gen_r31_qa.py"
s = open(p, encoding="utf-8").read()
s = s.replace("""  us.forEach(u => { u.w = 800; u.h = 800; u.x = 0; u.y = 0; u.tileField = false; });""",
"""  us.forEach(u => { u.w = 800; u.h = 800; u.x = 0; u.y = 0; u.tileField = false; u.shape = 'plain'; u.seed = 2026; });""")
s = s.replace("""      button: 0, buttons: 1, bubbles: true, pointerId: 1, isPrimary: true,
    }));
  };""",
"""      button: 0, buttons: 1, bubbles: true, pointerId: 1, isPrimary: true,
    }));
    cv.dispatchEvent(new PointerEvent('pointerup', {
      clientX: r.left + v.px(wx), clientY: r.top + v.py(wy),
      button: 0, buttons: 0, bubbles: true, pointerId: 1, isPrimary: true,
    }));
  };""")
open(p, "w", encoding="utf-8").write(s)
print('qa2 ok')
