#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arka plan silici (Pillow tabanlı, AI model bağımlılığı yok).
Karakter illüstrasyonlarında:
 1) Kenar baskın renginden yola çıkarak "arka plan rengi" tahmin eder,
 2) 4 köşeden başlayan flood fill (renk toleranslı) ile arka plana temas eden
    tüm pikselleri bulur,
 3) Bulunan maskeye 1 px erozyon + 3/5 px GaussBlur uygular (kenar yumuşatma),
 4) Alpha kanalına mask yazar (karakterlerin dışı saydam = arka plan silinmiş).
 5) Orijinal görselin üzerine yazar (!!! dosyalarınızın yedeğini alın !!!).

macOS Python 3.15 (RC) üzerinde çalışması için onnxruntime / rembg / numpy
gerektirmez — saf Pillow + stdlib kullanır.
"""

from __future__ import annotations

import argparse
import os
import unicodedata
from collections import deque

from PIL import Image, ImageFilter, ImageDraw


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------
def _bul(klasor: str) -> dict[str, str]:
    """Klasördeki PNG/JPG dosyalarının NFC-nomalize adı -> tam yol eşlemesini döner."""
    bulunan: dict[str, str] = {}
    for d in os.listdir(klasor):
        nd = unicodedata.normalize("NFC", d)
        if nd.startswith("._"):
            continue
        if nd.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            bulunan[nd] = os.path.join(klasor, d)
    return bulunan


def _kenar_rengi(im: Image.Image) -> tuple[int, int, int]:
    """Kenarlardan (4 köşe + 4 orta) örnek alarak RGB arka plan rengi tahmin eder."""
    w, h = im.size
    ornekler: list[tuple[int, int, int]] = []
    for (x, y) in [
        (0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
        (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2),
        (w // 3, h // 6), (2 * w // 3, h // 6),
        (w // 3, 5 * h // 6), (2 * w // 3, 5 * h // 6),
    ]:
        px = im.getpixel((max(0, min(w - 1, x)), max(0, min(h - 1, y))))
        ornekler.append((px[0], px[1], px[2]))
    r = sum(o[0] for o in ornekler) // len(ornekler)
    g = sum(o[1] for o in ornekler) // len(ornekler)
    b = sum(o[2] for o in ornekler) // len(ornekler)
    return (r, g, b)


def _renk_farki(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    """Renkler arası toplam kanalsal fark (basit L1 metriği)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _floodfill_mask(
    im: Image.Image,
    baslangic: list[tuple[int, int]],
    hedef_renk: tuple[int, int, int],
    tolerans: int,
) -> Image.Image:
    """BFS flood fill: başlangıç noktalarından başlayıp renk farkı <= tolerans
    olan tüm komşu pikselleri işaretler. Sonuç L mod maske (255 = arka plan)."""
    w, h = im.size
    rgb = im.convert("RGB")
    maske = Image.new("L", (w, h), 0)
    # Hız: piksel erişimini load() ile
    pxs = rgb.load()
    mload = maske.load()

    kuyruk: deque[tuple[int, int]] = deque()
    for (sx, sy) in baslangic:
        sx = max(0, min(w - 1, sx))
        sy = max(0, min(h - 1, sy))
        if mload[sx, sy] == 0 and _renk_farki(pxs[sx, sy], hedef_renk) <= tolerans:
            mload[sx, sy] = 255
            kuyruk.append((sx, sy))

    while kuyruk:
        x, y = kuyruk.popleft()
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and mload[nx, ny] == 0:
                if _renk_farki(pxs[nx, ny], hedef_renk) <= tolerans:
                    mload[nx, ny] = 255
                    kuyruk.append((nx, ny))
    return maske


def _karakter_kutusu(arka_plan_maskesi: Image.Image) -> tuple[int, int, int, int]:
    """Arka plan maskesinin TERSİ olan (karakter = arka plan olmayan)
    sınırlayıcı kutuyu bulur."""
    w, h = arka_plan_maskesi.size
    m = arka_plan_maskesi.load()
    min_x, min_y = w, h
    max_x, max_y = -1, -1
    for y in range(h):
        for x in range(w):
            if m[x, y] != 255:  # Karakter pikseli
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y
    if max_x < 0:
        return (0, 0, w - 1, h - 1)
    return (min_x, min_y, max_x, max_y)


