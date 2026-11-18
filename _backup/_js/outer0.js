
// ==================== 状态 ====================
const COLORS = ["#ffffff","#5eb6a8","#d96b5a","#7a9cd6","#b678c9","#8fbf6a","#d9c25a","#6ec4d9","#c98a6e"];
const DEFAULT_STYLE = { headWidth: 0.2, midWidth: 0.2, tailWidth: 0.2, opacity: 0.95, material: 'line' };
const PROJECT_FILE_VERSION = 3;
const SCHEMA_CURVES3D = 'curves3d/v2';
const SCHEMA_MOTION = 'silkworm-motion-model/v2';
const state = {
  video: null,
  canvas: null, ctx: null,
  mode: null,           // null | 'origin' | 'scale'
  cal: { ox: null, oy: null, scale: null, p1: null },
  worms: {},
  activeId: 1,
  pointer: null,
  segments: [],
  segmentIndex: 0,
  videoFps: 30,
  videoReady: false,
  maxWormTab: 1,
  bridge: { enabled: true, tension: 0.4 },
  regionDrag: null,
  boxDrag: null,
  editHistory: {},
  _trajCache: {},
  _draw: { raf: 0, dirtyTraj: true },
  uPlay: { playing: false, frame: 0, traj: null, raf: 0, lastT: 0 },
};
const PREVIEW_STORAGE_KEY = 'SILKWORM_PREVIEW_V1';
const FRAME = 1/30;
/** 绘制时仅用于采集笔迹的最低像素步长（与最终点距无关） */
const RAW_CAPTURE_STEP = 3;

function canvasPreviewWidthScale() {
  const cw = state.canvas && state.canvas.width ? state.canvas.width : 1280;
  return Math.max(8, cw / 260);
}

function getStrokeOpts() {
  return {
    uniformSpacing: getUniformSpacing(),
    smoothPass: parseInt(document.getElementById('strokeSmooth').value, 10) || 0,
    jitter: parseFloat(document.getElementById('strokeJitter').value) || 0,
  };
}
function getUniformSpacing() {
  const el = document.getElementById('strokeUniform');
  let s = parseFloat(el && el.value);
  if (!s || s < 1) {
    const cw = state.canvas && state.canvas.width ? state.canvas.width : 1280;
    s = Math.max(8, Math.round(cw / 270));
  }
  return s;
}
function updateStrokeUI() {
  const o = getStrokeOpts();
  document.getElementById('vUniform').textContent = o.uniformSpacing.toFixed(0) + 'px';
  document.getElementById('vSmooth').textContent = String(o.smoothPass);
  document.getElementById('vJitter').textContent = String(o.jitter);
}

function suggestUniformSpacingFromVideo() {
  const v = state.video;
  if (!v || !v.videoWidth) return;
  const s = Math.max(8, Math.min(80, Math.round(v.videoWidth / 270)));
  const el = document.getElementById('strokeUniform');
  if (el) el.value = s;
  updateStrokeUI();
}

// ==================== 初始化 ====================
window.addEventListener('load', () => {
  state.canvas = document.getElementById('canvas');
  state.ctx = state.canvas.getContext('2d');
  ensureWorm(1);
  document.getElementById('fileVideo').addEventListener('change', loadVideo);
  document.getElementById('fileProject').addEventListener('change', loadProject);
  const ft = document.getElementById('fileTrack');
  if (ft) ft.addEventListener('change', importTrackingJson);
  document.addEventListener('keydown', onKey);
  const c = state.canvas;
  c.addEventListener('pointerdown', onPointerDown);
  c.addEventListener('pointermove', onPointerMove);
  c.addEventListener('pointerup', onPointerUp);
  c.addEventListener('pointercancel', onPointerUp);
  updateStrokeUI();
  state.video = document.getElementById('video');
  const v = state.video;
  v.addEventListener('timeupdate', onVideoTimeUpdate);
  v.addEventListener('loadedmetadata', onVideoReady);
  v.addEventListener('loadeddata', () => { state.videoReady = true; draw(); });
  v.addEventListener('seeked', () => draw());
  v.addEventListener('play', () => { document.getElementById('playBtn').textContent = '⏸'; });
  v.addEventListener('pause', () => { document.getElementById('playBtn').textContent = '▶'; draw(); });
  v.addEventListener('error', () => {
    alert('视频无法解码。请尝试 H.264 的 MP4，或用浏览器打开（Chrome/Edge）。');
  });
  window.addEventListener('resize', () => { resizeCanvas(); draw(); });
  renderTabs();
  syncStyleUI();
  syncBridgeUI();
  draw();
});

function ensureWorm(id) {
  if (!state.worms[id]) {
    state.worms[id] = {
      color: COLORS[(id-1) % COLORS.length],
      points: [],
      strokes: [],
      style: { ...DEFAULT_STYLE },
      behaviorBoxes: [],
      selectedBoxId: null,
      nextBoxId: 1,
      motionPattern: 'figure8',
    };
  }
  if (!state.worms[id].strokes) state.worms[id].strokes = [];
  if (!Array.isArray(state.worms[id].behaviorBoxes)) {
    const old = state.worms[id].behaviorBox;
    state.worms[id].behaviorBoxes = old && old.x0 != null
      ? [{ id: old.id || 1, x0: old.x0, y0: old.y0, x1: old.x1, y1: old.y1 }]
      : [];
    state.worms[id].nextBoxId = state.worms[id].behaviorBoxes.reduce((m, b) => Math.max(m, b.id), 0) + 1;
    state.worms[id].selectedBoxId = state.worms[id].behaviorBoxes.length
      ? state.worms[id].behaviorBoxes[state.worms[id].behaviorBoxes.length - 1].id
      : null;
  }
  syncPrimaryBox(state.worms[id]);
}

// ==================== 视频 ====================
function loadVideo(e) {
  const f = e.target.files[0]; if (!f) return;
  const v = state.video || document.getElementById('video');
  state.video = v;
  state.videoReady = false;
  if (v._blobUrl) URL.revokeObjectURL(v._blobUrl);
  v._blobUrl = URL.createObjectURL(f);
  state.videoFileName = f.name;
  v.src = v._blobUrl;
  v.load();
  e.target.value = '';
}

const WEB_DEMO_MP4 = 'https://github.com/yuculikedogandfish-droid/silkworm-trajectory/releases/download/v0.1-demo/silkworm_demo.mp4';

function resolveBundledVideoSrc() {
  const localSeg = '../data/projects/家蚕_15s/家蚕运动_段00.mp4';
  const p = location.pathname.replace(/\\/g, '/');
  if (location.protocol === 'file:' || /\/editor\//.test(p) || /蚕轨迹描图器\.html$/i.test(p)) {
    return encodeURI(localSeg);
  }
  if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
    try { return new URL('demo/silkworm_demo.mp4', location.href).href; } catch (_) { /* */ }
  }
  return WEB_DEMO_MP4;
}

function loadBundledVideo() {
  const v = state.video || document.getElementById('video');
  state.video = v;
  state.videoReady = false;
  if (v._blobUrl) { URL.revokeObjectURL(v._blobUrl); v._blobUrl = null; }
  v.src = resolveBundledVideoSrc();
  v.load();
}

function onVideoReady() {
  const v = state.video;
  if (!v || !v.duration) return;
  document.getElementById('emptyHint').style.display = 'none';
  resizeCanvas();
  const frame = estimateVideoFps(v);
  if (frame) state.videoFps = frame;
  v.pause();
  v.currentTime = 0;
  rebuildSegments();
  suggestUniformSpacingFromVideo();
  const paint = () => {
    state.videoReady = v.readyState >= 2;
    draw();
    updateTime();
    updateSegStat();
  };
  if (v.readyState >= 2) paint();
  else v.addEventListener('loadeddata', function once() {
    v.removeEventListener('loadeddata', once);
    state.videoReady = true;
    paint();
  }, { once: true });
}

function estimateVideoFps(v) {
  if (typeof v.getVideoPlaybackQuality === 'function') {
    const q = v.getVideoPlaybackQuality();
    if (q.totalVideoFrames > 10 && v.duration > 0) {
      const fps = q.totalVideoFrames / v.duration;
      if (fps > 10 && fps < 120) return Math.round(fps);
    }
  }
  return 30;
}

function rebuildSegments() {
  const v = state.video;
  if (!v || !v.duration || !isFinite(v.duration)) {
    state.segments = [];
    updateSegStat();
    return;
  }
  const len = Math.max(5, parseFloat(document.getElementById('segLength').value) || 15);
  const segs = [];
  let t = 0, i = 0;
  while (t < v.duration - 0.01) {
    segs.push({ index: i, start: t, end: Math.min(t + len, v.duration) });
    t += len;
    i++;
  }
  if (!segs.length) segs.push({ index: 0, start: 0, end: v.duration });
  state.segments = segs;
  if (state.segmentIndex >= segs.length) state.segmentIndex = segs.length - 1;
  goToSegment(state.segmentIndex, false);
  updateSegStat();
}

function currentSegment() {
  return state.segments[state.segmentIndex] || null;
}

function goToSegment(idx, clampTime) {
  if (!state.segments.length) return;
  state.segmentIndex = Math.max(0, Math.min(idx, state.segments.length - 1));
  const seg = currentSegment();
  const v = state.video;
  if (!v || !seg) return;
  if (clampTime !== false) {
    v.pause();
    v.currentTime = Math.max(seg.start, Math.min(v.currentTime, seg.end - 0.001));
    if (v.currentTime < seg.start) v.currentTime = seg.start;
  }
  updateSegStat();
  draw();
  updateTime();
}

function prevSegment() {
  if (state.segmentIndex > 0) {
    state.segmentIndex--;
    const seg = currentSegment();
    state.video.pause();
    state.video.currentTime = seg.start;
    updateSegStat();
    draw();
    updateTime();
  }
}

function nextSegment() {
  if (state.segmentIndex < state.segments.length - 1) {
    state.segmentIndex++;
    const seg = currentSegment();
    state.video.pause();
    state.video.currentTime = seg.start;
    updateSegStat();
    draw();
    updateTime();
  }
}

function updateSegStat() {
  const el = document.getElementById('segStat');
  const v = state.video;
  if (!v || !v.duration) { el.textContent = '未载入视频'; return; }
  const n = state.segments.length;
  const i = state.segmentIndex + 1;
  const seg = currentSegment();
  if (!seg) { el.textContent = '—'; return; }
  el.innerHTML = `共 <b>${n}</b> 段 · 当前第 <b>${i}</b> 段<br>` +
    `${seg.start.toFixed(1)}s – ${seg.end.toFixed(1)}s（全长 ${v.duration.toFixed(1)}s）`;
}

function onVideoTimeUpdate() {
  const seg = currentSegment();
  const v = state.video;
  if (seg && v && !v.paused && v.currentTime >= seg.end - 0.05) {
    v.pause();
    v.currentTime = Math.max(seg.start, seg.end - 0.034);
  }
  draw();
  updateTime();
}

function resizeCanvas() {
  const v = state.video; if (!v || !v.videoWidth) return;
  const stage = document.getElementById('stage');
  const sw = stage.clientWidth, sh = stage.clientHeight;
  const vw = v.videoWidth, vh = v.videoHeight;
  const scale = Math.min(sw/vw, sh/vh);
  state.canvas.style.width = (vw*scale)+'px';
  state.canvas.style.height = (vh*scale)+'px';
  state.canvas.width = vw; state.canvas.height = vh;
  const tC = document.getElementById('canvasTraj');
  if (tC) {
    tC.style.width = state.canvas.style.width;
    tC.style.height = state.canvas.style.height;
    tC.width = vw;
    tC.height = vh;
  }
}

// ==================== 交互 ====================
function isTextInputFocus(e) {
  const t = e.target;
  if (!t || !t.tagName) return false;
  const tag = t.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || t.isContentEditable;
}

function onKey(e) {
  if (isTextInputFocus(e)) return;
  const mod = e.ctrlKey || e.metaKey;
  if (mod && e.code === 'KeyS') {
    e.preventDefault();
    saveProject();
    return;
  }
  if (mod && e.code === 'KeyO') {
    e.preventDefault();
    document.getElementById('fileProject').click();
    return;
  }
  if (mod && e.code === 'KeyE') {
    e.preventDefault();
    exportMotionModel();
    return;
  }
  if (mod && e.code === 'KeyZ' && !e.shiftKey) {
    e.preventDefault();
    undoStroke();
    return;
  }
  if (mod && e.code === 'KeyZ' && e.shiftKey) {
    e.preventDefault();
    undoLast();
    return;
  }
  if (mod && e.code === 'KeyY') {
    e.preventDefault();
    redoEdit();
    return;
  }
  if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
  else if (e.code === 'ArrowLeft' || e.code === 'Comma') { e.preventDefault(); stepFrame(-1); }
  else if (e.code === 'ArrowRight' || e.code === 'Period') { e.preventDefault(); stepFrame(1); }
  else if (e.code === 'BracketLeft') { e.preventDefault(); prevSegment(); }
  else if (e.code === 'BracketRight') { e.preventDefault(); nextSegment(); }
  else if (!mod && e.code === 'KeyO') { e.preventDefault(); setMode('origin'); }
  else if (!mod && e.code === 'KeyL') { e.preventDefault(); setMode('scale'); }
  else if (!mod && e.code === 'KeyR') { e.preventDefault(); setMode('region'); }
  else if (!mod && e.code === 'KeyB') {
    const el = document.getElementById('bridgeStrokes');
    if (el) { el.checked = !el.checked; onBridgeUI(); }
  }
  else if (/^Digit[1-9]$/.test(e.code)) {
    const id = parseInt(e.code.slice(5), 10);
    state.activeId = id;
    ensureWorm(id);
    if (id > state.maxWormTab) state.maxWormTab = id;
    syncStyleUI();
    renderTabs();
    updateBehaviorStat();
    draw();
  } else if (e.code === 'Escape') {
    state.mode = null; hideModeBanner();
    state.regionDrag = null;
    state.boxDrag = null;
    const ban = document.getElementById('modeBanner');
    if (ban) ban.style.display = 'none';
    draw();
  }
}

