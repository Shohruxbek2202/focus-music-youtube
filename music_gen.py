"""
1-QISM: Musiqa generatori (variatsiyali, ixtiyoriy davomiylik, faqat numpy).

Har chaqirilganda (yoki seed o'zgarsa) boshqacha ohang chiqadi: mood (kayfiyat),
tonalik (key), akkord tartibi va arpeggio naqshi tasodifiy tanlanadi/generatsiya
qilinadi — shu bilan YouTube uchun "har video boshqacha original kontent" talabi
qondiriladi.

Ishlatish (mustaqil holda ham ishlaydi):
    python3 music_gen.py --minutes 30 --mood calm --seed 7 --outdir output/mysong

Modul sifatida:
    from music_gen import generate
    result = generate(minutes=30, mood="calm", seed=7, outdir="output/mysong")
"""

import argparse
import json
import os
import wave
import numpy as np

SR = 44100
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Har bir mood: (akkord progressiyasi — root-position, C asosida yozilgan,
#                akkord davomiyligi soniyada, arpeggio zichligi, tembr sozlamalari)
MOODS = {
    "calm": {
        "chords": [
            ["C4", "E4", "G4", "B4"],   # Imaj7
            ["A3", "C4", "E4", "G4"],   # vi7
            ["F3", "A3", "C4", "E4"],   # IVmaj7
            ["G3", "B3", "D4", "F4"],   # V7
        ],
        "chord_duration": 14.0,
        "arp_density": (3, 6),
        "voices": 3,
        "harmonic_amps": (1.0, 0.35, 0.12),
    },
    "warm": {
        "chords": [
            ["F3", "A3", "C4", "E4"],   # IVmaj7
            ["D3", "F3", "A3", "C4"],   # ii7
            ["A#2", "D3", "F3", "A3"],  # bVIImaj7
            ["C3", "E3", "G3", "A#3"],  # I7
        ],
        "chord_duration": 16.0,
        "arp_density": (2, 4),
        "voices": 4,
        "harmonic_amps": (1.0, 0.45, 0.2, 0.08),
    },
    "dreamy": {
        "chords": [
            ["E3", "G#3", "B3", "D#4"],  # Imaj7
            ["C#3", "E3", "G#3", "B3"],  # vi7
            ["A2", "C#3", "E3", "G#3"],  # IVmaj7
            ["B2", "D#3", "F#3", "A3"],  # V7
        ],
        "chord_duration": 13.0,
        "arp_density": (4, 7),
        "voices": 3,
        "harmonic_amps": (1.0, 0.3, 0.15, 0.05),
    },
    "night": {
        "chords": [
            ["A3", "C4", "E4", "G4"],   # i7
            ["F3", "A3", "C4", "E4"],   # VImaj7
            ["C4", "E4", "G4", "B4"],   # IIImaj7
            ["G3", "B3", "D4", "F4"],   # VII7
        ],
        "chord_duration": 15.0,
        "arp_density": (2, 5),
        "voices": 3,
        "harmonic_amps": (1.0, 0.4, 0.1),
    },
}

CROSSFADE = 3.0
MASTER_VOLUME = 0.5


def note_to_midi(note: str) -> int:
    if note[1] == "#":
        name, octave = note[:2], int(note[2:])
    else:
        name, octave = note[0], int(note[1:])
    semitone = NOTE_NAMES.index(name)
    return (octave + 1) * 12 + semitone


def midi_to_note(midi: int) -> str:
    name = NOTE_NAMES[midi % 12]
    octave = midi // 12 - 1
    return f"{name}{octave}"


def midi_to_freq(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12))


def note_to_freq(note: str) -> float:
    return midi_to_freq(note_to_midi(note))


def transpose_chords(chords, semitones):
    return [[midi_to_note(note_to_midi(n) + semitones) for n in chord] for chord in chords]


