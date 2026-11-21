"""Shared word lists for VOXEL (used by make_voices.py and voxel.py)."""

# sustained vowels (TEXT = VOWELS mode); the spelling is what the TTS reads
VOWELS = [("ah", "Ahh."), ("oh", "Ohh."), ("ooh", "Oooh."), ("ee", "Eee."), ("mm", "Hmm.")]

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
NSPEAKERS = 8
SRC_SR = 22050