function togglePlay() {
  const v = state.video; if (!v || !v.src) return;
  if (v.paused) {
    v.play().catch(() => {
      state.videoReady = true;
      draw();
    });
  } else v.pause();
}
function stepFrame(dir) {
  const v = state.video; if (!v) return;
  v.pause();
  const fps = state.videoFps || 30;
  const seg = currentSegment();
  let t = v.currentTime + dir / fps;
  if (seg) t = Math.max(seg.start, Math.min(seg.end - 0.001, t));
  else t = Math.max(0, t);
  v.currentTime = t;
  draw();
  updateTime();
}
function seekTo(val) {
  const v = state.video; if (!v || !v.duration) return;
  const seg = currentSegment();
  if (seg) {
    const span = seg.end - seg.start;
    v.currentTime = seg.start + (val / 1000) * span;
  } else {
    v.currentTime = (val / 1000) * v.duration;
  }
  draw();
  updateTime();
}
function updateTime() {
  const v = state.video; if (!v || !v.duration) return;
  const seg = currentSegment();
  if (seg) {
    const local = v.currentTime - seg.start;
    const span = seg.end - seg.start;
    document.getElementById('timeLabel').textContent =
      local.toFixed(2) + 's / ' + span.toFixed(2) + 's · 段' + (state.segmentIndex + 1);
    const ratio = span > 0 ? local / span : 0;
    document.getElementById('seekBar').value = Math.round(ratio * 1000);
  } else {
    document.getElementById('timeLabel').textContent =
      v.currentTime.toFixed(2) + 's / ' + v.duration.toFixed(2) + 's';
    document.getElementById('seekBar').value = (v.currentTime / v.duration * 1000);
  }
  updateStat();
}

function hideModeBanner() {
  const ban = document.getElementById('modeBanner');
  if (ban && !state.mode) ban.style.display = 'none';
}
function setMode(m) {
  state.mode = m;
  const hints = {
    origin: '在画面上点一下格子的交点，这里就是 (0, 0)。',
    scale: '先点格子的一个角，再点相邻角。两点距离应等于下方的毫米数（默认 10 mm = 1 cm）。',
    region: '按住拖出一个新框。松开后它会得到新编号，原来的框和丝线都还在。',
    movebox: '点中编号框后拖动可挪位置。拖白色方块可改大小。不改丝线。',
  };
  const titles = { origin: '正在设原点', scale: '正在量一格', region: '正在加一个新框', movebox: '正在挪动或缩放框' };
  document.getElementById('calHint').innerHTML = '<b>' + titles[m] + '：</b>' + hints[m];
  const ban = document.getElementById('modeBanner');
  if (ban) {
    ban.style.display = 'block';
    ban.innerHTML = '<b>' + titles[m] + '</b><br>' + hints[m] + '<br><span style="color:#8a8f99">按 Esc 取消</span>';
  }
}

function pointerToCanvas(e) {
  const rect = state.canvas.getBoundingClientRect();
  return {
    x: (e.clientX - rect.left) * (state.canvas.width / rect.width),
    y: (e.clientY - rect.top) * (state.canvas.height / rect.height),
  };
}

function onPointerDown(e) {
  if (e.button !== 0 && e.pointerType === 'mouse') return;
  const { x, y } = pointerToCanvas(e);

  if (state.mode === 'origin' || state.mode === 'scale') {
    e.preventDefault();
    handleCalPoint(x, y);
    return;
  }

  if (state.mode === 'movebox') {
    e.preventDefault();
    const hit = hitBehaviorBox(state.activeId, x, y);
    if (!hit) return;
    ensureWorm(state.activeId);
    state.worms[state.activeId].selectedBoxId = hit.id;
    syncPrimaryBox(state.worms[state.activeId]);
    state.canvas.setPointerCapture(e.pointerId);
    const handle = hitBoxHandle(hit, x, y);
    state.boxDrag = handle
      ? { id: e.pointerId, boxId: hit.id, mode: 'resize', handle, x0: hit.x0, y0: hit.y0, x1: hit.x1, y1: hit.y1 }
      : { id: e.pointerId, boxId: hit.id, mode: 'move', ox: x - hit.x0, oy: y - hit.y0 };
    updateBehaviorStat();
    draw();
    return;
  }

  if (state.mode === 'region') {
    e.preventDefault();
    const v = state.video;
    if (v) v.pause();
    state.canvas.setPointerCapture(e.pointerId);
    state.regionDrag = { id: e.pointerId, x0: x, y0: y, x1: x, y1: y };
    draw();
    return;
  }

  const v = state.video;
  if (!v || !v.src) return;
  e.preventDefault();
  v.pause();
  state.canvas.setPointerCapture(e.pointerId);
  state.pointer = {
    id: e.pointerId,
    pts: [{ x, y }],
    lastCommitted: { x, y },
    prev: null,
    lastTime: performance.now(),
    moved: false,
    t0: v.currentTime,
    dist2: 0,
    lastRaw: { x, y },
  };
}

function handleCalPoint(x, y) {
  if (state.mode === 'origin') {
    state.cal.ox = x; state.cal.oy = y;
    state.mode = null; hideModeBanner();
    document.getElementById('calHint').innerHTML = '原点已设。接下来点「量比例尺」点两个格子交点。';
    updateCalStat(); draw(); return;
  }
  if (state.mode === 'scale') {
    if (!state.cal.p1) { state.cal.p1 = {x,y}; document.getElementById('calHint').textContent = '已记录第一点，点第二点。'; }
    else {
      const p2 = {x,y};
      const distPx = Math.hypot(p2.x-state.cal.p1.x, p2.y-state.cal.p1.y);
      const mm = parseFloat(document.getElementById('scaleDist').value) || 10;
      state.cal.scale = distPx / mm;  // px per mm
      state.cal.p1 = null; state.mode = null; hideModeBanner();
      document.getElementById('calHint').innerHTML = '标定完成：<b>'+state.cal.scale.toFixed(2)+' px/mm</b>。现在可以开始描点。';
      updateCalStat();
    }
    draw(); return;
  }
}

function acceptStrokeSample(ptr, x, y, opts) {
  const d = Math.hypot(x - ptr.lastCommitted.x, y - ptr.lastCommitted.y);
  if (d < RAW_CAPTURE_STEP) return false;

  if (opts.jitter > 0 && ptr.prev) {
    const v1x = ptr.lastCommitted.x - ptr.prev.x;
    const v1y = ptr.lastCommitted.y - ptr.prev.y;
    const v2x = x - ptr.lastCommitted.x;
    const v2y = y - ptr.lastCommitted.y;
    const len1 = Math.hypot(v1x, v1y) || 1;
    const len2 = Math.hypot(v2x, v2y) || 1;
    const cos = (v1x * v2x + v1y * v2y) / (len1 * len2);
    if (d < RAW_CAPTURE_STEP * 4 && cos < -0.3 + (1 - opts.jitter / 100) * 0.5) return false;
  }

  ptr.prev = { ...ptr.lastCommitted };
  ptr.lastCommitted = { x, y };
  ptr.pts.push({ x, y });
  ptr.moved = true;
  ptr.dist2 += d * d;
  return true;
}

function onPointerMove(e) {
  const rd = state.regionDrag;
  if (rd && rd.id === e.pointerId) {
    e.preventDefault();
    const { x, y } = pointerToCanvas(e);
    rd.x1 = x;
    rd.y1 = y;
    draw();
    return;
  }
  const bd = state.boxDrag;
  if (bd && bd.id === e.pointerId) {
    e.preventDefault();
    const { x, y } = pointerToCanvas(e);
    const w = state.worms[state.activeId];
    const box = wormBoxes(w).find(b => b.id === bd.boxId);
    if (box && bd.mode === 'resize') {
      let x0 = bd.x0, y0 = bd.y0, x1 = bd.x1, y1 = bd.y1;
      if (bd.handle.indexOf('w') >= 0) x0 = x;
      if (bd.handle.indexOf('e') >= 0) x1 = x;
      if (bd.handle.indexOf('n') >= 0) y0 = y;
      if (bd.handle.indexOf('s') >= 0) y1 = y;
      if (Math.abs(x1 - x0) >= 8 && Math.abs(y1 - y0) >= 8) {
        box.x0 = x0; box.y0 = y0; box.x1 = x1; box.y1 = y1;
        syncPrimaryBox(w);
      }
    } else if (box) {
      const bw = box.x1 - box.x0, bh = box.y1 - box.y0;
      box.x0 = x - bd.ox;
      box.y0 = y - bd.oy;
      box.x1 = box.x0 + bw;
      box.y1 = box.y0 + bh;
      syncPrimaryBox(w);
    }
    draw();
    return;
  }
  const ptr = state.pointer;
  if (!ptr || ptr.id !== e.pointerId || state.mode) return;
  e.preventDefault();
  const { x, y } = pointerToCanvas(e);
  ptr.lastRaw = { x, y };
  acceptStrokeSample(ptr, x, y, getStrokeOpts());
  scheduleDraw({ traj: true });
}

function chaikinSmooth(pts, passes) {
  if (passes <= 0 || pts.length < 3) return pts.map(p => ({ ...p }));
  let cur = pts.map(p => ({ x: p.x, y: p.y }));
  for (let pass = 0; pass < passes; pass++) {
    if (cur.length < 3) break;
    const next = [cur[0]];
    for (let i = 0; i < cur.length - 1; i++) {
      const p0 = cur[i], p1 = cur[i + 1];
      next.push(
        { x: 0.75 * p0.x + 0.25 * p1.x, y: 0.75 * p0.y + 0.25 * p1.y },
        { x: 0.25 * p0.x + 0.75 * p1.x, y: 0.25 * p0.y + 0.75 * p1.y }
      );
    }
    next.push(cur[cur.length - 1]);
    cur = next;
  }
  return cur;
}

function pointAtDistance(pts, lens, d, hintFrom) {
  if (!pts.length) return { x: 0, y: 0 };
  if (d <= 0) return { x: pts[0].x, y: pts[0].y };
  const total = lens[lens.length - 1];
  if (d >= total) return { x: pts[pts.length - 1].x, y: pts[pts.length - 1].y };
  let lo = Math.max(1, hintFrom || 1);
  let hi = lens.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (lens[mid] < d) lo = mid + 1;
    else hi = mid - 1;
  }
  const j = Math.min(lo, lens.length - 1);
  const d0 = lens[j - 1], d1 = lens[j];
  const t = d1 > d0 ? (d - d0) / (d1 - d0) : 0;
  return {
    x: pts[j - 1].x + (pts[j].x - pts[j - 1].x) * t,
    y: pts[j - 1].y + (pts[j].y - pts[j - 1].y) * t,
  };
}

function dedupeConsecutivePoints(pts, eps) {
  if (pts.length < 2) return pts.map(p => ({ x: p.x, y: p.y }));
  const out = [{ x: pts[0].x, y: pts[0].y }];
  for (let i = 1; i < pts.length; i++) {
    const p = pts[i];
    const last = out[out.length - 1];
    if (Math.hypot(p.x - last.x, p.y - last.y) > eps) out.push({ x: p.x, y: p.y });
  }
  return out.length ? out : [{ x: pts[0].x, y: pts[0].y }];
}

function resampleUniform(pts, spacing) {
  const clean = dedupeConsecutivePoints(pts, spacing * 0.05);
  if (clean.length < 2) return clean.map(p => ({ x: p.x, y: p.y }));
  const { lens, total } = pathLengths(clean);
  const tailTol = spacing * 0.35;
  if (total < spacing * 0.5) {
    return [{ x: clean[0].x, y: clean[0].y }, { x: clean[clean.length - 1].x, y: clean[clean.length - 1].y }];
  }
  const out = [pointAtDistance(clean, lens, 0)];
  let d = spacing;
  let segHint = 1;
  while (d < total - tailTol) {
    out.push(pointAtDistance(clean, lens, d, segHint));
    while (segHint < lens.length - 1 && lens[segHint] < d) segHint++;
    d += spacing;
  }
  const end = { x: clean[clean.length - 1].x, y: clean[clean.length - 1].y };
  const last = out[out.length - 1];
  if (Math.hypot(end.x - last.x, end.y - last.y) > spacing * 0.2) out.push(end);
  return out;
}

function ensureEditHistory(wormId) {
  if (!state.editHistory[wormId]) state.editHistory[wormId] = { undo: [], redo: [] };
}

function cloneWormGeometry(wormId) {
  const w = state.worms[wormId];
  return {
    points: w.points.map(p => ({ ...p })),
    strokes: (w.strokes || []).map(s => ({ start: s.start, end: s.end })),
  };
}

function applyWormGeometry(wormId, snap) {
  const w = state.worms[wormId];
  w.points = snap.points.map(p => ({ ...p }));
  w.strokes = snap.strokes.map(s => ({ start: s.start, end: s.end }));
}

function pushUndoSnapshot(wormId) {
  ensureEditHistory(wormId);
  const h = state.editHistory[wormId];
  h.undo.push(cloneWormGeometry(wormId));
  if (h.undo.length > 120) h.undo.shift();
  h.redo.length = 0;
  invalidateTrajCache(wormId);
  state._draw.dirtyTraj = true;
}

function redoEdit() {
  const id = state.activeId;
  const h = state.editHistory[id];
  if (!h || !h.redo.length) return;
  h.undo.push(cloneWormGeometry(id));
  applyWormGeometry(id, h.redo.pop());
  scheduleDraw({ traj: true });
  updateStat();
  updateMotionStat();
}

function resetEditHistory(all) {
  if (all) state.editHistory = {};
  else if (state.editHistory[state.activeId]) state.editHistory[state.activeId] = { undo: [], redo: [] };
}

function isFiniteNum(n) { return typeof n === 'number' && Number.isFinite(n); }

function isCalibrated() {
  const c = state.cal;
  return !!(c && isFiniteNum(c.scale) && c.scale > 0 && isFiniteNum(c.ox) && isFiniteNum(c.oy));
}

