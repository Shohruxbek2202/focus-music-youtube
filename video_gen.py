"""
2-QISM: Kinematik video renderer ("Lock in Focus" uslubi).

Berilgan outdir ichidagi background.jpg + track.wav + gen_meta.json + (ixtiyoriy)
youtube_metadata.json asosida focus_video.mp4 yasaydi:

  - fon rasmi + juda sekin Ken Burns zoom
  - B&W kino-grade + vignette + film grain
  - pastda oltin rangli audio-reaktiv to'lqin vizualizatori (WAV'dan FFT)
  - ~6s qora intro: markazda motivatsion matn (fade in/out)
  - qisqa audio loop ffmpeg bilan kerakli uzunlikka cho'ziladi (-stream_loop)

Faqat numpy + Pillow (chizish) va ffmpeg (kodlash).

Ishlatish:
    python3 video_gen.py output/monk_7 --minutes 30
    python3 video_gen.py output/monk_7 --preview 20
"""

import argparse
import json
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1600, 900
FPS = 20
BG_UPDATE_EVERY = 10         # Ken Burns fonni har necha kadrga bir yangilash
INTRO_SECONDS = 6.0
KEN_BURNS_ZOOM = 0.10        # video oxiriga borib +10% zoom
GRAIN_AMOUNT = 2.4           # film grain kuchi (past bo'lsa fayl hajmi kichik)
CRF = 23

FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")


def _font(name, size):
    path = os.path.join(FONT_DIR, name)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)


# ---------------------------------------------------------------- audio -> envelope
def _load_mono(wav_path):
    with wave.open(wav_path) as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    if ch == 2:
        raw = raw.reshape(-1, 2).mean(axis=1)
    return raw, sr


def _log_bins(n_fft, sr, n_bars, f_lo=60, f_hi=8000):
    freqs = np.fft.rfftfreq(n_fft, 1 / sr)
    edges = np.logspace(np.log10(f_lo), np.log10(f_hi), n_bars + 1)
    idx = [np.searchsorted(freqs, e) for e in edges]
    return idx


# ---------------------------------------------------------------- grade helpers
def _vignette(w, h, strength=0.55):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    d = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
    v = 1.0 - strength * np.clip((d - 0.35) / 0.9, 0, 1) ** 2
    return v[:, :, None]


def _grade(rgb):
    """uint8 RGB -> B&W kino-grade (uint8 RGB)."""
    f = rgb.astype(np.float32)
    lum = 0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]
    lum /= 255.0
    # S-egri kontrast
    lum = np.clip(lum, 0, 1)
    lum = lum ** 1.28
    lum = 0.5 - 0.5 * np.cos(np.pi * np.clip(lum, 0, 1))
    lum = 0.5 - 0.5 * np.cos(np.pi * np.clip(lum, 0, 1))   # ikki marta = kuchliroq S-kontrast
    lum = 0.035 + 0.90 * lum
    # sovuq tus
    tint = np.array([0.92, 0.98, 1.11], dtype=np.float32)
    out = lum[..., None] * 255.0 * tint
    return out


def _make_grain_bank(w, h, n=12, amount=GRAIN_AMOUNT, seed=0):
    rng = np.random.default_rng(seed)
    return [(rng.standard_normal((h, w, 1)).astype(np.float32) * amount) for _ in range(n)]


# ---------------------------------------------------------------- text layers
def _wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def _text_layer(text, font, max_w, line_gap=1.35, align_center=True):
    """Oq matnli RGBA layer (numpy: rgb float + alpha 0..1)."""
    tmp = Image.new("RGB", (10, 10))
    d0 = ImageDraw.Draw(tmp)
    lines = _wrap(d0, text, font, max_w)
    asc, desc = font.getmetrics()
    lh = int((asc + desc) * line_gap)
    tw = max((d0.textlength(ln, font=font) for ln in lines), default=1)
    th = lh * len(lines)
    img = Image.new("L", (int(tw) + 8, th + 8), 0)
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        lw = d.textlength(ln, font=font)
        x = (img.width - lw) / 2 if align_center else 0
        d.text((x, i * lh), ln, font=font, fill=255)
    alpha = np.asarray(img, dtype=np.float32) / 255.0
    return alpha


def _paste_alpha(frame, alpha, top_left, color, opacity):
    """frame (float32 HxWx3) ustiga alpha layer'ni color rangida opacity bilan qo'yadi."""
    if opacity <= 0:
        return
    x0, y0 = top_left
    ah, aw = alpha.shape
    x0 = int(x0); y0 = int(y0)
    x1, y1 = min(frame.shape[1], x0 + aw), min(frame.shape[0], y0 + ah)
    if x1 <= x0 or y1 <= y0:
        return
    a = alpha[: y1 - y0, : x1 - x0, None] * opacity
    region = frame[y0:y1, x0:x1, :]
    frame[y0:y1, x0:x1, :] = region * (1 - a) + np.asarray(color, dtype=np.float32) * a


