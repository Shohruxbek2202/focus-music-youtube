"""
1-QISM: Ambient / drone musiqa generatori ("Lock in Focus" uslubi, faqat numpy).

Har chaqirilganda (seed o'zgarsa) boshqacha chiqadi: mavzu (theme), tonalik,
akkord davomiyligi, solfeggio chastotasi va shovqin qatlami tasodifiy tanlanadi —
shu bilan "har video original kontent" talabi qondiriladi.

Xotira/vaqt tejash uchun bu modul QISQA seamless loop (bir necha daqiqa) render
qiladi; video_gen uni ffmpeg bilan kerakli uzunlikka aylantiradi (-stream_loop).

Ovoz qatlamlari:
  - sekin evolyutsiyalanuvchi synth pad'lar (akkordlar)
  - past drone (tonika, sub-oktava)
  - solfeggio shimmer (mavzu chastotasida sokin sinus)
  - binaural beat (L/R karrier farqi = beat_hz; naushnik uchun, past amplituda)
  - shovqin to'shagi (yomg'ir / shamol / havo — mavzuga qarab)
  - kamdan-kam qo'ng'iroq tovushlari (reverbli sinus)

Ishlatish:
    python3 music_gen.py --theme monk --seed 7 --outdir output/x
    from music_gen import generate
    r = generate(theme="monk", seed=7, outdir="output/x")
"""

import argparse
import json
import os
import wave

import numpy as np

from themes import THEMES, THEME_NAMES

SR = 44100
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

CROSSFADE = 5.0            # loop ulanish nuqtasi va akkordlar orasidagi crossfade
CYCLES_IN_LOOP = 2         # loop ichida progressiya necha marta takrorlanadi
MASTER_VOLUME = 0.5
DTYPE = np.float32         # xotira uchun


# ---------------------------------------------------------------- nota yordamchilari
def note_to_midi(note: str) -> int:
    if note[1] in ("#", "b"):
        name, octave = note[:2], int(note[2:])
    else:
        name, octave = note[0], int(note[1:])
    return (octave + 1) * 12 + NOTE_NAMES.index(name)


def midi_to_note(midi: int) -> str:
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def midi_to_freq(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12))


def note_to_freq(note: str) -> float:
    return midi_to_freq(note_to_midi(note))


def transpose(chords, semitones):
    return [[midi_to_note(note_to_midi(n) + semitones) for n in ch] for ch in chords]


# ---------------------------------------------------------------- signal bloklari
def _t(n):
    return np.arange(n, dtype=DTYPE) / SR