function requireCalibration(exportLabel) {
  if (isCalibrated()) return true;
  alert(`「${exportLabel}」需要先完成标定：设原点 + 量比例尺（格边 10mm）。\n未标定时可「保存工程」保留像素坐标，或使用 SVG（视图坐标）。`);
  return false;
}

function validateWorm(w, id) {
  if (!w || !Array.isArray(w.points)) return `蚕 ${id}：缺少 points`;
  for (let i = 0; i < w.points.length; i++) {
    const p = w.points[i];
    if (!isFiniteNum(p.x) || !isFiniteNum(p.y)) return `蚕 ${id} 点 ${i} 坐标无效`;
  }
  const strokes = w.strokes || [];
  let prevEnd = -1;
  for (let si = 0; si < strokes.length; si++) {
    const s = strokes[si];
    if (!Number.isInteger(s.start) || !Number.isInteger(s.end)) return `蚕 ${id} 笔 ${si} 索引非整数`;
    if (s.start < 0 || s.end >= w.points.length || s.start > s.end) return `蚕 ${id} 笔 ${si} 区间非法`;
    if (s.start < prevEnd) return `蚕 ${id} 笔 ${si} 与前一笔画重叠`;
    prevEnd = s.end;
  }
  for (const b of (w.behaviorBoxes || [])) {
    if (![b.x0, b.y0, b.x1, b.y1].every(isFiniteNum)) return `蚕 ${id} 框 ${b.id} 无效`;
  }
  if (w.style) {
    const st = w.style;
    if (st.opacity != null && (st.opacity < 0 || st.opacity > 1)) return `蚕 ${id} 透明度越界`;
  }
  return null;
}

function validateProjectData(data) {
  if (!data || typeof data !== 'object') return '工程不是有效对象';
  if (data.calibration && data.calibration.scale != null) {
    if (!isFiniteNum(data.calibration.scale) || data.calibration.scale <= 0) return '标定 scale 无效';
  }
  if (!data.worms || typeof data.worms !== 'object') return '缺少 worms';
  for (const id of Object.keys(data.worms)) {
    const err = validateWorm(data.worms[id], id);
    if (err) return err;
  }
  if (data.activeId != null && !data.worms[data.activeId]) return '活动蚕不存在';
  return null;
}

function normalizeLoadedProject(data) {
  if (!data.worms) data.worms = { 1: { points: [], strokes: [], style: {}, color: COLORS[0] } };
  for (const id of Object.keys(data.worms)) ensureWorm(+id);
  if (!data.calibration) data.calibration = { ox: null, oy: null, scale: null, p1: null };
  return data;
}

function invalidateTrajCache(wormId) {
  if (wormId == null) state._trajCache = {};
  else delete state._trajCache[wormId];
}

function wormGeomCacheKey(w) {
  return (w.strokes || []).length + ':' + w.points.length + ':' + (w.points[w.points.length - 1] && w.points[w.points.length - 1].x);
}

function scheduleDraw(opts) {
  if (opts && opts.traj) state._draw.dirtyTraj = true;
  if (state._draw.raf) return;
  state._draw.raf = requestAnimationFrame(() => {
    state._draw.raf = 0;
    draw();
  });
}

function commitStroke(ptr) {
  const id = state.activeId;
  pushUndoSnapshot(id);
  ensureWorm(id);
  const w = state.worms[id];
  const opts = getStrokeOpts();

  if (!ptr.moved || Math.sqrt(ptr.dist2) < 4) {
    const pt = { x: ptr.pts[0].x, y: ptr.pts[0].y, t: ptr.t0 };
    w.points.push(pt);
    w.strokes.push({ start: w.points.length - 1, end: w.points.length - 1 });
    return;
  }

  let geom = chaikinSmooth(ptr.pts, opts.smoothPass);
  geom = resampleUniform(geom, opts.uniformSpacing);
  const startIdx = w.points.length;
  for (let i = 0; i < geom.length; i++) {
    const pt = { x: geom[i].x, y: geom[i].y };
    if (i === 0) pt.t = ptr.t0;
    w.points.push(pt);
  }
  w.strokes.push({ start: startIdx, end: w.points.length - 1 });
  refreshUPlayTrajectory();
  if (!document.body.classList.contains('preview-off')) pushPreviewToPane();
}

function onPointerUp(e) {
  const bd = state.boxDrag;
  if (bd && bd.id === e.pointerId) {
    if (state.canvas.hasPointerCapture(e.pointerId)) state.canvas.releasePointerCapture(e.pointerId);
    state.boxDrag = null;
    updateBehaviorStat();
    draw();
    if (!document.body.classList.contains('preview-off')) pushPreviewToPane();
    return;
  }
  const rd = state.regionDrag;
  if (rd && rd.id === e.pointerId) {
    if (state.canvas.hasPointerCapture(e.pointerId)) {
      state.canvas.releasePointerCapture(e.pointerId);
    }
    normalizeBehaviorBox(rd);
    state.regionDrag = null;
    state.mode = null; hideModeBanner();
    document.getElementById('calHint').innerHTML = '新框已加上，原来的框和丝线都还在。点「挪动选中框」可以换位置。';
    draw();
    updateBehaviorStat();
    return;
  }
  const ptr = state.pointer;
  if (!ptr || ptr.id !== e.pointerId) return;
  if (state.canvas.hasPointerCapture(e.pointerId)) {
    state.canvas.releasePointerCapture(e.pointerId);
  }
  if (!state.mode) commitStroke(ptr);
  state.pointer = null;
  draw();
  updateMotionStat();
}

function wormBoxes(w) {
  if (!w) return [];
  if (!Array.isArray(w.behaviorBoxes)) {
    w.behaviorBoxes = w.behaviorBox && w.behaviorBox.x0 != null
      ? [{ id: w.behaviorBox.id || 1, x0: w.behaviorBox.x0, y0: w.behaviorBox.y0, x1: w.behaviorBox.x1, y1: w.behaviorBox.y1 }]
      : [];
    w.nextBoxId = w.behaviorBoxes.reduce((m, b) => Math.max(m, b.id), 0) + 1;
  }
  return w.behaviorBoxes;
}

function syncPrimaryBox(w) {
  const boxes = wormBoxes(w);
  const sel = boxes.find(b => b.id === w.selectedBoxId) || boxes[boxes.length - 1] || null;
  w.selectedBoxId = sel ? sel.id : null;
  w.behaviorBox = sel ? { id: sel.id, x0: sel.x0, y0: sel.y0, x1: sel.x1, y1: sel.y1 } : null;
}

function orderedBox(b) {
  return {
    id: b.id,
    x0: Math.min(b.x0, b.x1),
    y0: Math.min(b.y0, b.y1),
    x1: Math.max(b.x0, b.x1),
    y1: Math.max(b.y0, b.y1),
  };
}

function boxHandles(b) {
  const o = orderedBox(b);
  const mx = (o.x0 + o.x1) / 2, my = (o.y0 + o.y1) / 2;
  return {
    nw: { x: o.x0, y: o.y0 }, ne: { x: o.x1, y: o.y0 },
    sw: { x: o.x0, y: o.y1 }, se: { x: o.x1, y: o.y1 },
    n: { x: mx, y: o.y0 }, s: { x: mx, y: o.y1 },
    w: { x: o.x0, y: my }, e: { x: o.x1, y: my },
  };
}

function hitBoxHandle(box, x, y) {
  const hs = boxHandles(box);
  for (const key of ['nw', 'ne', 'sw', 'se', 'n', 's', 'w', 'e']) {
    if (Math.hypot(x - hs[key].x, y - hs[key].y) <= 12) return key;
  }
  return null;
}

function hitBehaviorBox(wormId, x, y) {
  const boxes = wormBoxes(state.worms[wormId]).slice().reverse();
  return boxes.find(b => {
    const o = orderedBox(b);
    return x >= o.x0 && x <= o.x1 && y >= o.y0 && y <= o.y1;
  }) || null;
}

function addBehaviorBox(rect) {
  ensureWorm(state.activeId);
  const w = state.worms[state.activeId];
  const boxes = wormBoxes(w);
  const id = w.nextBoxId || (boxes.reduce((m, b) => Math.max(m, b.id), 0) + 1);
  w.nextBoxId = id + 1;
  boxes.push({ id, x0: rect.x0, y0: rect.y0, x1: rect.x1, y1: rect.y1 });
  w.selectedBoxId = id;
  w.motionPattern = 'figure8';
  syncPrimaryBox(w);
}

function deleteSelectedBehaviorBox() {
  const w = state.worms[state.activeId];
  if (!w || w.selectedBoxId == null) { alert('先点「挪动选中框」，再点一下要删的框。'); return; }
  if (!confirm('只删除框 ' + w.selectedBoxId + '，已描的丝线会保留。')) return;
  w.behaviorBoxes = wormBoxes(w).filter(b => b.id !== w.selectedBoxId);
  w.selectedBoxId = w.behaviorBoxes.length ? w.behaviorBoxes[w.behaviorBoxes.length - 1].id : null;
  syncPrimaryBox(w);
  updateBehaviorStat();
  draw();
  if (!document.body.classList.contains('preview-off')) pushPreviewToPane();
}

function normalizeBehaviorBox(rd) {
  const x0 = Math.min(rd.x0, rd.x1);
  const x1 = Math.max(rd.x0, rd.x1);
  const y0 = Math.min(rd.y0, rd.y1);
  const y1 = Math.max(rd.y0, rd.y1);
  if (Math.abs(x1 - x0) < 4 || Math.abs(y1 - y0) < 4) return;
  addBehaviorBox({ x0, y0, x1, y1 });
}

function behaviorBoxMetrics(box) {
  if (!box) return null;
  const wPx = Math.abs(box.x1 - box.x0);
  const hPx = Math.abs(box.y1 - box.y0);
  const cell = parseFloat(document.getElementById('scaleDist').value) || 10;
  if (!state.cal.scale) {
    return { w_px: wPx, h_px: hPx, gridW: null, gridH: null };
  }
  const wMm = wPx / state.cal.scale;
  const hMm = hPx / state.cal.scale;
  return {
    w_mm: +wMm.toFixed(2),
    h_mm: +hMm.toFixed(2),
    gridW: +(wMm / cell).toFixed(2),
    gridH: +(hMm / cell).toFixed(2),
    cell_mm: cell,
  };
}

function updateBehaviorStat() {
  const el = document.getElementById('behaviorStat');
  if (!el) return;
  const w = state.worms[state.activeId];
  const boxes = wormBoxes(w);
  if (!boxes.length) {
    el.textContent = '还没有活动框';
    return;
  }
  const sel = boxes.find(b => b.id === w.selectedBoxId) || boxes[boxes.length - 1];
  const m = behaviorBoxMetrics(sel);
  const size = m && m.gridW != null
    ? `${m.gridW}×${m.gridH} 格 · ${m.w_mm}×${m.h_mm} mm`
    : `${m.w_px.toFixed(0)}×${m.h_px.toFixed(0)} px`;
  el.innerHTML = `共 <b>${boxes.length}</b> 个框，选中 <b>${sel.id}</b><br>${size}<br>丝线不受框的新增、挪动或删除影响`;
}

function presetBehaviorBox15() {
  if (!state.cal.scale) {
    alert('请先标定比例尺（格子 1cm → 间距填 10mm）。');
    return;
  }
  const cell = parseFloat(document.getElementById('scaleDist').value) || 10;
  const cellPx = state.cal.scale * cell;
  const w = state.worms[state.activeId];
  let cx, cy;
  if (w.points.length) {
    cx = w.points.reduce((s, p) => s + p.x, 0) / w.points.length;
    cy = w.points.reduce((s, p) => s + p.y, 0) / w.points.length;
  } else if (state.cal.ox != null) {
    cx = state.cal.ox + cellPx * 0.75;
    cy = state.cal.oy - cellPx * 0.75;
  } else {
    alert('请先设原点或描一点轨迹作为中心参考。');
    return;
  }
  const bw = cellPx * 1.5;
  const bh = cellPx * 1.5;
  addBehaviorBox({ x0: cx - bw / 2, y0: cy - bh / 2, x1: cx + bw / 2, y1: cy + bh / 2 });
  updateBehaviorStat();
  draw();
}

function exportBehaviorUnits() {
  const units = [];
  for (const id of Object.keys(state.worms).map(Number).sort((a, b) => a - b)) {
    const w = state.worms[id];
    const boxes = wormBoxes(w);
    if (!boxes.length) continue;
    boxes.forEach((box) => {
      const m = behaviorBoxMetrics(box);
      units.push({
        wormId: id,
        boxId: box.id,
        pattern: w.motionPattern || 'figure8',
        box_px: { id: box.id, x0: box.x0, y0: box.y0, x1: box.x1, y1: box.y1 },
        envelope_mm: m && m.w_mm ? { width_mm: m.w_mm, height_mm: m.h_mm } : null,
        envelope_grid: m && m.gridW ? { cols: m.gridW, rows: m.gridH, cell_mm: m.cell_mm } : null,
        note: 'Activity frame; silk strokes are stored separately and are not deleted with the frame',
      });
    });
  }
  return units;
}

function undoLast() {
  const w = state.worms[state.activeId]; if (!w || !w.points.length) return;
  pushUndoSnapshot(state.activeId);
  w.points.pop();
  if (w.strokes && w.strokes.length) {
    const last = w.strokes[w.strokes.length - 1];
    if (last.end >= w.points.length) {
      if (last.start >= w.points.length) w.strokes.pop();
      else w.strokes[w.strokes.length - 1] = { ...last, end: w.points.length - 1 };
    }
  }
  scheduleDraw({ traj: true });
  updateStat();
}
function undoStroke() {
  const w = state.worms[state.activeId];
  if (!w || !w.strokes || !w.strokes.length) return undoLast();
  pushUndoSnapshot(state.activeId);
  const seg = w.strokes.pop();
  w.points.splice(seg.start, Math.max(0, seg.end - seg.start + 1));
  for (const s of w.strokes) {
    const len = seg.end - seg.start + 1;
    if (s.start > seg.end) { s.start -= len; s.end -= len; }
  }
  scheduleDraw({ traj: true });
  updateStat();
}
function clearWorm() {
  if (!confirm('清空蚕 '+state.activeId+' 的所有点？')) return;
  pushUndoSnapshot(state.activeId);
  const w = state.worms[state.activeId];
  w.points = [];
  w.strokes = [];
  draw();
}

