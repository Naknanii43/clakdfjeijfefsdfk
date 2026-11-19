#!/usr/bin/env python3
"""Generates the Clonk Goblin Pure Data plugin (Camomile / plugdata).

    python3 tools/generate.py            -> writes ClonkGoblin/ plugin folder
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pdgen import Patch, legacy_color  # noqa: E402
import presets  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "ClonkGoblin")
NVOICES = 8
NBANKS = 520

# name, gui label, lo, hi, log
SOUND = [
    ("tune", "TUNE", -24, 24, 0), ("pdrop", "BONK", -24, 48, 0),
    ("pdec", "BONK-TIME", 1, 400, 1), ("adec", "DECAY", 10, 2500, 1),
    ("noise", "HISS", 0, 1, 0), ("ndec", "HISS-TIME", 2, 1000, 1),
    ("ncut", "HISS-COLOR", 30, 135, 0), ("nq", "HISS-PEAK", 0.5, 25, 1),
    ("fm", "FM-WOBBLE", 0, 8, 0), ("fmr", "FM-RATIO", 0.25, 8, 1),
    ("modal", "THINGNESS", 0, 1, 0), ("mat", "WOOD>METAL", 0, 1, 0),
    ("ring", "RING", 2, 600, 1), ("ks", "STRINGY", 0, 1, 0),
    ("ksfb", "STRING-FB", 0, 0.995, 0), ("crush", "CRUSH", 0, 1, 0),
    ("drive", "FUZZ", 0, 1, 0), ("wob", "DRUNK", 0, 1, 0),
]
FXP = [("dsync", "ECHO-STEPS", 0.5, 8, 0), ("dfb", "ECHO-FB", 0, 0.92, 0),
       ("dmix", "ECHO-MIX", 0, 1, 0), ("space", "SPACE", 0, 1, 0),
       ("vol", "VOLUME", 0, 1, 0)]
MACROS = [("mtune", "M-TUNE", -24, 24, 0), ("mdecay", "M-DECAY", -2, 2, 0),
          ("mtone", "M-TONE", -36, 36, 0), ("mcrunch", "M-CRUNCH", 0, 1, 0),
          ("mwob", "M-DRUNK", 0, 1, 0), ("mspace", "M-SPACE", 0, 1, 0)]
GROOVE_SCALARS = ["len", "rate", "swing", "chance", "oops"]
STEPS = 16
PATTERN = [f"{p}{i+1}" for p in "gan" for i in range(STEPS)]
USER = ["bpm", "run", "sync", "mode", "arpm", "oct", "root", "lock"]
# every parameter that lives in a [value] (pattern steps live in arrays too)
ALLVALS = ([s[0] for s in SOUND] + [f[0] for f in FXP] + [m[0] for m in MACROS]
           + GROOVE_SCALARS + USER + PATTERN)

# host (Camomile) parameters: (name, target, txt line)
HOSTP = [
    ("bank", "param -name Bank -min 0 -max %d -default 0 -nsteps %d;" % (NBANKS - 1, NBANKS)),
    ("mtune", "param -name Tune -label st -min -24 -max 24 -default 0;"),
    ("mdecay", "param -name Decay -min -2 -max 2 -default 0;"),
    ("mtone", "param -name Tone -label st -min -36 -max 36 -default 0;"),
    ("mcrunch", "param -name Crunch -min 0 -max 1 -default 0;"),
    ("mwob", "param -name Drunk -min 0 -max 1 -default 0;"),
    ("mspace", "param -name Space -min 0 -max 1 -default 0;"),
    ("mode", "param -name Mode -list Play/Arp/Seq/SeqArp -default 2;"),
    ("vol", "param -name Volume -min 0 -max 1 -default 0.8;"),
]

QUIPS = """the_goblin_is_hungry please_do_not_feed_the_snare spoon_detected
now_with_37%_more_clonk certified_organic_glitches the_teacup_has_feelings
a_raccoon_got_into_the_mixer have_you_tried_hitting_it? this_preset_is_legally_a_sandwich
do_not_lick_the_resonator your_kick_drum_is_wearing_socks bonk_responsibly
warning:_contains_small_parts the_robot_is_doing_its_best 100%_artisanal_bleeps
the_hi-hat_escaped_again tiny_gremlins_are_tapping_on_stuff it_sounded_like_a_fork
please_hold:_goblin_is_thinking someone_dropped_a_marble_in_here
the_pigeon_approves the_drawer_is_stuck_(rhythmically) extra_crispy_mode
sounds_like_a_kettle_with_opinions now_entering_the_wonk_zone
zero_actual_spoons_were_harmed squelch_level:_moderate the_waffle_is_resonating
glitch_happens oops_all_ratchets your_beat_has_been_goblinified bleep_bloop_respectfully
the_moth_is_dancing a_tiny_robot_sneezed this_one_goes_clonk_clonk_fzzt
we_dont_talk_about_bank_404 nobody_knows_what_the_toad_knob_does""".split()


def ensure_out():
    os.makedirs(OUT, exist_ok=True)


# =========================================================================
#  cg-params: [r cg-NAME] -> [v cgNAME]
# =========================================================================
def gen_params():
    p = Patch()
    p.text("Clonk Goblin parameter store: every GUI send cg-NAME is mirrored into [value cgNAME] so [expr] can read it.", 20, 5)
    p.at(20, 40)
    p.max_y = 900
    p.col_w = 200
    lv = p.obj("r cg-lvl-set")
    p.c(lv, p.obj("v cglvl"))
    for name in ALLVALS:
        r = p.obj(f"r cg-{name}")
        if name == "oct":
            a = p.obj("+ 1")
            p.c(r, a)
            r = a
        v = p.obj(f"v cg{name}")
        p.c(r, v)
    p.save(os.path.join(OUT, "cg-params.pd"))


# =========================================================================
#  cg-voice: one percussion voice (cloned NVOICES times)
# =========================================================================
def gen_voice():
    p = Patch(1200, 900)
    p.text("one Clonk Goblin voice: pitch-bonk sine + FM + filtered hiss -> 3-mode resonator + string -> fuzz -> crush -> pan", 20, 5)
    o = p.obj
    p.at(20, 40)
    p.obj("block~ 16", 900, 10)

    inl = o("inlet")
    unp = o("unpack f f")
    p.c(inl, unp)
    vvel = o("v cgxvel")
    p.c(unp, vvel, 1)

    D = "pow(2, cgmdecay)"
    W = "min(cgwob+cgmwob, 1)"
    VA = "pow(cgxvel/127, 1.5)"
    C = "min(cgcrush+cgmcrunch, 1)"
    DRV = "min(cgdrive+cgmcrunch*0.5, 1)"

    # ---------------- signal graph --------------------------------------
    p.at(420, 40)
    pe = o("vline~")
    pe2 = o("*~")
    p.c(pe, pe2)
    p.c(pe, pe2, 0, 1)
    pe3 = o("*~")
    p.c(pe2, pe3)
    p.c(pe, pe3, 0, 1)
    pdrop = o("*~ 0")
    p.c(pe3, pdrop)
    basep = o("+~ 0")
    p.c(pdrop, basep)
    mtof = o("mtof~")
    p.c(basep, mtof)
    F = o("clip~ 5 18000")
    p.c(mtof, F)

    # FM
    fmrm = o("*~ 0")
    p.c(F, fmrm)
    mod = o("osc~")
    p.c(fmrm, mod)
    fe = o("vline~")
    fxf = o("*~")
    p.c(F, fxf)
    p.c(fe, fxf, 0, 1)
    modd = o("*~")
    p.c(mod, modd)
    p.c(fxf, modd, 0, 1)
    fmd = o("*~ 0")
    p.c(modd, fmd)
    carf = o("+~")
    p.c(F, carf)
    p.c(fmd, carf, 0, 1)
    car = o("osc~")
    p.c(carf, car)

    # amp env
    ae = o("vline~")
    ae2 = o("*~")
    p.c(ae, ae2)
    p.c(ae, ae2, 0, 1)
    tone = o("*~")
    p.c(car, tone)
    p.c(ae2, tone, 0, 1)
    tgl_ = o("line~")
    toneg = o("*~")
    p.c(tone, toneg)
    p.c(tgl_, toneg, 0, 1)

    # noise
    p.at(700, 40)
    nz = o("noise~")
    ncs = o("sig~ 1000")
    vcf = o("vcf~ 1")
    p.c(nz, vcf)
    p.c(ncs, vcf, 0, 1)
    ne = o("vline~")
    ne2 = o("*~")
    p.c(ne, ne2)
    p.c(ne, ne2, 0, 1)
    nzе = o("*~")
    p.c(vcf, nzе)
    p.c(ne2, nzе, 0, 1)
    ngl = o("line~")
    nzg = o("*~")
    p.c(nzе, nzg)
    p.c(ngl, nzg, 0, 1)
    # dry = toneg + nzg (fan-in)

    # modal resonator (3 modes)
    r2 = o("*~ 2")
    p.c(F, r2)
    r2c = o("clip~ 20 18000")
    p.c(r2, r2c)
    r3 = o("*~ 3")
    p.c(F, r3)
    r3c = o("clip~ 20 18000")
    p.c(r3, r3c)
    m1 = o("vcf~ 20")
    m2 = o("vcf~ 20")
    m3 = o("vcf~ 20")
    for m in (m1, m2, m3):
        p.c(toneg, m)
        p.c(nzg, m)
    p.c(F, m1, 0, 1)
    p.c(r2c, m2, 0, 1)
    p.c(r3c, m3, 0, 1)
    w2 = o("*~ 0.6")
    w3 = o("*~ 0.45")
    p.c(m2, w2)
    p.c(m3, w3)
    mgl = o("line~")
    modo = o("*~")
    p.c(m1, modo)
    p.c(w2, modo)
    p.c(w3, modo)
    p.c(mgl, modo, 0, 1)

    # Karplus string
    p.at(980, 40)
    kdt = o("expr~ 1000/max($v1, 20)")
    p.c(F, kdt)
    kvd = o("vd~ $0-ks")
    p.c(kdt, kvd)
    klp = o("lop~ 6500")
    p.c(kvd, klp)
    kfb = o("*~ 0")
    p.c(klp, kfb)
    kex = o("*~ 0.5")
    p.c(toneg, kex)
    p.c(nzg, kex)
    kdw = o("delwrite~ $0-ks 250")
    p.c(kex, kdw)
    p.c(kfb, kdw)
    kgl = o("line~")
    kout = o("*~")
    p.c(kvd, kout)
    p.c(kgl, kout, 0, 1)

    # dry gain
    dgl = o("line~")
    dry = o("*~")
    p.c(toneg, dry)
    p.c(nzg, dry)
    p.c(dgl, dry, 0, 1)

    # sum -> drive
    drv = o("*~ 1")
    p.c(dry, drv)
    p.c(modo, drv)
    p.c(kout, drv)
    th = o("expr~ tanh($v1)")
    p.c(drv, th)
    comp = o("*~ 1")
    p.c(th, comp)

    # crush
    ph = o("phasor~ 24000")
    sh = o("samphold~")
    p.c(comp, sh)
    p.c(ph, sh, 0, 1)
    q = o("expr~ floor($v1*$f2+0.5)/max($f2, 1)")
    p.c(sh, q)
    cwl = o("line~")
    cw = o("*~")
    p.c(q, cw)
    p.c(cwl, cw, 0, 1)
    cdl = o("line~")
    cd = o("*~")
    p.c(comp, cd)
    p.c(cdl, cd, 0, 1)

    # pan + out
    gll = o("line~")
    grl = o("line~")
    gl = o("*~")
    gr = o("*~")
    for s in (cw, cd):
        p.c(s, gl)
        p.c(s, gr)
    p.c(gll, gl, 0, 1)
    p.c(grl, gr, 0, 1)
    outl = o("outlet~", 1000, 870)
    outr = o("outlet~", 1100, 870)
    p.c(gl, outl)
    p.c(gr, outr)

    # ---------------- control: per-hit computations ---------------------
    # (expr, dest_id, dest_inlet, via) via: None -> direct float, "ramp" -> "$1 2" to line~
    setters = [
        (f"cgxnote+cgtune+cgmtune+(random(0, 2001)/1000-1)*{W}*1.5", basep, 1, None),
        ("cgpdrop*(0.6+0.4*cgxvel/127)", pdrop, 1, None),
        ("cgfmr", fmrm, 1, None),
        ("cgfm", fmd, 1, None),
        (f"(1-cgnoise*0.6)*{VA}", tgl_, 0, "ramp"),
        ("440*pow(2, (min(cgncut+cgmtone+(cgxnote-60)*0.25, 135)-69)/12)", ncs, 0, None),
        ("cgnq", vcf, 2, None),
        (f"cgnoise*sqrt(cgnq)*1.4*{VA}", ngl, 0, "ramp"),
        ("1.59+cgmat*1.17", r2, 1, None),
        ("2.14+cgmat*3.26", r3, 1, None),
        ("max(cgring*pow(2, cgmdecay*0.5), 1)", m1, 2, None),
        ("max(cgring*pow(2, cgmdecay*0.5), 1)", m2, 2, None),
        ("max(cgring*pow(2, cgmdecay*0.5), 1)", m3, 2, None),
        ("cgmodal*pow(max(cgring, 1), 0.25)*0.6", mgl, 0, "ramp"),
        ("(1-cgmodal*0.85)*(1-cgks*0.6)", dgl, 0, "ramp"),
        ("min(cgksfb+max(cgmdecay, 0)*0.01, 0.998)", kfb, 1, None),
        ("cgks*1.2", kgl, 0, "ramp"),
        (f"1+{DRV}*20", drv, 1, None),
        (f"1/(1+{DRV}*2.5)", comp, 1, None),
        (f"24000*pow(0.04, {C})", ph, 0, None),
        (f"pow(2, 13-{C}*10)", q, 1, None),
        (f"if({C}>0.01, 1, 0)", cwl, 0, "ramp"),
        (f"if({C}>0.01, 0, 1)", cdl, 0, "ramp"),
        ("sqrt(1-cgxpan)*cglvl", gll, 0, "ramp"),
        ("sqrt(cgxpan)*cglvl", grl, 0, "ramp"),
    ]
    envs = [
        ("cgpdec*pow(2, cgmdecay*0.5)", pe, "1, 0 $1"),
        (f"cgadec*{D}*0.35", fe, "1, 0 $1"),
        (f"cgadec*{D}", ae, "1 0.3, 0 $1 0.3"),
        (f"cgndec*{D}", ne, "1 0.2, 0 $1 0.2"),
    ]
    p.at(20, 120)
    p.max_y = 880
    p.col_w = 390
    # trigger: rightmost outlet stores the note, then pan, then setters, then phase reset, then envelopes
    nb = len(envs) + 1 + len(setters) + 1  # bangs
    trig = o("t " + "b " * nb + "f")
    p.c(unp, trig)
    vnote = o("v cgxnote")
    p.c(trig, vnote, nb)
    out_i = nb - 1
    pan = o("expr 0.5")  # every hit dead centre (DRUNK now only detunes)
    p.c(trig, pan, out_i)
    vpan = o("v cgxpan")
    p.c(pan, vpan)
    out_i -= 1
    for ex, dest, inlet, via in setters:
        e = o(f"expr {ex}")
        p.c(trig, e, out_i)
        out_i -= 1
        if via == "ramp":
            m = p.msg("$1 2")
            p.c(e, m)
            p.c(m, dest, 0, inlet)
        else:
            p.c(e, dest, 0, inlet)
    z = p.msg("0")
    p.c(trig, z, out_i)
    out_i -= 1
    p.c(z, mod, 0, 1)
    p.c(z, car, 0, 1)
    for ex, dest, m in envs:
        e = o(f"expr {ex}")
        p.c(trig, e, out_i)
        out_i -= 1
        mm = p.msg(m)
        p.c(e, mm)
        p.c(mm, dest)
    assert out_i == -1, out_i
    p.save(os.path.join(OUT, "cg-voice.pd"))


# =========================================================================
#  cg-clock: internal metro or host playhead -> step ticks
# =========================================================================
def gen_clock():
    p = Patch(1000, 800)
    o = p.obj
    p.text("clock: internal metro (RUN) or host transport (SYNC + DAW playing). outputs absolute step counter.", 20, 5)
    p.at(20, 40)
    SPQ = "if(cgrate==0, 2, if(cgrate==1, 4, if(cgrate==2, 8, 6)))"
    # --- recompute step length when bpm / rate change
    rb = o("r cg-bpm")
    tb = o("t b f")
    p.c(rb, tb)
    vb = o("v cgbpm")
    p.c(tb, vb, 1)
    rr = o("r cg-rate")
    tr = o("t b f")
    p.c(rr, tr)
    vr = o("v cgrate")
    p.c(tr, vr, 1)
    lb = o("loadbang")
    sm = o(f"expr 60000/(max(cgbpm, 20)*{SPQ})")
    for s in (tb, tr, lb):
        p.c(s, sm)
    vsm = o("v cgstepms")
    p.c(sm, vsm)

    # --- running state: internal = run && !(sync && hostplay)
    p.at(260, 40)
    rrun = o("r cg-run")
    trun = o("t b f")
    p.c(rrun, trun)
    p.c(trun, o("v cgrun"), 1)
    rsy = o("r cg-sync")
    tsy = o("t b f")
    p.c(rsy, tsy)
    p.c(tsy, o("v cgsync"), 1)
    rph = o("r playhead")
    route = o("route playing bpm position")
    p.c(rph, route)
    chp = o("change")
    p.c(route, chp)
    thp = o("t b f")
    p.c(chp, thp)
    p.c(thp, o("v cghostplay"), 1)
    st = o("expr if(cgrun && !(cgsync && cghostplay), 1, 0)")
    for s in (trun, tsy, thp):
        p.c(s, st)
    stc = o("change")
    p.c(st, stc)
    sel = o("sel 1")
    p.c(stc, sel)
    rst = p.msg("0")
    p.c(sel, rst)
    met = o("metro 125")
    p.c(stc, met)
    p.c(sm, met, 0, 1)
    cnt = o("f")
    inc = o("+ 1")
    p.c(met, cnt)
    p.c(cnt, inc)
    p.c(inc, cnt, 0, 1)
    p.c(rst, cnt, 0, 1)

    # --- host bpm (only when sync)
    hbpm = o("change")
    p.c(route, hbpm, 1)
    hb = o("expr if(cgsync, $f1, -1)")
    p.c(hbpm, hb)
    hbm = o("moses 1")
    p.c(hb, hbm)
    hbr = o("expr int($f1*10+0.5)/10")
    p.c(hbm, hbr, 1)
    p.c(hbr, o("s cg-bpm-set"))

    # --- host position -> step
    p.at(520, 40)
    up = o("unpack f f f")
    p.c(route, up, 2)
    hs = o(f"expr if(cgsync && cghostplay, floor($f1*{SPQ}+0.0001), -1)")
    p.c(up, hs)
    hsm = o("moses 0")
    p.c(hs, hsm)
    hsc = o("change")
    p.c(hsm, hsc, 1)

    # --- swing: odd steps are delayed
    p.at(760, 40)
    sw = o("t f f")
    p.c(cnt, sw)
    p.c(hsc, sw)
    odd = o("mod 2")
    pk = o("pack f f")
    p.c(sw, pk, 1, 1)
    p.c(sw, odd, 0, 0)
    p.c(odd, pk)
    rt = o("route 0 1")
    p.c(pk, rt)
    outl = o("outlet")
    p.c(rt, outl, 0)
    tod = o("t b f")
    p.c(rt, tod, 1)
    hold = o("f")
    p.c(tod, hold, 1, 1)
    dt = o("expr cgswing*cgstepms*0.5")
    p.c(tod, dt, 0)
    dl = o("delay")
    p.c(dt, dl)
    p.c(dl, hold)
    p.c(hold, outl)
    # stop: flush pending swing
    stp = p.msg("stop")
    p.c(sel, stp, 1)
    p.c(stp, dl)
    p.save(os.path.join(OUT, "cg-clock.pd"))


# =========================================================================
#  cg-brain: sequencer + arpeggiator + play mode + OOPS ratchets
# =========================================================================
def gen_brain():
    p = Patch(1400, 1000)
    o = p.obj
    p.text("brain: left inlet = clock ticks, right inlet = MIDI 'note vel'. modes 0 PLAY / 1 ARP / 2 SEQ / 3 SEQ+ARP.", 20, 5)
    p.at(20, 40)
    p.max_y = 950
    p.col_w = 330
    for arr, n in (("cggate", STEPS), ("cgacc", STEPS), ("cgpit", STEPS),
                   ("cgheld", 128), ("cgsorted", 128)):
        o(f"array define {arr} {n}")
    for i in range(STEPS):
        for pref, arr in (("g", "cggate"), ("a", "cgacc"), ("n", "cgpit")):
            r = o(f"r cg-{pref}{i+1}")
            a = o(f"array set {arr} {i}")
            p.c(r, a)

    # ---- MIDI in
    p.at(400, 40)
    p.col_w = 330
    mid = o("inlet", 700, 10)
    tm = o("t b l l")
    p.c(mid, tm)
    sw = p.msg("$2 $1")
    p.c(tm, sw, 2)
    tw = o("tabwrite cgheld")
    p.c(sw, tw)
    sn = o("stripnote")
    p.c(tm, sn, 1)
    pkn = o("pack f f")
    p.c(sn, pkn, 0, 0)
    p.c(sn, pkn, 1, 1)
    tn = o("t l l")
    p.c(pkn, tn)
    lastu = o("unpack f f")
    p.c(tn, lastu, 1)
    p.c(lastu, o("v cglast"))
    spg = o("spigot")
    p.c(tn, spg, 0)
    rmode = o("r cg-mode")
    eqm = o("== 0")
    p.c(rmode, eqm)
    p.c(eqm, spg, 0, 1)
    lbm = o("loadbang")
    m2 = p.msg("2")
    p.c(lbm, m2)
    p.c(m2, eqm)
    # unstick: clear held notes (button + CC123 all-notes-off)
    run = o("r cg-unstick")
    cc = o("ctlin 123")
    clr = p.msg("const 0")
    p.c(run, clr)
    p.c(cc, clr)
    sclr = o("s cgheld")
    p.c(clr, sclr)
    # rescan held -> sorted list
    resc = o("t b b")
    p.c(tm, resc, 0)
    p.c(clr, resc)
    z = p.msg("0")
    p.c(resc, z, 1)
    p.c(z, o("v cgcount"))
    n128 = p.msg("128")
    p.c(resc, n128, 0)
    until = o("until")
    p.c(n128, until)
    ic = o("f")
    ii = o("+ 1")
    p.c(until, ic)
    p.c(ic, ii)
    p.c(ii, ic, 0, 1)
    p.c(z, ic, 0, 1)
    hit = o("expr if(cgheld[$f1]>0, $f1, -1)")
    p.c(ic, hit)
    mo = o("moses 0")
    p.c(hit, mo)
    tfb = o("t f b b")
    p.c(mo, tfb, 1)
    ecnt = o("expr cgcount")
    p.c(tfb, ecnt, 2)
    tws = o("tabwrite cgsorted")
    p.c(ecnt, tws, 0, 1)
    einc = o("expr cgcount+1")
    p.c(tfb, einc, 1)
    p.c(einc, o("v cgcount"))
    p.c(tfb, tws, 0)

    # ---- ticks
    p.at(740, 40)
    tick = o("inlet", 20, 10)
    stp = o("expr $f1 % max(cglen, 1)")
    p.c(tick, stp)
    tst = o("t f f")
    p.c(stp, tst)
    p.c(tst, o("s cg-stepdisp"), 1)
    tst2 = o("t b f")
    p.c(tst, tst2, 0)
    p.c(tst2, o("v cgstep"), 1)
    gate = o("expr if(cgmode==1, cgcount>0, if(cgmode>=2, cggate[cgstep]>0 && random(0, 1000)<cgchance*1000, 0))")
    p.c(tst2, gate, 0)
    gsel = o("sel 0")
    p.c(gate, gsel)
    t3 = o("t b b b")
    p.c(gsel, t3, 1)
    # arp
    usearp = o("expr cgmode!=2 && cgcount>0")
    p.c(t3, usearp, 2)
    us = o("sel 1")
    p.c(usearp, us)
    apos = o("f")
    ainc = o("+ 1")
    p.c(us, apos)
    p.c(apos, ainc)
    p.c(ainc, apos, 0, 1)
    N = "(cgcount*cgoct)"
    P = f"max(2*{N}-2, 1)"
    arpk = o(f"expr if(cgarpm==0, $f1%{N}, if(cgarpm==1, {N}-1-$f1%{N}, if(cgarpm==2, if($f1%{P}<{N}, $f1%{P}, 2*{N}-2-$f1%{P}), if(cgarpm==3, random(0, {N}), min(max(cgprevk+random(-1, 2), 0), {N}-1)))))")
    p.c(apos, arpk)
    tk = o("t f f")
    p.c(arpk, tk)
    p.c(tk, o("v cgprevk"), 1)
    an = o("expr cgsorted[$f1%cgcount]+12*int($f1/cgcount)")
    p.c(tk, an, 0)
    p.c(an, o("v cgarpnote"))
    # velocity
    vel = o("expr min(if(cgacc[cgstep]>0, 120, 84)+random(-6, 7), 127)")
    p.c(t3, vel, 1)
    note = o("expr if(cgmode==1, cgarpnote, if(cgmode==2, if(cgheld[cglast]>0, cglast, cgroot)+floor(cgpit[cgstep]+0.5), if(cgcount>0, cgarpnote, cgroot)+floor(cgpit[cgstep]+0.5)))")
    p.c(t3, note, 0)
    nclip = o("clip 0 127")
    p.c(note, nclip)
    pk = o("pack f f")
    p.c(nclip, pk)
    p.c(vel, pk, 0, 1)

    # ---- audition (POKE)
    poke = o("r cg-poke")
    pm = o("expr cgroot")
    p.c(poke, pm)
    pkp = o("pack f 110")
    p.c(pm, pkp)

    # ---- output stage + OOPS ratchets
    p.at(1080, 40)
    st = o("t l l")
    p.c(pk, st)
    p.c(spg, st)
    p.c(pkp, st)
    outl = o("outlet")
    p.c(st, outl, 0)
    p.c(st, o("s cg-played"), 0)
    tr = o("t l b")
    p.c(st, tr, 1)
    roll = o("expr random(0, 1000) < cgoops*1000")
    p.c(tr, roll, 1)
    rs = o("spigot")
    p.c(roll, rs, 0, 1)
    p.c(tr, rs, 0)
    ru = o("unpack f f")
    p.c(rs, ru)
    tnv = o("t b f")
    p.c(ru, tnv, 0)
    p.c(ru, o("v cgratvel"), 1)
    p.c(tnv, o("v cgratnote"), 1)
    rr = o("expr random(2, 5)")
    p.c(tnv, rr, 0)
    trr = o("t b b b f")
    p.c(rr, trr)
    p.c(trr, o("v cgratr"), 3)
    for i in (1, 2, 3):
        d = o(f"expr if({i}<cgratr, {i}*cgstepms/cgratr, -1)")
        p.c(trr, d, 3 - i)
        mm = o("moses 0")
        p.c(d, mm)
        dl = o("delay")
        p.c(mm, dl, 1)
        tbb = o("t b b")
        p.c(dl, tbb)
        nn = o("expr cgratnote+if(random(0, 5)==0, 12, 0)")
        p.c(tbb, nn, 0)
        vv = o(f"expr cgratvel*pow(0.72, {i})")
        p.c(tbb, vv, 1)
        pr = o("pack f f")
        p.c(nn, pr)
        p.c(vv, pr, 0, 1)
        p.c(pr, outl)
    p.save(os.path.join(OUT, "cg-brain.pd"))


# =========================================================================
#  cg-fx: ping-pong dub echo + tiny junkyard reverb
# =========================================================================
def gen_fx():
    p = Patch(1200, 900)
    o = p.obj
    p.text("fx: tempo-synced ping-pong echo + small schroeder 'space'", 20, 5)
    p.at(20, 40)
    il = o("inlet~", 300, 10)
    ir = o("inlet~", 400, 10)
    # control poll
    lb = o("loadbang")
    met = o("metro 40")
    p.c(lb, met)
    params = [
        ("min(max(cgdsync*cgstepms, 5), 2900)", "$1 80"),
        ("cgdfb", "$1 40"),
        ("cgdmix", "$1 40"),
        ("min(cgspace+cgmspace, 1)", "$1 40"),
    ]
    lines = []
    for ex, m in params:
        e = o(f"expr {ex}")
        p.c(met, e)
        ch = o("change")
        p.c(e, ch)
        mm = p.msg(m)
        p.c(ch, mm)
        ln = o("line~")
        p.c(mm, ln)
        lines.append(ln)
    tline, fbline, mixline, spline = lines

    p.at(300, 40)
    mono = o("*~ 0.5")
    p.c(il, mono)
    p.c(ir, mono)
    # balanced echo: both sides get the same input and the same time = equal L/R
    dwl = o("delwrite~ $0-dl 4500")
    dwr = o("delwrite~ $0-dr 4500")
    p.c(mono, dwl)
    p.c(mono, dwr)
    vdl = o("vd~ $0-dl")
    vdr = o("vd~ $0-dr")
    p.c(tline, vdl)
    p.c(tline, vdr)
    for src, dst in ((vdl, dwl), (vdr, dwr)):
        lp = o("lop~ 3200")
        p.c(src, lp)
        hp = o("hip~ 90")
        p.c(lp, hp)
        th = o("expr~ tanh($v1*1.3)")
        p.c(hp, th)
        fb = o("*~")
        p.c(th, fb)
        p.c(fbline, fb, 0, 1)
        p.c(fb, dst)
    wl = o("*~")
    wr = o("*~")
    p.c(vdl, wl)
    p.c(vdr, wr)
    p.c(mixline, wl, 0, 1)
    p.c(mixline, wr, 0, 1)
    # dry + echo
    sl = o("+~")
    sr = o("+~")
    p.c(il, sl)
    p.c(wl, sl, 0, 1)
    p.c(ir, sr)
    p.c(wr, sr, 0, 1)

    # reverb
    p.at(600, 40)
    rin0 = o("*~ 0.25")
    p.c(sl, rin0)
    p.c(sr, rin0)
    rin1 = o("hip~ 220")  # keep the lows out of the reverb (less mud, equal L/R)
    p.c(rin0, rin1)
    rin = o("hip~ 220")
    p.c(rin1, rin)
    combs = []
    for k, ms in enumerate((29.7, 37.1, 41.1, 43.7)):
        sm = o("+~")
        p.c(rin, sm)
        dw = o(f"delwrite~ $0-c{k} 100")
        p.c(sm, dw)
        dr = o(f"delread~ $0-c{k} {ms}")
        lp = o("lop~ 3800")
        p.c(dr, lp)
        g = o("*~ 0.83")
        p.c(lp, g)
        p.c(g, sm, 0, 1)
        combs.append(dr)
    csum = o("*~ 0.25")
    for dr in combs:
        p.c(dr, csum)

    def allpass(src, name, ms, g=0.6):
        w = o("+~")
        p.c(src, w)
        dw = o(f"delwrite~ $0-{name} 50")
        p.c(w, dw)
        dr = o(f"delread~ $0-{name} {ms}")
        gd = o(f"*~ {g}")
        p.c(dr, gd)
        p.c(gd, w, 0, 1)
        gw = o(f"*~ {-g}")
        p.c(w, gw)
        y = o("+~")
        p.c(dr, y)
        p.c(gw, y, 0, 1)
        return y

    a1 = allpass(csum, "a1", 5.1)
    revl = allpass(a1, "al", 1.7)
    # identical reverb on both sides: percussion stays perfectly centred
    revr = revl
    wsl = o("*~")
    wsr = o("*~")
    p.c(revl, wsl)
    p.c(revr, wsr)
    p.c(spline, wsl, 0, 1)
    p.c(spline, wsr, 0, 1)
    ol = o("outlet~", 600, 870)
    orr = o("outlet~", 700, 870)
    for s in (sl, wsl):
        p.c(s, ol)
    for s in (sr, wsr):
        p.c(s, orr)
    p.save(os.path.join(OUT, "cg-fx.pd"))


# =========================================================================
#  cg-bank: sound banks, grooves, goblin mutation, dice, quips
# =========================================================================
def gen_bank():
    p = Patch(1300, 900)
    o = p.obj
    p.text("banks: line N of banks.txt = 'Name CATEGORY key value ...', line N of grooves.txt = pattern. GOBLIN steals random knobs from another bank.", 20, 5)
    p.at(20, 40)
    p.max_y = 850
    tb = o("text define cgbanks")
    tg = o("text define cggrooves")
    tq = o("text define cgquips")
    lb = o("loadbang")
    t = o("t b b b b")
    p.c(lb, t)
    for out_i, (tid, fn) in zip((3, 2, 1), ((tb, "banks.txt"), (tg, "grooves.txt"), (tq, "quips.txt"))):
        m = p.msg(f"read {fn}")
        p.c(t, m, out_i)
        p.c(m, tid)
    p.c(t, p.msg("; cg-bank-set 0"), 0)

    def dripper(gate_expr=None):
        """list of 'key value' pairs -> ; cg-KEY-set VALUE  (optionally random-gated)"""
        sp = o("list split 2")
        back = o("list")
        p.c(sp, back, 1)
        p.c(back, sp)
        out = sp
        if gate_expr:
            tt = o("t l b")
            p.c(sp, tt, 0)
            g = o(f"expr {gate_expr}")
            p.c(tt, g, 1)
            spg = o("spigot")
            p.c(g, spg, 0, 1)
            p.c(tt, spg, 0)
            out = spg
        p.c(out, p.msg("; cg-$1-set $2"))
        return sp, out

    def locked_gate(src, outlet):
        """returns a spigot that is open only while LOCK-GROOVE is off"""
        tt = o("t f b")
        p.c(src, tt, outlet)
        lk = o("expr cglock==0")
        p.c(tt, lk, 1)
        sp = o("spigot")
        p.c(lk, sp, 0, 1)
        p.c(tt, sp, 0)
        return sp

    # ---- load bank N
    p.at(280, 40)
    rb = o("r cg-bank")
    cl = o(f"clip 0 {NBANKS-1}")
    p.c(rb, cl)
    tl = o("t b f f f")
    p.c(cl, tl)
    p.c(tl, o("v cgbank"), 3)
    get = o("text get cgbanks")
    p.c(tl, get, 2)
    sp2 = o("list split 2")
    p.c(get, sp2)
    nm = o("unpack s s")
    p.c(sp2, nm)
    p.c(nm, p.msg("; cg-name-lbl label $1"), 0)
    p.c(nm, p.msg("; cg-cat-lbl label $1"), 1)
    d_in, _ = dripper()
    p.c(sp2, d_in, 1)
    gsp = locked_gate(tl, 1)
    gget = o("text get cggrooves")
    p.c(gsp, gget)
    g_in, _ = dripper()
    p.c(gget, g_in)
    # quip on every load
    rq = o("r cg-quip")
    qr = o("random 1000")
    p.c(tl, qr, 0)
    p.c(rq, qr)
    qm = o("t f b")
    p.c(qr, qm)
    qs = o("text size cgquips")
    p.c(qm, qs, 1)
    qmod = o("mod 1")
    p.c(qs, qmod, 0, 1)
    p.c(qm, qmod, 0)
    qget = o("text get cgquips")
    p.c(qmod, qget)
    p.c(qget, p.msg("; cg-quip-lbl label $1"))

    # ---- prev / next / random
    p.at(560, 40)
    for rcv, ex in (("cg-prev", f"(cgbank-1+{NBANKS})%{NBANKS}"),
                    ("cg-next", f"(cgbank+1)%{NBANKS}"),
                    ("cg-rand", f"random(0, {NBANKS})")):
        r = o(f"r {rcv}")
        e = o(f"expr {ex}")
        p.c(r, e)
        p.c(e, o("s cg-bank-set"))

    # ---- GOBLIN: steal ~35% of the knobs (and ~25% of the groove) from a random bank
    rg = o("r cg-goblin")
    tgb = o("t b b b")
    p.c(rg, tgb)
    z = p.msg("0")
    p.c(tgb, z, 2)
    p.c(z, o("v cgstolen"))
    rnd = o(f"random {NBANKS}")
    p.c(tgb, rnd, 1)
    trn = o("t f f")
    p.c(rnd, trn)
    gget1 = o("text get cgbanks")
    p.c(trn, gget1, 1)
    gsp1 = o("list split 4")  # skip name, category and the lvl trim
    p.c(gget1, gsp1)
    din, dout = dripper("random(0, 100)<35")
    p.c(gsp1, din, 1)
    cnt = o("expr cgstolen+1")
    p.c(dout, cnt)
    p.c(cnt, o("v cgstolen"))
    lsp = locked_gate(trn, 0)
    gget2 = o("text get cggrooves")
    p.c(lsp, gget2)
    din2, _ = dripper("random(0, 100)<25")
    p.c(gget2, din2)
    sc = o("expr cgstolen")
    p.c(tgb, sc, 0)
    mf = o("makefilename goblin_swapped_%d_bones")
    p.c(sc, mf)
    p.c(mf, p.msg("; cg-quip-lbl label $1"))

    # ---- DICE: random pattern
    p.at(840, 40)
    rd = o("r cg-dice")
    td = o("t b b")
    p.c(rd, td)
    tz = o("t b b")
    p.c(td, tz, 1)
    n16 = p.msg(str(STEPS))
    z2 = p.msg("0")
    p.c(tz, z2, 1)
    p.c(tz, n16, 0)
    un = o("until")
    p.c(n16, un)
    fi = o("f")
    fi1 = o("+ 1")
    p.c(un, fi)
    p.c(fi, fi1)
    p.c(fi1, fi, 0, 1)
    p.c(z2, fi, 0, 1)
    step = o("t f f f")
    p.c(fi1, step)
    for k, (pref, ex) in enumerate((
            ("n", "if(random(0, 10)<5, 0, if(random(0, 3)==0, 12*(random(0, 2)*2-1), random(-7, 8)))"),
            ("a", "random(0, 100)<25"),
            ("g", "random(0, 100)<45"))):
        mk = o(f"makefilename cg-{pref}%d-set")
        p.c(step, mk, 2 - k)
        tt = o("t s b")
        p.c(mk, tt)
        e = o(f"expr {ex}")
        p.c(tt, e, 1)
        pk = o("pack s f")
        p.c(e, pk, 0, 1)
        p.c(tt, pk, 0)
        p.c(pk, p.msg("; $1 $2"))
    p.c(td, p.msg("; cg-quip-lbl label the_dice_have_spoken"), 0)
    p.save(os.path.join(OUT, "cg-bank.pd"))


# =========================================================================
#  cg-host: Camomile parameter + state bridge (silently idle elsewhere)
# =========================================================================
def gen_host():
    p = Patch(1300, 900)
    o = p.obj
    p.text("host bridge for Camomile: [r param] -> GUI, save/load of the whole state. Does nothing in plugdata / vanilla Pd.", 20, 5)
    p.at(20, 40)
    rp = o("r param")
    rt = o("route " + " ".join(str(i + 1) for i in range(len(HOSTP))))
    p.c(rp, rt)
    p.at(20, 100)
    p.col_w = 150
    p.max_y = 300
    for i, (name, _) in enumerate(HOSTP):
        ch = o("change")
        p.c(rt, ch, i)
        tf = o("t f f")
        p.c(ch, tf)
        ne = o(f"expr $f1 != cg{name}")
        p.c(tf, ne, 1)
        sp = o("spigot")
        p.c(ne, sp, 0, 1)
        p.c(tf, sp, 0)
        p.c(sp, o(f"s cg-{name}-set"))

    # ---- save: bank last so that on load (reverse drip) it is applied first
    p.at(20, 360)
    p.col_w = 220
    p.max_y = 880
    rs = o("r save")
    names = [n for n in ALLVALS if n not in ("run",)] + ["lvl", "bank"]
    t = o("t b " + "b " * len(names) + "b")
    p.c(rs, t)
    store = o("list store")
    clear = p.msg("list")
    p.c(t, clear, len(names) + 1)
    p.c(clear, store, 0, 1)
    for k, n in enumerate(names):
        v = o(f"v cg{n}")
        p.c(t, v, len(names) - k)
        if n == "oct":
            mm = o("- 1")
            p.c(v, mm)
            v = mm
        am = p.msg(f"append {n} $1")
        p.c(v, am)
        p.c(am, store)
    out = p.msg("bang")
    p.c(t, out, 0)
    p.c(out, store)
    pre = o("list prepend save")
    p.c(store, pre)
    tr = o("list trim")
    p.c(pre, tr)
    p.c(tr, o("s camomile"))
    # ---- load
    rl = o("r load")
    ll = o("list")
    p.c(rl, ll)
    sp = o("list split 2")
    p.c(ll, sp)
    back = o("list")
    p.c(sp, back, 1)
    p.c(back, sp)
    p.c(sp, p.msg("; cg-$1-set $2"))
    p.save(os.path.join(OUT, "cg-host.pd"))


# =========================================================================
#  main patch + GUI
# =========================================================================
PAL = dict(bg="#fdf0c2", title="#1d1b26", yellow="#ffd23f", pink="#ff7aa2",
           sound="#ffd6e0", fx="#c1f0dc", macro="#ffe5a8", brain="#d6dcff",
           pat="#bde0fe", ink="#2b2340", green="#7bd389", cyan="#7ee8fa",
           led_off="#5a6b8c", led_on="#ff3b6b", quip="#fff3b0")


def gen_main():
    p = Patch(1500, 900, 10)
    W, H = 780, 480
    P = PAL
    cnv = p.cnv
    # backgrounds
    cnv(0, 0, W, H, P["bg"])
    cnv(0, 0, W, 54, P["title"], "CLONK_GOBLIN", 10, 18, 22, P["yellow"])
    p.label(12, 42, "percussive_nonsense_engine_//_520_banks", 9, P["pink"], P["title"])
    # bank row
    t = P["title"]
    p.bng(262, 10, 18, "cg-prev", "empty", "<", "#ffffff", P["cyan"], P["ink"], 6, 9, 11)
    p.nbx(284, 10, 4, 18, 0, NBANKS - 1, "cg-bank", "cg-bank-set", "BANK", "#000000",
          P["yellow"], P["yellow"], 0, -6, 9)
    p.bng(338, 10, 18, "cg-next", "empty", ">", "#ffffff", P["cyan"], P["ink"], 6, 9, 11)
    p.bng(360, 10, 18, "cg-rand", "empty", "?", "#ffffff", P["pink"], P["ink"], 6, 9, 11)
    p.label(390, 17, "loading...", 14, "#ffffff", t, "cg-name-lbl")
    p.label(390, 38, "...", 9, P["cyan"], t, "cg-cat-lbl")
    p.bng(612, 7, 40, "cg-goblin", "empty", "GOBLIN!", "#ffffff", P["green"], P["ink"], 1, 20, 10)
    p.tgl(660, 8, 14, "cg-lock", "cg-lock-set", "LOCK-GROOVE", P["ink"], "#ffffff", P["yellow"], 17, 7, 8)
    p.bng(660, 30, 14, "cg-dice", "empty", "DICE", "#ffffff", P["pink"], P["yellow"], 17, 7, 8)
    p.bng(732, 7, 40, "cg-poke", "empty", "POKE", "#ffffff", P["pink"], P["ink"], 6, 20, 10)
    # quip strip
    cnv(0, 54, W, 20, P["quip"])
    p.label(10, 64, "the_goblin_is_waking_up", 11, "#6b4e00", P["quip"], "cg-quip-lbl")

    # sound panel
    cnv(4, 78, 386, 236, P["sound"], "THE_NOISE", 6, 9, 11, P["ink"])
    for k, (name, lab, lo, hi, lg) in enumerate(SOUND):
        col, row = divmod(k, 9)
        x = 10 + col * 192
        y = 96 + row * 24
        p.hsl(x, y, 100, 14, lo, hi, f"cg-{name}", f"cg-{name}-set", lab, lg,
              P["ink"], "#ffffff", P["ink"])
    # fx panel
    cnv(394, 78, 190, 150, P["fx"], "THE_ROOM", 6, 9, 11, P["ink"])
    for k, (name, lab, lo, hi, lg) in enumerate(FXP):
        p.hsl(400, 96 + k * 24, 90, 14, lo, hi, f"cg-{name}", f"cg-{name}-set", lab, lg,
              P["ink"], "#ffffff", P["ink"])
    # macro panel
    cnv(588, 78, 188, 150, P["macro"], "BIG_KNOBS_(DAW)", 6, 9, 11, P["ink"])
    for k, (name, lab, lo, hi, lg) in enumerate(MACROS):
        p.hsl(594, 96 + k * 22, 90, 13, lo, hi, f"cg-{name}", f"cg-{name}-set", lab, lg,
              P["ink"], "#ffffff", P["ink"])
    # brain panel
    cnv(394, 232, 382, 120, P["brain"], "THE_BRAIN", 6, 9, 11, P["ink"])
    y1 = 248
    p.tgl(470, y1 - 6, 16, "cg-run", "cg-run-set", "RUN", P["led_on"], "#ffffff", P["ink"])
    p.tgl(512, y1 - 6, 16, "cg-sync", "cg-sync-set", "DAW-SYNC", P["ink"], "#ffffff", P["ink"])
    p.nbx(592, y1 - 6, 4, 16, 20, 300, "cg-bpm", "cg-bpm-set", "BPM", "#000000", "#ffffff", P["ink"])
    p.nbx(680, y1 - 6, 3, 16, 12, 108, "cg-root", "cg-root-set", "ROOT", "#000000", "#ffffff", P["ink"])
    y2 = 268
    p.label(400, y2 + 7, "MODE", 9, P["ink"], P["brain"])
    p.hradio(434, y2, 14, 4, "cg-mode", "cg-mode-set", "empty", P["ink"], "#ffffff", P["ink"])
    p.label(494, y2 + 7, "SEQ", 9, "#c2185b", P["brain"], "cg-modename")
    p.label(584, y2 + 7, "RATE", 9, P["ink"], P["brain"])
    p.hradio(614, y2, 14, 4, "cg-rate", "cg-rate-set", "empty", P["ink"], "#ffffff", P["ink"])
    p.label(674, y2 + 7, "1/16", 9, "#c2185b", P["brain"], "cg-ratename")
    y3 = 288
    p.label(400, y3 + 7, "ARP", 9, P["ink"], P["brain"])
    p.hradio(434, y3, 14, 5, "cg-arpm", "cg-arpm-set", "empty", P["ink"], "#ffffff", P["ink"])
    p.label(508, y3 + 7, "UP", 9, "#c2185b", P["brain"], "cg-arpname")
    p.label(584, y3 + 7, "OCT", 9, P["ink"], P["brain"])
    p.hradio(614, y3, 14, 4, "cg-oct", "cg-oct-set", "empty", P["ink"], "#ffffff", P["ink"])
    p.bng(700, y3, 14, "cg-unstick", "empty", "UNSTICK", "#ffffff", P["yellow"], P["ink"], 17, 7, 8)
    y4 = 310
    p.nbx(400, y4, 2, 14, 1, 16, "cg-len", "cg-len-set", "LEN", "#000000", "#ffffff", P["ink"], 30, 7, 9)
    p.hsl(460, y4, 60, 12, 0, 0.6, "cg-swing", "cg-swing-set", "SWING", 0, P["ink"], "#ffffff", P["ink"])
    p.hsl(570, y4, 50, 12, 0, 1, "cg-chance", "cg-chance-set", "MAYBE", 0, P["ink"], "#ffffff", P["ink"])
    p.hsl(670, y4, 50, 12, 0, 1, "cg-oops", "cg-oops-set", "OOPS", 0, P["led_on"], "#ffffff", P["ink"])
    p.label(400, 340, "PLAY=midi_ARP=hold_keys_SEQ=pattern", 8, "#555577", P["brain"])

    # pattern panel
    cnv(4, 318, 386, 34, P["brain"])
    p.label(10, 328, "tip:_RUN_or_press_DAW_play._POKE_to_test.", 9, P["ink"], P["brain"])
    p.label(10, 342, "GOBLIN!_mutates._DICE_re-rolls_the_pattern.", 9, P["ink"], P["brain"])
    cnv(4, 356, 772, 120, P["pat"], "THE_PATTERN", 6, 9, 11, P["ink"])
    p.label(8, 381, "LED", 8, P["ink"], P["pat"])
    p.label(8, 396, "HIT", 9, P["ink"], P["pat"])
    p.label(8, 422, "OOMPH", 8, P["ink"], P["pat"])
    p.label(8, 448, "PITCH", 8, P["ink"], P["pat"])
    for i in range(STEPS):
        x = 60 + i * 45
        shade = "#a2d2ff" if (i // 4) % 2 else P["pat"]
        if shade != P["pat"]:
            cnv(x - 8, 368, 42, 106, shade)
        p.raw(f"bng 9 110 50 0 empty cg-led{i} empty 0 0 0 8 {P['led_off']} {P['led_on']} #000000", x + 7, 371)
        p.tgl(x, 384, 24, f"cg-g{i+1}", f"cg-g{i+1}-set", "empty", P["ink"], "#ffffff")
        p.tgl(x + 5, 414, 14, f"cg-a{i+1}", f"cg-a{i+1}-set", "empty", P["led_on"], "#ffffff")
        p.vsl(x + 7, 434, 10, 34, -12, 12, f"cg-n{i+1}", f"cg-n{i+1}-set", "empty",
              P["ink"], "#ffffff")
    p.gop(W, H)

    # ---------------- engine (outside the GOP area) ----------------------
    o = p.obj
    X = 820
    p.text("CLONK GOBLIN - everything left of here is the plugin face. engine below.", X, 10)
    o("cg-params", X, 40)
    o("cg-bank", X, 64)
    o("cg-host", X, 88)
    clock = o("cg-clock", X, 130)
    brain = o("cg-brain", X, 180)
    p.c(clock, brain)
    ni = o("notein", X + 160, 130)
    npk = o("pack f f", X + 160, 155)
    p.c(ni, npk, 0, 0)
    p.c(ni, npk, 1, 1)
    p.c(npk, brain, 0, 1)
    rn = o("r cg-note", X + 260, 155)
    p.c(rn, brain, 0, 1)
    # voice allocator: round robin
    ta = o("t a b", X, 210)
    p.c(brain, ta)
    cf = o("f", X + 120, 235)
    cp = o("+ 1", X + 160, 235)
    cm = o(f"mod {NVOICES}", X + 120, 260)
    p.c(ta, cf, 1)
    p.c(cf, cp)
    p.c(cp, cm)
    p.c(cm, cf, 0, 1)
    lp = o("list prepend", X, 285)
    p.c(cf, lp, 0, 1)
    p.c(ta, lp, 0)
    tr = o("list trim", X, 310)
    p.c(lp, tr)
    cl = o(f"clone cg-voice {NVOICES}", X, 335)
    p.c(tr, cl)
    fx = o("cg-fx", X, 365)
    p.c(cl, fx, 0, 0)
    p.c(cl, fx, 1, 1)
    # master volume + soft clip
    rv = o("r cg-vol", X + 200, 365)
    vm = p.msg("$1 30", X + 200, 390)
    p.c(rv, vm)
    vl = o("line~", X + 200, 415)
    gl = o("*~", X, 415)
    gr = o("*~", X + 80, 415)
    p.c(fx, gl, 0)
    p.c(fx, gr, 1)
    p.c(vl, gl, 0, 1)
    p.c(vl, gr, 0, 1)
    p.c(vm, vl)
    hl = o("hip~ 8", X, 440)
    hr = o("hip~ 8", X + 80, 440)
    p.c(gl, hl)
    p.c(gr, hr)
    cl1 = o("expr~ tanh($v1*1.1)", X, 465)
    cl2 = o("expr~ tanh($v1*1.1)", X + 160, 465)
    p.c(hl, cl1)
    p.c(hr, cl2)
    dac = o("dac~ 1 2", X, 495)
    p.c(cl1, dac, 0, 0)
    p.c(cl2, dac, 0, 1)
    p.c(cl1, o("s~ cg-master-l", X + 100, 520))
    p.c(cl2, o("s~ cg-master-r", X + 220, 520))

    # LED step display: flash the step's bang
    rs = o("r cg-stepdisp", X + 400, 40)
    mk = o("makefilename cg-led%d", X + 400, 65)
    p.c(rs, mk)
    p.c(mk, p.msg("; $1 bang", X + 400, 90))

    # name labels for radios
    def namer(rcv, dest, names, y):
        r = o(f"r {rcv}", X + 400, y)
        s = o("sel " + " ".join(str(i) for i in range(len(names))), X + 400, y + 25)
        p.c(r, s)
        for i, nm in enumerate(names):
            m = p.msg(f"; {dest} label {nm}", X + 400 + i * 120, y + 50)
            p.c(s, m, i)

    namer("cg-mode", "cg-modename", ["PLAY", "ARP", "SEQ", "SEQ+ARP"], 260)
    namer("cg-rate", "cg-ratename", ["1/8", "1/16", "1/32", "1/16T"], 340)
    namer("cg-arpm", "cg-arpname", ["UP", "DOWN", "UP+DOWN", "RANDOM", "DRUNK"], 420)

    # defaults for things that are not in a bank
    lb = o("loadbang", X, 560)
    init = ("; cg-bpm-set 120; cg-mode-set 2; cg-arpm-set 0; cg-oct-set 0; "
            "cg-root-set 48; cg-vol-set 0.8; cg-sync-set 1; cg-run-set 0; cg-lock-set 0; "
            "cg-mtune-set 0; cg-mdecay-set 0; cg-mtone-set 0; cg-mcrunch-set 0; "
            "cg-mwob-set 0; cg-mspace-set 0")
    m = p.msg(init, X, 585)
    p.c(lb, m)
    p.save(os.path.join(OUT, "ClonkGoblin.pd"))


def gen_txt():
    lines = ["type instrument;", "code ClGb;", "midiin true;", "midiout false;",
             "playhead true;", "bus 0 2;", "taillength 4;", "compatibility v1.0.7;"]
    lines += [h[1] for h in HOSTP]
    with open(os.path.join(OUT, "ClonkGoblin.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")


def gen_quips():
    with open(os.path.join(OUT, "quips.txt"), "w") as f:
        for q in QUIPS:
            f.write(q + ";\n")


def main():
    ensure_out()
    gen_params()
    gen_voice()
    gen_clock()
    gen_brain()
    gen_fx()
    gen_bank()
    gen_host()
    gen_main()
    gen_txt()
    gen_quips()
    import json
    lv = os.path.join(ROOT, "tools", "levels.json")
    levels = json.load(open(lv)) if os.path.exists(lv) else {}
    banks = presets.write(OUT, NBANKS, levels)
    print(f"wrote {OUT} with {len(banks)} banks")


if __name__ == "__main__":
    main()