def adsr(n, attack, release):
    env = np.ones(n, dtype=DTYPE)
    a = max(1, min(int(SR * attack), n // 2))
    r = max(1, min(int(SR * release), n // 2))
    env[:a] = np.linspace(0, 1, a)
    env[-r:] = np.linspace(1, 0, r)
    return env


def pad_tone(freq, dur, voices, harmonic_amps, detune_cents=7, rng=None):
    n = int(dur * SR)
    t = _t(n)
    out = np.zeros(n, dtype=DTYPE)
    rng = rng or np.random.default_rng(int(freq * 1000) % (2 ** 31))
    for _ in range(voices):
        f = freq * (2 ** (rng.uniform(-1, 1) * detune_cents / 1200))
        # yumshoq vibrato
        vib = 1 + 0.0025 * np.sin(2 * np.pi * rng.uniform(0.05, 0.15) * t + rng.uniform(0, 6))
        phase = 2 * np.pi * f * np.cumsum(vib) / SR
        voice = np.zeros(n, dtype=DTYPE)
        for i, amp in enumerate(harmonic_amps):
            voice += amp * np.sin(phase * (i + 1))
        out += voice / voices
    out *= adsr(n, attack=min(4.0, dur * 0.3), release=min(5.0, dur * 0.4))
    return out


def chord_pad(freqs, dur, voices, harmonic_amps, amp, seed_base):
    n = int(dur * SR)
    mix = np.zeros(n, dtype=DTYPE)
    for i, f in enumerate(freqs):
        mix += pad_tone(f, dur, voices, harmonic_amps,
                        rng=np.random.default_rng(seed_base + i))
    return mix * (amp / len(freqs))


def low_drone(freq, dur, amp=0.09):
    n = int(dur * SR)
    t = _t(n)
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.03 * t)
    tone = (np.sin(2 * np.pi * freq * t)
            + 0.3 * np.sin(2 * np.pi * freq * 2 * t)
            + 0.12 * np.sin(2 * np.pi * freq * 0.5 * t))
    return (amp * tone * lfo).astype(DTYPE)


def solfeggio_shimmer(freq, dur, amp=0.016):
    n = int(dur * SR)
    t = _t(n)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t + 1.0)
    tone = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * freq * 2 * t)
    return (amp * tone * lfo).astype(DTYPE)


def binaural_pair(beat_hz, dur, carrier=126.0, amp=0.05):
    """Chapga karrier, o'ngga karrier+beat. Naushnikda 'beat_hz' urishi seziladi."""
    n = int(dur * SR)
    t = _t(n)
    swell = 0.6 + 0.4 * np.sin(2 * np.pi * 0.02 * t)
    left = amp * swell * np.sin(2 * np.pi * carrier * t)
    right = amp * swell * np.sin(2 * np.pi * (carrier + beat_hz) * t)
    return left.astype(DTYPE), right.astype(DTYPE)


def _box(x, win):
    """Vektorlashtirilgan siljuvchi o'rtacha (cumsum orqali)."""
    win = max(1, int(win))
    if win <= 1:
        return x
    c = np.cumsum(np.concatenate([np.zeros(1, dtype=np.float64), x.astype(np.float64)]))
    y = (c[win:] - c[:-win]) / win
    # uzunlikni saqlash uchun chetlarini to'ldiramiz
    pad = len(x) - len(y)
    if pad > 0:
        y = np.concatenate([np.full(pad, y[0]), y])
    return y.astype(DTYPE)


def _lowpass(x, cutoff_hz):
    """Ikki marta box-filtr = yumshoq past-o'tkazgichga yaqin (to'liq vektorlashtirilgan)."""
    win = max(1, SR / max(cutoff_hz, 20.0))
    return _box(_box(x, win), win)


def noise_bed(texture, dur, rng):
    n = int(dur * SR)
    white = rng.standard_normal(n).astype(DTYPE)
    # pushti-ga yaqin: kumulyativ + normalizatsiya
    pink = np.cumsum(white)
    pink -= pink.mean()
    pink /= (np.abs(pink).max() + 1e-9)

    presets = {
        "air":        (0.028, 900,  0.0),
        "wind":       (0.055, 500,  0.35),
        "rain":       (0.070, 2600, 0.0),
        "rain_heavy": (0.110, 4000, 0.0),
    }
    amp, cutoff, gust = presets.get(texture, presets["air"])
    t = _t(n)

    if texture in ("rain", "rain_heavy"):
        # tomchi hissi uchun tez tasodifiy modulyatsiya + past-o'tkazgich
        drops = np.abs(rng.standard_normal(n).astype(DTYPE)) ** 2
        sig = white * (0.4 + 0.6 * drops)
        sig = np.asarray(_lowpass(sig, cutoff), dtype=DTYPE)
        sig *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.05 * t)
    else:
        sig = np.asarray(_lowpass(pink, cutoff), dtype=DTYPE)
        if gust:
            g = 1 - gust + gust * (0.5 + 0.5 * np.sin(2 * np.pi * 0.06 * t + rng.uniform(0, 6)))
            sig = sig * g.astype(DTYPE)

    sig /= (np.abs(sig).max() + 1e-9)
    return (sig * amp).astype(DTYPE)


def bell(freq, dur=6.0, amp=0.06):
    n = int(dur * SR)
    t = _t(n)
    tone = (np.sin(2 * np.pi * freq * t)
            + 0.5 * np.sin(2 * np.pi * freq * 2.01 * t)
            + 0.25 * np.sin(2 * np.pi * freq * 3.0 * t))
    return (amp * tone * np.exp(-t * 0.9)).astype(DTYPE)


def simple_reverb(sig, delay_ms=320, decay=0.34, repeats=5):
    out = sig.copy()
    d = int(SR * delay_ms / 1000)
    tap = sig.copy()
    for _ in range(repeats):
        tap = np.roll(tap, d) * decay
        tap[:d] = 0
        out += tap
    return out


def add_at(track, sig, start, gain=1.0):
    end = min(len(track), start + len(sig))
    if end <= start:
        return
    track[start:end] += sig[:end - start] * gain