// ==================== 样式 ====================
function updateStyle() {
  const w = state.worms[state.activeId]; if (!w) return;
  invalidateTrajCache(state.activeId);
  w.style.headWidth = parseFloat(document.getElementById('sHead').value);
  w.style.midWidth  = parseFloat(document.getElementById('sMid').value);
  w.style.tailWidth = parseFloat(document.getElementById('sTail').value);
  w.style.opacity   = parseFloat(document.getElementById('sOp').value);
  w.style.material  = document.getElementById('sMat').value;
  const colEl = document.getElementById('sColor');
  if (colEl) w.color = colEl.value;
  document.getElementById('vHead').textContent = w.style.headWidth.toFixed(2);
  document.getElementById('vMid').textContent  = w.style.midWidth.toFixed(2);
  document.getElementById('vTail').textContent = w.style.tailWidth.toFixed(2);
  document.getElementById('vOp').textContent   = w.style.opacity.toFixed(2);
  const tab = document.querySelector('.worm-tabs button.active');
  if (tab) tab.style.background = w.color;
  drawStylePreview();
  draw();
}
function syncStyleUI() {
  const w = state.worms[state.activeId]; if (!w) return;
  document.getElementById('sHead').value = w.style.headWidth;
  document.getElementById('sMid').value  = w.style.midWidth;
  document.getElementById('sTail').value = w.style.tailWidth;
  document.getElementById('sOp').value   = w.style.opacity;
  const colEl = document.getElementById('sColor');
  if (colEl) colEl.value = w.color;
  const mat = String(w.style.material || 'ribbon').toLowerCase();
  const sel = document.getElementById('sMat');
  if ([...sel.options].some(o => o.value === mat)) sel.value = mat;
  else sel.value = 'ribbon';
  document.getElementById('vHead').textContent = w.style.headWidth.toFixed(2);
  document.getElementById('vMid').textContent = w.style.midWidth.toFixed(2);
  document.getElementById('vTail').textContent = w.style.tailWidth.toFixed(2);
  document.getElementById('vOp').textContent = w.style.opacity.toFixed(2);
  drawStylePreview();
}

function drawStylePreview() {
  const cvs = document.getElementById('stylePreview');
  if (!cvs) return;
  const w = state.worms[state.activeId];
  if (!w) return;
  const ctx = cvs.getContext('2d');
  const W = cvs.width, H = cvs.height;
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#0a0b0d';
  ctx.fillRect(0, 0, W, H);
  const pts = [];
  for (let i = 0; i <= 40; i++) {
    const t = i / 40;
  const x = 12 + t * (W - 24);
  const y = H * 0.55 + Math.sin(t * Math.PI) * (H * 0.22);
    pts.push({ x, y });
  }
  ctx.save();
  drawStyledPathOnCtx(ctx, pts, w.style, w.color, null, 1.8);
  ctx.restore();
}

function bridgeSettings() {
  const el = document.getElementById('bridgeStrokes');
  const tEl = document.getElementById('bridgeTension');
  return {
    enabled: el ? el.checked : state.bridge.enabled,
    tension: tEl ? parseFloat(tEl.value) : state.bridge.tension,
  };
}

function wormBridgeEnabled(w) {
  if (!bridgeSettings().enabled) return false;
  if (w && w.bridgeStrokes === false) return false;
  return true;
}

function syncBridgeUI() {
  const b = state.bridge;
  const el = document.getElementById('bridgeStrokes');
  const tEl = document.getElementById('bridgeTension');
  if (el) el.checked = b.enabled;
  if (tEl) tEl.value = b.tension;
  document.getElementById('vBridgeT').textContent = (b.tension || 0.4).toFixed(2);
  updateMotionStat();
}

function onBridgeUI() {
  state.bridge.enabled = document.getElementById('bridgeStrokes').checked;
  state.bridge.tension = parseFloat(document.getElementById('bridgeTension').value) || 0.4;
  document.getElementById('vBridgeT').textContent = state.bridge.tension.toFixed(2);
  invalidateTrajCache();
  scheduleDraw({ traj: true });
  updateMotionStat();
}

function applyBridgeToAll() {
  const on = bridgeSettings().enabled;
  for (const id in state.worms) state.worms[id].bridgeStrokes = on ? null : false;
  draw();
  updateMotionStat();
}

function strokeTangentEnd(pts) {
  const n = pts.length;
  if (n < 2) return { x: 1, y: 0 };
  const dx = pts[n - 1].x - pts[n - 2].x;
  const dy = pts[n - 1].y - pts[n - 2].y;
  const l = Math.hypot(dx, dy) || 1;
  return { x: dx / l, y: dy / l };
}

function strokeTangentStart(pts) {
  if (pts.length < 2) return { x: 1, y: 0 };
  const dx = pts[1].x - pts[0].x;
  const dy = pts[1].y - pts[0].y;
  const l = Math.hypot(dx, dy) || 1;
  return { x: dx / l, y: dy / l };
}

function cubicBezier(p0, p1, p2, p3, t) {
  const u = 1 - t;
  return {
    x: u * u * u * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t * t * t * p3.x,
    y: u * u * u * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t * t * t * p3.y,
  };
}

function sampleBezierBridge(p0, p3, tan0, tan3, tension, spacing) {
  const chord = Math.hypot(p3.x - p0.x, p3.y - p0.y);
  const k = Math.max(chord * tension, spacing * 2);
  const p1 = { x: p0.x + tan0.x * k, y: p0.y + tan0.y * k };
  const p2 = { x: p3.x - tan3.x * k, y: p3.y - tan3.y * k };
  const steps = Math.max(4, Math.ceil(chord / Math.max(spacing, 1)));
  const raw = [];
  for (let i = 0; i <= steps; i++) raw.push(cubicBezier(p0, p1, p2, p3, i / steps));
  return resampleUniform(raw, spacing);
}

function buildWormTrajectory(w) {
  const segs = wormStrokeList(w)
    .map((s, strokeIndex) => ({
      strokeIndex,
      points: w.points.slice(s.start, s.end + 1),
    }))
    .filter(s => s.points.length >= 1);
  const bridgeOn = wormBridgeEnabled(w);
  const { tension } = bridgeSettings();
  const spacing = getUniformSpacing();
  const parts = [];

  segs.forEach((seg, si) => {
    parts.push({ kind: 'stroke', strokeIndex: seg.strokeIndex, points: seg.points.map(p => ({ ...p })) });
    if (bridgeOn && si < segs.length - 1) {
      const next = segs[si + 1];
      const p0 = seg.points[seg.points.length - 1];
      const p3 = next.points[0];
      if (Math.hypot(p3.x - p0.x, p3.y - p0.y) > 0.5) {
        const tan0 = strokeTangentEnd(seg.points);
        const tan3 = strokeTangentStart(next.points);
        const bridgePts = sampleBezierBridge(p0, p3, tan0, tan3, tension, spacing);
        if (bridgePts.length >= 2) {
          parts.push({
            kind: 'bridge',
            strokeIndex: seg.strokeIndex,
            bridgeTo: next.strokeIndex,
            points: bridgePts.map(p => ({ x: p.x, y: p.y })),
          });
        }
      }
    }
  });

  const poly = [];
  const segmentTable = [];
  let cum = 0;
  const lens = [];

  parts.forEach(part => {
    const i0 = poly.length;
    part.points.forEach((p, j) => {
      if (poly.length && j === 0) {
        const last = poly[poly.length - 1];
        if (Math.hypot(p.x - last.x, p.y - last.y) < 0.01) return;
      }
      poly.push({
        x: p.x, y: p.y, t: p.t,
        kind: part.kind,
        strokeIndex: part.strokeIndex,
        bridgeTo: part.bridgeTo,
      });
    });
    const i1 = poly.length - 1;
    if (part.kind === 'stroke' && i1 >= i0) {
      segmentTable.push({
        strokeIndex: part.strokeIndex,
        pointIndexStart: i0,
        pointIndexEnd: i1,
        kind: 'stroke',
      });
    }
    if (part.kind === 'bridge' && i1 >= i0) {
      segmentTable.push({
        strokeIndex: part.strokeIndex,
        bridgeTo: part.bridgeTo,
        pointIndexStart: i0,
        pointIndexEnd: i1,
        kind: 'bridge',
      });
    }
  });

  const { lens: arc, total } = pathLengths(poly);
  const segAtPoint = new Array(poly.length);
  for (const seg of segmentTable) {
    for (let ii = seg.pointIndexStart; ii <= seg.pointIndexEnd; ii++) segAtPoint[ii] = seg;
  }
  const strokeArc = {};
  for (const seg of segmentTable) {
    if (seg.kind !== 'stroke') continue;
    const sub = poly.slice(seg.pointIndexStart, seg.pointIndexEnd + 1).map(q => ({ x: q.x, y: q.y }));
    const { lens, total: stotal } = pathLengths(sub);
    strokeArc[seg.strokeIndex] = { lens, total: stotal, i0: seg.pointIndexStart };
  }
  poly.forEach((p, i) => {
    p.u = total > 0 ? arc[i] / total : 0;
    const m = toMM(p);
    p.x_px = m.x_px;
    p.y_px = m.y_px;
    p.x_mm = m.x_mm != null ? +m.x_mm.toFixed(4) : null;
    p.y_mm = m.y_mm != null ? +m.y_mm.toFixed(4) : null;
    p.coordUnit = m.unit;
    p.z_mm = p.z_mm != null ? p.z_mm : 0;
    p.u = +p.u.toFixed(6);
  const seg = segAtPoint[i];
    let uLocal = null;
    if (seg && seg.kind === 'stroke' && strokeArc[seg.strokeIndex]) {
      const sa = strokeArc[seg.strokeIndex];
      const li = i - sa.i0;
      uLocal = sa.total > 0 ? sa.lens[li] / sa.total : 0;
    } else if (seg && seg.kind === 'stroke') {
      const sl = seg.pointIndexEnd - seg.pointIndexStart;
      uLocal = sl > 0 ? (i - seg.pointIndexStart) / sl : 0;
    }
    if (uLocal != null) p.u_within_stroke = +uLocal.toFixed(6);
    let uStyle = p.u;
    if (p.kind === 'stroke' && p.u_within_stroke != null) uStyle = p.u_within_stroke;
    else if (p.kind === 'bridge') uStyle = 0.5;
    p.width_mm = +widthAlongStyle(w.style, uStyle).toFixed(4);
  });

  segmentTable.forEach(seg => {
    if (poly[seg.pointIndexStart]) seg.u0 = poly[seg.pointIndexStart].u;
    if (poly[seg.pointIndexEnd]) seg.u1 = poly[seg.pointIndexEnd].u;
    seg.length_mm = isCalibrated()
      ? +polylineLengthMm(
          poly.slice(seg.pointIndexStart, seg.pointIndexEnd + 1).map(q => ({ x_mm: q.x_mm, y_mm: q.y_mm }))
        ).toFixed(3)
      : null;
    seg.length_px = +pathLengths(
      poly.slice(seg.pointIndexStart, seg.pointIndexEnd + 1).map(q => ({ x: q.x, y: q.y }))
    ).total.toFixed(2);
  });

  return {
    wormId: null,
    bridgeEnabled: bridgeOn,
    pointCount: poly.length,
    length_mm: +total > 0 && state.cal.scale ? +(total / state.cal.scale).toFixed(3) : null,
    length_px: +total.toFixed(2),
    points: poly,
    segments: segmentTable,
    strokes: segs.map(s => s.strokeIndex),
  };
}

function buildAllTrajectories() {
  return Object.keys(state.worms).map(Number).sort((a, b) => a - b).map(id => {
    const t = buildWormTrajectory(state.worms[id]);
    t.wormId = id;
    t.color = state.worms[id].color;
    t.style = { ...state.worms[id].style };
    return t;
  }).filter(t => t.pointCount >= 2);
}

function statsArray(arr) {
  if (!arr.length) return { mean: 0, std: 0, min: 0, max: 0, n: 0 };
  const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
  const v = arr.reduce((a, b) => a + (b - mean) ** 2, 0) / arr.length;
  return {
    mean: +mean.toFixed(6),
    std: +Math.sqrt(v).toFixed(6),
    min: +Math.min(...arr).toFixed(6),
    max: +Math.max(...arr).toFixed(6),
    n: arr.length,
  };
}

function computeMotionFeatures(traj) {
  const steps = [];
  const turns = [];
  const widths = [];
  const pts = traj.points;
  for (let i = 1; i < pts.length; i++) {
    steps.push(distBetweenPoints(pts[i], pts[i - 1]));
    widths.push(pts[i].width_mm);
  }
  for (let i = 2; i < pts.length; i++) {
    const v0x = (pts[i - 1].x_mm != null ? pts[i - 1].x_mm : pts[i - 1].x_px) - (pts[i - 2].x_mm != null ? pts[i - 2].x_mm : pts[i - 2].x_px);
    const v0y = (pts[i - 1].y_mm != null ? pts[i - 1].y_mm : pts[i - 1].y_px) - (pts[i - 2].y_mm != null ? pts[i - 2].y_mm : pts[i - 2].y_px);
    const v1x = (pts[i].x_mm != null ? pts[i].x_mm : pts[i].x_px) - (pts[i - 1].x_mm != null ? pts[i - 1].x_mm : pts[i - 1].x_px);
    const v1y = (pts[i].y_mm != null ? pts[i].y_mm : pts[i].y_px) - (pts[i - 1].y_mm != null ? pts[i - 1].y_mm : pts[i - 1].y_px);
    const a0 = Math.atan2(v0y, v0x);
    const a1 = Math.atan2(v1y, v1x);
    let d = a1 - a0;
    while (d > Math.PI) d -= Math.PI * 2;
    while (d < -Math.PI) d += Math.PI * 2;
    turns.push(d);
  }
  const perSegment = traj.segments
    .filter(s => s.kind === 'stroke')
  .map(s => ({
    strokeIndex: s.strokeIndex,
    u0: s.u0,
    u1: s.u1,
    length_mm: s.length_mm,
  }));
  return {
    arcLength_mm: traj.length_mm,
    pointCount: traj.pointCount,
    bridgeEnabled: traj.bridgeEnabled,
    stepLength_mm: statsArray(steps),
    turning_rad: statsArray(turns),
    width_mm: statsArray(widths),
    strokeBlocks: perSegment,
  };
}