# ---------------------------------------------------------------- render
def render(outdir, target_minutes=None, preview_seconds=None):
    bg_path = os.path.join(outdir, "background.jpg")
    wav_path = os.path.join(outdir, "track.wav")
    out_path = os.path.join(outdir, "focus_video.mp4")
    meta_path = os.path.join(outdir, "gen_meta.json")
    ymeta_path = os.path.join(outdir, "youtube_metadata.json")

    gen_meta = json.load(open(meta_path))
    ymeta = json.load(open(ymeta_path)) if os.path.exists(ymeta_path) else {}

    loop_seconds = gen_meta["loop_seconds"]
    if target_minutes is None:
        target_minutes = gen_meta.get("target_seconds", 1800) / 60.0
    duration = preview_seconds or target_minutes * 60.0
    n_frames = int(duration * FPS)

    intro_text = ymeta.get("intro_text") or gen_meta.get("intro_template", "").format(
        hz=int(gen_meta.get("base_freq", 0))
    )
    title_text = ymeta.get("title_short") or gen_meta.get("theme_display", "")
    caption = f"{gen_meta.get('theme_display','')}  ·  {int(gen_meta.get('base_freq',0))}Hz"

    # --- fon rasmi ---
    src = Image.open(bg_path).convert("RGB")
    if src.size != (WIDTH, HEIGHT):
        src = src.resize((WIDTH, HEIGHT), Image.LANCZOS)
    src_arr = np.asarray(src)

    vign = _vignette(WIDTH, HEIGHT)
    grain_bank = _make_grain_bank(WIDTH, HEIGHT, seed=gen_meta.get("seed") or 0)

    # --- audio / vizualizator tayyorgarligi ---
    mono, sr = _load_mono(wav_path)
    loop_n = len(mono)
    N_FFT = 2048
    N_BARS = 40                       # bir tomon uchun; markazdan ikki yonga oyna qilib chiziladi
    bin_idx = _log_bins(N_FFT, sr, N_BARS, f_lo=70, f_hi=6000)
    window = np.hanning(N_FFT).astype(np.float32)
    bar_smooth = np.zeros(N_BARS, dtype=np.float32)
    # yuqori chastotalarni ko'tarish uchun yumshoq "whitening" egri chizig'i
    whiten = np.linspace(1.0, 3.2, N_BARS).astype(np.float32)

    viz_half = WIDTH * 0.42          # markazdan har tomonga
    viz_cx = WIDTH / 2
    viz_baseline = int(HEIGHT * 0.72)
    bar_w = viz_half / N_BARS
    viz_max_h = HEIGHT * 0.065
    GOLD = np.array([255, 200, 115], dtype=np.float32)
    GOLD_HOT = np.array([255, 235, 185], dtype=np.float32)

    # --- matn layerlari ---
    intro_font = _font("Oswald-Variable.ttf", 44)
    title_font = _font("Oswald-Variable.ttf", 40)
    cap_font = _font("Oswald-Variable.ttf", 26)
    intro_alpha = _text_layer(intro_text, intro_font, int(WIDTH * 0.62)) if intro_text else None
    title_alpha = _text_layer(title_text.upper(), title_font, int(WIDTH * 0.7)) if title_text else None
    cap_alpha = _text_layer(caption, cap_font, WIDTH) if caption else None

    # --- ffmpeg ---
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS),
        "-i", "pipe:0",
        "-stream_loop", "-1", "-i", wav_path,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "faster", "-crf", str(CRF), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{duration:.2f}",
        "-movflags", "+faststart",
        out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    bg_cache = None
    for fi in range(n_frames):
        t = fi / FPS

        # ---- Ken Burns fon (har BG_UPDATE_EVERY kadrga bir marta qayta gradelanadi) ----
        if bg_cache is None or fi % BG_UPDATE_EVERY == 0:
            prog = t / max(duration, 1e-6)
            zoom = 1.0 + KEN_BURNS_ZOOM * prog
            cw, chh = WIDTH / zoom, HEIGHT / zoom
            # yengil diagonal pan
            px = (WIDTH - cw) * (0.5 + 0.18 * np.sin(prog * np.pi))
            py = (HEIGHT - chh) * (0.5 + 0.12 * prog)
            crop = src.crop((int(px), int(py), int(px + cw), int(py + chh))).resize(
                (WIDTH, HEIGHT), Image.BILINEAR
            )
            graded = _grade(np.asarray(crop)) * vign
            bg_cache = graded

        frame = bg_cache.copy()

        # ---- intro dim: ilk INTRO_SECONDS davomida fon qorayadi ----
        if t < INTRO_SECONDS + 1.0:
            dim = np.clip((t - INTRO_SECONDS) / 1.0 + 1.0, 0, 1)  # 0->1
            dim = 0.16 + 0.84 * dim
            frame *= dim

        # ---- audio-reaktiv to'lqin ----
        center = int((t % loop_seconds) * sr)
        s0 = center - N_FFT // 2
        if s0 < 0:
            chunk = np.concatenate([mono[s0:], mono[:s0 + N_FFT]])
        elif s0 + N_FFT > loop_n:
            chunk = np.concatenate([mono[s0:], mono[: s0 + N_FFT - loop_n]])
        else:
            chunk = mono[s0:s0 + N_FFT]
        spec = np.abs(np.fft.rfft(chunk * window))
        bars = np.array([
            spec[bin_idx[i]:max(bin_idx[i] + 1, bin_idx[i + 1])].mean()
            for i in range(N_BARS)
        ], dtype=np.float32)
        bars = np.log1p(bars * whiten * 5.0)
        mx = bars.max()
        if mx > 1e-6:
            bars /= mx
        # attack tez, release sekin
        up = bars > bar_smooth
        bar_smooth = np.where(up, bar_smooth + 0.5 * (bars - bar_smooth),
                              bar_smooth + 0.14 * (bars - bar_smooth)).astype(np.float32)

        viz_op = float(np.clip((t - INTRO_SECONDS + 1.5) / 2.0, 0, 1)) * 0.8
        if viz_op > 0:
            for i, val in enumerate(bar_smooth):
                bh = int(val * viz_max_h) + 2
                y_top = max(0, viz_baseline - bh)
                y_bot = min(HEIGHT, viz_baseline + bh)
                col = GOLD * (1 - val) + GOLD_HOT * val
                blend = col * viz_op
                keep = 1 - viz_op
                bw = max(2, int(bar_w * 0.58))
                for sign in (-1, 1):                      # markazdan chapga va o'ngga oyna
                    if sign > 0:
                        bx0 = int(viz_cx + (i + 0.6) * bar_w)
                    else:
                        bx0 = int(viz_cx - (i + 0.6) * bar_w) - bw
                    bx1 = min(WIDTH, bx0 + bw)
                    bx0 = max(0, bx0)
                    if bx1 <= bx0:
                        continue
                    reg = frame[y_top:y_bot, bx0:bx1, :]
                    frame[y_top:y_bot, bx0:bx1, :] = reg * keep + blend

        # ---- matnlar ----
        # intro matn: 0.6->1 (fade in), hold, ->0 (fade out)
        if intro_alpha is not None and t < INTRO_SECONDS:
            if t < 1.2:
                op = t / 1.2
            elif t < INTRO_SECONDS - 1.6:
                op = 1.0
            else:
                op = max(0.0, (INTRO_SECONDS - t) / 1.6)
            _paste_alpha(frame, intro_alpha,
                         ((WIDTH - intro_alpha.shape[1]) / 2, (HEIGHT - intro_alpha.shape[0]) / 2),
                         (245, 245, 245), op * 0.96)

        # sarlavha: introdan keyin ~14s ko'rinadi, keyin so'nadi
        if title_alpha is not None and INTRO_SECONDS <= t < INTRO_SECONDS + 16:
            lt = t - INTRO_SECONDS
            op = min(1.0, lt / 1.5) if lt < 13 else max(0.0, (16 - lt) / 3.0)
            _paste_alpha(frame, title_alpha,
                         ((WIDTH - title_alpha.shape[1]) / 2, HEIGHT * 0.12),
                         (240, 240, 240), op * 0.9)

        # doimiy sokin izoh (pastki chap)
        if cap_alpha is not None and t > INTRO_SECONDS:
            op = min(1.0, (t - INTRO_SECONDS) / 3.0) * 0.32
            _paste_alpha(frame, cap_alpha, (WIDTH * 0.045, HEIGHT * 0.9),
                         (230, 230, 230), op)

        # ---- film grain ----
        frame += grain_bank[fi % len(grain_bank)]

        np.clip(frame, 0, 255, out=frame)
        proc.stdin.write(frame.astype(np.uint8).tobytes())

        if fi % (FPS * 120) == 0:
            print(f"  kadr {fi}/{n_frames}  (t={t/60:.1f} daq)")

    proc.stdin.close()
    proc.wait()
    return out_path


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("outdir")
    p.add_argument("--minutes", type=float, default=None)
    p.add_argument("--preview", type=float, default=None)
    args = p.parse_args()
    out = render(args.outdir, target_minutes=args.minutes, preview_seconds=args.preview)
    print(f"Tayyor: {out}")
