# focus-music-youtube

"Lock in Focus" uslubidagi **fokus / deep-work musiqasi** videolarini har safar
noldan, kreativ tarzda generatsiya qiladigan va YouTube'ga yuklaydigan pipeline.

Har render:

- **mavzu** (`warrior`, `stoic`, `monk`, `midnight`, `storm`, `summit`) tasodifiy
- **fon rasmi** — Openverse (CC-litsenziyali, **kalit kerak emas**) yoki Pexels (`PEXELS_API_KEY` bo'lsa); ikkalasi ham ishlamasa protsedural fon
- **musiqa** — sekin ambient synth pad + past drone + solfeggio ohang + binaural beat + shovqin qatlami; qisqa seamless loop
- **video** — B&W kino-grade + sekin Ken Burns zoom + grain + vignette + pastda oltin audio-to'lqin vizualizatori + ~6s intro motivatsion matn
- **metadata** — o'zbekcha konsept-sarlavha, motivatsion tavsif, teglar
- **thumbnail** — B&W kadr + bitta katta so'z (Anton shrift)

## Ishlatish

```bash
pip install numpy Pillow
# YouTube yuklash uchun qo'shimcha:
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

# ixtiyoriy — sifatliroq rasmlar uchun (bo'lmasa Openverse ishlatiladi):
export PEXELS_API_KEY=...          # bepul: https://www.pexels.com/api/

python3 pipeline.py --minutes 45 --theme random
python3 pipeline.py --minutes 45 --theme monk --seed 7 --preview 20   # tez sinov
python3 youtube_upload.py output/monk_7_XX␣ --privacy unlisted
```

Alohida bosqichlar: `assets.py`, `music_gen.py`, `metadata_gen.py`, `video_gen.py`,
`thumbnail_gen.py` — har biri mustaqil CLI sifatida ham ishlaydi.

## Avtomatlashtirish

`.github/workflows/auto_upload.yml` har 6 soatda pipeline'ni ishga tushirib,
videoni public qilib yuklaydi. Qo'lda ishga tushirish (Actions → Run workflow)
`privacy` / `theme` / `minutes` tanlash imkonini beradi.

Kerakli GitHub Secrets: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`
(`PEXELS_API_KEY` — ixtiyoriy).

## Sozlamalar

- Video: `video_gen.py` yuqorisidagi `WIDTH/HEIGHT/FPS/CRF/GRAIN_AMOUNT`
  (standart 1600×900 @ 20fps; 45 daq ≈ 16 daq render, ≈ 250 MB).
- Mavzular / chastotalar / akkordlar / intro matnlar: `themes.py`.
- Rasm so'rovlari: har mavzudagi `queries` ro'yxati.

## Litsenziya eslatmasi

Pexels rasmlaridan foydalanilganda tavsifga fotograf krediti avtomatik qo'shiladi.