def adsr(n_samples, sr, attack, release):
    env = np.ones(n_samples)
    a = max(1, min(int(sr * attack), n_samples // 2))
    r = max(1, min(int(sr * release), n_samples // 2))
    env[:a] = np.linspace(0, 1, a)
    env[-r:] = np.linspace(1, 0, r)
    return env


def pad_tone(freq, duration, sr, voices, harmonic_amps, detune_cents=6, seed=None):
    n = int(duration * sr)
    t = np.arange(n) / sr
    out = np.zeros(n)
    rng = np.random.default_rng(seed if seed is not None else int(freq * 1000) % (2 ** 31))
    for _ in range(voices):
        detune = rng.uniform(-1, 1) * detune_cents
        f = freq * (2 ** (detune / 1200))
        voice = np.zeros(n)
        for i, amp in enumerate(harmonic_amps):
            voice += amp * np.sin(2 * np.pi * f * (i + 1) * t)
        out += voice / voices
    out *= adsr(n, sr, attack=min(2.5, duration * 0.25), release=min(3.5, duration * 0.35))
    return out


def chord_pad(freqs, duration, sr, voices, harmonic_amps, amp=0.18, seed_base=0):
    n = int(duration * sr)
    mix = np.zeros(n)
    for i, f in enumerate(freqs):
        mix += pad_tone(note_to_freq(f), duration, sr, voices, harmonic_amps, seed=seed_base + i)
    mix *= amp / len(freqs)
    return mix


def pluck_note(freq, duration, sr, amp=0.12):
    n = int(duration * sr)
    t = np.arange(n) / sr
    tone = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * freq * 2 * t)
    env = np.exp(-t * 2.2)
    return amp * tone * env


def add_at(track_l, track_r, signal, start_sample, pan=0.5):
    n = len(signal)
    end = start_sample + n
    if end > len(track_l):
        n = len(track_l) - start_sample
        if n <= 0:
            return
        signal = signal[:n]
        end = start_sample + n
    track_l[start_sample:end] += signal * (1 - pan)
    track_r[start_sample:end] += signal * pan


def simple_reverb(signal, sr, delay_ms=280, decay=0.32, repeats=4):
    out = signal.copy()
    delay_samples = int(sr * delay_ms / 1000)
    tap = signal.copy()
    for _ in range(repeats):
        tap = np.roll(tap, delay_samples) * decay
        tap[:delay_samples] = 0
        out = out + tap
    return out


def generate(minutes=30.0, mood="calm", seed=None, key_shift=None, outdir="output/track",
             arpeggio_on=True):
    if mood not in MOODS:
        mood = "calm"
    cfg = MOODS[mood]
    rng_master = np.random.default_rng(seed)
    if key_shift is None:
        key_shift = int(rng_master.integers(-3, 4))  # -3..+3 yarim ton

    chords = transpose_chords(cfg["chords"], key_shift)
    chord_duration = cfg["chord_duration"]
    voices = cfg["voices"]
    harmonic_amps = cfg["harmonic_amps"]
    arp_lo, arp_hi = cfg["arp_density"]

    target_seconds = minutes * 60
    cycle_len = len(chords) * chord_duration
    cycles = max(1, int(np.ceil(target_seconds / cycle_len)))

    total_duration = cycles * cycle_len + 5
    n_total = int(total_duration * SR)
    left = np.zeros(n_total)
    right = np.zeros(n_total)

    events = []
    cursor = 0.0
    rng = np.random.default_rng(seed)

    for cycle in range(cycles):
        for ci, chord in enumerate(chords):
            start_sample = int(cursor * SR)
            pad = chord_pad(chord, chord_duration + CROSSFADE, SR, voices, harmonic_amps,
                             seed_base=cycle * 10 + ci)
            add_at(left, right, pad, start_sample, pan=0.5)
            add_at(right, left, pad, start_sample, pan=0.5)

            for note in chord:
                events.append({"midi": note_to_midi(note), "start": cursor,
                               "dur": chord_duration + CROSSFADE, "type": "chord"})

            if arpeggio_on:
                n_notes = rng.integers(arp_lo, arp_hi + 1)
                for _ in range(n_notes):
                    note = chord[rng.integers(0, len(chord))]
                    octave_up = rng.choice([0, 1])
                    midi = note_to_midi(note) + (12 if octave_up else 0)
                    freq = midi_to_freq(midi)
                    t_offset = rng.uniform(0.5, chord_duration - 1.0)
                    abs_start = cursor + t_offset
                    note_start = int(abs_start * SR)
                    pan = rng.uniform(0.15, 0.85)
                    note_sig = pluck_note(freq, 2.5, SR, amp=0.09)
                    add_at(left, right, note_sig, note_start, pan=pan)
                    events.append({"midi": midi, "start": abs_start, "dur": 1.1, "type": "arp"})

            cursor += chord_duration

    left = simple_reverb(left, SR)
    right = simple_reverb(right, SR)
    peak = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-9)
    scale = MASTER_VOLUME / peak
    left *= scale
    right *= scale

    os.makedirs(outdir, exist_ok=True)
    wav_path = os.path.join(outdir, "track.wav")
    events_path = os.path.join(outdir, "events.json")
    meta_path = os.path.join(outdir, "gen_meta.json")

    _write_wav(wav_path, left, right, SR)

    gen_meta = {
        "mood": mood, "seed": seed, "key_shift": key_shift,
        "chords": chords, "chord_duration": chord_duration,
        "cycles": cycles, "duration_seconds": len(left) / SR,
    }
    with open(events_path, "w") as f:
        json.dump({"events": events, "sr": SR, "n_samples": len(left)}, f)
    with open(meta_path, "w") as f:
        json.dump(gen_meta, f, indent=2)

    return {
        "wav": wav_path, "events": events_path, "meta": meta_path,
        "duration_seconds": len(left) / SR, "mood": mood, "seed": seed, "key_shift": key_shift,
    }


def _write_wav(path, left, right, sr):
    left_i16 = np.clip(left, -1, 1) * 32767
    right_i16 = np.clip(right, -1, 1) * 32767
    interleaved = np.empty(len(left_i16) * 2, dtype=np.int16)
    interleaved[0::2] = left_i16.astype(np.int16)
    interleaved[1::2] = right_i16.astype(np.int16)
    with wave.open(path, "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(interleaved.tobytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=float, default=30.0)
    parser.add_argument("--mood", type=str, default="calm", choices=list(MOODS.keys()))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--outdir", type=str, default="output/track")
    args = parser.parse_args()

    print(f"Generatsiya: mood={args.mood} minutes={args.minutes} seed={args.seed}")
    result = generate(minutes=args.minutes, mood=args.mood, seed=args.seed, outdir=args.outdir)
    print(json.dumps(result, indent=2))
