"""
4-QISM (avvalgi rejadagi 2-band): Metadata generatori.

Har safar biroz boshqacha, lekin mood'ga mos sarlavha/tavsif/teglar generatsiya
qiladi (shablon + tasodifiy tanlov). YouTube'ga qo'lda yoki keyingi bosqichda
avtomatik yuklashda ishlatish uchun.

Ishlatish:
    python3 metadata_gen.py output/calm_101 --mood calm --duration-min 30 --seed 101
"""

import argparse
import json
import os
import random

MOOD_WORDS = {
    "calm": {
        "adjectives": ["Calm", "Peaceful", "Gentle", "Serene", "Soft"],
        "activities": ["Deep Work", "Studying", "Reading", "Focus", "Concentration"],
        "extra_tags": ["piano music", "study music", "calm piano", "relaxing piano"],
    },
    "warm": {
        "adjectives": ["Warm", "Cozy", "Mellow", "Golden", "Tender"],
        "activities": ["Deep Work", "Late Night Study", "Coding", "Writing"],
        "extra_tags": ["warm piano", "cozy music", "jazz piano", "lofi piano"],
    },
    "dreamy": {
        "adjectives": ["Dreamy", "Ethereal", "Floating", "Airy", "Weightless"],
        "activities": ["Focus", "Meditation", "Studying", "Relaxation"],
        "extra_tags": ["dreamy piano", "ambient piano", "sleep music", "meditation music"],
    },
    "night": {
        "adjectives": ["Midnight", "Nocturne", "Late Night", "Moonlit", "Quiet"],
        "activities": ["Deep Focus", "Studying", "Coding at Night", "Insomnia Relief"],
        "extra_tags": ["night piano", "sleep piano", "midnight music", "nocturne"],
    },
}

TITLE_TEMPLATES = [
    "{adj} Piano Music for {activity} | {dur} Minutes",
    "{dur} Min {adj} Piano — {activity} Music",
    "{adj} Piano | Deep {activity} Music ({dur} Minutes)",
    "{activity} Music — {adj} Piano ({dur} Min, No Ads Mid-Roll)",
]

DESCRIPTION_TEMPLATE = """{dur} minutes of original, AI-generated {mood} piano music — composed algorithmically for {activity_lower}, deep work, and relaxation.

🎹 Style: {adj} piano, generative harmony, no lyrics
⏱ Duration: {dur} minutes
🎧 Best with headphones or quiet background listening

This track was procedurally composed (chord progression: {chords_str}) and is fully original — safe for background listening while you work or study.

#pianomusic #focusmusic #studymusic
"""

TAGS_BASE = [
    "focus music", "study music", "work music", "concentration music",
    "instrumental music", "background music", "piano", "ambient",
]


def generate(outdir, mood, duration_min, seed=None, chords=None):
    rng = random.Random(seed)
    words = MOOD_WORDS.get(mood, MOOD_WORDS["calm"])

    adj = rng.choice(words["adjectives"])
    activity = rng.choice(words["activities"])
    template = rng.choice(TITLE_TEMPLATES)
    title = template.format(adj=adj, activity=activity, dur=int(round(duration_min)))

    chords_str = " → ".join(["-".join(c) for c in chords]) if chords else "generativ"

    description = DESCRIPTION_TEMPLATE.format(
        dur=int(round(duration_min)), mood=mood, activity_lower=activity.lower(),
        adj=adj, chords_str=chords_str,
    )

    tags = list(dict.fromkeys(TAGS_BASE + words["extra_tags"] + [mood + " music", activity.lower()]))

    result = {"title": title, "description": description, "tags": tags}

    meta_path = os.path.join(outdir, "youtube_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    desc_path = os.path.join(outdir, "description.txt")
    with open(desc_path, "w") as f:
        f.write(f"TITLE:\n{title}\n\nDESCRIPTION:\n{description}\n\nTAGS:\n{', '.join(tags)}\n")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("outdir")
    parser.add_argument("--mood", default="calm")
    parser.add_argument("--duration-min", type=float, default=30.0)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    chords = None
    meta_path = os.path.join(args.outdir, "gen_meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            chords = json.load(f).get("chords")

    result = generate(args.outdir, args.mood, args.duration_min, seed=args.seed, chords=chords)
    print(json.dumps(result, indent=2, ensure_ascii=False))
