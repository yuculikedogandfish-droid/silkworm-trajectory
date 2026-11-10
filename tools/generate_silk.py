#!/usr/bin/env python3
"""Generate virtual silk trajectories from motion-model.json (stochastic layer on real unified paths)."""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from copy import deepcopy
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description='Batch virtual silk from motion-model.json')
    p.add_argument('--input', '-i', required=True, help='motion-model.json path')
    p.add_argument('--output', '-o', default='curves-generated.json', help='output JSON path')
    p.add_argument('--count', '-n', type=int, default=5, help='number of virtual worms')
    p.add_argument('--seed', type=int, default=42, help='RNG seed (reproducible)')
    p.add_argument('--noise', type=float, default=1.0, help='noise scale multiplier')
    p.add_argument('--scale', type=float, default=1.0, help='xy scale on mm coordinates')
    p.add_argument('--worm-id', type=int, default=None, help='use only this wormId as template')
    return p.parse_args()


def lognormal_sample(rng: random.Random, mu: float, sigma: float) -> float:
    return math.exp(rng.gauss(mu, sigma))


def perturb_trajectory(traj: dict, rng: random.Random, noise: float, scale: float, synth: dict):
    stoch = (synth or {}).get('stochasticLayer', {})
    step_cfg = stoch.get('stepLength_mm', {})
    turn_cfg = stoch.get('turn_rad', {})
    width_cfg = stoch.get('width_mm', {})
    sigma_step = float(step_cfg.get('sigma', 0.15)) * noise
    sigma_turn = float(turn_cfg.get('sigma', 0.08)) * noise
    sigma_width = float(width_cfg.get('sigma', 0.06)) * noise
    mu_step = float(step_cfg.get('mu', 0))

    pts = deepcopy(traj.get('points') or [])
    if len(pts) < 2:
        return None

    out = []
    for i, p in enumerate(pts):
        if p.get('x_mm') is None or p.get('y_mm') is None:
            return None
        x, y = float(p['x_mm']) * scale, float(p['y_mm']) * scale
        if 0 < i < len(pts) - 1:
            jx = rng.gauss(0, sigma_step * max(0.5, abs(p.get('width_mm') or 1)))
            jy = rng.gauss(0, sigma_step * max(0.5, abs(p.get('width_mm') or 1)))
            x += jx
            y += jy
        w = float(p.get('width_mm') or 1) * (1 + rng.gauss(0, sigma_width) * noise)
        out.append({
            'u': p.get('u', i / max(1, len(pts) - 1)),
            'x_mm': round(x, 4),
            'y_mm': round(y, 4),
            'z_mm': p.get('z_mm', 0),
            'kind': p.get('kind', 'stroke'),
            'strokeIndex': p.get('strokeIndex'),
            'width_mm': round(max(0.01, w), 4),
            'turn_jitter_rad': round(rng.gauss(0, sigma_turn), 6) if i else 0,
        })

    return {
        'sourceWormId': traj.get('wormId'),
        'pointCount': len(out),
        'generator': {
            'tool': 'tools/generate_silk.py',
            'noise': noise,
            'scale': scale,
            'note': 'synthetic perturbation of measured template — not a physical measurement',
        },
        'points': out,
        'segments': traj.get('segments', []),
    }


def main():
    args = parse_args()
    src = Path(args.input)
    if not src.is_file():
        print(f'Input not found: {src}', file=sys.stderr)
        return 2
    try:
        data = json.loads(src.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        print(f'Invalid JSON: {e}', file=sys.stderr)
        return 2

    trajs = data.get('unifiedTrajectories') or []
    if args.worm_id is not None:
        trajs = [t for t in trajs if t.get('wormId') == args.worm_id]
    if not trajs:
        print('No unifiedTrajectories in motion model', file=sys.stderr)
        return 2

    template = trajs[0]
    synth = data.get('synthesis') or {}
    rng = random.Random(args.seed)

    generated = []
    for k in range(args.count):
        child_rng = random.Random(args.seed + k * 104729)
        g = perturb_trajectory(template, child_rng, args.noise, args.scale, synth)
        if g:
            g['virtualId'] = k + 1
            generated.append(g)

    out_doc = {
        'schema': 'curves3d/v2',
        'unit': 'mm',
        'generator': 'generate_silk.py',
        'templateMotionModel': str(src),
        'seed': args.seed,
        'count': len(generated),
        'curves': generated,
        'provenance': 'synthetic_from_measured_template',
    }
    Path(args.output).write_text(json.dumps(out_doc, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Wrote {len(generated)} curves -> {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
