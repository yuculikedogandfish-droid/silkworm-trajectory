#!/usr/bin/env node
/** Pure geometry tests mirroring editor algorithms (keep in sync with 蚕轨迹描图器.html). */
import assert from 'node:assert/strict';

function pathLengths(pts) {
  const lens = [0];
  let total = 0;
  for (let i = 1; i < pts.length; i++) {
    total += Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
    lens.push(total);
  }
  return { lens, total };
}

function pointAtDistance(pts, lens, d, hintFrom) {
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

// --- tests ---
const line = [{ x: 0, y: 0 }, { x: 100, y: 0 }];
const rs = resampleUniform(line, 10);
assert.equal(rs[0].x, 0);
assert.equal(rs[rs.length - 1].x, 100);
for (let i = 1; i < rs.length; i++) {
  const seg = Math.hypot(rs[i].x - rs[i - 1].x, rs[i].y - rs[i - 1].y);
  assert.ok(seg <= 10.5 && seg >= 9.5 || i === rs.length - 1);
}

const dup = [{ x: 0, y: 0 }, { x: 0, y: 0 }, { x: 50, y: 0 }, { x: 100, y: 0 }];
assert.ok(resampleUniform(dup, 10).length >= 2);

const sm = chaikinSmooth([{ x: 0, y: 0 }, { x: 50, y: 10 }, { x: 100, y: 0 }], 1);
assert.equal(sm[0].x, 0);
assert.equal(sm[sm.length - 1].x, 100);

console.log('geometry_tests.mjs: OK (' + rs.length + ' resampled points on 100px line)');