function lognormalMuSigmaFromSamples(vals) {
  const pos = vals.filter(v => v > 0 && Number.isFinite(v));
  if (pos.length < 3) return { fitted: false, mu: 0, sigma: 0.15, n: pos.length };
  const logs = pos.map(v => Math.log(v));
  const st = statsArray(logs);
  return { fitted: true, mu: st.mean, sigma: Math.max(0.02, st.std), n: pos.length };
}

function buildSynthesisRecipe(featuresList) {
  const stepSamples = featuresList.flatMap(f => {
    if (!f.stepLength_mm || !f.stepLength_mm.n) return [];
    return [f.stepLength_mm.mean];
  });
  const turnStdSamples = featuresList.flatMap(f => {
    if (!f.turning_rad || !f.turning_rad.n) return [];
    return [f.turning_rad.std];
  });
  const widthStdSamples = featuresList.flatMap(f => {
    if (!f.width_mm || !f.width_mm.n) return [];
    return [f.width_mm.std];
  });
  const lnStep = lognormalMuSigmaFromSamples(stepSamples);
  const turnStats = statsArray(turnStdSamples);
  const widthStats = statsArray(widthStdSamples);
  return {
    parameterization: 'Arc-length u in [0,1]; position in mm when calibrated; optional t_video on stroke starts',
    bridgeCurve: 'Cubic Bezier between strokes; tension from project bridge.tension',
    dataProvenance: {
      measuredWorms: featuresList.length,
      note: 'stochasticLayer values tagged fitted vs default',
    },
    stochasticLayer: {
      description: 'Add per-instance noise when batch-generating virtual silk',
      stepLength_mm: {
        distribution: 'lognormal',
        mu: lnStep.mu,
        sigma: lnStep.sigma,
        source: lnStep.fitted ? 'fitted_from_measured_step_means' : 'default_insufficient_samples',
        sampleCount: lnStep.n,
      },
      turn_rad: {
        distribution: 'normal',
        mu: 0,
        sigma: turnStats.n >= 2 ? Math.max(0.02, turnStats.mean) : 0.08,
        source: turnStats.n >= 2 ? 'fitted_from_measured_turn_spread' : 'default',
        sampleCount: turnStats.n,
      },
      width_mm: {
        distribution: 'normal',
        scale: 'multiply (1 + N(0, sigma)) on widthAlongStyle(u)',
        sigma: widthStats.n >= 2 ? Math.max(0.02, widthStats.mean) : 0.06,
        source: widthStats.n >= 2 ? 'fitted_from_measured_width_spread' : 'default',
        sampleCount: widthStats.n,
      },
      seedNote: 'Use random seed per virtual worm; keep segment u-ranges from strokeBlocks',
    },
    touchDesigner: {
      hint: 'Import motion-model.json → point CHOP with u → Add SOP Line/Resample → Noise SOP on P with sigma from stochasticLayer',
      chopExpr: 'u drives Phase; length_mm * u gives approximate distance along spine',
    },
    batchPipeline: [
      '1) Fit strokeBlocks u0/u1 from real data',
      '2) Sample control points with stepLength noise',
      '3) Optional Chaikin + bridgeBezier between blocks',
      '4) width = widthAlongStyle(u) * width noise',
    ],
  };
}

function updateMotionStat() {
  const el = document.getElementById('motionStat');
  if (!el) return;
  const trajs = buildAllTrajectories();
  if (!trajs.length) {
    el.textContent = '尚无完整轨迹';
    return;
  }
  const t = trajs.find(x => x.wormId === state.activeId) || trajs[0];
  const strokeN = t.segments.filter(s => s.kind === 'stroke').length;
  const bridgeN = t.segments.filter(s => s.kind === 'bridge').length;
  el.innerHTML =
    `当前蚕 <b>${t.wormId}</b>：统一 <b>${t.pointCount}</b> 点 · ` +
    `<b>${strokeN}</b> 笔 · 过渡 <b>${bridgeN}</b> · ` +
    (t.length_mm != null ? `长约 <b>${t.length_mm}</b> mm · ` : '') +
    `连接 <b>${t.bridgeEnabled ? '开' : '关'}</b> · u=0→1`;
}

function getCachedWormTrajectory(w, wormId) {
  const key = wormGeomCacheKey(w) + ':' + (wormBridgeEnabled(w) ? 1 : 0) + ':' + bridgeSettings().tension;
  const cache = state._trajCache[wormId];
  if (cache && cache.key === key) return cache.traj;
  const traj = buildWormTrajectory(w);
  state._trajCache[wormId] = { key, traj };
  return traj;
}

function drawWormTrajectories(ctx, w, wormId) {
  const bridgeOn = wormBridgeEnabled(w);
  if (!bridgeOn) {
    for (const seg of wormStrokeList(w)) {
      if (seg.end <= seg.start) continue;
      const slice = w.points.slice(seg.start, seg.end + 1);
      if (slice.length >= 2) drawStyledPath(ctx, slice, w.style, w.color);
    }
    return;
  }
  const id = wormId != null ? wormId : state.activeId;
  const traj = getCachedWormTrajectory(w, id);
  let i = 0;
  while (i < traj.points.length) {
    const p0 = traj.points[i];
    const kind = p0.kind;
    let j = i + 1;
    while (j < traj.points.length && traj.points[j].kind === kind
      && (kind !== 'stroke' || traj.points[j].strokeIndex === p0.strokeIndex)) j++;
    const slice = traj.points.slice(i, j);
    if (slice.length >= 2) {
      const style = kind === 'bridge'
        ? { ...w.style, headWidth: w.style.tailWidth, midWidth: (w.style.tailWidth + w.style.headWidth) / 2, tailWidth: w.style.headWidth }
        : w.style;
      const col = kind === 'bridge' ? mixColor(w.color, true, 0.15) : w.color;
      drawStyledPath(ctx, slice.map(p => ({ x: p.x, y: p.y })), style, col, w.style.opacity * (kind === 'bridge' ? 0.75 : 1));
    }
    i = j;
  }
}
function applyToAll() {
  const cur = { ...state.worms[state.activeId].style };
  for (const id in state.worms) state.worms[id].style = { ...cur };
  draw();
}

function pathLengths(pts) {
  const lens = [0];
  let total = 0;
  for (let i = 1; i < pts.length; i++) {
    total += Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
    lens.push(total);
  }
  return { lens, total };
}

function widthAlongStyle(style, u) {
  const h = style.headWidth, m = style.midWidth, t = style.tailWidth;
  if (u <= 0.5) return h + (m - h) * (u / 0.5);
  return m + (t - m) * ((u - 0.5) / 0.5);
}

function pathPerpAt(pts, i) {
  let dx = 0, dy = 0;
  if (i < pts.length - 1) {
    dx = pts[i + 1].x - pts[i].x;
    dy = pts[i + 1].y - pts[i].y;
  } else if (i > 0) {
    dx = pts[i].x - pts[i - 1].x;
    dy = pts[i].y - pts[i - 1].y;
  } else dy = 1;
  const l = Math.hypot(dx, dy) || 1;
  return { x: -dy / l, y: dx / l };
}

function mixColor(hex, towardWhite, amt) {
  const h = hex.replace('#', '');
  if (h.length !== 6) return hex;
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  const mix = (c) => Math.round(c + (255 - c) * amt);
  return `rgb(${mix(r)},${mix(g)},${mix(b)})`;
}

function ribbonPolygon(pts, lens, total, style, halfScale) {
  const left = [], right = [];
  for (let i = 0; i < pts.length; i++) {
    const u = total > 0 ? lens[i] / total : (pts.length > 1 ? i / (pts.length - 1) : 0);
    const hw = widthAlongStyle(style, u) * 0.5 * halfScale;
    const n = pathPerpAt(pts, i);
    left.push({ x: pts[i].x + n.x * hw, y: pts[i].y + n.y * hw });
    right.push({ x: pts[i].x - n.x * hw, y: pts[i].y - n.y * hw });
  }
  return { left, right };
}

function fillRibbon(ctx, left, right, fill) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.moveTo(left[0].x, left[0].y);
  for (let i = 1; i < left.length; i++) ctx.lineTo(left[i].x, left[i].y);
  for (let i = right.length - 1; i >= 0; i--) ctx.lineTo(right[i].x, right[i].y);
  ctx.closePath();
  ctx.fill();
}

function previewStyle(style, scaleMul) {
  const s = (scaleMul != null ? scaleMul : 1) * canvasPreviewWidthScale();
  return {
    ...style,
    headWidth: style.headWidth * s,
    midWidth: style.midWidth * s,
    tailWidth: style.tailWidth * s,
  };
}

function drawStyledPathOnCtx(ctx, pts, style, color, layerOpacity, scaleMul) {
  if (pts.length < 2) return;
  style = previewStyle(style, scaleMul);
  const mat = String(style.material || 'ribbon').toLowerCase();
  const { lens, total } = pathLengths(pts);
  const op = layerOpacity != null ? layerOpacity : style.opacity;

  ctx.save();
  ctx.globalAlpha = op;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  if (mat === 'line') {
    for (let i = 0; i < pts.length - 1; i++) {
      const u0 = total > 0 ? lens[i] / total : 0;
      const u1 = total > 0 ? lens[i + 1] / total : 1;
      const lw = (widthAlongStyle(style, u0) + widthAlongStyle(style, u1)) * 0.5;
      ctx.strokeStyle = color;
      ctx.lineWidth = Math.max(0.5, lw);
      ctx.beginPath();
      ctx.moveTo(pts[i].x, pts[i].y);
      ctx.lineTo(pts[i + 1].x, pts[i + 1].y);
      ctx.stroke();
    }
  } else if (mat === 'silk' || mat === 'tube') {
    ctx.shadowColor = mat === 'silk' ? 'rgba(255,236,200,0.55)' : 'rgba(0,0,0,0.45)';
    ctx.shadowBlur = Math.max(4, style.midWidth * (mat === 'silk' ? 0.35 : 0.15));
    const outer = ribbonPolygon(pts, lens, total, style, 1);
    fillRibbon(ctx, outer.left, outer.right, color);
    ctx.shadowBlur = 0;
    const innerStyle = { ...style, headWidth: style.headWidth * 0.35, midWidth: style.midWidth * 0.35, tailWidth: style.tailWidth * 0.35 };
    const inner = ribbonPolygon(pts, lens, total, innerStyle, 1);
    ctx.globalAlpha = op * 0.85;
    fillRibbon(ctx, inner.left, inner.right, mixColor(color, true, mat === 'silk' ? 0.82 : 0.62));
  } else {
    const rib = ribbonPolygon(pts, lens, total, style, 1);
    fillRibbon(ctx, rib.left, rib.right, color);
  }
  ctx.restore();
}

function drawStyledPath(ctx, pts, style, color, layerOpacity) {
  drawStyledPathOnCtx(ctx, pts, style, color, layerOpacity, null);
}

function wormTabCount() {
  const ids = Object.keys(state.worms).map(Number);
  const maxUsed = ids.length ? Math.max(...ids) : 1;
  return Math.min(9, Math.max(state.maxWormTab, maxUsed, state.activeId));
}

function addWormTab() {
  if (state.maxWormTab >= 9) return;
  state.maxWormTab++;
  ensureWorm(state.maxWormTab);
  renderTabs();
}

function renderTabs() {
  const box = document.getElementById('wormTabs');
  box.innerHTML = '';
  const n = wormTabCount();
  for (let i = 1; i <= n; i++) {
    ensureWorm(i);
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = i;
    b.style.background = state.worms[i].color;
    b.style.color = '#111';
    if (i === state.activeId) b.classList.add('active');
    b.onclick = () => {
      state.activeId = i;
      if (i > state.maxWormTab) state.maxWormTab = i;
      syncStyleUI();
      renderTabs();
      updateBehaviorStat();
      draw();
    };
    box.appendChild(b);
  }
}

