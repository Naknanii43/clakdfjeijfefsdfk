"""Procedural sound-bank + groove designer for Clonk Goblin.

Every bank is a recipe (category) rolled with a fixed seed, so the output is
reproducible.  Values must stay inside the GUI slider ranges in generate.py.
"""
import random

SOUND_KEYS = ["tune", "pdrop", "pdec", "adec", "ndec", "noise", "ncut", "nq",
              "fm", "fmr", "modal", "mat", "ring", "ks", "ksfb", "crush",
              "drive", "wob", "dsync", "dfb", "dmix", "space"]

ADJ = """Crispy Moist Wobbly Grumpy Tiny Sneaky Rubber Polite Haunted Soggy
Turbo Sleepy Feral Velvet Crunchy Shiny Rusty Lukewarm Spicy Fizzy Clumsy Bouncy
Nervous Fancy Dusty Chunky Squishy Electric Frozen Wonky Gentle Angry Salty Hollow
Itchy Jolly Lazy Mighty Noisy Plastic Quiet Rickety Silly Tangled Useless Vintage
Wet Zippy Glitchy Melted Wooden Glass Tinfoil Cosmic Pickled Fluffy Bent Tipsy
Ticklish Sticky Prickly Smug Hungry Bashful Feisty Dizzy Loopy Crumbly Spongy""".split()

NOUN = """Spoon Teacup Doorknob Kazoo Pigeon Toaster Gremlin Marble Pebble Kettle
Slipper Noodle Bucket Cricket Biscuit Wrench Ladle Pretzel Robot Raccoon Bubble
Sprocket Lobster Drawer Pickle Hamster Muffin Zipper Thimble Goblin Penguin Bongo
Cactus Waffle Gnome Sponge Trombone Jellybean Hinge Squirrel Button Teapot Walrus
Snorkel Pancake Banjo Crumpet Toad Faucet Clam Turnip Moth Radiator Clothespin
Paperclip Cymbal Tadpole Bagel Sardine Pudding Gizmo Beetle Rattle Croissant
Cupboard Lantern Mitten Goose Sock Nugget Eggshell Bellows Chopstick Cushion""".split()

SUFFIX = ["", "", "", "", "", "", "Jr", "3000", "Deluxe", "XL", "Mk2", "Supreme",
          "Lite", "Classic", "of_Doom", "Remix", "Pro", "Mini"]

SCALES = {
    "minpent": [0, 3, 5, 7, 10, 12],
    "majpent": [0, 2, 4, 7, 9, 12],
    "phryg": [0, 1, 3, 5, 7, 8, 10, 12],
    "lydian": [0, 2, 4, 6, 7, 9, 11, 12],
    "whole": [0, 2, 4, 6, 8, 10, 12],
    "fifths": [0, 7, 12, -5, -12],
    "wonk": [0, 1, 6, 7, 11, 13, -6],
}


def U(r, a, b):
    return r.uniform(a, b)


def LU(r, a, b):
    """Log-uniform."""
    import math
    return math.exp(r.uniform(math.log(a), math.log(b)))


def C(r, *xs):
    return r.choice(xs)


def fx(r, wet=0.3):
    return dict(dsync=C(r, 0.5, 0.75, 1, 1.5, 2, 3, 3, 1.5),
                dfb=U(r, 0, 0.65), dmix=U(r, 0, wet) if r.random() < 0.7 else 0,
                space=U(r, 0, 0.55) if r.random() < 0.75 else 0)


def base(r):
    d = dict(tune=0, pdrop=0, pdec=20, adec=200, ndec=50, noise=0, ncut=100, nq=1,
             fm=0, fmr=1, modal=0, mat=0.5, ring=20, ks=0, ksfb=0.9, crush=0,
             drive=0.1, wob=U(r, 0, 0.25))
    d.update(fx(r))
    return d


# ---------------------------------------------------------------- recipes
def kick(r):
    d = base(r)
    d.update(tune=U(r, -16, -7), pdrop=U(r, 16, 42), pdec=LU(r, 8, 70),
             adec=LU(r, 140, 750), noise=U(r, 0, 0.2), ndec=LU(r, 4, 25),
             ncut=U(r, 85, 120), nq=U(r, 0.6, 2), fm=U(r, 0, 1.4), fmr=C(r, 0.5, 1, 1, 2),
             drive=U(r, 0.1, 0.7), crush=C(r, 0, 0, 0, U(r, 0, 0.3)))
    if r.random() < 0.3:
        d.update(modal=U(r, 0.1, 0.4), mat=U(r, 0, 0.3), ring=LU(r, 8, 40))
    d["dmix"] *= 0.3
    return d


