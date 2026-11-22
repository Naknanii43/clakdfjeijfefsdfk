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
               "Thank you.", "Goodbye.",
               # added later (keep the first twenty in place: keys map to them in order)
               "Hi!", "Hey there!", "Oh my god!", "Oh wow!", "Yay!", "Woo!", "Hooray!", "Uh oh.",
               "Oops!", "Ouch!", "Eww.", "Aww.", "Mmm, yummy.", "Huh?", "Hmm?", "Right.", "Sure.",
               "Nope.", "Maybe.", "Really?", "Seriously?", "Cool.", "Nice!", "Amazing!", "Oh yeah!",
               "Let's go!", "Wait!", "Stop!", "Sorry.", "Please.", "Bye!", "Good night."]

# everyday spoken phrases (SPEAK = PHRASES)
PHRASES = ["How are you today?", "I'm on my way.", "Can you hear me?", "Are you ready?", "Here we go.",
           "One, two, three, four.", "Turn it up.", "Welcome to the show.", "Thank you so much.",
           "I love this song.", "What a beautiful day.", "Is anybody out there?", "Don't stop now.",
           "Everybody, put your hands up!", "Let me tell you something.", "Once upon a time.",
           "This is the end.", "I can't believe it.", "Look at the stars.", "Do you remember?",
           "Take a deep breath.", "Everything will be okay.", "I'll see you tomorrow.",
           "It's getting late.", "Where are you going?", "Follow me.", "Listen to the rhythm.",
           "Feel the music.", "We are live.", "Good morning, everyone.", "Have a nice day.",
           "I miss you.", "Call me back.", "It's time to go.", "Never give up.", "Close your eyes.",
           "Welcome home.", "Is this real?", "Just breathe.", "Ladies and gentlemen."]


def spoken_line(line):
    words = ["I" if w == "i" else w for w in line.split()]
    s = " ".join(words)
    return s[0].upper() + s[1:] + "."


SPEAK_CLIPS = [spoken_line(l) for l in LYRICS] + EXPRESSIONS + PHRASES  # in this order
NLINES = len(LYRICS)
NEXPR = len(EXPRESSIONS)
NPHR = len(PHRASES)
SPEAK_SR = 16000  # speech is stored at 16 kHz (plenty for talking, half the size)