// ==================== 绘制 ====================
function draw() {
  const ctx = state.ctx; if (!ctx) return;
  const v = state.video;
  const cw = state.canvas.width;
  const ch = state.canvas.height;
  if (!cw || !ch) return;
  ctx.clearRect(0, 0, cw, ch);

  if (v && state.videoReady && v.videoWidth > 0 && v.readyState >= 2) {
    try {
      ctx.drawImage(v, 0, 0, cw, ch);
    } catch (err) {
      ctx.fillStyle = '#111';
      ctx.fillRect(0, 0, cw, ch);
      ctx.fillStyle = '#8a8f99';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('视频帧无法绘制（请换 H.264 MP4）', cw / 2, ch / 2);
    }
  } else if (v && v.src) {
    ctx.fillStyle = '#111';
    ctx.fillRect(0, 0, cw, ch);
    ctx.fillStyle = '#8a8f99';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('正在加载视频…', cw / 2, ch / 2);
  }

  // 网格
  if (document.getElementById('tGrid').checked && state.cal.scale) {
    ctx.strokeStyle = 'rgba(255,255,255,0.08)';
    ctx.lineWidth = 1;
    const pxPerMm = state.cal.scale;
    for (let x=state.cal.ox; x<state.canvas.width; x+=pxPerMm*10) {
      ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,state.canvas.height); ctx.stroke();
    }
    for (let x=state.cal.ox-pxPerMm*10; x>0; x-=pxPerMm*10) {
      ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,state.canvas.height); ctx.stroke();
    }
    for (let y=state.cal.oy; y<state.canvas.height; y+=pxPerMm*10) {
      ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(state.canvas.width,y); ctx.stroke();
    }
    for (let y=state.cal.oy-pxPerMm*10; y>0; y-=pxPerMm*10) {
      ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(state.canvas.width,y); ctx.stroke();
    }
    // 原点十字
    ctx.strokeStyle = 'rgba(232,160,76,0.7)';
    ctx.beginPath();
    ctx.moveTo(state.cal.ox-10, state.cal.oy); ctx.lineTo(state.cal.ox+10, state.cal.oy);
    ctx.moveTo(state.cal.ox, state.cal.oy-10); ctx.lineTo(state.cal.ox, state.cal.oy+10);
    ctx.stroke();
  }

  const showBeh = !document.getElementById('tBehBox') || document.getElementById('tBehBox').checked;
  if (showBeh) {
    for (const id in state.worms) {
      const worm = state.worms[id];
      const boxes = wormBoxes(worm);
      boxes.forEach((wb) => {
      const o = orderedBox(wb);
      const x = o.x0, y = o.y0, w = o.x1 - o.x0, h = o.y1 - o.y0;
      const active = +id === state.activeId;
      const selected = active && wb.id === worm.selectedBoxId;
      ctx.strokeStyle = selected ? 'rgba(232,160,76,1)' : (active ? 'rgba(120,230,210,1)' : 'rgba(94,182,168,0.7)');
      ctx.lineWidth = selected ? 4 : 2.5;
      ctx.setLineDash([]);
      ctx.strokeRect(x, y, w, h);
      ctx.fillStyle = selected ? 'rgba(232,160,76,0.14)' : 'rgba(94,182,168,0.08)';
      ctx.fillRect(x, y, w, h);
      ctx.fillStyle = selected ? '#e8a04c' : 'rgba(120,230,210,0.95)';
      ctx.font = 'bold 18px sans-serif';
      ctx.fillText(String(wb.id), x + 8, y + 22);
      if (selected) {
        ctx.fillStyle = '#ffffff';
        const hs = boxHandles(wb);
        Object.keys(hs).forEach((key) => {
          ctx.fillRect(hs[key].x - 4, hs[key].y - 4, 8, 8);
        });
      }
      });
    }
  }
  if (state.regionDrag) {
    const rd = state.regionDrag;
    const x = Math.min(rd.x0, rd.x1);
    const y = Math.min(rd.y0, rd.y1);
    const w = Math.abs(rd.x1 - rd.x0);
    const h = Math.abs(rd.y1 - rd.y0);
    ctx.strokeStyle = '#5eb6a8';
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.strokeRect(x, y, w, h);
    ctx.setLineDash([]);
  }

  drawTrajOverlay(v);
}