# ---------------------------------------------------------------- asosiy generator
def generate(theme=None, seed=None, outdir="output/track", target_minutes=45.0,
             key_shift=None, base_freq=None):
    if theme not in THEMES:
        theme = np.random.default_rng(seed).choice(THEME_NAMES) if theme in (None, "random") else "stoic"
    cfg = THEMES[theme]
    rng = np.random.default_rng(seed)

    if key_shift is None:
        key_shift = int(rng.integers(-4, 5))
    if base_freq is None:
        base_freq = float(rng.choice(cfg["freqs"]))
    beat_hz = float(cfg["beat_hz"])

    chords = transpose(cfg["progression"], key_shift)
    lo, hi = cfg["chord_seconds"]
    chord_dur = float(rng.uniform(lo, hi))
    voices = cfg["voices"]
    hamps = cfg["harmonic_amps"]
    texture = cfg["texture"]

    cycle_len = len(chords) * chord_dur
    loop_len = CYCLES_IN_LOOP * cycle_len + CROSSFADE   # crossfade quyrug'i keyin kesiladi
    n_total = int(loop_len * SR)

    left = np.zeros(n_total, dtype=DTYPE)
    right = np.zeros(n_total, dtype=DTYPE)

    # --- pad'lar (akkord bo'yicha) ---
    cursor = 0.0
    for cyc in range(CYCLES_IN_LOOP):
        for ci, chord in enumerate(chords):
            start = int(cursor * SR)
            freqs = [note_to_freq(nn) for nn in chord]
            pad = chord_pad(freqs, chord_dur + CROSSFADE, voices, hamps,
                            amp=0.20, seed_base=(cyc * 17 + ci * 3 + 100))
            add_at(left, pad, start, gain=0.5 + 0.5 * (1 - 0.15))
            add_at(right, pad, start, gain=0.5 + 0.5 * (1 - 0.15))
            # yengil stereo kengaytma: har akkordga ozgina panorama
            pan = 0.5 + 0.12 * np.sin(cyc + ci)
            add_at(left, pad, start, gain=(1 - pan) * 0.25)
            add_at(right, pad, start, gain=pan * 0.25)
            cursor += chord_dur

    # --- past drone (butun loop bo'ylab, tonika) ---
    root_midi = note_to_midi(chords[0][0]) - 12
    drone = low_drone(midi_to_freq(root_midi), loop_len, amp=0.085)
    add_at(left, drone, 0)
    add_at(right, drone, 0)

    # --- solfeggio shimmer ---
    sh = solfeggio_shimmer(base_freq, loop_len, amp=0.015)
    add_at(left, sh, 0, gain=0.9)
    add_at(right, sh, 0, gain=0.9)

    # --- binaural beat ---
    bl, br = binaural_pair(beat_hz, loop_len, amp=0.045)
    add_at(left, bl, 0)
    add_at(right, br, 0)

    # --- shovqin to'shagi ---
    nb = noise_bed(texture, loop_len, rng)
    nb2 = noise_bed(texture, loop_len, np.random.default_rng((seed or 0) + 999))
    add_at(left, nb, 0)
    add_at(right, nb2, 0)

    # --- kamdan-kam qo'ng'iroqlar ---
    n_bells = int(rng.integers(2, 5))
    for _ in range(n_bells):
        chord = chords[rng.integers(0, len(chords))]
        nn = chord[rng.integers(0, len(chord))]
        freq = note_to_freq(nn)
        b = bell(freq * 2, dur=7.0, amp=0.05)
        at = int(rng.uniform(0, loop_len - 8) * SR)
        pan = rng.uniform(0.2, 0.8)
        add_at(left, b, at, gain=(1 - pan))
        add_at(right, b, at, gain=pan)

    # --- reverb + seamless loop crossfade ---
    left = simple_reverb(left)
    right = simple_reverb(right)

    xf = int(CROSSFADE * SR)
    core = int(CYCLES_IN_LOOP * cycle_len * SR)
    for ch in (left, right):
        # loop oxiridagi quyruqni boshiga aralashtiramiz
        tail = ch[core:core + xf].copy()
        fade = np.linspace(0, 1, xf, dtype=DTYPE)
        ch[:xf] = ch[:xf] * fade + tail * (1 - fade)
    left = left[:core]
    right = right[:core]

    # --- normalizatsiya ---
    peak = max(float(np.max(np.abs(left))), float(np.max(np.abs(right))), 1e-9)
    scale = MASTER_VOLUME / peak
    left = (left * scale).astype(DTYPE)
    right = (right * scale).astype(DTYPE)

    os.makedirs(outdir, exist_ok=True)
    wav_path = os.path.join(outdir, "track.wav")
    _write_wav(wav_path, left, right)

    loop_seconds = len(left) / SR
    gen_meta = {
        "theme": theme,
        "theme_display": cfg["display"],
        "seed": seed,
        "key_shift": key_shift,
        "base_freq": base_freq,
        "beat_hz": beat_hz,
        "texture": texture,
        "chords": chords,
        "chord_duration": chord_dur,
        "loop_seconds": loop_seconds,
        "target_seconds": target_minutes * 60,
        "queries": cfg["queries"],
        "intro_template": cfg["intro"],
    }
    with open(os.path.join(outdir, "gen_meta.json"), "w") as f:
        json.dump(gen_meta, f, indent=2, ensure_ascii=False)

    return {
        "wav": wav_path,
        "loop_seconds": loop_seconds,
        "target_seconds": target_minutes * 60,
        "theme": theme,
        "base_freq": base_freq,
        "seed": seed,
    }


def _write_wav(path, left, right):
    li = np.clip(left, -1, 1) * 32767
    ri = np.clip(right, -1, 1) * 32767
    inter = np.empty(len(li) * 2, dtype=np.int16)
    inter[0::2] = li.astype(np.int16)
    inter[1::2] = ri.astype(np.int16)
    with wave.open(path, "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(inter.tobytes())


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--theme", default="random", choices=THEME_NAMES + ["random"])
    p.add_argument("--minutes", type=float, default=45.0)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--outdir", default="output/track")
    args = p.parse_args()
    res = generate(theme=args.theme, seed=args.seed, outdir=args.outdir,
                   target_minutes=args.minutes)
    print(json.dumps(res, indent=2, ensure_ascii=False))
