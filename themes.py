"""
Umumiy mavzular (themes) — musiqa, video, thumbnail va metadata shu yerdan oziqlanadi.

Har bir mavzu "Lock in Focus" uslubidagi bitta kayfiyat: kinematik B&W rasm,
sekin ambient musiqa va solfeggio/binaural chastota.

Har render'da mavzu tasodifiy tanlanadi (yoki --theme bilan majburlanadi), so'ng
mavzu ichidagi konsept so'z, kontekst, rasm so'rovi, chastota va tonalik
seed asosida tasodifiy tanlanadi — shu bilan "har video original kontent" bo'ladi.
"""

# Akkordlar C asosida (root-position) yozilgan; music_gen tasodifiy transpoze qiladi.
THEMES = {
    "warrior": {
        "display": "WARRIOR",
        "concepts": ["Qarshilik", "Temir Iroda", "Jangchi Ruhi", "Sindirilmas", "Ichki Olov"],
        "contexts": [
            "Bosim ostida ishlash uchun fokus musiqasi",
            "Mashaqqatli mehnat uchun diqqat qulfi",
            "Charchoqni yengish uchun 40Hz sinf",
        ],
        "queries": [
            "boxing gym", "boxer training", "boxing ring", "weightlifting", "gym workout dark", "stadium empty",
        ],
        "freqs": [40, 174, 285],
        "beat_hz": 40.0,          # gamma — o'tkir diqqat
        "texture": "wind",
        "progression": [
            ["A2", "C3", "E3", "G3"],   # i7
            ["F2", "A2", "C3", "E3"],   # VImaj7
            ["C3", "E3", "G3", "B3"],   # IIImaj7
            ["G2", "B2", "D3", "F3"],   # VII7
        ],
        "chord_seconds": (22.0, 28.0),
        "voices": 4,
        "harmonic_amps": (1.0, 0.42, 0.16, 0.06),
        "intro": (
            "Yakuniy maydonga xush kelibsiz. Eng kuchli raqibingiz tashqarida emas — "
            "u oynada senga qarab turibdi. Ushbu {hz}Hz synth pad'lar ikkilanishni "
            "muzlatib, zehningni to'liq ijroga qulflasin."
        ),
    },
    "stoic": {
        "display": "STOIC",
        "concepts": ["Sabr", "Toqat", "Metin", "Ataraksiya", "Sokin Kuch"],
        "contexts": [
            "Antik donolik bilan chuqur ish",
            "Xotirjam diqqat uchun 432Hz musiqa",
            "Uzoq mashg'ulot uchun barqaror ohang",
        ],
        "queries": [
            "greek marble statue", "roman sculpture", "classical statue", "ancient sculpture", "marble bust",
        ],
        "freqs": [432, 528],
        "beat_hz": 10.0,          # alpha — tinch, ammo hushyor
        "texture": "air",
        "progression": [
            ["C3", "E3", "G3", "B3"],   # Imaj7
            ["A2", "C3", "E3", "G3"],   # vi7
            ["F2", "A2", "C3", "E3"],   # IVmaj7
            ["G2", "B2", "D3", "F3"],   # V7
        ],
        "chord_seconds": (24.0, 30.0),
        "voices": 4,
        "harmonic_amps": (1.0, 0.45, 0.2, 0.08),
        "intro": (
            "Sen boshqara olmaydigan narsalar bor. Ular shu yerda qolsin. "
            "Bu {hz}Hz ohang ortiqcha shovqinni kesib, faqat muhim ishga joy qoldiradi."
        ),
    },
    "monk": {
        "display": "MONK",
        "concepts": ["Rohib Rejimi", "Sukunat", "Tazkiya", "Yolg'iz Zehn", "Ichki Bo'shliq"],
        "contexts": [
            "Chuqur diqqat uchun 963Hz musiqa",
            "Sukunatda ishlash rejimi",
            "Zehnni tozalash uchun ambient",
        ],
        "queries": [
            "buddhist monastery", "zen garden", "monk meditation", "temple fog",
            "pagoda mist", "old monastery interior",
        ],
        "freqs": [963, 852],
        "beat_hz": 6.0,           # theta — meditativ
        "texture": "air",
        "progression": [
            ["E2", "G#2", "B2", "D#3"],  # Imaj7
            ["C#2", "E2", "G#2", "B2"],  # vi7
            ["A1", "C#2", "E2", "G#2"],  # IVmaj7
            ["B1", "D#2", "F#2", "A2"],  # V7
        ],
        "chord_seconds": (26.0, 34.0),
        "voices": 3,
        "harmonic_amps": (1.0, 0.3, 0.12, 0.04),
        "intro": (
            "Bu yer sokin. Telefon yo'q, ovoz yo'q, bahona yo'q. "
            "{hz}Hz to'lqinlar zehningni bir nuqtaga to'plasin va ushlab tursin."
        ),
    },
    "midnight": {
        "display": "MIDNIGHT",
        "concepts": ["Yarim Tun", "Tungi Smena", "Uyqusiz Zehn", "Sokin Soatlar", "Qorong'ida Yorug'"],
        "contexts": [
            "Tunda kodlash uchun fokus musiqasi",
            "Kechqurun deep work uchun 396Hz",
            "Tungi mashg'ulot uchun ambient",
        ],
        "queries": [
            "city skyline night", "rainy street night", "neon city street", "night city lights", "dark alley night",
        ],
        "freqs": [396, 417],
        "beat_hz": 12.0,
        "texture": "rain",
        "progression": [
            ["D3", "F3", "A3", "C4"],   # ii7
            ["A2", "C3", "E3", "G3"],   # vi7
            ["A#2", "D3", "F3", "A3"],  # bVIImaj7
            ["C3", "E3", "G3", "A#3"],  # I7
        ],
        "chord_seconds": (22.0, 28.0),
        "voices": 4,
        "harmonic_amps": (1.0, 0.4, 0.18, 0.07),
        "intro": (
            "Hamma uxlab yotibdi. Bu soatlar faqat seniki. "
            "Yomg'ir va {hz}Hz pad'lar ostida ishni oxiriga yetkaz."
        ),
    },
    "storm": {
        "display": "STORM",
        "concepts": ["Bo'ron", "Ichki Kuch", "Toshqin", "Momaqaldiroq", "Tinch Markaz"],
        "contexts": [
            "Tartibsizlikni yengish uchun fokus musiqasi",
            "Kuchli bosim ostida 285Hz",
            "Diqqatni qayta qo'lga olish uchun ambient",
        ],
        "queries": [
            "storm clouds", "ocean waves storm", "lightning sky", "rough sea", "dramatic clouds", "dark sea horizon",
        ],
        "freqs": [285, 174],
        "beat_hz": 14.0,
        "texture": "rain_heavy",
        "progression": [
            ["D2", "F2", "A2", "C3"],   # i7
            ["A#1", "D2", "F2", "A2"],  # VImaj7
            ["F2", "A2", "C3", "E3"],   # IIImaj7
            ["C2", "E2", "G2", "A#2"],  # VII7
        ],
        "chord_seconds": (20.0, 26.0),
        "voices": 4,
        "harmonic_amps": (1.0, 0.5, 0.22, 0.1),
        "intro": (
            "Bo'ron tashqarida guvillaydi, sen esa markazda tinchsan. "
            "{hz}Hz ohang bilan tartibsizlikni ish quvvatiga aylantir."
        ),
    },
    "summit": {
        "display": "SUMMIT",
        "concepts": ["Cho'qqi", "Yolg'iz Yo'l", "Balandlik", "Sovuq Havo", "Uzoq Maqsad"],
        "contexts": [
            "Uzoq maqsad uchun fokus musiqasi",
            "Sekin, barqaror mehnat uchun 528Hz",
            "Kun bo'yi diqqat uchun ambient",
        ],
        "queries": [
            "mountain fog", "mountain summit clouds", "snowy mountain peak", "alpine landscape", "mountain ridge mist",
        ],
        "freqs": [528, 639],
        "beat_hz": 10.0,
        "texture": "wind",
        "progression": [
            ["G2", "B2", "D3", "F#3"],  # Imaj7
            ["E2", "G2", "B2", "D3"],   # vi7
            ["C2", "E2", "G2", "B2"],   # IVmaj7
            ["D2", "F#2", "A2", "C3"],  # V7
        ],
        "chord_seconds": (24.0, 32.0),
        "voices": 3,
        "harmonic_amps": (1.0, 0.38, 0.16, 0.05),
        "intro": (
            "Cho'qqi bir kunda zabt etilmaydi. Bir qadam, keyin yana biri. "
            "{hz}Hz pad'lar qadamingni bir maromda ushlab tursin."
        ),
    },
}

THEME_NAMES = list(THEMES.keys())