function drawTrajOverlay(v) {
  const cvs = document.getElementById('canvasTraj');
  if (!cvs || !cvs.width) return;
  const ctx = cvs.getContext('2d');
  ctx.clearRect(0, 0, cvs.width, cvs.height);

  if (document.getElementById('tTraj').checked) {
    for (const id in state.worms) {
      const w = state.worms[id];
      if (w.points.length < 2) continue;
      drawWormTrajectories(ctx, w, +id);
    }
  }

  if (state.pointer && state.pointer.pts.length >= 1) {
    const w = state.worms[state.activeId];
    const col = w ? w.color : COLORS[0];
    const style = w ? w.style : { headWidth: 0.3, midWidth: 1, tailWidth: 0.15, opacity: 0.85, material: 'ribbon' };
    const previewPts = state.pointer.pts.slice();
    if (state.pointer.lastRaw) previewPts.push(state.pointer.lastRaw);
    if (previewPts.length >= 2) {
      ctx.save();
      ctx.setLineDash([5, 4]);
      drawStyledPath(ctx, previewPts, style, col, Math.min(1, style.opacity * 0.95));
      ctx.setLineDash([]);
      ctx.restore();
    }
  }

  if (document.getElementById('tPts').checked) {
    for (const id in state.worms) {
      const w = state.worms[id];
      ctx.fillStyle = w.color;
      for (const p of w.points) {
        ctx.beginPath(); ctx.arc(p.x, p.y, id == state.activeId ? 3 : 1.5, 0, Math.PI * 2); ctx.fill();
      }
    }
    if (v) {
      const w = state.worms[state.activeId];
      const t = v.currentTime;
      const near = w.points.find(p => Math.abs(p.t - t) < FRAME);
      if (near) {
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(near.x, near.y, 7, 0, Math.PI * 2); ctx.stroke();
      }
    }
  }

  const up = state.uPlay;
  if (up.traj && up.traj.length >= 2 && up.frame > 0) {
    const p = up.traj[Math.min(up.frame, up.traj.length - 1)];
    ctx.strokeStyle = '#fff';
    ctx.fillStyle = 'rgba(232,160,76,0.85)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }
}

function updateCalStat() {
  const el = document.getElementById('calStat');
  if (state.cal.scale) {
    el.innerHTML = '原点 ('+state.cal.ox.toFixed(0)+','+state.cal.oy.toFixed(0)+') px<br>'+
                   '比例尺 <b>'+state.cal.scale.toFixed(2)+' px/mm</b>';
  } else el.textContent = '未标定';
}
function updateStat() {
  let total = 0;
  for (const id in state.worms) total += state.worms[id].points.length;
  document.getElementById('statBox').innerHTML =
    '蚕数量：<b>'+Object.keys(state.worms).length+'</b><br>'+
    '总点数：<b>'+total+'</b><br>'+
    '当前蚕 <b>'+state.activeId+'</b>：'+state.worms[state.activeId].points.length+' 点';
  updateMotionStat();
}

// ==================== 导出 ====================
function toMM(p) {
  const x_px = +p.x;
  const y_px = +p.y;
  if (!isCalibrated()) {
    return { unit: 'px', x_px, y_px, x_mm: null, y_mm: null };
  }
  return {
    unit: 'mm',
    x_px,
    y_px,
    x_mm: (p.x - state.cal.ox) / state.cal.scale,
    y_mm: (state.cal.oy - p.y) / state.cal.scale,
  };
}

function distBetweenPoints(a, b) {
  if (a.x_mm != null && b.x_mm != null) return Math.hypot(a.x_mm - b.x_mm, a.y_mm - b.y_mm);
  const ax = a.x_px != null ? a.x_px : a.x;
  const ay = a.y_px != null ? a.y_px : a.y;
  const bx = b.x_px != null ? b.x_px : b.x;
  const by = b.y_px != null ? b.y_px : b.y;
  return Math.hypot(bx - ax, by - ay);
}

function wormStrokeList(w) {
  if (w.strokes && w.strokes.length) return w.strokes;
  if (w.points.length >= 2) return [{ start: 0, end: w.points.length - 1 }];
  return [];
}

function polylineLengthMm(pts) {
  let L = 0;
  for (let i = 1; i < pts.length; i++) {
    L += Math.hypot(pts[i].x_mm - pts[i - 1].x_mm, pts[i].y_mm - pts[i - 1].y_mm);
  }
  return L;
}

function axisPointMm(p, z) {
  const axis = (document.getElementById('expAxis') && document.getElementById('expAxis').value) || 'rhino';
  const zv = z != null ? z : (p.z_mm != null ? p.z_mm : 0);
  if (axis === 'blender') return [p.x_mm, p.y_mm, zv];
  return [p.x_mm, p.y_mm, zv];
}

function collectExportCurves() {
  const calibrated = isCalibrated();
  const withWidth = !document.getElementById('expWidth') || document.getElementById('expWidth').checked;
  const withPx = !document.getElementById('expPx') || document.getElementById('expPx').checked;
  const curves = [];
  const ids = Object.keys(state.worms).map(Number).sort((a, b) => a - b);
  for (const id of ids) {
    const w = state.worms[id];
    wormStrokeList(w).forEach((seg, si) => {
      if (seg.end <= seg.start) return;
      const slice = w.points.slice(seg.start, seg.end + 1);
      if (slice.length < 2) return;
      const points = slice.map((p, i) => {
        const m = toMM(p);
        const u = slice.length > 1 ? i / (slice.length - 1) : 0;
        const pt = {
          index: i,
          x_mm: calibrated && m.x_mm != null ? +m.x_mm.toFixed(4) : null,
          y_mm: calibrated && m.y_mm != null ? +m.y_mm.toFixed(4) : null,
          z_mm: p.z_mm != null ? +p.z_mm : 0,
        };
        if (withWidth) pt.width_mm = +widthAlongStyle(w.style, u).toFixed(4);
        if (p.t != null) pt.t_video = +p.t.toFixed(4);
        if (withPx) {
          pt.x_px = +p.x.toFixed(3);
          pt.y_px = +p.y.toFixed(3);
        }
        return pt;
      });
      curves.push({
        id: `${id}_${si}`,
        wormId: id,
        strokeIndex: si,
        name: `worm_${id}_stroke_${si}`,
        color: w.color,
        material: w.style.material,
        style: {
          headWidth_mm: w.style.headWidth,
          midWidth_mm: w.style.midWidth,
          tailWidth_mm: w.style.tailWidth,
          opacity: w.style.opacity,
          material: w.style.material,
        },
        pointCount: points.length,
        length_mm: calibrated ? +polylineLengthMm(points).toFixed(3) : null,
        points,
      });
    });
  }
  return curves;
}

function exportMetaBlock() {
  const v = state.video;
  const calibrated = isCalibrated();
  return {
    generator: 'silkworm-trajectory-editor',
    schema: SCHEMA_CURVES3D,
    schemaLegacy: 'curves3d/v1',
    axis: (document.getElementById('expAxis') && document.getElementById('expAxis').value) || 'rhino',
    unit: calibrated ? 'mm' : 'px',
    coordinateNote: calibrated
      ? 'x_mm/y_mm are physical after calibration'
      : 'Not calibrated: use x_px/y_px; do not treat x_mm as millimeters',
    note: 'Top-view silk curves; Z=0 unless z_mm set. width_mm for sweep/tube in DCC.',
    video: v && v.videoWidth ? { width_px: v.videoWidth, height_px: v.videoHeight, fps: state.videoFps } : null,
    calibration: calibrated ? {
      originPx: [state.cal.ox, state.cal.oy],
      scalePxPerMm: state.cal.scale,
      cell_mm: parseFloat(document.getElementById('scaleDist').value) || 10,
    } : null,
  };
}

function exportSVG() {
  const v = state.video;
  const W = v ? v.videoWidth : 1920, H = v ? v.videoHeight : 1080;
  let paths = '';
  const curves = collectExportCurves();
  const ribbon = document.getElementById('expSvgRibbon') && document.getElementById('expSvgRibbon').checked;
  for (const c of curves) {
    const w = state.worms[c.wormId];
    const d = svgPathFromPointsMm(c.points, ribbon, w.style);
    const meta = JSON.stringify({
      name: c.name, wormId: c.wormId, style: c.style, length_mm: c.length_mm, ribbon,
    });
    if (ribbon) {
      paths += `<path id="${c.name}" d="${d}" fill="${w.color}" fill-opacity="${w.style.opacity}" stroke="none"><desc>${meta.replace(/</g,'&lt;')}</desc></path>\n`;
    } else {
      paths += `<path id="${c.name}" d="${d}" fill="none" stroke="${w.color}" stroke-width="${w.style.midWidth}" opacity="${w.style.opacity}" stroke-linecap="round" stroke-linejoin="round"><desc>${meta.replace(/</g,'&lt;')}</desc></path>\n`;
    }
  }
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<metadata>${JSON.stringify(exportMetaBlock()).replace(/</g,'&lt;')}</metadata>
${paths}</svg>`;
  download('trajectories.svg', svg, 'image/svg+xml');
}

function exportCurves3D() {
  if (!requireCalibration('3D 曲线 JSON')) return;
  const data = {
    ...exportMetaBlock(),
    curveType: 'polyline',
    bridge: bridgeSettings(),
    curves: collectExportCurves(),
  };
  const uniOn = !document.getElementById('expUnified') || document.getElementById('expUnified').checked;
  if (uniOn) {
    data.unifiedTrajectories = buildAllTrajectories().map(t => ({
      wormId: t.wormId,
      color: t.color,
      style: t.style,
      bridgeEnabled: t.bridgeEnabled,
      length_mm: t.length_mm,
      points: t.points.map(p => ({
        u: p.u,
        x_mm: p.x_mm,
        y_mm: p.y_mm,
        z_mm: p.z_mm,
        kind: p.kind,
        strokeIndex: p.strokeIndex,
        bridgeTo: p.bridgeTo,
        u_within_stroke: p.u_within_stroke,
        width_mm: p.width_mm,
      })),
      segments: t.segments,
    }));
  }
  download('curves-3d.json', JSON.stringify(data, null, 2), 'application/json');
}

function exportMotionModel() {
  if (!requireCalibration('运动模型 JSON')) return;
  const trajs = buildAllTrajectories();
  if (!trajs.length) {
    alert('请先描好至少一条轨迹（每笔至少 2 个点）。');
    return;
  }
  const features = trajs.map(t => ({
    wormId: t.wormId,
    color: t.color,
    ...computeMotionFeatures(t),
  }));
  const data = {
    ...exportMetaBlock(),
    schema: SCHEMA_MOTION,
    schemaLegacy: 'silkworm-motion-model/v1',
    bridge: bridgeSettings(),
    unifiedTrajectories: trajs.map(t => ({
      wormId: t.wormId,
      bridgeEnabled: t.bridgeEnabled,
      length_mm: t.length_mm,
      pointCount: t.pointCount,
      segments: t.segments,
      points: t.points,
    })),
    features,
    synthesis: buildSynthesisRecipe(features),
    behaviorUnits: exportBehaviorUnits(),
    gridReference: {
      cell_mm: parseFloat(document.getElementById('scaleDist').value) || 10,
      typicalFigure8_grid: { cols: 1.5, rows: 1, note: 'empirical; use behaviorUnits per take' },
    },
  };
  updateMotionStat();
  download('motion-model.json', JSON.stringify(data, null, 2), 'application/json');
}

function exportJSON() {
  const calibrated = isCalibrated();
  const data = {
    fps: state.videoFps || 30,
    ...exportMetaBlock(),
    curves3d: collectExportCurves(),
    silkworms: Object.keys(state.worms).map(id => {
      const w = state.worms[id];
      return {
        id: +id, color: w.color,
        style: {...w.style},
        points: w.points.map((p, i) => {
          const m = toMM(p);
          const out = {
            index: i,
            x_mm: calibrated && m.x_mm != null ? +m.x_mm.toFixed(3) : null,
            y_mm: calibrated && m.y_mm != null ? +m.y_mm.toFixed(3) : null,
            z_mm: null,
            x_px: +p.x.toFixed(2),
            y_px: +p.y.toFixed(2),
            unit: m.unit,
          };
          if (p.t != null) out.t_video = +p.t.toFixed(3);
          return out;
        }),
        strokes: (w.strokes || []).map(s => ({ start: s.start, end: s.end }))
      };
    })
  };
  download('trajectories.json', JSON.stringify(data, null, 2), 'application/json');
}

function exportCSV() {
  if (!requireCalibration('CSV')) return;
  let rows = 'curve_name,worm_id,stroke_index,point_index,x_mm,y_mm,z_mm,width_mm,x_px,y_px,t_video\n';
  for (const c of collectExportCurves()) {
    c.points.forEach((p, i) => {
      const tv = p.t_video != null ? p.t_video : '';
      const wmm = p.width_mm != null ? p.width_mm : '';
      const xpx = p.x_px != null ? p.x_px : '';
      const ypx = p.y_px != null ? p.y_px : '';
      rows += `${c.name},${c.wormId},${c.strokeIndex},${i},${p.x_mm},${p.y_mm},${p.z_mm},${wmm},${xpx},${ypx},${tv}\n`;
    });
  }
  download('trajectories.csv', rows, 'text/csv');
}

function dxfEsc(s) {
  return String(s).replace(/[^\x20-\x7e]/g, '_');
}

function exportDXF() {
  if (!requireCalibration('DXF')) return;
  const curves = collectExportCurves();
  if (!curves.length) { alert('没有可导出的曲线'); return; }
  let dxf = `0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n`;
  for (const c of curves) {
    const layer = dxfEsc(c.name);
    dxf += `0\nPOLYLINE\n8\n${layer}\n62\n${((c.wormId - 1) % 7) + 1}\n66\n1\n70\n8\n`;
    for (const p of c.points) {
      const [x, y, z] = axisPointMm(p, p.z_mm);
      dxf += `0\nVERTEX\n8\n${layer}\n10\n${x.toFixed(4)}\n20\n${y.toFixed(4)}\n30\n${z.toFixed(4)}\n`;
    }
    dxf += `0\nSEQEND\n8\n${layer}\n`;
  }
  dxf += `0\nENDSEC\n0\nEOF\n`;
  download('silkworm-curves.dxf', dxf, 'application/dxf');
}

function exportOBJ() {
  if (!requireCalibration('OBJ')) return;
  const curves = collectExportCurves();
  if (!curves.length) { alert('没有可导出的曲线'); return; }
  const axis = (document.getElementById('expAxis') && document.getElementById('expAxis').value) || 'rhino';
  let obj = `# silkworm trajectories unit:mm axis:${axis}\n# object per stroke — Blender: File > Import > Wavefront (.obj)\n`;
  let vi = 1;
  for (const c of curves) {
    obj += `o ${c.name}\n`;
    obj += `# color ${c.color} material ${c.material} length_mm ${c.length_mm}\n`;
    const start = vi;
    for (const p of c.points) {
      const [x, y, z] = axisPointMm(p, p.z_mm);
      obj += `v ${x.toFixed(4)} ${y.toFixed(4)} ${z.toFixed(4)}\n`;
      vi++;
    }
    if (c.points.length >= 2) {
      obj += 'l';
      for (let i = 0; i < c.points.length; i++) obj += ` ${start + i}`;
      obj += '\n';
    }
  }
  download('silkworm-curves.obj', obj, 'text/plain');
}

function exportGLTF() {
  if (!requireCalibration('glTF')) return;
  const curves = collectExportCurves();
  if (!curves.length) { alert('没有可导出的曲线'); return; }
  const buffers = [];
  const bufferViews = [];
  const accessors = [];
  const meshes = [];
  const nodes = [];
  curves.forEach((c, ci) => {
    const floats = [];
    for (const p of c.points) {
      const [x, y, z] = axisPointMm(p, p.z_mm);
      if (![x, y, z].every(Number.isFinite)) continue;
      floats.push(x, y, z);
    }
    if (floats.length < 3) return;
    const bin = new Float32Array(floats);
    const bytes = new Uint8Array(bin.buffer);
    let binStr = '';
    for (let i = 0; i < bytes.length; i++) binStr += String.fromCharCode(bytes[i]);
    const b64 = btoa(binStr);
    const byteLength = bytes.length;
    const xs = [], ys = [], zs = [];
    for (let i = 0; i < floats.length; i += 3) { xs.push(floats[i]); ys.push(floats[i + 1]); zs.push(floats[i + 2]); }
    buffers.push({ uri: `data:application/octet-stream;base64,${b64}`, byteLength });
    bufferViews.push({ buffer: buffers.length - 1, byteOffset: 0, byteLength });
    accessors.push({
      bufferView: buffers.length - 1,
      componentType: 5126,
      count: floats.length / 3,
      type: 'VEC3',
      min: [Math.min(...xs), Math.min(...ys), Math.min(...zs)],
      max: [Math.max(...xs), Math.max(...ys), Math.max(...zs)],
    });
    const accIdx = accessors.length - 1;
    const meshIdx = meshes.length;
    meshes.push({
      name: c.name,
      primitives: [{ attributes: { POSITION: accIdx }, mode: 1 }],
    });
    nodes.push({ name: c.name, mesh: meshIdx });
  });
  const gltf = {
    asset: { version: '2.0', generator: 'silkworm-trajectory-editor', unitHint: 'mm top-view' },
    scene: 0,
    scenes: [{ nodes: nodes.map((_, i) => i) }],
    nodes,
    meshes,
    accessors,
    bufferViews,
    buffers,
  };
  download('silkworm-curves.gltf', JSON.stringify(gltf, null, 2), 'model/gltf+json');
}

function exportRhinoPy() {
  if (!requireCalibration('Rhino Python')) return;
  const curves = collectExportCurves();
  if (!curves.length) { alert('没有可导出的曲线'); return; }
  let py = `# -*- coding: utf-8 -*-\n# Run in Rhino Python (EditPythonScript). Creates one interpolated curve per stroke.\nimport rhinoscriptsyntax as rs\n\n`;
  curves.forEach((c) => {
    const pts = c.points.map(p => {
      const [x, y, z] = axisPointMm(p, p.z_mm);
      return `(${x}, ${y}, ${z})`;
    });
    py += `pts_${c.name} = [${pts.join(', ')}]\n`;
    py += `deg = 3 if len(pts_${c.name}) > 3 else 1\n`;
    py += `rs.AddCurve(pts_${c.name}, degree=deg)\n`;
    py += `# ${c.name} color hint: ${c.color}\n\n`;
  });
  download('import_silkworm_rhino.py', py, 'text/plain');
}

function exportBlenderPy() {
  if (!requireCalibration('Blender Python')) return;
  const curves = collectExportCurves();
  if (!curves.length) { alert('没有可导出的曲线'); return; }
  let py = `import bpy\n\n# Run in Blender Scripting tab. Units: mm (set scene if needed).\n`;
  curves.forEach((c) => {
    py += `c = bpy.data.curves.new('${c.name}', type='CURVE')\n`;
    py += `c.dimensions = '3D'\n`;
    py += `s = bpy.data.objects.new('${c.name}', c)\n`;
    py += `bpy.context.collection.objects.link(s)\n`;
    py += `spl = c.splines.new('POLY')\n`;
    py += `spl.points.add(${Math.max(0, c.points.length - 1)})\n`;
    c.points.forEach((p, i) => {
      const [x, y, z] = axisPointMm(p, p.z_mm);
      py += `spl.points[${i}].co = (${x / 1000}, ${y / 1000}, ${z / 1000}, 1)\n`;
    });
    py += `# width profile: head ${c.style.headWidth_mm} mid ${c.style.midWidth_mm} tail ${c.style.tailWidth_mm}\n\n`;
  });
  py += `print('Imported ${curves.length} silk curves')\n`;
  download('import_silkworm_blender.py', py, 'text/plain');
}

function download(name, content, type) {
  const blob = new Blob([content], {type: type+';charset=utf-8'});
  const a = document.createElement('a');
  const url = URL.createObjectURL(blob);
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

// ==================== 点序播放 / 吐丝预览 / 追踪导入 ====================
function refreshUPlayTrajectory() {
  const w = state.worms[state.activeId];
  if (!w || w.points.length < 2) {
    state.uPlay.traj = null;
    return;
  }
  const built = buildWormTrajectory(w);
  state.uPlay.traj = built.points.map(p => ({ x: p.x, y: p.y, u: p.u }));
  state.uPlay.frame = Math.min(state.uPlay.frame, state.uPlay.traj.length - 1);
  const el = document.getElementById('uPlayStat');
  if (el) el.textContent = `统一轨迹 ${state.uPlay.traj.length} 点（当前帧 ${state.uPlay.frame}）`;
}

function uPlayTick(ts) {
  const up = state.uPlay;
  if (!up.playing) return;
  if (!up.lastT) up.lastT = ts;
  const dt = (ts - up.lastT) / 1000;
  up.lastT = ts;
  const pps = parseFloat(document.getElementById('uPlayPps').value) || 40;
  up.frame += Math.max(1, Math.round(dt * pps));
  if (up.traj && up.frame >= up.traj.length - 1) {
    up.frame = up.traj.length - 1;
    up.playing = false;
    document.getElementById('uPlayBtn').textContent = '点序播放';
  }
  const u = up.traj && up.traj[up.frame] ? up.traj[up.frame].u : 0;
  document.getElementById('uPlaySlider').value = Math.round((u || 0) * 1000);
  refreshUPlayTrajectory();
  scheduleDraw({ traj: true });
  if (up.playing) requestAnimationFrame(uPlayTick);
}

function toggleUPointPlay() {
  refreshUPlayTrajectory();
  const up = state.uPlay;
  if (!up.traj || up.traj.length < 2) {
    alert('请先描好至少 2 个点的轨迹。');
    return;
  }
  up.playing = !up.playing;
  up.lastT = 0;
  document.getElementById('uPlayBtn').textContent = up.playing ? '暂停点序' : '点序播放';
  if (up.playing) requestAnimationFrame(uPlayTick);
}

function resetUPointPlay() {
  state.uPlay.playing = false;
  state.uPlay.frame = 0;
  state.uPlay.lastT = 0;
  document.getElementById('uPlayBtn').textContent = '点序播放';
  document.getElementById('uPlaySlider').value = 0;
  scheduleDraw({ traj: true });
  refreshUPlayTrajectory();
}

function scrubUPointPlay(v) {
  refreshUPlayTrajectory();
  const u = parseInt(v, 10) / 1000;
  const up = state.uPlay;
  if (!up.traj) return;
  let best = 0, bestD = 1e9;
  for (let i = 0; i < up.traj.length; i++) {
    const d = Math.abs((up.traj[i].u || 0) - u);
    if (d < bestD) { bestD = d; best = i; }
  }
  up.frame = best;
  up.playing = false;
  document.getElementById('uPlayBtn').textContent = '点序播放';
  scheduleDraw({ traj: true });
  refreshUPlayTrajectory();
}

function buildPreviewPayload() {
  const trajs = [];
  for (const id of Object.keys(state.worms).map(Number).sort((a, b) => a - b)) {
    const w = state.worms[id];
    if (w.points.length < 2) continue;
    let points;
    let synth = null;
    try {
      const built = buildWormTrajectory(w);
      points = built.points.map(p => ({
        x: p.x, y: p.y,
        x_mm: p.x_mm, y_mm: p.y_mm,
        u: p.u, width_mm: p.width_mm, kind: p.kind,
      }));
    } catch (_) {
      points = w.points.map((p, i, arr) => ({
        x: p.x, y: p.y, u: arr.length > 1 ? i / (arr.length - 1) : 0,
      }));
    }
    trajs.push({ wormId: id, color: w.color, style: { ...w.style }, points });
  }
  let synthesis = null;
  try {
    const models = trajs.map(t => ({ wormId: t.wormId, ...computeMotionFeatures({ points: t.points.map(p => ({ x_mm: p.x_mm || p.x, y_mm: p.y_mm || p.y, width_mm: p.width_mm || 1 })), segments: [] }) }));
    synthesis = buildSynthesisRecipe(models);
  } catch (_) { /* */ }
  return {
    type: 'silkworm-preview/v1',
    unit: isCalibrated() ? 'mm' : 'px',
    calibration: isCalibrated() ? {
      scalePxPerMm: state.cal.scale,
      originPx: [state.cal.ox, state.cal.oy],
      cell_mm: parseFloat(document.getElementById('scaleDist').value) || 10,
    } : null,
    behaviorBoxes: exportBehaviorUnits(),
    provenance: 'measured',
    synthesis,
    trajectories: trajs,
  };
}

function pushPreviewToPane(silent) {
  const payload = buildPreviewPayload();
  if (!payload.trajectories.length) {
    if (!silent) alert('请先描好至少一条轨迹（≥2 点）。');
    return false;
  }
  try { sessionStorage.setItem(PREVIEW_STORAGE_KEY, JSON.stringify(payload)); } catch (_) { /* */ }
  const frame = document.getElementById('previewFrame');
  if (frame && frame.contentWindow) {
    frame.contentWindow.postMessage({ type: 'silkworm-preview-push', payload }, '*');
  }
  return true;
}

function showSplitPreview() {
  document.body.classList.remove('preview-off');
  const frame = document.getElementById('previewFrame');
  frame.style.display = 'block';
  const btn = document.getElementById('btnPreviewToggle');
  if (btn) btn.textContent = '收起运动预览';
  window.addEventListener('message', onPreviewFrameReady);
  pushPreviewToPane(true);
}

function toggleSplitPreview() {
  const frame = document.getElementById('previewFrame');
  if (document.body.classList.contains('preview-off')) showSplitPreview();
  else {
    document.body.classList.add('preview-off');
    frame.style.display = 'none';
    const btn = document.getElementById('btnPreviewToggle');
    if (btn) btn.textContent = '展开运动预览';
  }
}

/* 预览里载入的轨迹同步给蚕室；蚕室挪到外层全宽区块后靠这条通路取数据 */
function onPreviewTrajData(ev) {
  if (!ev.data || ev.data.type !== 'silkworm-preview/data') return;
  const list = Array.isArray(ev.data.trajectories) ? ev.data.trajectories : [];
  window.__previewTrajs = list.filter(t => t && Array.isArray(t.points) && t.points.length >= 2);
  if (window.__studioHabitat && window.__studioHabitat.syncMeasured) window.__studioHabitat.syncMeasured();
}

function onPreviewFrameReady(ev) {
  if (!ev.data) return;
  if (ev.data.type === 'silkworm-preview-ready') {
    pushPreviewToPane(true);
    pushConditionsToPreview();
    const frame = document.getElementById('previewFrame');
    if (frame && frame.contentWindow) frame.contentWindow.postMessage({ type: 'silkworm-preview/request-data' }, '*');
  }
  if (ev.data.type === 'silkworm-studio/conditions' && ev.data.conditions) {
    applyConditions(ev.data.conditions);
  }
  if (ev.data.type === 'silkworm-habitat/import' && window.__studioHabitat) {
    window.__studioHabitat.import(ev.data.habitat);
  }
  if (ev.data.type === 'silkworm-goto-habitat') {
    const h = document.getElementById('habitat');
    if (h) h.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  onPreviewTrajData(ev);
}
window.addEventListener('message', onPreviewTrajData);

function gotoHabitat() {
  const h = document.getElementById('habitat');
  if (!h) return;
  h.scrollIntoView({ behavior: 'smooth', block: 'start' });
  const hab = window.__studioHabitat;
  const n = hab && hab.syncMeasured ? hab.syncMeasured() : 0;
  if (hab && hab.toast) {
    if (n) hab.toast('已同步 ' + n + ' 条实测轨迹进蚕室，可拖动或右侧微调。', 'ok');
    else hab.toast('还没有描好的轨迹（至少 2 点）：先在上方描线，再回来。', 'err');
  }
}

function importTrackingJson(e) {
  const f = e.target.files[0];
  if (!f) return;
  const reader = new FileReader();
  reader.onload = () => {
    let data;
    try { data = JSON.parse(reader.result); } catch (err) {
      alert('JSON 解析失败'); e.target.value = ''; return;
    }
    const list = data.silkworms || data.worms;
    if (!list || !list.length) {
      alert('未找到 silkworms / worms 数组');
      e.target.value = '';
      return;
    }
  const mode = confirm('确定覆盖当前工程全部蚕？\n取消 = 导入为新蚕编号（推荐）') ? 'replace' : 'new';
  if (mode === 'replace') {
    state.worms = {};
    list.forEach(sw => {
      const id = sw.id || 1;
      state.worms[id] = {
        color: sw.color || COLORS[(id - 1) % COLORS.length],
        points: (sw.points || []).map(pt => ({
          x: pt.x, y: pt.y, t: pt.t != null ? pt.t : pt.t_video,
        })),
        strokes: sw.strokes || [{ start: 0, end: (sw.points || []).length - 1 }],
        style: sw.style || { ...DEFAULT_STYLE },
        behaviorBox: sw.behaviorBox || null,
        motionPattern: 'figure8',
      };
    });
    state.activeId = list[0].id || 1;
  } else {
    let next = Math.max(1, ...Object.keys(state.worms).map(Number)) + 1;
    for (const sw of list) {
      const id = next++;
      const pts = (sw.points || []).map(pt => ({
        x: pt.x, y: pt.y, t: pt.t != null ? pt.t : pt.t_video,
      }));
      state.worms[id] = {
        color: sw.color || COLORS[(id - 1) % COLORS.length],
        points: pts,
        strokes: [{ start: 0, end: Math.max(0, pts.length - 1) }],
        style: sw.style || { ...DEFAULT_STYLE },
        behaviorBox: null,
        motionPattern: 'figure8',
      };
    }
    state.activeId = next - 1;
    if (state.activeId > state.maxWormTab) state.maxWormTab = state.activeId;
  }
    resetEditHistory(true);
    invalidateTrajCache();
    alert('已导入追踪 JSON（坐标：像素）。可手修后继续描线。');
    renderTabs(); syncStyleUI(); updateStat(); scheduleDraw({ traj: true });
    e.target.value = '';
  };
  reader.readAsText(f);
}

function svgPathFromPointsMm(points, ribbon, style) {
  if (!ribbon) {
    return points.map((p, i) => {
      const px = state.cal.scale ? state.cal.ox + p.x_mm * state.cal.scale : (p.x_px || 0);
      const py = state.cal.scale ? state.cal.oy - p.y_mm * state.cal.scale : (p.y_px || 0);
      return (i ? 'L' : 'M') + px.toFixed(2) + ' ' + py.toFixed(2);
    }).join(' ');
  }
  const pts = points.map(p => ({
    x: state.cal.scale ? state.cal.ox + p.x_mm * state.cal.scale : p.x_px,
    y: state.cal.scale ? state.cal.oy - p.y_mm * state.cal.scale : p.y_px,
  }));
  const { lens, total } = pathLengths(pts);
  const rib = ribbonPolygon(pts, lens, total, style, 1);
  let d = `M ${rib.left[0].x.toFixed(2)} ${rib.left[0].y.toFixed(2)} `;
  for (let i = 1; i < rib.left.length; i++) d += `L ${rib.left[i].x.toFixed(2)} ${rib.left[i].y.toFixed(2)} `;
  for (let i = rib.right.length - 1; i >= 0; i--) d += `L ${rib.right[i].x.toFixed(2)} ${rib.right[i].y.toFixed(2)} `;
  return d + 'Z';
}

function exportCanvasImage() {
  const base = state.canvas;
  if (!base || !base.width) { alert('请先载入视频'); return; }
  const out = document.createElement('canvas');
  out.width = base.width;
  out.height = base.height;
  const c = out.getContext('2d');
  c.drawImage(base, 0, 0);
  const traj = document.getElementById('canvasTraj');
  if (traj && traj.width) c.drawImage(traj, 0, 0);
  out.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'silk-frame-' + Date.now() + '.png';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }, 'image/png');
}

// ==================== 实验条件 ====================
let applyingConditions = false;

function readConditions() {
  const recordedAt = (document.getElementById('condTime').value || '').trim() || null;
  const t = parseFloat(document.getElementById('condTemp').value);
  const h = parseFloat(document.getElementById('condHum').value);
  return {
    recordedAt,
    temperatureC: Number.isFinite(t) ? t : null,
    humidity: Number.isFinite(h) ? h : null,
  };
}

function formatConditions(c) {
  if (!c || (!c.recordedAt && c.temperatureC == null && c.humidity == null)) return '未填写实验条件';
  const when = c.recordedAt ? String(c.recordedAt).replace('T', ' ') : '时间未填';
  const temp = c.temperatureC == null ? '温度未填' : c.temperatureC + ' °C';
  const hum = c.humidity == null ? '湿度未填' : c.humidity + '%';
  return when + ' · ' + temp + ' · 湿度 ' + hum;
}

function syncConditionPreset() {
  const sel = document.getElementById('condPreset');
  if (!sel) return;
  const key = document.getElementById('condTemp').value + ',' + document.getElementById('condHum').value;
  sel.value = [...sel.options].some(o => o.value === key) ? key : '';
}

function applyConditions(c) {
  const next = c || { recordedAt: null, temperatureC: null, humidity: null };
  applyingConditions = true;
  document.getElementById('condTime').value = next.recordedAt ? String(next.recordedAt).slice(0, 16) : '';
  document.getElementById('condTemp').value = next.temperatureC == null ? '' : next.temperatureC;
  document.getElementById('condHum').value = next.humidity == null ? '' : next.humidity;
  applyingConditions = false;
  syncConditionPreset();
  const stat = document.getElementById('condStat');
  if (stat) stat.textContent = formatConditions(readConditions());
}

function pushConditionsToPreview() {
  const frame = document.getElementById('previewFrame');
  if (!frame || !frame.contentWindow || frame.style.display === 'none') return;
  frame.contentWindow.postMessage({ type: 'silkworm-studio/conditions', conditions: readConditions() }, '*');
}

function onConditionsEdited() {
  syncConditionPreset();
  const stat = document.getElementById('condStat');
  if (stat) stat.textContent = formatConditions(readConditions());
  if (applyingConditions) return;
  pushConditionsToPreview();
}

function fillConditionNow() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  document.getElementById('condTime').value = d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + 'T' + p(d.getHours()) + ':' + p(d.getMinutes());
  onConditionsEdited();
}

