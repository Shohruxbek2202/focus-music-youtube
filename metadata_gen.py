"""
PART 3: Metadata generator (English, "Lock in Focus" style).

From gen_meta.json (theme, frequency, key) plus the background image attribution
it generates the YouTube title / description / tags, and also the intro text for
the video and the thumbnail word. Slightly different every time, driven by seed.

Usage:
    python3 metadata_gen.py output/monk_7 --duration-min 30
"""

import argparse
import json
import os
import random

from themes import THEMES

TITLE_TEMPLATES = [
    "{concept} | {context}",
    "{concept} — {hz}Hz Focus Music | {dur} min",
    "{concept} | Lock In Focus ({hz}Hz)",
    "{concept} | {dur} min Deep Focus · {hz}Hz",
]

INTRO_LINES = [
    "Take your phone, put it in another room. The next {dur} minutes are for one thing only.",
    "Focus is a muscle. Today we train it for {dur} minutes.",
    "Big things get done in small steps. Let's begin.",
    "No one is coming to save you. You start — now.",
    "There is no perfect moment. There is only this one.",
]

DESC_INTRO = [
    "This is fully original ambient focus music, generated algorithmically. "
    "No words, no ad breaks, nothing to pull your attention away.",
    "Every track is generated programmatically from scratch — never repeated. "
    "For deep work, study and meditation.",
]

DESC_BODY = """🎧 Style: {theme_display} — slow synth pads, low drone, a {hz}Hz tone and a binaural beat ({beat}Hz)
⏱ Length: ~{dur} minutes
🎼 Key shift: {key:+d} semitones · chords: {chords}
🔊 Best experienced: on headphones, or low as background

This track is composed procedurally and is completely original — safe to leave playing in the background while you work or study.

{credit}#focusmusic #studymusic #ambient #deepwork #{theme}"""

TAGS_BASE = [
    "focus music", "study music", "concentration music", "deep work music",
    "ambient music", "study with me", "reading music", "work music",
    "background music", "binaural beats", "solfeggio", "no ads music", "lock in",
]


def _thumb_word(concept):
    words = concept.upper().split()
    if len(concept) <= 9:
        return concept.upper()
    return max(words, key=len)


def generate(outdir, duration_min, seed=None, bg_info=None):
    gen_meta = json.load(open(os.path.join(outdir, "gen_meta.json")))
    theme = gen_meta["theme"]
    cfg = THEMES[theme]
    rng = random.Random(seed)

    concept = rng.choice(cfg["concepts"])
    context = rng.choice(cfg["contexts"])
    hz = int(gen_meta.get("base_freq", 0))
    beat = int(gen_meta.get("beat_hz", 0))
    key = int(gen_meta.get("key_shift", 0))
    dur = int(round(duration_min))
    chords = " → ".join("-".join(c) for c in gen_meta.get("chords", []))

    title = rng.choice(TITLE_TEMPLATES).format(concept=concept, context=context, hz=hz, dur=dur)

    # intro text: the theme's own template + one generic line
    intro_text = cfg["intro"].format(hz=hz) + " " + rng.choice(INTRO_LINES).format(dur=dur)

    credit = ""
    if bg_info and bg_info.get("source") == "pexels":
        who = bg_info.get("photographer") or "Pexels"
        credit = f"📷 Image: {who} / Pexels ({bg_info.get('pexels_url', 'pexels.com')})\n\n"
    elif bg_info and bg_info.get("source") == "openverse":
        who = bg_info.get("photographer") or "unknown artist"
        lic = (bg_info.get("license") or "").upper()
        link = bg_info.get("pexels_url") or bg_info.get("photographer_url") or "openverse.org"
        credit = f"📷 Image: {who} — {lic} ({link}) · via openverse.org\n\n"

    description = (
        rng.choice(DESC_INTRO) + "\n\n" +
        DESC_BODY.format(
            theme_display=cfg["display"], hz=hz, beat=beat, dur=dur, key=key,
            chords=chords or "generative", credit=credit, theme=theme,
        )
    )

    tags = list(dict.fromkeys(
        TAGS_BASE + [f"{hz}hz", f"{hz} hz music", theme, cfg["display"].lower(),
                     concept.lower(), f"{dur} minute focus"]
    ))

    result = {
        "title": title,
        "description": description,
        "tags": tags,
        "intro_text": intro_text,
        "title_short": concept,
        "thumb_word": _thumb_word(concept),
        "hz": hz,
        "theme": theme,
    }

    with open(os.path.join(outdir, "youtube_metadata.json"), "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    with open(os.path.join(outdir, "description.txt"), "w") as f:
        f.write(f"TITLE:\n{title}\n\nDESCRIPTION:\n{description}\n\nTAGS:\n{', '.join(tags)}\n")

    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("outdir")
    p.add_argument("--duration-min", type=float, default=30.0)
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()
    bg = None
    bgp = os.path.join(args.outdir, "background_info.json")
    if os.path.exists(bgp):
        bg = json.load(open(bgp))
    print(json.dumps(generate(args.outdir, args.duration_min, args.seed, bg), indent=2, ensure_ascii=False))
