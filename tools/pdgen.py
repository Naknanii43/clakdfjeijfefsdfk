"""Tiny helper for writing Pure Data patch files from Python."""


def esc(text):
    """Escape a Pd box text for the .pd file format."""
    out = []
    for tok in str(text).replace(",", " , ").replace(";", " ; ").split():
        if tok == ",":
            out.append("\\,")
        elif tok == ";":
            out.append("\\;")
        else:
            out.append(tok.replace("$", "\\$"))
    return " ".join(out)


def legacy_color(hexstr):
    """Hex '#rrggbb' -> old-style iemgui float colour (for 'color' messages)."""
    h = hexstr.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return -(((r >> 2) << 12) | ((g >> 2) << 6) | (b >> 2)) - 1


class Patch:
    def __init__(self, w=900, h=700, font=10, x0=20, y0=20):
        self.head = f"#N canvas 0 50 {w} {h} {font};"
        self.lines = []
        self.conns = []
        self.n = 0
        self.cx, self.cy = x0, y0
        self.col_w = 260
        self.max_y = 3000
        self.coords = None

    # ---- placement -------------------------------------------------------
    def at(self, x, y):
        self.cx, self.cy = x, y
        return self

    def _pos(self, x, y):
        if x is None:
            x, y = self.cx, self.cy
            self.cy += 24
            if self.cy > self.max_y:
                self.cy = 20
                self.cx += self.col_w
        return x, y

    # ---- boxes -----------------------------------------------------------
    def obj(self, text, x=None, y=None):
        x, y = self._pos(x, y)
        self.lines.append(f"#X obj {x} {y} {esc(text)};")
        self.n += 1
        return self.n - 1

    def raw(self, text, x=None, y=None):
        """Object line with already-escaped text (used for GUI objects)."""
        x, y = self._pos(x, y)
        self.lines.append(f"#X obj {x} {y} {text};")
        self.n += 1
        return self.n - 1

    def msg(self, text, x=None, y=None):
        x, y = self._pos(x, y)
        self.lines.append(f"#X msg {x} {y} {esc(text)};")
        self.n += 1
        return self.n - 1

    def text(self, text, x=None, y=None):
        x, y = self._pos(x, y)
        self.lines.append(f"#X text {x} {y} {esc(text)};")
        self.n += 1
        return self.n - 1

    def c(self, a, b, outlet=0, inlet=0):
        self.conns.append(f"#X connect {a} {outlet} {b} {inlet};")

    def chain(self, *ids):
        for a, b in zip(ids, ids[1:]):
            self.c(a, b)
        return ids[-1]

    # ---- iemgui ----------------------------------------------------------
    @staticmethod
    def _s(name):
        return name if name else "empty"

    def cnv(self, x, y, w, h, bg, label="", lx=4, ly=8, fs=10, lcol="#000000",
            rcv=""):
        lab = label if label else "empty"
        return self.raw(f"cnv 1 {w} {h} empty {self._s(rcv)} {lab} {lx} {ly} 0 {fs} "
                        f"{bg} {lcol} 0", x, y)

    def label(self, x, y, txt, fs=10, col="#000000", bg=None, rcv=""):
        """Invisible 1x1 canvas used as a text label (comments don't show in GOP)."""
        return self.raw(f"cnv 1 1 1 empty {self._s(rcv)} {txt if txt else 'empty'} 0 0 0 {fs} "
                        f"{bg or '#ffffff'} {col} 0", x, y)

    def hsl(self, x, y, w, h, lo, hi, snd, rcv, label, log=0, fg="#000000",
            bg="#ffffff", lcol="#000000", fs=9, lx=None, ly=None):
        lx = w + 5 if lx is None else lx
        ly = h // 2 if ly is None else ly
        return self.raw(f"hsl {w} {h} {lo} {hi} {log} 0 {snd} {rcv} {label} {lx} {ly} 0 {fs} "
                        f"{bg} {fg} {lcol} 0 1", x, y)

    def vsl(self, x, y, w, h, lo, hi, snd, rcv, label="empty", fg="#000000",
            bg="#ffffff", lcol="#000000"):
        return self.raw(f"vsl {w} {h} {lo} {hi} 0 0 {snd} {rcv} {label} 0 -8 0 9 "
                        f"{bg} {fg} {lcol} 0 1", x, y)

    def tgl(self, x, y, size, snd, rcv, label="empty", fg="#000000",
            bg="#ffffff", lcol="#000000", lx=None, ly=None, fs=9):
        lx = size + 4 if lx is None else lx
        ly = size // 2 if ly is None else ly
        return self.raw(f"tgl {size} 0 {snd} {rcv} {label} {lx} {ly} 0 {fs} "
                        f"{bg} {fg} {lcol} 0 1", x, y)

    def bng(self, x, y, size, snd, rcv, label="empty", fg="#000000",
            bg="#ffffff", lcol="#000000", lx=None, ly=None, fs=9):
        lx = size + 4 if lx is None else lx
        ly = size // 2 if ly is None else ly
        return self.raw(f"bng {size} 180 50 0 {snd} {rcv} {label} {lx} {ly} 0 {fs} "
                        f"{bg} {fg} {lcol}", x, y)

    def hradio(self, x, y, size, num, snd, rcv, label="empty", fg="#000000",
               bg="#ffffff", lcol="#000000"):
        return self.raw(f"hradio {size} 1 0 {num} {snd} {rcv} {label} 0 -8 0 9 "
                        f"{bg} {fg} {lcol} 0", x, y)

    def nbx(self, x, y, digits, h, lo, hi, snd, rcv, label="empty", fg="#000000",
            bg="#ffffff", lcol="#000000", lx=None, ly=None, fs=10):
        lx = digits * 8 + 16 if lx is None else lx
        ly = h // 2 if ly is None else ly
        return self.raw(f"nbx {digits} {h} {lo} {hi} 0 0 {snd} {rcv} {label} {lx} {ly} 0 {fs} "
                        f"{bg} {fg} {lcol} 0 256", x, y)

    # ---- output ----------------------------------------------------------
    def gop(self, w, h, x0=0, y0=0):
        self.coords = f"#X coords 0 -1 1 1 {w} {h} 2 {x0} {y0};"

    def render(self):
        parts = [self.head] + self.lines + self.conns
        if self.coords:
            parts.append(self.coords)
        return "\n".join(parts) + "\n"

    def save(self, path):
        with open(path, "w") as f:
            f.write(self.render())
