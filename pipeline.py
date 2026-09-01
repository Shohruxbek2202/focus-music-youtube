"""
5-QISM: Orkestrator (pipeline).

Hammasini bitta buyruq bilan bog'laydi:
    fon rasmi -> ambient musiqa -> metadata -> kinematik video -> thumbnail

Ishlatish:
    python3 pipeline.py --minutes 45 --theme monk
    python3 pipeline.py --minutes 45 --theme random --seed 55
    python3 pipeline.py --minutes 45 --theme random --preview 20   # tez sinov
"""

import argparse
import json
import os
import random
import time

import assets
import music_gen
import metadata_gen
import video_gen
import thumbnail_gen
from themes import THEMES, THEME_NAMES

OUTPUT_ROOT = "output"


def run(minutes, theme, seed=None, preview=None):
    if theme in (None, "random"):
        theme = random.Random(seed).choice(THEME_NAMES)
    if seed is None:
        seed = random.randint(0, 999_999)

    slug = f"{theme}_{seed}_{int(time.time())}"
    outdir = os.path.join(OUTPUT_ROOT, slug)
    os.makedirs(outdir, exist_ok=True)

    print(f"\n=== [1/5] Fon rasmi olinmoqda (theme={theme}) ===")
    bg_info = assets.fetch_background(THEMES[theme]["queries"], outdir, seed=seed)
    with open(os.path.join(outdir, "background_info.json"), "w") as f:
        json.dump(bg_info, f, indent=2, ensure_ascii=False)
    print(f"    -> {bg_info['source']}: {bg_info['path']}")

    print(f"=== [2/5] Ambient musiqa (loop) generatsiya qilinmoqda (seed={seed}) ===")
    gen = music_gen.generate(theme=theme, seed=seed, outdir=outdir, target_minutes=minutes)
    print(f"    -> {gen['loop_seconds']:.0f}s loop · base {gen['base_freq']:.0f}Hz")

    print("=== [3/5] Metadata (o'zbekcha sarlavha/tavsif/teglar) ===")
    meta = metadata_gen.generate(outdir, minutes, seed=seed, bg_info=bg_info)
    print(f"    -> {meta['title']}")

    print("=== [4/5] Kinematik video render qilinmoqda (eng uzun bosqich) ===")
    video_path = video_gen.render(outdir, target_minutes=minutes, preview_seconds=preview)
    print(f"    -> {video_path}")

    print("=== [5/5] Thumbnail yasalmoqda ===")
    thumb = thumbnail_gen.generate(outdir, word=meta["thumb_word"],
                                   duration_min=minutes, hz=meta["hz"])
    print(f"    -> {thumb}")

    print(f"\nTayyor! Hammasi shu papkada: {os.path.abspath(outdir)}")
    return outdir


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--minutes", type=float, default=45.0)
    p.add_argument("--theme", type=str, default="random", choices=THEME_NAMES + ["random"])
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--preview", type=float, default=None, help="faqat shuncha soniya render qilish (sinov)")
    args = p.parse_args()
    run(args.minutes, args.theme, args.seed, args.preview)
