  function weaveCellSpecAt(agent, ix, iy, seed) {
    const rng = mulberry32(seed >>> 0);
    const base = Math.min(agent.w, agent.h);
    const shape = agent.shape || 'plain';
    const cell = { w: agent.w, h: agent.h, shape, ix, iy, notch: null, island: null };
    if (shape === 'notch' || shape === 'notchIsland') {
      const corner = Math.floor(rng() * 4);
      cell.notch = {
        corner,
        cx: (corner % 2 === 1 ? 1 : -1) * agent.w / 2,
        cy: (corner < 2 ? -1 : 1) * agent.h / 2,
        r: base * (0.24 + rng() * 0.20),
      };
    }
    if (shape === 'island' || shape === 'notchIsland') {
      cell.island = {
        cx: (rng() - 0.5) * agent.w * 0.30,
        cy: (rng() - 0.5) * agent.h * 0.30,
        r: base * (0.14 + rng() * 0.12),
      };
    }
    return cell;
  }

  function weaveCellSpec(agent) { return weaveCellSpecAt(agent, 0, 0, (agent.seed >>> 0) || 1); }

