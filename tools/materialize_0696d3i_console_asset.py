#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha" / "assets" / "airship_props" / "set01_redux"
SOURCE = SRC / "navigation_console_base.png"
OUTPUT = SRC / "navigation_console_body_d3i.png"

def is_beige_candidate(r: int, g: int, b: int, a: int) -> bool:
    return (
        a > 0
        and r >= 205
        and g >= 155
        and b >= 95
        and (r - b) >= 60
        and (g - b) >= 35
    )

def main() -> None:
    im = Image.open(SOURCE).convert("RGBA")
    px = im.load()
    w, h = im.size
    candidate = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            candidate[y][x] = is_beige_candidate(*px[x, y])

    seen = [[False] * w for _ in range(h)]
    remove: set[tuple[int, int]] = set()

    for y in range(h):
        for x in range(w):
            if not candidate[y][x] or seen[y][x]:
                continue

            q = deque([(x, y)])
            seen[y][x] = True
            comp: list[tuple[int, int]] = []
            touches_edge = False
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                touches_edge |= cx == 0 or cy == 0 or cx == w - 1 or cy == h - 1
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and candidate[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        q.append((nx, ny))

            # Matte is the large beige field connected to the canvas edge. Interior brass/light
            # details are deliberately preserved.
            if touches_edge or len(comp) > 500:
                remove.update(comp)

    out = im.copy()
    out_px = out.load()
    for x, y in remove:
        r, g, b, _ = out_px[x, y]
        out_px[x, y] = (r, g, b, 0)

    # Two-pixel connected fringe cleanup only around already-removed matte.
    for _ in range(2):
        extra: set[tuple[int, int]] = set()
        for y in range(h):
            for x in range(w):
                if (x, y) in remove:
                    continue
                r, g, b, a = out_px[x, y]
                if a == 0 or not (r >= 190 and g >= 140 and b >= 85 and (r - b) >= 55):
                    continue
                if any((x + dx, y + dy) in remove for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))):
                    extra.add((x, y))
        for x, y in extra:
            r, g, b, _ = out_px[x, y]
            out_px[x, y] = (r, g, b, 0)
        remove.update(extra)

    out.save(OUTPUT)

    alpha = [a for *_, a in out.getdata()]
    transparent = sum(a == 0 for a in alpha)
    opaque = sum(a == 255 for a in alpha)
    beige_opaque = sum(
        a > 0 and is_beige_candidate(r, g, b, a)
        for r, g, b, a in out.getdata()
    )

    if out.size != (112, 80):
        raise SystemExit(f"unexpected output size {out.size}")
    if set(alpha) != {0, 255}:
        raise SystemExit("D3-I console must remain hard-alpha")
    if transparent < 3000:
        raise SystemExit(f"matte cleanup too weak: transparent={transparent}")
    if beige_opaque > 250:
        raise SystemExit(f"too much beige matte survived: beigeOpaque={beige_opaque}")
    if opaque < 5000:
        raise SystemExit(f"machine detail over-cut: opaque={opaque}")

    print(f"D3-I console materialized: {OUTPUT}")
    print(f"transparent={transparent} opaque={opaque} beigeOpaque={beige_opaque}")

if __name__ == "__main__":
    main()
