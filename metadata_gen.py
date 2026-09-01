"""
3-QISM: Metadata generatori (o'zbekcha, "Lock in Focus" uslubi).

gen_meta.json (mavzu, chastota, tonalik) + fon rasmi atributsiyasi asosida
YouTube sarlavha / tavsif / teglar, shuningdek video uchun intro matni va
thumbnail so'zini generatsiya qiladi. Har safar seed bo'yicha biroz boshqacha.

Ishlatish:
    python3 metadata_gen.py output/monk_7 --duration-min 30
"""

import argparse
import json
import os
import random

from themes import THEMES

TITLE_TEMPLATES = [
    "{concept} | {context}",
    "{concept} — {hz}Hz Focus Music | {dur} daqiqa",
    "{concept} | Fokusni qulflash ({hz}Hz)",
    "{concept} | {dur} daqiqa chuqur diqqat · {hz}Hz",
]

INTRO_LINES = [
    "Telefonni ol, boshqa xonaga qo'y. Keyingi {dur} daqiqa faqat bitta ish uchun.",
    "Diqqat — bu mushak. Bugun uni {dur} daqiqa mashq qildiramiz.",
    "Kichik qadamlar bilan katta ishlar bitadi. Boshladik.",
    "Hech kim kelib seni qutqarmaydi. O'zing boshlaysan — hozir.",
    "Mukammal payt yo'q. Faqat shu payt bor.",
]

DESC_INTRO = [
    "Bu — algoritmik yo'l bilan yaratilgan, to'liq original ambient fokus musiqasi. "
    "So'zsiz, reklama pauzalarisiz, chalg'itmaydigan.",
    "Har bir trek dasturiy tarzda, noldan generatsiya qilinadi — takrorlanmaydi. "
    "Deep work, o'qish va meditatsiya uchun.",
]

DESC_BODY = """🎧 Uslub: {theme_display} — sekin synth pad'lar, past drone, {hz}Hz ohang va binaural urish ({beat}Hz)
⏱ Davomiyligi: ~{dur} daqiqa
🎼 Tonallik siljishi: {key:+d} yarim ton · akkordlar: {chords}
🔊 Eng yaxshi natija: naushnikda yoki past ovozda fon sifatida

Bu trek protsedural tarzda tuzilgan va butunlay original — ishlayotgan yoki o'qiyotgan paytingizda fonda tinglash uchun xavfsiz.

{credit}#focusmusic #studymusic #ambient #deepwork #{theme}"""

TAGS_BASE = [
    "focus music", "study music", "concentration music", "deep work music",
    "ambient music", "fokus musiqa", "diqqat musiqa", "oqish uchun musiqa",
    "ishlash uchun musiqa", "binaural beats", "solfeggio", "no ads music",
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

    # intro matn: mavzuning o'z shabloni + umumiy bitta qator
    intro_text = cfg["intro"].format(hz=hz) + " " + rng.choice(INTRO_LINES).format(dur=dur)

    credit = ""
    if bg_info and bg_info.get("source") == "pexels":
        who = bg_info.get("photographer") or "Pexels"
        credit = f"📷 Rasm: {who} / Pexels ({bg_info.get('pexels_url', 'pexels.com')})\n\n"
    elif bg_info and bg_info.get("source") == "openverse":
        who = bg_info.get("photographer") or "noma'lum muallif"
        lic = (bg_info.get("license") or "").upper()
        link = bg_info.get("pexels_url") or bg_info.get("photographer_url") or "openverse.org"
        credit = f"📷 Rasm: {who} — {lic} ({link}) · openverse.org orqali\n\n"

    description = (
        rng.choice(DESC_INTRO) + "\n\n" +
        DESC_BODY.format(
            theme_display=cfg["display"], hz=hz, beat=beat, dur=dur, key=key,
            chords=chords or "generativ", credit=credit, theme=theme,
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
