# focus-music-youtube

A pipeline that generates "Lock in Focus"-style **focus / deep-work music**
videos from scratch every time, creatively, and uploads them to YouTube.

Each render:

- **theme** (`warrior`, `stoic`, `monk`, `midnight`, `storm`, `summit`) picked at random
- **background image** — Openverse (CC-licensed, **no key needed**) or Pexels (if `PEXELS_API_KEY` is set); if neither works, a procedural background
- **music** — slow ambient synth pads + low drone + a solfeggio tone + binaural beat + a noise layer; a short seamless loop
- **video** — B&W cinematic grade + slow Ken Burns zoom + grain + vignette + a gold audio-reactive waveform visualizer at the bottom + a ~6s motivational intro text
- **metadata** — English concept title, motivational description, tags
- **thumbnail** — B&W frame + one big word (Anton font)

## Usage

```bash
pip install numpy Pillow
# for uploading to YouTube, also:
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

# optional — for higher-quality images (falls back to Openverse otherwise):
export PEXELS_API_KEY=...          # free: https://www.pexels.com/api/

python3 pipeline.py --minutes 45 --theme random
python3 pipeline.py --minutes 45 --theme monk --seed 7 --preview 20   # quick test
python3 youtube_upload.py output/monk_7_XX␣ --privacy unlisted
```

Individual stages: `assets.py`, `music_gen.py`, `metadata_gen.py`, `video_gen.py`,
`thumbnail_gen.py` — each also works as a standalone CLI.

## Automation

`.github/workflows/auto_upload.yml` runs the pipeline every 6 hours and
uploads the video as public. A manual run (Actions → Run workflow) lets you
choose `privacy` / `theme` / `minutes`.

Required GitHub Secrets: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`
(`PEXELS_API_KEY` — optional).

## Settings

- Video: `WIDTH/HEIGHT/FPS/CRF/GRAIN_AMOUNT` at the top of `video_gen.py`
  (default 1600×900 @ 20fps; 45 min ≈ 16 min render, ≈ 250 MB).
- Themes / frequencies / chords / intro text: `themes.py`.
- Image queries: the `queries` list under each theme.

## License note

When a Pexels image is used, photographer credit is added to the description automatically.