def snare(r):
    d = base(r)
    d.update(tune=U(r, -3, 8), pdrop=U(r, 4, 20), pdec=LU(r, 4, 30), adec=LU(r, 60, 260),
             noise=U(r, 0.45, 0.92), ndec=LU(r, 70, 320), ncut=U(r, 88, 120),
             nq=LU(r, 0.6, 4), fm=U(r, 0, 3), fmr=U(r, 1.3, 3.6), modal=U(r, 0, 0.45),
             mat=U(r, 0.3, 1), ring=LU(r, 8, 80), drive=U(r, 0.2, 0.8),
             crush=C(r, 0, 0, U(r, 0, 0.45)))
    return d


def hat(r):
    d = base(r)
    d.update(tune=U(r, 18, 36), pdrop=U(r, 0, 10), pdec=LU(r, 2, 10), adec=LU(r, 12, 110),
             noise=U(r, 0.7, 1), ndec=LU(r, 8, 160), ncut=U(r, 112, 134), nq=LU(r, 1, 12),
             fm=U(r, 2, 8), fmr=C(r, 1.41, 2.31, 3.17, 4.53, 5.6, 7.1, U(r, 1, 8)),
             modal=U(r, 0, 0.5), mat=U(r, 0.75, 1), ring=LU(r, 20, 220),
             crush=C(r, 0, 0, U(r, 0, 0.5)), drive=U(r, 0, 0.4))
    return d


def foley(r):
    d = base(r)
    d.update(tune=U(r, -6, 26), pdrop=U(r, -12, 24), pdec=LU(r, 2, 60),
             adec=LU(r, 15, 300), noise=U(r, 0.1, 0.8), ndec=LU(r, 3, 90),
             ncut=U(r, 70, 130), nq=LU(r, 0.6, 18), fm=U(r, 0, 2.5), fmr=U(r, 0.5, 6),
             modal=U(r, 0.5, 1), mat=U(r, 0, 0.65), ring=LU(r, 12, 260),
             ks=C(r, 0, 0, U(r, 0, 0.5)), ksfb=U(r, 0.7, 0.97), drive=U(r, 0, 0.4))
    return d


def metal(r):
    d = base(r)
    d.update(tune=U(r, 10, 36), pdrop=C(r, 0, 0, U(r, -3, 5)), pdec=LU(r, 5, 40),
             adec=LU(r, 250, 2200), noise=U(r, 0, 0.35), ndec=LU(r, 3, 30),
             ncut=U(r, 100, 134), nq=LU(r, 1, 8), fm=U(r, 0, 4),
             fmr=C(r, 1.41, 2.76, 3.5, 5.4, 0.5, 7), modal=U(r, 0.6, 1), mat=U(r, 0.7, 1),
             ring=LU(r, 150, 600), drive=U(r, 0, 0.3))
    d["space"] = U(r, 0.2, 0.7)
    return d


def zap(r):
    d = base(r)
    d.update(tune=U(r, 0, 30), pdrop=C(r, U(r, 24, 48), U(r, 24, 48), U(r, -24, -8)),
             pdec=LU(r, 25, 320), adec=LU(r, 70, 500), noise=U(r, 0, 0.3),
             ndec=LU(r, 5, 60), ncut=U(r, 90, 130), nq=LU(r, 2, 20), fm=U(r, 1, 7),
             fmr=U(r, 0.5, 6), crush=C(r, 0, U(r, 0, 0.6)), drive=U(r, 0.1, 0.6))
    return d


def pluck(r):
    d = base(r)
    d.update(tune=U(r, -2, 26), pdrop=C(r, 0, 0, U(r, 0, 12)), pdec=LU(r, 2, 20),
             adec=LU(r, 20, 180), noise=U(r, 0.3, 0.9), ndec=LU(r, 2, 20),
             ncut=U(r, 90, 130), nq=LU(r, 0.6, 3), fm=U(r, 0, 2), fmr=C(r, 1, 2, 3),
             ks=U(r, 0.6, 1), ksfb=U(r, 0.88, 0.995), modal=U(r, 0, 0.3),
             mat=U(r, 0, 1), ring=LU(r, 10, 100), drive=U(r, 0, 0.5))
    return d


def glitch(r):
    d = base(r)
    d.update(tune=U(r, -12, 36), pdrop=U(r, -24, 48), pdec=LU(r, 1, 80),
             adec=LU(r, 10, 140), noise=U(r, 0, 1), ndec=LU(r, 2, 60), ncut=U(r, 40, 135),
             nq=LU(r, 0.5, 25), fm=U(r, 2, 8), fmr=LU(r, 0.25, 8), modal=U(r, 0, 0.7),
             mat=U(r, 0, 1), ring=LU(r, 5, 300), crush=U(r, 0.35, 1), drive=U(r, 0.2, 1),
             wob=U(r, 0.3, 1))
    return d


