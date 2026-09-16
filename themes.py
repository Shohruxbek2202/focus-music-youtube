"""
Shared themes — music, video, thumbnail and metadata all feed from here.

Each theme is a single "Lock in Focus"-style mood: a cinematic B&W image,
slow ambient music and a solfeggio/binaural frequency.

On every render a theme is picked at random (or forced with --theme); then the
concept word, context, image query, frequency and key inside that theme are
chosen from a seed — so "every video is original content".
"""

# Chords are written in C (root position); music_gen transposes them at random.
THEMES = {
    "warrior": {
        "display": "WARRIOR",
        "concepts": ["Resistance", "Iron Will", "Warrior Mind", "Unbreakable", "Inner Fire"],
        "contexts": [
            "Focus music for working under pressure",
            "Deep concentration for hard work",
            "40Hz gamma for beating fatigue",
        ],
        "queries": [
            "boxing gym", "boxer training", "boxing ring", "weightlifting", "gym workout dark", "stadium empty",
        ],
        "freqs": [40, 174, 285],
        "beat_hz": 40.0,          # gamma — sharp focus
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
            "Welcome to the final arena. Your toughest opponent isn't out there — "
            "it's staring back at you in the mirror. Let these {hz}Hz synth pads "
            "freeze the hesitation and lock your mind into full execution."
        ),
    },
    "stoic": {
        "display": "STOIC",
        "concepts": ["Patience", "Endurance", "Steadfast", "Ataraxia", "Quiet Strength"],
        "contexts": [
            "Deep work with ancient wisdom",
            "432Hz music for calm focus",
            "A steady tone for long sessions",
        ],
        "queries": [
            "greek marble statue", "roman sculpture", "classical statue", "ancient sculpture", "marble bust",
        ],
        "freqs": [432, 528],
        "beat_hz": 10.0,          # alpha — calm but alert
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
            "Some things are not in your control. Leave them at the door. "
            "This {hz}Hz tone cuts the extra noise and leaves room only for the work that matters."
        ),
    },
    "monk": {
        "display": "MONK",
        "concepts": ["Monk Mode", "Silence", "Clarity", "Solitary Mind", "Inner Void"],
        "contexts": [
            "963Hz music for deep focus",
            "Work-in-silence mode",
            "Ambient to clear the mind",
        ],
        "queries": [
            "buddhist monastery", "zen garden", "monk meditation", "temple fog",
            "pagoda mist", "old monastery interior",
        ],
        "freqs": [963, 852],
        "beat_hz": 6.0,           # theta — meditative
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
            "This place is quiet. No phone, no voices, no excuses. "
            "Let these {hz}Hz waves gather your mind to a single point and hold it there."
        ),
    },
    "midnight": {
        "display": "MIDNIGHT",
        "concepts": ["Midnight", "Night Shift", "Sleepless Mind", "Quiet Hours", "Light in the Dark"],
        "contexts": [
            "Focus music for coding at night",
            "396Hz for late-night deep work",
            "Ambient for the night shift",
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
            "Everyone is asleep. These hours belong to you alone. "
            "Under the rain and the {hz}Hz pads, take the work to the finish."
        ),
    },
    "storm": {
        "display": "STORM",
        "concepts": ["The Storm", "Inner Force", "The Surge", "Thunder", "Calm Center"],
        "contexts": [
            "Focus music for taming chaos",
            "285Hz under heavy pressure",
            "Ambient to reclaim your focus",
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
            "The storm roars outside while you stay calm at the center. "
            "Turn the chaos into working energy with this {hz}Hz tone."
        ),
    },
    "summit": {
        "display": "SUMMIT",
        "concepts": ["The Summit", "Lonely Road", "Altitude", "Cold Air", "Distant Goal"],
        "contexts": [
            "Focus music for the long goal",
            "528Hz for slow, steady work",
            "Ambient for all-day focus",
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
            "The summit isn't taken in a day. One step, then another. "
            "Let the {hz}Hz pads keep your pace steady."
        ),
    },
}

THEME_NAMES = list(THEMES.keys())
