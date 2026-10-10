#!/usr/bin/env python3
"""r27: 32x32 pixel icons for the hand grenades (pure stdlib PNG writer).
usage: python3 tools/make_grenade_icons_r27.py   -> assets/aiarsenal/textures/item/grenade_*.png"""
import os, struct, zlib, math

OUT = os.path.join(os.path.dirname(__file__), '..', 'mods', 'aiarsenal', 'src', 'main', 'resources',
                   'assets', 'aiarsenal', 'textures', 'item')
N = 32

def png(path, px):
    raw = b''.join(b'\x00' + bytes(c for p in row for c in p) for row in px)
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    data = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', N, N, 8, 6, 0, 0, 0))
    data += chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'wb').write(data)

def icon(body, band=None, lever=(150, 150, 150), outline=(20, 20, 20)):
    px = [[(0, 0, 0, 0)] * N for _ in range(N)]
    # body: ellipse centred low on the icon (a classic egg-shaped grenade)
    cx, cy, rx, ry = 15.5, 18.5, 9.5, 10.5
    for y in range(N):
        for x in range(N):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1.0:
                shade = 0.75 + 0.35 * (1.0 - (x - cx) / rx) * 0.5 - 0.25 * max(0.0, (y - cy) / ry)
                c = tuple(max(0, min(255, int(v * shade))) for v in body)
                if band and abs(y - 19) <= 1 and d > 0.25:
                    c = band
                px[y][x] = c + (255,)
            elif d <= 1.12:
                px[y][x] = outline + (255,)
    # fuse cap (dark) and lever (lighter)
    for y in range(7, 12):
        for x in range(12, 20):
            px[y][x] = (60, 60, 62, 255)
    for x in range(11, 22):
        px[7][x] = outline + (255,)
    for i in range(6):
        px[6 - i // 2][20 + i] = lever + (255,)
    px[5][25] = lever + (255,)
    return px

KINDS = {
    'grenade_rgd5': dict(body=(70, 84, 46)),                       # RGD-5 olive
    'grenade_f1': dict(body=(96, 110, 58), band=(60, 70, 36)),     # F-1 lemon, ribbed
    'grenade_flashbang': dict(body=(70, 70, 74), band=(235, 235, 220)),
    'grenade_smoke_white': dict(body=(214, 214, 210)),
    'grenade_smoke_red': dict(body=(170, 36, 30), band=(230, 200, 60)),
    'grenade_smoke_green': dict(body=(40, 130, 46), band=(230, 230, 210)),
    'grenade_smoke_blue': dict(body=(38, 84, 190), band=(230, 230, 210)),
    'grenade_incendiary': dict(body=(120, 72, 40), band=(230, 130, 30)),
}

if __name__ == '__main__':
    for name, kw in KINDS.items():
        png(os.path.join(OUT, name + '.png'), icon(**kw))
        print('wrote', name)