def blip(r):
    d = base(r)
    d.update(tune=U(r, 8, 36), pdrop=C(r, 0, U(r, -5, 12)), pdec=LU(r, 2, 30),
             adec=LU(r, 20, 160), noise=C(r, 0, 0, U(r, 0, 0.2)), ndec=LU(r, 2, 15),
             fm=C(r, 0, U(r, 0, 1.5)), fmr=C(r, 1, 2, 3, 4), drive=U(r, 0, 0.3))
    d["dmix"] = U(r, 0.1, 0.45)
    return d


def goop(r):
    d = base(r)
    d.update(tune=U(r, -14, 12), pdrop=C(r, U(r, -24, -6), U(r, 8, 30)), pdec=LU(r, 60, 400),
             adec=LU(r, 120, 700), noise=U(r, 0, 0.3), ndec=LU(r, 10, 80),
             ncut=U(r, 60, 100), nq=LU(r, 1, 10), fm=U(r, 0.5, 4), fmr=U(r, 0.5, 2),
             modal=U(r, 0.2, 0.6), mat=U(r, 0, 0.3), ring=LU(r, 8, 60),
             drive=U(r, 0.4, 1), wob=U(r, 0.3, 0.9))
    return d


def bongo(r):
    d = base(r)
    d.update(tune=U(r, -6, 14), pdrop=U(r, 3, 16), pdec=LU(r, 8, 70), adec=LU(r, 80, 420),
             noise=U(r, 0, 0.3), ndec=LU(r, 3, 30), ncut=U(r, 80, 120), nq=LU(r, 0.7, 4),
             fm=U(r, 0, 1.5), fmr=C(r, 1, 1.5, 2), modal=U(r, 0.2, 0.65),
             mat=U(r, 0, 0.4), ring=LU(r, 10, 90), drive=U(r, 0, 0.5))
    return d


def clank(r):
    """Junkyard: metallic + crushed noise + string bits."""
    d = base(r)
    d.update(tune=U(r, -4, 24), pdrop=U(r, -6, 20), pdec=LU(r, 2, 40), adec=LU(r, 40, 600),
             noise=U(r, 0.2, 0.8), ndec=LU(r, 10, 200), ncut=U(r, 80, 130),
             nq=LU(r, 1, 15), fm=U(r, 1, 6), fmr=LU(r, 0.7, 7.5), modal=U(r, 0.4, 0.9),
             mat=U(r, 0.5, 1), ring=LU(r, 30, 400), ks=U(r, 0, 0.6),
             ksfb=U(r, 0.8, 0.98), crush=U(r, 0, 0.6), drive=U(r, 0.2, 0.8))
    return d


def drip(r):
    """Water drops, bubbles, rising boinks."""
    d = base(r)
    d.update(tune=U(r, 6, 30), pdrop=U(r, -24, -6), pdec=LU(r, 8, 90), adec=LU(r, 25, 200),
             noise=C(r, 0, U(r, 0, 0.25)), ndec=LU(r, 2, 10), fm=C(r, 0, U(r, 0, 1.2)),
             fmr=C(r, 1, 2), modal=U(r, 0.2, 0.7), mat=U(r, 0.1, 0.6),
             ring=LU(r, 20, 160), drive=U(r, 0, 0.2))
    d["space"] = U(r, 0.15, 0.6)
    return d


RECIPES = [
    ("BONK", kick), ("SNAP", snare), ("TSST", hat), ("FOLEY", foley),
    ("METAL", metal), ("ZAP", zap), ("PLUCK", pluck), ("GLITCH", glitch),
    ("BLIP", blip), ("GOOP", goop), ("BONGO", bongo), ("CLANK", clank),
    ("DRIP", drip),
]


# ---------------------------------------------------------------- grooves
def euclid(k, n, rot=0):
    pat = [1 if ((i * k) % n) < k else 0 for i in range(n)]
    return pat[-rot:] + pat[:-rot] if rot else pat


