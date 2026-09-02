"""Genre & style library for the Psychedelic Speech Engine batch generator.

Every track carries a "signature" tag set so the channel has a consistent
identity ("our own sound") regardless of the sub-genre.
"""

# Applied to EVERY track -> the channel's signature sound.
# (Kept compact: Suno's style field is capped at 200 characters.)
SIGNATURE_TAGS = (
    "instrumental, hypnotic spiritual journey, deep meditative groove, psychedelic"
)

# Keeps generations instrumental (Suno sometimes adds vocals otherwise).
NEGATIVE_TAGS = "vocals, lyrics, singing, voice, acapella, rap, spoken word"

# Psytrance sub-styles (the PRIMARY genre). Each has a BPM window used to pick
# the target BPM plus a Suno style tag set.
PSYTRANCE_STYLES = {
    "fullon": {
        "bpm": (144, 148),
        "tags": "psytrance, full-on, Goa trance, rolling bassline, acid squelches, "
                "tribal percussion, lush pads",
    },
    "darkpsy": {
        "bpm": (148, 160),
        "tags": "darkpsy, forest psytrance, dark atmosphere, fast rolling bass, "
                "organic textures, eerie leads, hypnotic",
    },
    "hitech": {
        "bpm": (160, 170),
        "tags": "hi-tech psytrance, rapid-fire bassline, glitchy stabs, "
                "intense driving energy, futuristic",
    },
}

# Additional genres: 3 of these (random, distinct) per every 4 psytrance tracks.
OTHER_GENRES = {
    "tech_house": {
        "bpm": (122, 128),
        "tags": "tech house, rolling tech house bass, crisp percussion, minimal groove, hypnotic",
    },
    "hard_techno": {
        "bpm": (138, 155),
        "tags": "hard techno, pounding kick, industrial warehouse, relentless driving energy",
    },
    "drum_and_bass": {
        "bpm": (168, 178),
        "tags": "drum and bass, liquid dnb, rolling breakbeats, deep sub bass, energetic",
    },
    "dubstep": {
        "bpm": (140, 150),
        "tags": "dubstep, heavy wobble bass, half-time groove, dark, powerful drops",
    },
    "hardstyle": {
        "bpm": (150, 160),
        "tags": "hardstyle, distorted kick, reverse bass, euphoric melody, high energy",
    },
    "jcore": {
        "bpm": (170, 200),
        "tags": "japanese hardcore, j-core, fast kicks, melodic, high energy, euphoric",
    },
    "jtechno_synthpop": {
        "bpm": (130, 150),
        "tags": "japanese techno synthpop, melodic, retro synthesizer, driving, catchy",
    },
    "detroit_house_techno": {
        "bpm": (125, 135),
        "tags": "detroit techno, detroit house, deep, soulful chords, hypnotic",
    },
}

# Randomized "creative twist" added to every track's style for variety.
CREATIVE_TWISTS = [
    "mind-bending key changes",
    "polyrhythmic layers",
    "hypnotic acid lines",
    "modular synth textures",
    "cinematic breakdown",
    "glitchy transitions",
    "deep evolving pads",
    "trippy arpeggios",
]