function applyConditionPreset() {
  const v = document.getElementById('condPreset').value;
  if (!v) return;
  const parts = v.split(',');
  document.getElementById('condTemp').value = parts[0];
  document.getElementById('condHum').value = parts[1];
  onConditionsEdited();
}

// ==================== 工程保存/打开 ====================
function tracerProjectCore() {
  return {
    schema: 'silkworm-studio/project',
    projectVersion: PROJECT_FILE_VERSION,
    savedAt: new Date().toISOString(),
    conditions: readConditions(),
    calibration: state.cal,
    worms: state.worms,
    activeId: state.activeId,
    strokeOpts: getStrokeOpts(),
    bridge: { ...state.bridge },
    segments: state.segments,
    segmentIndex: state.segmentIndex,
    maxWormTab: state.maxWormTab,
    videoFps: state.videoFps,
    videoFileName: state.videoFileName || null,
  };
}

function downloadProject(data) {
  const err = validateProjectData(data);
  if (err) { alert('工程校验失败：' + err); return; }
  download('silkworm-project-' + Date.now() + '.json', JSON.stringify(data, null, 2), 'application/json');
}

function saveProject() {
  const data = tracerProjectCore();
  const frame = document.getElementById('previewFrame');
  if (!frame || !frame.contentWindow || document.body.classList.contains('preview-off')) {
    downloadProject(data);
    return;
  }
  let settled = false;
  const finish = (extra) => {
    if (settled) return;
    settled = true;
    window.removeEventListener('message', onExport);
    if (extra) {
      data.preview = extra.preview || null;
      const local = data.conditions || readConditions();
      const remote = extra.conditions;
      const localEmpty = !local.recordedAt && local.temperatureC == null && local.humidity == null;
      const remoteHas = remote && (remote.recordedAt || remote.temperatureC != null || remote.humidity != null);
      if (localEmpty && remoteHas) data.conditions = remote;
    }
    data.habitat = window.__studioHabitat ? window.__studioHabitat.export() : null;
    downloadProject(data);
  };
  const onExport = (ev) => {
    if (ev.data && ev.data.type === 'silkworm-studio/export') finish(ev.data);
  };
  window.addEventListener('message', onExport);
  frame.contentWindow.postMessage({ type: 'silkworm-studio/export-request' }, '*');
  setTimeout(() => finish(null), 500);
}
function loadProject(e) {
  const f = e.target.files[0]; if (!f) return;
  const reader = new FileReader();
  reader.onload = () => {
    let data;
    try {
      data = JSON.parse(reader.result);
    } catch (err) {
      alert('工程 JSON 解析失败：' + err.message);
      e.target.value = '';
      return;
    }
    data = normalizeLoadedProject(data);
    const vErr = validateProjectData(data);
    if (vErr) {
      alert('工程校验未通过，未加载：' + vErr);
      e.target.value = '';
      return;
    }
    state.cal = data.calibration || state.cal;
    state.worms = data.worms;
    state.activeId = data.activeId || 1;
    for (const id in state.worms) ensureWorm(+id);
    resetEditHistory(true);
    invalidateTrajCache();
    if (data.strokeOpts) {
      const o = data.strokeOpts;
      const uEl = document.getElementById('strokeUniform');
      if (uEl) {
        if (o.uniformSpacing != null) uEl.value = o.uniformSpacing;
        else if (o.minDist != null) uEl.value = o.minDist;
      }
      if (o.smoothPass != null) document.getElementById('strokeSmooth').value = o.smoothPass;
      if (o.jitter != null) document.getElementById('strokeJitter').value = o.jitter;
      updateStrokeUI();
    }
    if (data.maxWormTab != null) state.maxWormTab = data.maxWormTab;
    else state.maxWormTab = Math.min(9, Math.max(1, ...Object.keys(state.worms).map(Number)));
    if (data.segmentIndex != null) state.segmentIndex = data.segmentIndex;
    if (data.segments && data.segments.length) state.segments = data.segments;
    if (data.videoFps) state.videoFps = data.videoFps;
    if (data.videoFileName) state.videoFileName = data.videoFileName;
    if (data.bridge) {
      state.bridge = { ...state.bridge, ...data.bridge };
      syncBridgeUI();
    }
    renderTabs(); syncStyleUI(); updateCalStat(); updateSegStat(); updateStat(); updateBehaviorStat();
    scheduleDraw({ traj: true });
    applyConditions(data.conditions || null);
    if (data.videoFileName) {
      const seg = document.getElementById('segStat');
      if (seg) seg.textContent = '工程记录的视频：' + data.videoFileName + '（请重新载入该文件）';
    }
    const frame = document.getElementById('previewFrame');
    if (frame && frame.contentWindow && (data.preview || data.habitat || data.conditions)) {
      frame.contentWindow.postMessage({
        type: 'silkworm-studio/import',
        preview: data.preview || null,
        habitat: data.habitat || null,
        conditions: data.conditions || null,
      }, '*');
    }
    else if (!document.body.classList.contains('preview-off')) pushPreviewToPane(true);
    e.target.value = '';
  };
  reader.onerror = () => { alert('无法读取工程文件'); e.target.value = ''; };
  reader.readAsText(f);
}
showSplitPreview();
