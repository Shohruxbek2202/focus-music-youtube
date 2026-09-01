"""
0-QISM: Fon rasmi manbai.

Mavzuga mos kinematik rasmni oladi. Manba tartibi:
  1. Openverse API — KALIT KERAK EMAS (CC-litsenziyali rasmlar, Wikimedia/Flickr/...)
  2. Pexels API — agar PEXELS_API_KEY muhit o'zgaruvchisi bo'lsa (ixtiyoriy, sifatliroq)
  3. Protsedural fon — internet yo'q / natija yo'q bo'lsa (pipeline hech qachon to'xtamaydi)

Faqat standart kutubxona (urllib) ishlatiladi.

Ishlatish:
    from assets import fetch_background
    info = fetch_background(["greek marble statue", "roman sculpture"], "output/x", seed=7)
"""

import json
import os
import random
import ssl
import urllib.parse
import urllib.request

import numpy as np
from PIL import Image, ImageFilter

OPENVERSE_SEARCH = "https://api.openverse.org/v1/images/"
PEXELS_SEARCH = "https://api.pexels.com/v1/search"
TARGET_W, TARGET_H = 1920, 1080
_UA = "focus-music-youtube/1.0 (github.com/Shohruxbek2202/focus-music-youtube)"
_MIN_W = 1200  # bundan tor rasmlarni rad etamiz