# ---------------------------------------------------------------------------
# Tek görsel için arka plan temizleme
# ---------------------------------------------------------------------------
def arka_plani_sil(
    yol: str,
    tolerans: int = 52,
    feather: int = 3,
    erozyon: int = 1,
    yaz: bool = True,
) -> Image.Image:
    """
    tolerans: Renk farkı toplamı (R+G+B kanalları) — arka planla çok az
              farklı olan gölge / gürültü piksellerini de yakalamak için
              40..70 arası iyi çalışır (beyaz/bej arka planlar).
    feather : Kenar yumuşatma miktarı (GaussBlur radius). 2..5
    erozyon : Flood fill maskesini karaktere doğru 1-2 px daraltır — yanlış
              arka plan pikseli karaktere sızarsa arttır.
    yaz     : True ise orijinal dosyanın ÜSTÜNE yazar.
    """
    im = Image.open(yol).convert("RGBA")
    w, h = im.size

    # 1) Arka plan rengi tahmin et
    tahmin_rengi = _kenar_rengi(im)
    # 2) Başlangıç noktaları: dört köşe + her kenardan 3 örnek (bol başlangıç)
    baslangic: list[tuple[int, int]] = []
    for s in range(0, 11):
        t = s / 10.0
        baslangic.append((int((w - 1) * t), 0))
        baslangic.append((int((w - 1) * t), h - 1))
        baslangic.append((0, int((h - 1) * t)))
        baslangic.append((w - 1, int((h - 1) * t)))

    # 3) Flood fill: arka planı işaretleyen L mod maske
    ap_maske = _floodfill_mask(im, baslangic, tahmin_rengi, tolerans)

    # 4) Maskeye erozyon uygula (feather sızmadan önce 1 px daralt —
    #    karakter kenarlarının yanlışlıkla arka plan diye sayılmasını azalt)
    if erozyon > 0:
        ap_maske = ap_maske.filter(ImageFilter.MinFilter(2 * erozyon + 1))

    # 5) Feather (kenar yumuşatma): gauss blur ile alpha yumuşak kenarlar
    if feather > 0:
        ap_maske = ap_maske.filter(ImageFilter.GaussianBlur(feather))

    # 6) Alpha kanalına yaz: arka plan maskesinin TERSİ karakter = görünür olsun
    #    L 255 (arka plan) → alpha 0 (saydam)
    #    L 0   (karakter) → alpha 255 (opak)
    ters_maske = Image.eval(ap_maske, lambda v: 255 - v)
    rgba = im.convert("RGBA")
    r_ch, g_ch, b_ch, _ = rgba.split()
    yeni = Image.merge("RGBA", (r_ch, g_ch, b_ch, ters_maske))

    # 7) Karakteri kutuya sıkıştır (opsiyonel, padding korunur,
    #    kare formatı bozmak istemiyoruz — orijinal boyutta kal)
    # Sadece saf beyaz (tamamen saydam) olmayan alanı korumak yeterli:
    if yaz:
        # Orijinal dosyanın üzerine kaydet (PNG olarak)
        kaydedilecek = yol
        if not kaydedilecek.lower().endswith(".png"):
            kok, _ = os.path.splitext(kaydedilecek)
            kaydedilecek = kok + "_bgsiz.png"
        yeni.save(kaydedilecek, format="PNG", optimize=True)
    return yeni


# ---------------------------------------------------------------------------
# Komut satırı
# ---------------------------------------------------------------------------
def main():
    prs = argparse.ArgumentParser(
        description="Karakter görsellerinden arka planı sil (Pillow-only)."
    )
    prs.add_argument(
        "klasor", nargs="?", default=os.path.dirname(os.path.abspath(__file__)),
        help="Görsellerin bulunduğu klasör (varsayılan: bu dosyanın klasörü)",
    )
    prs.add_argument("--tolerans", type=int, default=52, help="Renk farkı toleransı (40-70)")
    prs.add_argument("--feather", type=int, default=3, help="Kenar yumuşatma (0-6)")
    prs.add_argument("--erozyon", type=int, default=1, help="Maske daraltma (0-3)")
    prs.add_argument("--yaz", type=str, choices=("evet", "hayir"), default="evet",
                     help="Dosyaların üzerine yaz (evet/hayir)")
    args = prs.parse_args()

    klasor = os.path.abspath(args.klasor)
    if not os.path.isdir(klasor):
        raise SystemExit(f"Klasör bulunamadı: {klasor}")

    liste = _bul(klasor)
    if not liste:
        raise SystemExit(f"{klasor} içinde görsel bulunamadı.")

    yaz = args.yaz == "evet"
    for ad, yol in sorted(liste.items()):
        print(f"🖼  {ad}  (tolerans={args.tolerans} feather={args.feather} erozyon={args.erozyon})")
        try:
            arka_plani_sil(
                yol, tolerans=args.tolerans,
                feather=args.feather, erozyon=args.erozyon, yaz=yaz,
            )
            print(f"   ✓ Bitti -> {yol}")
        except Exception as e:
            print(f"   ✗ HATA: {e}")


if __name__ == "__main__":
    main()
