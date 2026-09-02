#!/usr/bin/env python3
"""PWAアイコンを生成する（依存ライブラリなし）。

    python3 gen_icons.py

icon-192.png / icon-512.png / icon-512-maskable.png を書き出す。
3倍解像度で描いてから縮小することでアンチエイリアスをかけている。
"""
import struct
import zlib

BRAND1 = (0x6D, 0x5C, 0xFF)
BRAND2 = (0xA8, 0x55, 0xF7)
WHITE = (0xFF, 0xFF, 0xFF)
CYAN = (0x7D, 0xD3, 0xFC)
GREEN = (0x4A, 0xDE, 0x80)

SS = 3  # スーパーサンプリング倍率


def write_png(path, w, h, rgb):
    """rgb: bytearray(w*h*3) をPNG(RGB8)として書き出す。"""
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type 0
        raw += rgb[y * w * 3:(y + 1) * w * 3]

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def blend(dst, src, a):
    return tuple(int(round(d * (1 - a) + s * a)) for d, s in zip(dst, src))


def render(size, rounded=True):
    """size×size のアイコンを描く。rounded=False は maskable 用の全面塗り。"""
    S = size * SS
    r = int(S * 0.22)          # 角丸半径
    buf = [[(0, 0, 0)] * S for _ in range(S)]

    # --- 背景（角丸 + 斜めグラデーション） ---
    for y in range(S):
        for x in range(S):
            if rounded:
                cx = min(max(x, r), S - 1 - r)
                cy = min(max(y, r), S - 1 - r)
                if (x - cx) ** 2 + (y - cy) ** 2 > r * r:
                    buf[y][x] = (0xF6, 0xF7, 0xFC)   # 角の外側（下地色）
                    continue
            t = (x + y) / (2.0 * S)
            buf[y][x] = tuple(int(round(a + (b - a) * t)) for a, b in zip(BRAND1, BRAND2))

    # --- カード（外枠：白） ---
    ch = int(S * 0.60)
    cw = int(ch * 63 / 88)
    x0 = (S - cw) // 2
    y0 = (S - ch) // 2
    x1, y1 = x0 + cw, y0 + ch
    ow = max(2, int(S * 0.022))          # 外枠の線幅
    ix0 = x0 + int(cw * 0.20)            # 内枠（左に寄せてセンタリングのズレを表現）
    ix1 = x1 - int(cw * 0.12)
    iy0 = y0 + int(ch * 0.11)
    iy1 = y1 - int(ch * 0.11)
    iw = max(2, int(S * 0.013))

    def in_stroke(x, y, ax0, ay0, ax1, ay1, w):
        inside = ax0 <= x < ax1 and ay0 <= y < ay1
        core = ax0 + w <= x < ax1 - w and ay0 + w <= y < ay1 - w
        return inside and not core

    for y in range(max(0, y0 - ow), min(S, y1 + ow)):
        for x in range(max(0, x0 - ow), min(S, x1 + ow)):
            # 余白帯（左右）を薄く塗って「どこを測っているか」を示す
            if iy0 <= y < iy1 and (x0 <= x < ix0 or ix1 <= x < x1):
                buf[y][x] = blend(buf[y][x], GREEN, 0.62)
            if in_stroke(x, y, ix0, iy0, ix1, iy1, iw):
                buf[y][x] = CYAN
            if in_stroke(x, y, x0, y0, x1, y1, ow):
                buf[y][x] = WHITE

    # --- 3x3 平均で縮小 ---
    out = bytearray(size * size * 3)
    for y in range(size):
        for x in range(size):
            rs = gs = bs = 0
            for dy in range(SS):
                rowbuf = buf[y * SS + dy]
                for dx in range(SS):
                    p = rowbuf[x * SS + dx]
                    rs += p[0]; gs += p[1]; bs += p[2]
            n = SS * SS
            i = (y * size + x) * 3
            out[i] = rs // n
            out[i + 1] = gs // n
            out[i + 2] = bs // n
    return out


if __name__ == '__main__':
    for size in (192, 512):
        write_png('icon-%d.png' % size, size, size, render(size, rounded=True))
        print('icon-%d.png' % size)
    write_png('icon-512-maskable.png', 512, 512, render(512, rounded=False))
    print('icon-512-maskable.png')