def _http_get_json(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _prep_image_url(url, target_w=1920):
    """Wikimedia to'liq rasm URL'ini kichikroq thumbnail URL'iga aylantiradi (tez yuklash)."""
    marker = "/wikipedia/commons/"
    if "upload.wikimedia.org" in url and marker in url and "/thumb/" not in url:
        tail = url.split(marker, 1)[1]              # "9/9f/Name.jpg"
        parts = tail.split("/")
        if len(parts) == 3:
            fname = parts[2]
            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{tail}/{target_w}px-{fname}"
    return url


def _download(url, dest, timeout=45):
    req = urllib.request.Request(_prep_image_url(url), headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
        data = resp.read()
    if len(data) < 8000:
        raise ValueError("rasm juda kichik / bo'sh")
    with open(dest, "wb") as f:
        f.write(data)


def _cover_resize(img, w=TARGET_W, h=TARGET_H):
    """Rasmni w×h ni to'liq qoplaydigan qilib kesib o'lchamlaydi (object-fit: cover)."""
    img = img.convert("RGB")
    sr = img.width / img.height
    dr = w / h
    if sr > dr:
        nw, nh = int(round(h * sr)), h
    else:
        nw, nh = w, int(round(w / sr))
    img = img.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - w) // 2, (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def _finalize(raw_path, dest):
    img = _cover_resize(Image.open(raw_path))
    img.save(dest, quality=92)
    try:
        os.remove(raw_path)
    except OSError:
        pass


# ---------------------------------------------------------------- Openverse (kalitsiz)
def _openverse_query(query, rng, loose):
    params = {
        "q": query,
        "license_type": "all",
        "page_size": 20,
        "page": rng.randint(1, 2),
        "mature": "false",
    }
    if not loose:
        params["aspect_ratio"] = "wide"
        params["size"] = "large"
    url = OPENVERSE_SEARCH + "?" + urllib.parse.urlencode(params)
    data = _http_get_json(url)
    min_w = _MIN_W if not loose else 900
    results = [
        r for r in data.get("results", [])
        if (r.get("width") or 0) >= min_w
        and (r.get("width") or 1) >= (r.get("height") or 1)   # landshaft
        and r.get("url")
    ]
    rng.shuffle(results)
    return results


def _try_openverse(queries, outdir, dest, rng):
    for query in queries:
        for loose in (False, True):
            try:
                results = _openverse_query(query, rng, loose)
            except Exception as e:  # noqa: BLE001
                print(f"  [assets] Openverse '{query}' xato: {e}")
                continue
            for r in results[:6]:
                try:
                    raw = os.path.join(outdir, "_bg_raw")
                    _download(r["url"], raw)
                    _finalize(raw, dest)
                    print(f"  [assets] Openverse: '{query}' -> {r.get('creator')} ({r.get('license')})")
                    return {
                        "path": dest, "source": "openverse",
                        "photographer": r.get("creator"),
                        "photographer_url": r.get("creator_url"),
                        "pexels_url": r.get("foreign_landing_url"),
                        "license": r.get("license"),
                        "provider": r.get("provider"),
                        "query": query,
                    }
                except Exception as e:  # noqa: BLE001
                    print(f"  [assets] Openverse rasm o'tkazib yuborildi: {e}")
                    continue
    return None


# ---------------------------------------------------------------- Pexels (ixtiyoriy)
def _try_pexels(queries, outdir, dest, rng, api_key):
    headers = {"Authorization": api_key, "User-Agent": _UA}
    for query in queries:
        try:
            url = PEXELS_SEARCH + "?" + urllib.parse.urlencode({
                "query": query, "orientation": "landscape",
                "size": "large", "per_page": 30, "page": rng.randint(1, 5),
            })
            data = _http_get_json(url, headers)
            photos = data.get("photos") or []
            if not photos:
                continue
            photo = rng.choice(photos)
            src = photo.get("src", {})
            img_url = src.get("original") or src.get("large2x") or src.get("large")
            if not img_url:
                continue
            raw = os.path.join(outdir, "_bg_raw")
            _download(img_url, raw)
            _finalize(raw, dest)
            print(f"  [assets] Pexels: '{query}' -> {photo.get('photographer')}")
            return {
                "path": dest, "source": "pexels",
                "photographer": photo.get("photographer"),
                "photographer_url": photo.get("photographer_url"),
                "pexels_url": photo.get("url"),
                "license": "Pexels License",
                "provider": "pexels",
                "query": query,
            }
        except Exception as e:  # noqa: BLE001
            print(f"  [assets] Pexels '{query}' xato: {e}")
            continue
    return None


# ---------------------------------------------------------------- protsedural fallback
def _procedural_background(dest, seed, queries):
    rng = np.random.default_rng(seed)
    top = np.array([18, 20, 34]) + rng.integers(-6, 10, 3)
    bottom = np.array([3, 3, 8])
    grad = np.linspace(0, 1, TARGET_H)[:, None, None]
    base = top[None, None, :] * (1 - grad) + bottom[None, None, :] * grad
    canvas = np.broadcast_to(base, (TARGET_H, TARGET_W, 3)).astype(np.float64).copy()

    yy, xx = np.mgrid[0:TARGET_H, 0:TARGET_W]
    for _ in range(rng.integers(3, 6)):
        cx, cy = rng.uniform(0, TARGET_W), rng.uniform(0, TARGET_H)
        r = rng.uniform(250, 700)
        blob = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))
        canvas += blob[:, :, None] * rng.uniform(8, 26)

    canvas += rng.normal(0, 4, canvas.shape)
    canvas = np.clip(canvas, 0, 255).astype(np.uint8)
    Image.fromarray(canvas).filter(ImageFilter.GaussianBlur(1.2)).save(dest, quality=90)
    return {
        "path": dest, "source": "procedural",
        "photographer": None, "photographer_url": None, "pexels_url": None,
        "license": None, "provider": "procedural",
        "query": queries[0] if queries else None,
    }


def fetch_background(queries, outdir, seed=None, api_key=None):
    """Mavzu so'rovlari ro'yxatidan bittasini tanlab, rasm yuklaydi.

    Qaytaradi: dict — path va atributsiya ma'lumotlari (tavsifga qo'shish uchun).
    """
    os.makedirs(outdir, exist_ok=True)
    dest = os.path.join(outdir, "background.jpg")
    rng = random.Random(seed)
    queries = list(queries) or ["dark cinematic"]
    rng.shuffle(queries)

    api_key = api_key or os.environ.get("PEXELS_API_KEY", "").strip()
    if api_key:
        info = _try_pexels(queries, outdir, dest, rng, api_key)
        if info:
            return info

    info = _try_openverse(queries, outdir, dest, rng)
    if info:
        return info

    print("  [assets] Onlayn manba natija bermadi — protsedural fon")
    return _procedural_background(dest, seed or 0, queries)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--query", nargs="+", default=["foggy mountain peak"])
    p.add_argument("--outdir", default="output/_assets_test")
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()
    print(json.dumps(fetch_background(args.query, args.outdir, args.seed), indent=2, ensure_ascii=False))
