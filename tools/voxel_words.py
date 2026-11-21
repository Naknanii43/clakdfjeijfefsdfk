"""Shared word lists for VOXEL (used by make_voices.py and voxel.py)."""

# sustained vowels (TEXT = VOWELS mode); the spelling is what the TTS reads
VOWELS = [("ah", "Ahh."), ("oh", "Ohh."), ("ooh", "Oooh."), ("ee", "Eee."), ("mm", "Hmm."),
          # added later (keep the first five in place: banks refer to them by number)
          ("eh", "Eh."), ("uh", "Uhh."), ("ay", "Ay."), ("eye", "Eye."), ("la", "Lah."),
          ("na", "Nah."), ("da", "Dah."), ("ya", "Yah."), ("hey", "Hey."), ("whoa", "Whoa.")]

# lyric lines: SING / LYRICS mode sings them one word per note
LYRICS = [
    "i feel you in the night",
    "hold on to me",
    "we fly so high",
    "stay with me now",
    "rain falls on my heart",
    "dream of the sky",
    "you are my light",
    "let go and be free",
    "slow down the time",
    "come home to me",
    # added later (keep the first ten in place: banks refer to them by number)
    "the stars are out tonight",
    "take my hand and run",
    "all i need is love",
    "sing it loud and clear",
    "hear the ocean call",
    "we are young and wild",
    "you and i are one",
    "fall in love again",
    "never let me go",
    "light up the dark",
    "follow the sun",
    "dance with me tonight",
    "i will wait for you",
    "there is no one else",
    "close your eyes and breathe",
    "the moon is shining bright",
    "find a way back home",
    "nothing lasts forever",
    "keep the fire burning",
    "sweet dreams my love",
]


def all_words():
    words = [v[0] for v in VOWELS]
    for line in LYRICS:
        for w in line.split():
            if w not in words:
                words.append(w)
    return words


def tts_text(word):
    for key, text in VOWELS:
        if key == word:
            return text
    return {"i": "I."}.get(word, word.capitalize() + ".")


WORDS = all_words()
NSPEAKERS = 12  # 6 pitch ranges x (warm, bright)
SRC_SR = 22050


# ---- SPEAK mode: natural speech (no musical pitch), one clip per key
EXPRESSIONS = ["Hey!", "Oh!", "Wow.", "Hmm.", "Yeah!", "Okay.", "Hello.", "Ha ha ha!", "Oh no.",
               "Uh huh.", "Whoa!", "Yes!", "No.", "What?", "Come on!", "Listen.", "Shh.", "Ahh.",
               "Thank you.", "Goodbye."]


def spoken_line(line):
    words = ["I" if w == "i" else w for w in line.split()]
    s = " ".join(words)
    return s[0].upper() + s[1:] + "."


SPEAK_CLIPS = [spoken_line(l) for l in LYRICS] + EXPRESSIONS  # lines first, then expressions
NLINES = len(LYRICS)
NEXPR = len(EXPRESSIONS)
