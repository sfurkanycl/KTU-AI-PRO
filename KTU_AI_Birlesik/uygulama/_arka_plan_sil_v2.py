#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Güçlendirilmiş arka plan silici.
- 2-pass flood fill (dışarıdan içeri)
- Her piksel RGB L1 farkı (max 765) toleransı YÜKSEK (200-230)
- Flood fill başlangıcı: tüm 1 px kenar + 5 px ileri
- Sonra: flood fill maskesini 2 kez MaxFilter (genişlet)
- Sonra: MinFilter 1 kez (erozyon — hatalı sızan alanları temizle)
- Sonra: GaussianBlur feather (kenar yumuşatma)
- Alpha ters maske yazılır.
"""

from __future__ import annotations
import argparse, os, unicodedata, sys
from collections import deque
from PIL import Image, ImageFilter


def _bul(klasor):
    out = {}
    for d in os.listdir(klasor):
        nd = unicodedata.normalize("NFC", d)
        if nd.startswith("._"): continue
        if nd.lower().endswith((".png",".jpg",".jpeg",".webp")):
            out[nd] = os.path.join(klasor, d)
    return out


def _floodfill(im, tol):
    w, h = im.size
    rgb = im.convert("RGB")
    p = rgb.load()
    m = Image.new("L", (w, h), 0)
    mp = m.load()
    q = deque()
    # Tüm 1px kenar piksellerini başlangıç noktası olarak kabul et
    # (arka plan her zaman dışarıdan temas eder çünkü karakter ortada)
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))
    # Başlangıç noktalarının her birinin kendi referans rengiyle karşılaştırılmasını
    # engellemek yerine — baskın referans: tüm üst 10 satır, alt 10 satır,
    # sol 10 sütun, sağ 10 sütunun ortalama R/G/B'si (tek referans rengi).
    kenar_rgb = []
    for x in range(w):
        for oy in range(min(12, h)):
            kenar_rgb.append(p[x, oy])
            kenar_rgb.append(p[x, h - 1 - oy])
    for y in range(h):
        for ox in range(min(12, w)):
            kenar_rgb.append(p[ox, y])
            kenar_rgb.append(p[w - 1 - ox, y])
    R = sum(r for r,_,_ in kenar_rgb)//len(kenar_rgb)
    G = sum(g for _,g,_ in kenar_rgb)//len(kenar_rgb)
    B = sum(b for _,_,b in kenar_rgb)//len(kenar_rgb)
    REF = (R, G, B)
    print(f"    → Referans arka plan RGB={REF}  (tol={tol})")
    # Başlangıç kuyruğunu doldur
    visited = set()
    while q:
        xy = q.popleft()
        if xy in visited: continue
        visited.add(xy)
        x, y = xy
        r,g,b = p[x,y]
        d = abs(r-REF[0]) + abs(g-REF[1]) + abs(b-REF[2])
        if d <= tol and mp[x,y] != 255:
            mp[x,y] = 255
            if x>0: q.append((x-1,y))
            if x<w-1: q.append((x+1,y))
            if y>0: q.append((x,y-1))
            if y<h-1: q.append((x,y+1))
    return m


def arka_plani_sil_v2(yol, tol=220, genislet=2, daralt=1, feather=4, yaz=True):
    im = Image.open(yol).convert("RGBA")
    w, h = im.size
    mask = _floodfill(im, tol)

    # Genişlet: arka plan maskesini büyüt (komşu 1px katmanları da dahil et)
    for _ in range(genislet):
        mask = mask.filter(ImageFilter.MaxFilter(3))
    # Daralt (erozyon): sızan kısımları geri al
    for _ in range(daralt):
        mask = mask.filter(ImageFilter.MinFilter(3))
    # Kenar yumuşatma
    if feather:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))

    # Ters maske → alpha: arka plan(255) → saydam(0)
    ters = Image.eval(mask, lambda v: 255 - v)
    r, g, b, _ = im.split()
    out = Image.merge("RGBA", (r, g, b, ters))
    if yaz:
        out.save(yol, format="PNG", optimize=True)
    return out


def main():
    prs = argparse.ArgumentParser()
    prs.add_argument("klasor", nargs="?", default=os.path.dirname(os.path.abspath(__file__)))
    prs.add_argument("--tol", type=int, default=230)
    prs.add_argument("--genislet", type=int, default=3)
    prs.add_argument("--daralt", type=int, default=1)
    prs.add_argument("--feather", type=int, default=5)
    args = prs.parse_args()
    klasor = os.path.abspath(args.klasor)
    liste = _bul(klasor)
    if not liste: raise SystemExit("Görsel yok: " + klasor)
    for ad, yol in sorted(liste.items()):
        print(f"🖼  {ad}")
        im = arka_plani_sil_v2(
            yol, tol=args.tol, genislet=args.genislet,
            daralt=args.daralt, feather=args.feather, yaz=True
        )
        ap = im.getchannel("A").load()
        w, h = im.size
        opak = saydam = 0
        for y in range(h):
            for x in range(w):
                v = ap[x,y]
                if v > 200: opak += 1
                elif v < 25: saydam += 1
        top = w*h
        print(f"    opak={opak/top*100:.1f}%  saydam={saydam/top*100:.1f}%")


if __name__ == "__main__":
    main()
