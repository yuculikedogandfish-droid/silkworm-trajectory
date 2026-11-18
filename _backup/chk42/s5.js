
/* ===== r38 拖拽上传 + 图层组（PS 式）——全部独立，不改既有函数 ===== */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const H = () => window.__studioHabitat;

  /* ---------- 1) 拖拽上传图片 ---------- */
  const drop = $('habRecDrop');
  const fileEl = $('habRecFile');
  const dropText = $('habRecDropText');
  if (drop && fileEl) {
    const hi = (on) => drop.classList.toggle('hi', !!on);
    ['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, (e) => { e.preventDefault(); e.stopPropagation(); hi(true); }));
    ['dragleave', 'dragend'].forEach(ev => drop.addEventListener(ev, (e) => { e.preventDefault(); hi(false); }));
    drop.addEventListener('drop', (e) => {
      e.preventDefault(); e.stopPropagation(); hi(false);
      const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (!f) return;
      if (!/^image\//.test(f.type)) { const n = $('habRecImageNote'); if (n) n.textContent = '这不是图片文件，换一张 png / jpg。'; return; }
      if (dropText) dropText.textContent = '已接收：' + f.name;
      const note = $('habRecImageNote');
      if (note) note.textContent = '读图中：' + f.name;
      try {
        window.__imgRec.readImage(f, () => {
          const st = window.__imgRec.state;
          if (note) note.textContent = '已载入 ' + st.img.w + '×' + st.img.h + '（缩放后）。点「识别并预览」。';
        });
      } catch (err) { if (note) note.textContent = '读图出错：' + err.message; }
    });
    // 整个框点一下也能选文件
    drop.addEventListener('click', (e) => { if (e.target !== fileEl) fileEl.click(); });
    fileEl.addEventListener('change', () => {
      const f = fileEl.files && fileEl.files[0];
      if (f && dropText) dropText.textContent = '已接收：' + f.name;
    });
  }

  /* （r39 起：图层已并入右栏统一面板，旧 r38 图层模块整段移除） */
})();