def groove(r, cat):
    g = [0] * 16
    a = [0] * 16
    n = [0] * 16
    length = 16
    rate = 1
    swing = C(r, 0, 0, U(r, 0, 0.3))
    chance = 1.0
    oops = C(r, 0, 0, U(r, 0, 0.15))

    melodic = cat in ("METAL", "PLUCK", "BLIP", "DRIP", "ZAP")
    if cat == "BONK":
        g = euclid(C(r, 3, 4, 4, 5), 16, C(r, 0, 0, 2, 3))
        length = C(r, 16, 16, 16, 12, 15)
        a = [1 if i % 8 == 0 else 0 for i in range(16)]
        n = [C(r, 0, 0, 0, 0, -5, 7, 12) if g[i] else 0 for i in range(16)]
        chance = U(r, 0.88, 1)
    elif cat == "SNAP":
        g = [1 if i in (4, 12) else 0 for i in range(16)]
        for i in range(16):
            if not g[i] and r.random() < 0.18:
                g[i] = 1
        a = [1 if i in (4, 12) else 0 for i in range(16)]
        chance = U(r, 0.85, 1)
    elif cat == "TSST":
        g = euclid(C(r, 7, 9, 11, 13, 16), 16, C(r, 0, 1, 2))
        a = [1 if i % 4 == 2 else 0 for i in range(16)]
        rate = C(r, 1, 1, 1, 2)
        chance = U(r, 0.6, 0.95)
        oops = U(r, 0.04, 0.3)
        n = [C(r, 0, 0, 0, 2, -2) for _ in range(16)]
    elif cat in ("GLITCH", "CLANK"):
        g = [1 if r.random() < 0.5 else 0 for _ in range(16)]
        a = [1 if r.random() < 0.3 else 0 for _ in range(16)]
        rate = C(r, 1, 2, 2, 3)
        length = C(r, 16, 13, 11, 9, 7, 15)
        n = [C(r, 0, 0, 12, -12, 7, 1, 6) for _ in range(16)]
        chance = U(r, 0.6, 1)
        oops = U(r, 0.2, 0.7)
    elif cat in ("FOLEY", "GOOP", "BONGO"):
        dens = U(r, 0.25, 0.55)
        g = [1 if r.random() < dens else 0 for _ in range(16)]
        a = [1 if r.random() < 0.25 else 0 for _ in range(16)]
        length = C(r, 16, 16, 5, 7, 9, 11, 12, 13)
        n = [C(r, 0, 0, 0, 3, 5, 7, -5, -7, 12) for _ in range(16)]
        rate = C(r, 1, 1, 1, 3)
        chance = U(r, 0.7, 1)
        oops = U(r, 0, 0.3)
    if melodic:
        scale = SCALES[r.choice(list(SCALES))]
        dens = U(r, 0.35, 0.7)
        g = [1 if r.random() < dens else 0 for _ in range(16)]
        a = [1 if r.random() < 0.3 else 0 for _ in range(16)]
        n = [r.choice(scale) for _ in range(16)]
        length = C(r, 16, 16, 8, 10, 12, 14, 7, 11)
        rate = C(r, 1, 1, 1, 3, 2, 0)
        chance = U(r, 0.75, 1)
        oops = C(r, 0, U(r, 0, 0.2))
    g[0] = 1  # always start with something
    a[0] = 1
    d = dict(len=length, rate=rate, swing=swing, chance=chance, oops=oops)
    for i in range(16):
        d[f"g{i+1}"] = g[i]
        d[f"a{i+1}"] = a[i]
        d[f"n{i+1}"] = n[i]
    return d


def fmt(v):
    if isinstance(v, int):
        return str(v)
    s = f"{v:.4g}"
    return s


def build(count=520, seed=8675309):
    r = random.Random(seed)
    names = set()
    banks, grooves = [], []
    for i in range(count):
        cat, fn = RECIPES[i % len(RECIPES)]
        while True:
            nm = f"{r.choice(ADJ)}_{r.choice(NOUN)}"
            suf = r.choice(SUFFIX)
            if suf:
                nm += "_" + suf
            if nm not in names:
                names.add(nm)
                break
        d = fn(r)
        banks.append((nm, cat, d))
        grooves.append(groove(r, cat))
    return banks, grooves


def write(dirpath, count=520, levels=None):
    levels = levels or {}
    banks, grooves = build(count)
    open_lines = []
    with open(f"{dirpath}/banks.txt", "w") as f:
        for nm, cat, d in banks:
            pairs = " ".join(f"{k} {fmt(d[k])}" for k in SOUND_KEYS)
            lvl = levels.get(str(len(open_lines)), 1) * {"METAL": 0.6, "CLANK": 0.65}.get(cat, 1)
            open_lines.append(nm)
            f.write(f"{nm} {cat} lvl {lvl:.3f} {pairs};\n")
    with open(f"{dirpath}/grooves.txt", "w") as f:
        for g in grooves:
            f.write(" ".join(f"{k} {fmt(v)}" for k, v in g.items()) + ";\n")
    return banks
