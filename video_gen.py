"""
2-QISM: Piano-roll video renderer (Synthesia uslubi).

Berilgan outdir ichidagi track.wav + events.json asosida piano_video.mp4 yasaydi.
Faqat numpy (chizish) va ffmpeg (kodlash) ishlatiladi. Nota qidiruvi numpy
vektorlashtirilgan bo'lgani uchun uzun (30+ daqiqalik) videolarda ham tez ishlaydi.

Ishlatish:
    python3 video_gen.py output/calm_101
    python3 video_gen.py output/calm_101 --preview 15
"""

import argparse
import json
import os
import subprocess
import sys
import numpy as np

WIDTH, HEIGHT = 1280, 720
FPS = 30
FALL_SECONDS = 3.0
KB_HEIGHT = 160
MIDI_LOW, MIDI_HIGH = 48, 84  # C3..C6

BG_TOP = np.array([10, 12, 30])
BG_BOTTOM = np.array([2, 2, 8])
WHITE_KEY_COLOR = np.array([235, 235, 240])
BLACK_KEY_COLOR = np.array([25, 25, 30])
WHITE_KEY_BORDER = np.array([150, 150, 155])
CHORD_COLOR = np.array([70, 200, 220])
ARP_COLOR = np.array([250, 190, 90])
KEY_HILITE_CHORD = np.array([60, 170, 190])
KEY_HILITE_ARP = np.array([235, 150, 40])

WHITE_OFFSETS_IN_OCTAVE = [0, 2, 4, 5, 7, 9, 11]
BLACK_AFTER_WHITE = {0: 1, 1: 3, 3: 6, 4: 8, 5: 10}


def build_keyboard_layout():
    white_midis = [m for m in range(MIDI_LOW, MIDI_HIGH + 1) if (m % 12) in WHITE_OFFSETS_IN_OCTAVE]
    n_white = len(white_midis)
    white_w = WIDTH / n_white
    white_x = {m: i * white_w for i, m in enumerate(white_midis)}

    black_x = {}
    black_w = white_w * 0.6
    for m in white_midis[:-1]:
        semitone = m % 12
        idx = WHITE_OFFSETS_IN_OCTAVE.index(semitone)
        if idx in BLACK_AFTER_WHITE:
            black_midi = m + 1
            center = white_x[m] + white_w
            black_x[black_midi] = center - black_w / 2
    return white_x, white_w, black_x, black_w


WHITE_X, WHITE_W, BLACK_X, BLACK_W = build_keyboard_layout()
IS_BLACK = lambda m: (m % 12) not in WHITE_OFFSETS_IN_OCTAVE


def key_column(midi):
    if IS_BLACK(midi):
        x0 = BLACK_X.get(midi, 0)
        return x0, x0 + BLACK_W
    x0 = WHITE_X.get(midi, 0)
    return x0, x0 + WHITE_W


def make_background():
    grad = np.linspace(0, 1, HEIGHT)[:, None]
    bg = (BG_TOP[None, :] * (1 - grad) + BG_BOTTOM[None, :] * grad)
    return np.broadcast_to(bg[:, None, :], (HEIGHT, WIDTH, 3)).astype(np.uint8).copy()


def draw_rect(frame, x0, x1, y0, y1, color):
    x0 = max(0, int(x0)); x1 = min(WIDTH, int(x1))
    y0 = max(0, int(y0)); y1 = min(HEIGHT, int(y1))
    if x1 <= x0 or y1 <= y0:
        return
    frame[y0:y1, x0:x1] = color


def draw_keyboard(frame, active_now):
    kb_top = HEIGHT - KB_HEIGHT
    for m, x in WHITE_X.items():
        color = WHITE_KEY_COLOR
        if m in active_now:
            color = KEY_HILITE_CHORD if active_now[m] == "chord" else KEY_HILITE_ARP
        draw_rect(frame, x, x + WHITE_W, kb_top, HEIGHT, color)
        draw_rect(frame, x, x + 1.5, kb_top, HEIGHT, WHITE_KEY_BORDER)
    black_h = int(KB_HEIGHT * 0.62)
    for m, x in BLACK_X.items():
        color = BLACK_KEY_COLOR
        if m in active_now:
            color = KEY_HILITE_CHORD if active_now[m] == "chord" else KEY_HILITE_ARP
        draw_rect(frame, x, x + BLACK_W, kb_top, kb_top + black_h, color)


def render(outdir, preview_seconds=None):
    audio_file = os.path.join(outdir, "track.wav")
    events_file = os.path.join(outdir, "events.json")
    output_file = os.path.join(outdir, "piano_video.mp4")

    with open(events_file) as f:
        data = json.load(f)
    events = data["events"]
    total_duration = data["n_samples"] / data["sr"]

    starts = np.array([e["start"] for e in events])
    durs = np.array([e["dur"] for e in events])
    midis = np.array([e["midi"] for e in events])
    is_chord = np.array([e["type"] == "chord" for e in events])

    duration = preview_seconds if preview_seconds else total_duration
    n_frames = int(duration * FPS)
    kb_top = HEIGHT - KB_HEIGHT
    fall_zone_h = kb_top
    bg_template = make_background()

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS),
        "-i", "pipe:0",
        "-i", audio_file,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_file,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for frame_idx in range(n_frames):
        t = frame_idx / FPS
        frame = bg_template.copy()

        active_mask = (starts <= t) & (t <= starts + durs)
        falling_mask = (t < starts) & ((starts - t) <= FALL_SECONDS)

        active_now = {}
        for m, c in zip(midis[active_mask], is_chord[active_mask]):
            active_now[int(m)] = "chord" if c else "arp"

        idxs = np.nonzero(falling_mask)[0]
        for i in idxs:
            s, d, m, c = starts[i], durs[i], int(midis[i]), is_chord[i]
            progress = 1 - (s - t) / FALL_SECONDS
            bottom_y = fall_zone_h * progress
            length_px = max(6, (d / FALL_SECONDS) * fall_zone_h)
            top_y = bottom_y - length_px
            x0, x1 = key_column(m)
            color = CHORD_COLOR if c else ARP_COLOR
            draw_rect(frame, x0 + 1, x1 - 1, top_y, bottom_y, color)

        draw_keyboard(frame, active_now)
        proc.stdin.write(frame.tobytes())

        if frame_idx % (FPS * 60) == 0:
            print(f"  frame {frame_idx}/{n_frames}  (t={t/60:.1f} min)")

    proc.stdin.close()
    proc.wait()
    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("outdir")
    parser.add_argument("--preview", type=float, default=None)
    args = parser.parse_args()

    print(f"Video render: {args.outdir}")
    out = render(args.outdir, preview_seconds=args.preview)
    print(f"Tayyor: {out}")
