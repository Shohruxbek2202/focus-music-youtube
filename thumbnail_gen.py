"""
4-QISM: Thumbnail generatori ("Lock in Focus" uslubi).

background.jpg ni oladi, B&W kino-grade + vignette qo'yadi, ustiga bitta katta
konsept so'z (Anton shrift) va kichik subtitr (davomiylik · Hz) chizadi.

Ishlatish:
    python3 thumbnail_gen.py output/monk_7
"""

import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720
FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")


def _font(name, size):
    path = os.path.join(FONT_DIR, name)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)


def _cover(img):
    img = img.convert("RGB")
    r_src, r_dst = img.width / img.height, W / H
    if r_src > r_dst:
        nh, nw = H, int(round(H * r_src))
    else:
        nw, nh = W, int(round(W / r_src))
    img = img.resize((nw, nh), Image.LANCZOS)
    return img.crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))


def _grade_bw(img):
    f = np.asarray(img, dtype=np.float32)
    lum = (0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]) / 255.0
    lum = 0.5 - 0.5 * np.cos(np.pi * np.clip(lum ** 1.12, 0, 1))
    lum = 0.05 + 0.9 * lum
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vig = 1.0 - 0.6 * np.clip((d - 0.3) / 0.9, 0, 1) ** 2
    tint = np.array([0.93, 0.98, 1.10], dtype=np.float32)
    out = np.clip(lum[..., None] * vig[..., None] * 255.0 * tint, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def _fit_font(draw, text, font_name, max_w, start=210, min_size=90):
    size = start
    while size > min_size:
        f = _font(font_name, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 6
    return _font(font_name, min_size)


def generate(outdir, word=None, duration_min=30, hz=None, mood=None):
    ymeta_path = os.path.join(outdir, "youtube_metadata.json")
    gmeta_path = os.path.join(outdir, "gen_meta.json")
    ymeta = json.load(open(ymeta_path)) if os.path.exists(ymeta_path) else {}
    gmeta = json.load(open(gmeta_path)) if os.path.exists(gmeta_path) else {}

    word = (word or ymeta.get("thumb_word") or gmeta.get("theme_display") or "FOCUS").upper()
    hz = hz or ymeta.get("hz") or int(gmeta.get("base_freq", 0))
    subtitle = f"{int(round(duration_min))} MIN  ·  {hz}Hz  ·  FOCUS MUSIC"

    bg_path = os.path.join(outdir, "background.jpg")
    img = _grade_bw(_cover(Image.open(bg_path))).convert("RGB")

    # pastdan yuqoriga qoraytiruvchi gradient (matn o'qilishi uchun)
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        grad.putpixel((0, y), int(180 * max(0, (y / H - 0.35) / 0.65) ** 1.5))
    grad = grad.resize((W, H))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.composite(black, img, grad)

    draw = ImageDraw.Draw(img)
    word_font = _fit_font(draw, word, "Anton-Regular.ttf", W * 0.88)
    sub_font = _font("Oswald-Variable.ttf", 40)

    wl = draw.textlength(word, font=word_font)
    wa, wd_ = word_font.getmetrics()
    wh = wa + wd_
    wx = (W - wl) / 2
    wy = H * 0.60 - wh / 2

    # yumshoq soya
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.text((wx, wy), word, font=word_font, fill=(0, 0, 0, 220))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    img.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), shadow.split()[3])

    draw.text((wx, wy), word, font=word_font, fill=(245, 245, 245))

    sl = draw.textlength(subtitle, font=sub_font)
    draw.text(((W - sl) / 2, wy + wh + 14), subtitle, font=sub_font, fill=(255, 205, 120))

    out_path = os.path.join(outdir, "thumbnail.png")
    img.save(out_path)
    return out_path


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("outdir")
    p.add_argument("--word", default=None)
    p.add_argument("--duration-min", type=float, default=30.0)
    p.add_argument("--hz", type=int, default=None)
    args = p.parse_args()
    print("Tayyor:", generate(args.outdir, args.word, args.duration_min, args.hz))
