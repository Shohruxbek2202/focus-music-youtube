"""
3-QISM: Thumbnail generatori.

Videodan bir kadr olib (ffmpeg), ustiga sarlavha va davomiylik matnini
Pillow bilan chizadi.

Ishlatish:
    python3 thumbnail_gen.py output/calm_101 --title "Deep Focus Piano" --duration-min 30
"""

import argparse
import json
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

def _first_existing(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return paths[-1]


FONT_BOLD = _first_existing([
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",  # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Ubuntu (GitHub Actions)
])
FONT_REGULAR = _first_existing([
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
])


def _extract_frame(video_path, seek_seconds, out_path):
    cmd = [
        "ffmpeg", "-y", "-ss", str(seek_seconds), "-i", video_path,
        "-frames:v", "1", "-update", "1", out_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def generate(outdir, title, duration_min, mood, seek_seconds=None):
    video_path = os.path.join(outdir, "piano_video.mp4")
    raw_frame_path = os.path.join(outdir, "_thumb_raw.png")
    out_path = os.path.join(outdir, "thumbnail.png")

    if seek_seconds is None:
        meta_path = os.path.join(outdir, "gen_meta.json")
        seek_seconds = 20.0
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            seek_seconds = min(30.0, meta.get("duration_seconds", 60) * 0.05)

    _extract_frame(video_path, seek_seconds, raw_frame_path)

    img = Image.open(raw_frame_path).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img, "RGBA")

    band_h = 220
    draw.rectangle([0, H - band_h, W, H], fill=(0, 0, 0, 150))

    title_font = ImageFont.truetype(FONT_BOLD, 62)
    subtitle_font = ImageFont.truetype(FONT_REGULAR, 32)

    subtitle_text = f"{duration_min:.0f} MIN  ·  {mood.upper()} FOCUS MUSIC"

    def centered_x(text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return (W - (bbox[2] - bbox[0])) / 2

    draw.text((centered_x(title, title_font), H - 190), title, font=title_font,
               fill=(255, 255, 255, 255))
    draw.text((centered_x(subtitle_text, subtitle_font), H - 100), subtitle_text,
               font=subtitle_font, fill=(245, 200, 98, 255))

    img.save(out_path)
    os.remove(raw_frame_path)
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("outdir")
    parser.add_argument("--title", default="Deep Focus Piano")
    parser.add_argument("--duration-min", type=float, default=30.0)
    parser.add_argument("--mood", default="calm")
    args = parser.parse_args()

    out = generate(args.outdir, args.title, args.duration_min, args.mood)
    print(f"Tayyor: {out}")
