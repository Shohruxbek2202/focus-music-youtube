"""
5-QISM: Orkestrator (pipeline).

Hammasini bitta buyruq bilan bog'laydi: musiqa -> piano video -> thumbnail -> metadata.
YouTube'ga yuklash (6-qism) keyinroq shu yerga qo'shiladi.

Ishlatish:
    python3 pipeline.py --minutes 30 --mood calm
    python3 pipeline.py --minutes 30 --mood warm --seed 55
    python3 pipeline.py --minutes 30 --mood random   # tasodifiy mood tanlaydi
"""

import argparse
import json
import os
import random
import time

import music_gen
import video_gen
import thumbnail_gen
import metadata_gen

OUTPUT_ROOT = "output"


def run(minutes, mood, seed=None):
    if mood == "random":
        mood = random.choice(list(music_gen.MOODS.keys()))
    if seed is None:
        seed = random.randint(0, 999_999)

    slug = f"{mood}_{seed}_{int(time.time())}"
    outdir = os.path.join(OUTPUT_ROOT, slug)

    print(f"\n=== [1/4] Musiqa generatsiya qilinmoqda (mood={mood}, seed={seed}, {minutes} daq) ===")
    gen = music_gen.generate(minutes=minutes, mood=mood, seed=seed, outdir=outdir)
    print(f"    -> {gen['duration_seconds']/60:.1f} daqiqa audio tayyor")

    print("=== [2/4] Piano-roll video render qilinmoqda (bu eng uzun bosqich) ===")
    video_path = video_gen.render(outdir)
    print(f"    -> {video_path}")

    print("=== [3/4] Thumbnail yasalmoqda ===")
    with open(os.path.join(outdir, "gen_meta.json")) as f:
        gen_meta = json.load(f)

    print("=== [4/4] Metadata (sarlavha/tavsif/teglar) generatsiya qilinmoqda ===")
    meta_result = metadata_gen.generate(
        outdir, mood, gen["duration_seconds"] / 60, seed=seed, chords=gen_meta["chords"]
    )
    thumb_path = thumbnail_gen.generate(
        outdir, meta_result["title"], gen["duration_seconds"] / 60, mood
    )
    print(f"    -> {thumb_path}")
    print(f"    -> sarlavha: {meta_result['title']}")

    print(f"\nTayyor! Hammasi shu papkada: {os.path.abspath(outdir)}")
    return outdir


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=float, default=30.0)
    parser.add_argument("--mood", type=str, default="calm",
                         choices=list(music_gen.MOODS.keys()) + ["random"])
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    run(args.minutes, args.mood, args.seed)
