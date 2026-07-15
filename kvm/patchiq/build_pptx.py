#!/usr/bin/env python3
"""
PatchIQ — PPTX presentation builder (watsonx Challenge 2026).
Run from any directory:
    python3 /Users/kencheru/kvm/patchiq/build_pptx.py
Output: /Users/kencheru/kvm/patchiq/PatchIQ_Presentation_2026.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

OUT = "/Users/kencheru/kvm/patchiq/PatchIQ_Presentation_2026.pptx"

# ── Palette ────────────────────────────────────────────────────────────────
DARK     = RGBColor(0x1A, 0x1D, 0x2E)
GREEN    = RGBColor(0x22, 0xC5, 0x5E)
BLUE     = RGBColor(0x60, 0xA5, 0xFA)
PURPLE   = RGBColor(0x7C, 0x5C, 0xD8)
ORANGE   = RGBColor(0xF9, 0x73, 0x16)
YELLOW   = RGBColor(0xFA, 0xCC, 0x15)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
GREY     = RGBColor(0x9C, 0xA3, 0xAF)
MIDGREY  = RGBColor(0x37, 0x41, 0x51)
SURFACE  = RGBColor(0x1E, 0x22, 0x36)
RED      = RGBColor(0xEF, 0x44, 0x44)

SW, SH = Inches(13.33), Inches(7.5)   # widescreen 16:9

# ── helpers ────────────────────────────────────────────────────────────────
def add_slide(prs, layout_index=6):
    layout = prs.slide_layouts[layout_index]
    slide  = prs.slides.add_slide(layout)
    for ph in slide.placeholders:
        sp = ph._element
        sp.getparent().remove(sp)
    return slide

def bg(slide, color=DARK):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color

def box(slide, x, y, w, h, fill=None, line=None, line_w=Pt(1)):
    from pptx.util import Emu
    sp = slide.shapes.add_shape(1, x, y, w, h)   # MSO_SHAPE_TYPE.RECTANGLE = 1
    sp.line.width = line_w
    if fill:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    else:
        sp.fill.background()
    if line:
        sp.line.color.rgb = line
    else:
        sp.line.fill.background()
    return sp

def txt(slide, text, x, y, w, h, size=18, bold=False, color=WHITE,
        align=PP_ALIGN.LEFT, italic=False, wrap=True):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p  = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.color.rgb = color
    run.font.italic    = italic
    return tb

def heading(slide, title, subtitle=None):
    txt(slide, title, Inches(0.5), Inches(0.22), Inches(12.3), Inches(0.65),
        size=28, bold=True, color=WHITE)
    # green underline bar
    box(slide, Inches(0.5), Inches(0.88), Inches(1.1), Inches(0.055),
        fill=GREEN, line=None)
    if subtitle:
        txt(slide, subtitle, Inches(0.5), Inches(0.95), Inches(12), Inches(0.45),
            size=14, color=GREY)

def card(slide, x, y, w, h, border=MIDGREY, fill=SURFACE):
    box(slide, x, y, w, h, fill=fill, line=border, line_w=Pt(1.2))

# ── SLIDE BUILDERS ─────────────────────────────────────────────────────────

def slide_01_title(prs):
    """Title — dark bg, green stripe, big PatchIQ, italic subtitle."""
    s = add_slide(prs)
    bg(s, DARK)
    # Left green stripe
    box(s, Inches(0), Inches(0), Inches(0.18), SH, fill=GREEN, line=None)
    # Title
    txt(s, "PatchIQ", Inches(0.5), Inches(1.6), Inches(12), Inches(1.8),
        size=80, bold=True, color=WHITE, align=PP_ALIGN.LEFT)
    # Short green underline
    box(s, Inches(0.5), Inches(3.35), Inches(2.2), Inches(0.1),
        fill=GREEN, line=None)
    # Subtitle
    txt(s, "AI-Powered Patch Review for KVM · Kernel · QEMU · libvirt",
        Inches(0.5), Inches(3.6), Inches(10), Inches(0.65),
        size=20, italic=True, color=BLUE, align=PP_ALIGN.LEFT)
    # Footer
    txt(s, "watsonx Challenge 2026  ·  IBM KVM & Linux Open Source Team",
        Inches(0.5), Inches(6.8), Inches(12), Inches(0.5),
        size=13, color=GREY, align=PP_ALIGN.LEFT)

def slide_02_team(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "Team")
    team = [
        ("Ken Cheruiyot",     "KVM & Linux Engineer",          "cheruiyo@us.ibm.com"),
        ("Team Member 2",     "KVM & Linux Engineer",          "member2@us.ibm.com"),
        ("Team Member 3",     "QEMU / libvirt Engineer",       "member3@us.ibm.com"),
        ("Team Member 4",     "Kernel Engineer",               "member4@us.ibm.com"),
        ("Team Member 5",     "Test & Automation",             "member5@us.ibm.com"),
        ("Team Member 6",     "AI / watsonx Integration",      "member6@us.ibm.com"),
    ]
    cols, rows = 3, 2
    cw, ch = Inches(3.9), Inches(1.55)
    gap_x, gap_y = Inches(0.28), Inches(0.28)
    ox, oy = Inches(0.5), Inches(1.45)
    for i, (name, role, email) in enumerate(team):
        col, row = i % cols, i // cols
        x = ox + col * (cw + gap_x)
        y = oy + row * (ch + gap_y)
        card(s, x, y, cw, ch)
        box(s, x, y, Inches(0.09), ch, fill=GREEN, line=None)
        txt(s, name,  x+Inches(0.18), y+Inches(0.2),  cw-Inches(0.25), Inches(0.42), size=15, bold=True,  color=WHITE)
        txt(s, role,  x+Inches(0.18), y+Inches(0.62), cw-Inches(0.25), Inches(0.38), size=12, color=BLUE)
        txt(s, email, x+Inches(0.18), y+Inches(1.0),  cw-Inches(0.25), Inches(0.38), size=11, color=GREY)

def slide_03_agenda(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "Agenda")
    items = [
        ("01", "Motivation — the patch review bottleneck"),
        ("02", "Problem vs Solution"),
        ("03", "How PatchIQ Works — four-stage pipeline"),
        ("04", "Test Suite — 68 tests, 5 Python versions"),
        ("05", "Live Patch Review Results"),
        ("06", "Comparison with Sashiko"),
        ("07", "Summary & Roadmap"),
    ]
    cw, ch = Inches(5.6), Inches(0.72)
    gap = Inches(0.15)
    for i, (num, label) in enumerate(items):
        col, row = i % 2, i // 2
        x = Inches(0.5) + col * Inches(6.45)
        y = Inches(1.45) + row * (ch + gap)
        if i == 6:  # last item centred
            x = Inches(3.87)
        card(s, x, y, cw, ch)
        txt(s, num,   x+Inches(0.15), y+Inches(0.16), Inches(0.55), Inches(0.45),
            size=20, bold=True, color=GREEN)
        txt(s, label, x+Inches(0.72), y+Inches(0.2),  cw-Inches(0.8), Inches(0.45),
            size=13, color=WHITE)

def slide_04_motivation(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "Motivation", "Patch review is the #1 bottleneck in Linux/KVM upstream contribution")

    # KPI strip
    kpis = [
        ("6–8 weeks",   "avg. kernel review cycle"),
        ("40%",         "patches need ≥2 revisions"),
        ("12+ rules",   "KVM style conventions"),
        ("3 layers",    "kernel · QEMU · libvirt"),
    ]
    kw = Inches(2.9); kh = Inches(1.15); ky = Inches(1.45)
    for i, (val, lbl) in enumerate(kpis):
        kx = Inches(0.5) + i*(kw + Inches(0.28))
        card(s, kx, ky, kw, kh, border=GREEN)
        txt(s, val, kx+Inches(0.15), ky+Inches(0.1),  kw-Inches(0.2), Inches(0.55),
            size=26, bold=True, color=GREEN, align=PP_ALIGN.CENTER)
        txt(s, lbl, kx+Inches(0.1),  ky+Inches(0.65), kw-Inches(0.15), Inches(0.38),
            size=12, color=GREY, align=PP_ALIGN.CENTER)

    # Pain-point panel
    pains = [
        "Manual style checks eat 30–60 min per patch",
        "Inconsistent rule application across reviewers",
        "No automated per-layer (kernel/QEMU/libvirt) enforcement",
        "Developers learn conventions only after rejection",
        "First-time contributors face steep learning curve",
    ]
    card(s, Inches(0.5), Inches(2.85), Inches(5.5), Inches(4.2))
    txt(s, "Pain Points", Inches(0.65), Inches(2.92), Inches(5.2), Inches(0.45),
        size=14, bold=True, color=ORANGE)
    for i, p in enumerate(pains):
        txt(s, f"▸  {p}", Inches(0.7), Inches(3.45)+i*Inches(0.58),
            Inches(5.1), Inches(0.52), size=12, color=WHITE)

    # Simple bar chart (SVG-style via rectangles)
    chart_x, chart_y = Inches(6.35), Inches(2.85)
    cw2, ch2 = Inches(6.5), Inches(4.2)
    card(s, chart_x, chart_y, cw2, ch2)
    txt(s, "Review Revision Rate by Layer", chart_x+Inches(0.15), chart_y+Inches(0.12),
        cw2-Inches(0.2), Inches(0.38), size=13, bold=True, color=WHITE)
    bars = [("Kernel/KVM", 0.62, RED), ("QEMU", 0.48, ORANGE), ("libvirt", 0.38, YELLOW)]
    bar_h = Inches(0.72)
    max_w = Inches(4.8)
    for i, (lbl, pct, col) in enumerate(bars):
        by = chart_y + Inches(0.7) + i*(bar_h + Inches(0.22))
        txt(s, lbl, chart_x+Inches(0.15), by, Inches(1.3), bar_h, size=12, color=GREY)
        box(s, chart_x+Inches(1.5), by+Inches(0.14), max_w*pct, Inches(0.44),
            fill=col, line=None)
        txt(s, f"{int(pct*100)}%",
            chart_x+Inches(1.55)+max_w*pct, by+Inches(0.14), Inches(0.6), Inches(0.44),
            size=12, bold=True, color=col)

def slide_05_problem_solution(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "Problem vs Solution")

    half = Inches(6.1)
    # Problem
    card(s, Inches(0.4), Inches(1.35), half, Inches(5.75), border=RED)
    txt(s, "Without PatchIQ", Inches(0.55), Inches(1.42), half-Inches(0.2), Inches(0.5),
        size=16, bold=True, color=RED)
    probs = [
        "Manual trawl through Linux kernel coding style docs",
        "Per-reviewer inconsistency on KVM locking rules",
        "printk / ioremap mistakes only caught at review",
        "No unified score — hard to prioritise",
        "Patches rejected → discouragement, slower upstream",
    ]
    for i, p in enumerate(probs):
        txt(s, f"✗  {p}", Inches(0.55), Inches(2.05)+i*Inches(0.7),
            half-Inches(0.25), Inches(0.62), size=12, color=WHITE)

    # Solution
    card(s, Inches(6.83), Inches(1.35), half, Inches(5.75), border=GREEN)
    txt(s, "With PatchIQ", Inches(6.98), Inches(1.42), half-Inches(0.2), Inches(0.5),
        size=16, bold=True, color=GREEN)
    sols = [
        "14 deterministic rules enforced automatically",
        "Per-layer rule sets: kernel / QEMU / libvirt",
        "K001–K004 / Q001–Q004 / L001–L003 / U001–U003",
        "0–100 quality score with per-finding deduction",
        "watsonx Granite AI narrative + actionable suggestions",
    ]
    for i, sol in enumerate(sols):
        txt(s, f"✓  {sol}", Inches(6.98), Inches(2.05)+i*Inches(0.7),
            half-Inches(0.25), Inches(0.62), size=12, color=WHITE)

    # Arrow
    txt(s, "→", Inches(6.25), Inches(4.0), Inches(0.6), Inches(0.6),
        size=36, bold=True, color=GREEN, align=PP_ALIGN.CENTER)

def slide_06_pipeline(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "How It Works — Four-Stage Pipeline")

    stages = [
        ("①  parse_diff()",    "Split unified diff into\nper-file hunks, extract\nSubject header",  GREEN,  "analyzer.py"),
        ("②  detect_layer()",  "Match file path regex:\nkernel · qemu · libvirt\n· unknown",         BLUE,   "analyzer.py"),
        ("③  run_rules()",     "14 deterministic style\nchecks per layer\n→ List[Finding]",          ORANGE, "rules.py"),
        ("④  ai_review()",     "watsonx Granite 13B\nJSON: summary +\nsuggestions[]",               PURPLE, "analyzer.py"),
    ]
    sw2 = Inches(2.7); sh2 = Inches(3.2); gap = Inches(0.42)
    oy = Inches(1.55)
    ox = Inches(0.55)
    for i, (title, body, col, src) in enumerate(stages):
        sx = ox + i*(sw2+gap)
        card(s, sx, oy, sw2, sh2, border=col)
        box(s, sx, oy, sw2, Inches(0.08), fill=col, line=None)
        txt(s, title, sx+Inches(0.12), oy+Inches(0.14), sw2-Inches(0.2), Inches(0.52),
            size=13, bold=True, color=col)
        txt(s, body,  sx+Inches(0.12), oy+Inches(0.72), sw2-Inches(0.2), Inches(2.1),
            size=12, color=WHITE)
        txt(s, src,   sx+Inches(0.12), oy+Inches(2.75), sw2-Inches(0.2), Inches(0.35),
            size=10, italic=True, color=GREY)
        # Arrow (except after last)
        if i < 3:
            ax = sx + sw2 + Inches(0.08)
            txt(s, "→", ax, oy+Inches(1.3), Inches(0.32), Inches(0.55),
                size=24, bold=True, color=GREY, align=PP_ALIGN.CENTER)

    # Score formula
    card(s, Inches(0.55), Inches(5.05), Inches(12.2), Inches(1.25), border=GREEN)
    txt(s, "⑤  Score  =  100  −  (errors×20)  −  (warnings×8)  −  (info×2)   ·   floor = 0   ·   clean patch = 100/100",
        Inches(0.75), Inches(5.2), Inches(11.8), Inches(0.55),
        size=14, bold=True, color=GREEN, align=PP_ALIGN.CENTER)
    txt(s, "analyzer.py  ·  rules.py",
        Inches(0.75), Inches(5.75), Inches(11.8), Inches(0.38),
        size=11, italic=True, color=GREY, align=PP_ALIGN.CENTER)

def slide_07_tests(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "Test Suite — 68 Tests, 5 Python Versions")

    # Big pass badge
    card(s, Inches(0.5), Inches(1.42), Inches(3.5), Inches(2.2), border=GREEN)
    txt(s, "68 / 68", Inches(0.6), Inches(1.6), Inches(3.3), Inches(1.1),
        size=52, bold=True, color=GREEN, align=PP_ALIGN.CENTER)
    txt(s, "All tests passing", Inches(0.6), Inches(2.7), Inches(3.3), Inches(0.45),
        size=14, color=WHITE, align=PP_ALIGN.CENTER)

    # Python matrix
    card(s, Inches(4.3), Inches(1.42), Inches(8.6), Inches(2.2), border=BLUE)
    txt(s, "CI matrix (GitHub Actions)", Inches(4.5), Inches(1.52),
        Inches(8.2), Inches(0.42), size=13, bold=True, color=BLUE)
    pyvers = ["3.8", "3.9", "3.10", "3.11", "3.12"]
    for i, v in enumerate(pyvers):
        px = Inches(4.5) + i * Inches(1.6)
        card(s, px, Inches(2.05), Inches(1.45), Inches(1.25), border=GREEN, fill=SURFACE)
        txt(s, f"Python\n{v}", px+Inches(0.1), Inches(2.12), Inches(1.28), Inches(0.7),
            size=13, bold=True, color=GREEN, align=PP_ALIGN.CENTER)
        txt(s, "✓ pass", px+Inches(0.1), Inches(2.82), Inches(1.28), Inches(0.32),
            size=11, color=WHITE, align=PP_ALIGN.CENTER)

    # Coverage + breakdown
    tests = [
        ("test_rules.py",    "36 tests", "Every K/Q/L/U rule — positive + negative case"),
        ("test_analyzer.py", "32 tests", "Diff parser, layer detect, scoring, end-to-end"),
        ("No credentials",   "required", "All tests run offline — no watsonx API key needed"),
    ]
    oy = Inches(3.85)
    for i, (f, cnt, desc) in enumerate(tests):
        ry = oy + i * Inches(1.05)
        card(s, Inches(0.5), ry, Inches(12.3), Inches(0.88))
        txt(s, f,    Inches(0.7), ry+Inches(0.15), Inches(2.2), Inches(0.58),
            size=13, bold=True, color=GREEN)
        txt(s, cnt,  Inches(3.0), ry+Inches(0.15), Inches(1.1), Inches(0.58),
            size=13, bold=True, color=YELLOW)
        txt(s, desc, Inches(4.2), ry+Inches(0.18), Inches(8.4), Inches(0.52),
            size=12, color=WHITE)

def slide_08_scores(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "Live Patch Review — Scores")

    patches = [
        ("kernel.patch",  56, 7, [("U001","warn"), ("U002","warn"), ("U003","info"),
                                   ("K001","warn"), ("K002","info"), ("K003","warn"), ("K004","warn")]),
        ("qemu.patch",    78, 5, [("U003","info"), ("Q001","warn"), ("Q002","info"),
                                   ("Q003","info"), ("Q004","warn")]),
        ("libvirt.patch", 82, 3, [("L001","warn"), ("L002","info"), ("L003","warn")]),
    ]
    sev_colors = {"warn": ORANGE, "info": BLUE, "error": RED}
    score_colors = {56: ORANGE, 78: YELLOW, 82: GREEN}

    for i, (name, score, nf, findings) in enumerate(patches):
        cy = Inches(1.42) + i * Inches(1.88)
        card(s, Inches(0.5), cy, Inches(12.3), Inches(1.72))

        # Score circle (rectangle stand-in)
        sc = score_colors[score]
        box(s, Inches(0.6), cy+Inches(0.22), Inches(1.35), Inches(1.28),
            fill=SURFACE, line=sc, line_w=Pt(2))
        txt(s, str(score), Inches(0.6), cy+Inches(0.3), Inches(1.35), Inches(0.7),
            size=34, bold=True, color=sc, align=PP_ALIGN.CENTER)
        txt(s, "/100", Inches(0.6), cy+Inches(1.02), Inches(1.35), Inches(0.38),
            size=12, color=GREY, align=PP_ALIGN.CENTER)

        txt(s, name, Inches(2.15), cy+Inches(0.2), Inches(4.0), Inches(0.48),
            size=16, bold=True, color=WHITE)
        txt(s, f"{nf} findings", Inches(2.15), cy+Inches(0.68), Inches(2.0), Inches(0.38),
            size=12, color=GREY)

        # Findings pills
        px = Inches(2.15)
        for rule_id, sev in findings:
            col = sev_colors.get(sev, WHITE)
            box(s, px, cy+Inches(1.15), Inches(0.92), Inches(0.38),
                fill=SURFACE, line=col, line_w=Pt(0.8))
            txt(s, rule_id, px, cy+Inches(1.18), Inches(0.92), Inches(0.32),
                size=10, bold=True, color=col, align=PP_ALIGN.CENTER)
            px += Inches(1.0)

def slide_09_kernel(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "Kernel Patch Deep-Dive — 56/100")

    findings = [
        ("K001", "warning", "pr_info / pr_err over printk()",
         'printk(KERN_INFO "kvm: vcpu %d created\\n", vcpu->vcpu_id);'),
        ("K002", "info",    "goto for cleanup after alloc",
         "return -ENOMEM;  (after kzalloc)"),
        ("K003", "warning", "ioremap → __iomem pointer",
         "void *mmio = ioremap(addr, PAGE_SIZE);"),
        ("K004", "warning", "vcpu state write without lock",
         "vcpu->arch.regs[0] = 0;"),
        ("U001", "warning", "Line exceeds 100 chars (110)",
         "int longvar_with_a_very_descriptive_name = some_function_call(…);"),
        ("U002", "warning", "Trailing whitespace",
         "(same line as U001)"),
        ("U003", "info",    "Unresolved TODO marker",
         "/* TODO: handle error path */"),
    ]
    sev_col = {"warning": ORANGE, "info": BLUE}
    for i, (rid, sev, msg, code) in enumerate(findings):
        ry = Inches(1.42) + i * Inches(0.83)
        card(s, Inches(0.5), ry, Inches(12.3), Inches(0.72))
        col = sev_col.get(sev, WHITE)
        box(s, Inches(0.5), ry, Inches(0.06), Inches(0.72), fill=col, line=None)
        txt(s, rid,  Inches(0.65), ry+Inches(0.15), Inches(0.72), Inches(0.42),
            size=12, bold=True, color=col)
        txt(s, msg,  Inches(1.5),  ry+Inches(0.15), Inches(4.5),  Inches(0.42),
            size=11, color=WHITE)
        txt(s, code, Inches(6.15), ry+Inches(0.15), Inches(6.5),  Inches(0.42),
            size=10, italic=True, color=GREY)

def slide_10_qemu(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "QEMU Patch Deep-Dive — 78/100")

    findings = [
        ("Q001", "warning", "error_propagate() not error_free()",
         "error_free(&err);"),
        ("Q002", "info",    "g_new0(Type,n) not g_malloc0(sizeof)",
         "s = g_malloc0(sizeof(VirtIOBlk));"),
        ("Q003", "info",    "g_assert_not_reached() not assert(0)",
         "assert(0);"),
        ("Q004", "warning", "More object_unref (3) than object_ref (0)",
         "object_unref×3 — double-free risk"),
        ("U003", "info",    "Unresolved FIXME marker",
         "/* FIXME: double-free risk here */"),
    ]
    sev_col = {"warning": ORANGE, "info": BLUE}
    for i, (rid, sev, msg, code) in enumerate(findings):
        ry = Inches(1.42) + i * Inches(1.0)
        card(s, Inches(0.5), ry, Inches(12.3), Inches(0.85))
        col = sev_col.get(sev, WHITE)
        box(s, Inches(0.5), ry, Inches(0.06), Inches(0.85), fill=col, line=None)
        txt(s, rid,  Inches(0.65), ry+Inches(0.2),  Inches(0.72), Inches(0.42),
            size=12, bold=True, color=col)
        txt(s, msg,  Inches(1.5),  ry+Inches(0.2),  Inches(5.2),  Inches(0.42),
            size=11, color=WHITE)
        txt(s, code, Inches(6.85), ry+Inches(0.2),  Inches(5.9),  Inches(0.42),
            size=10, italic=True, color=GREY)

def slide_11_libvirt(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "libvirt Patch Deep-Dive — 82/100")

    findings = [
        ("L001", "warning", "virReportError() not fprintf(stderr, ...)",
         'fprintf(stderr, "error: network init failed for %s\\n", def->name);'),
        ("L002", "info",    "VIR_ALLOC without cleanup: label",
         "VIR_ALLOC(priv)  — no cleanup: label found"),
        ("L003", "warning", "virStrdup() not strdup()",
         "priv->name = strdup(def->name);"),
    ]
    sev_col = {"warning": ORANGE, "info": BLUE}
    for i, (rid, sev, msg, code) in enumerate(findings):
        ry = Inches(1.55) + i * Inches(1.5)
        card(s, Inches(0.5), ry, Inches(12.3), Inches(1.3))
        col = sev_col.get(sev, WHITE)
        box(s, Inches(0.5), ry, Inches(0.08), Inches(1.3), fill=col, line=None)
        txt(s, rid,  Inches(0.7),  ry+Inches(0.15), Inches(0.8), Inches(0.48),
            size=14, bold=True, color=col)
        txt(s, msg,  Inches(1.65), ry+Inches(0.15), Inches(10.9), Inches(0.48),
            size=13, color=WHITE)
        txt(s, code, Inches(1.65), ry+Inches(0.72), Inches(10.9), Inches(0.42),
            size=11, italic=True, color=GREY)

def slide_12_sashiko(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "PatchIQ vs Sashiko")

    half = Inches(5.85)
    # PatchIQ col
    card(s, Inches(0.5), Inches(1.35), half, Inches(5.8), border=GREEN)
    box(s, Inches(0.5), Inches(1.35), half, Inches(0.06), fill=GREEN, line=None)
    txt(s, "PatchIQ", Inches(0.65), Inches(1.45), half-Inches(0.2), Inches(0.52),
        size=18, bold=True, color=GREEN)
    piq = [
        "Developer-side  ·  pre-push",
        "14 deterministic style rules",
        "Kernel + QEMU + libvirt layers",
        "watsonx Granite AI narrative",
        "0–100 quality score",
        "Python · MIT license",
        "Runs offline (no credentials req.)",
        "68-test CI suite — 5 Python versions",
    ]
    for i, l in enumerate(piq):
        txt(s, f"✓  {l}", Inches(0.65), Inches(2.08)+i*Inches(0.58),
            half-Inches(0.2), Inches(0.52), size=12, color=WHITE)

    # Sashiko col
    card(s, Inches(6.95), Inches(1.35), half, Inches(5.8), border=PURPLE)
    box(s, Inches(6.95), Inches(1.35), half, Inches(0.06), fill=PURPLE, line=None)
    txt(s, "Sashiko  (github.com/sashiko-dev)", Inches(7.1), Inches(1.45),
        half-Inches(0.2), Inches(0.52), size=18, bold=True, color=PURPLE)
    sas = [
        "Maintainer-side  ·  post-merge",
        "11-stage agentic bug hunter",
        "53.6% bug recall on kernel patches",
        "LLM-heavy — no deterministic rules",
        "Rust · Linux Foundation · 897★",
        "Requires cloud LLM access",
        "Complementary — different use case",
        "No QEMU / libvirt layer support",
    ]
    for i, l in enumerate(sas):
        txt(s, f"•  {l}", Inches(7.1), Inches(2.08)+i*Inches(0.58),
            half-Inches(0.2), Inches(0.52), size=12, color=WHITE)

    txt(s, "PatchIQ (dev side) + Sashiko (maintainer side) = complete coverage",
        Inches(0.5), Inches(7.05), Inches(12.3), Inches(0.38),
        size=13, bold=True, color=YELLOW, align=PP_ALIGN.CENTER)

def slide_13_rules(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "Rule Coverage Matrix")

    rules = [
        ("K001","kernel",    "warning","Prefer pr_info/pr_err over printk()"),
        ("K002","kernel",    "info",   "goto for cleanup after allocation"),
        ("K003","kernel",    "warning","ioremap → __iomem pointer"),
        ("K004","kernel/kvm","warning","vcpu state write without lock"),
        ("Q001","qemu",      "warning","error_propagate() not error_free()"),
        ("Q002","qemu",      "info",   "g_new0() not g_malloc0(sizeof)"),
        ("Q003","qemu",      "info",   "g_assert_not_reached() not assert(0)"),
        ("Q004","qemu",      "warning","object_unref>object_ref — double-free"),
        ("L001","libvirt",   "warning","virReportError() not fprintf(stderr)"),
        ("L002","libvirt",   "info",   "VIR_ALLOC without cleanup: label"),
        ("L003","libvirt",   "warning","virStrdup() not strdup()"),
        ("U001","all",       "warning","Line length (100 kernel/libvirt, 80 QEMU)"),
        ("U002","all",       "warning","Trailing whitespace"),
        ("U003","all",       "info",   "TODO/FIXME/HACK/XXX marker"),
    ]
    sev_col = {"warning": ORANGE, "info": BLUE, "error": RED}
    layer_col = {"kernel": GREEN, "kernel/kvm": GREEN, "qemu": BLUE,
                 "libvirt": PURPLE, "all": YELLOW}

    col_w = [Inches(0.85), Inches(1.45), Inches(1.2), Inches(8.5)]
    headers = ["ID", "Layer", "Severity", "Description"]
    hx = Inches(0.45)
    hy = Inches(1.38)
    rh = Inches(0.365)

    # Header row
    box(s, Inches(0.45), hy, sum(col_w)+Inches(0.1), rh, fill=MIDGREY, line=None)
    for j, (hdr, cw) in enumerate(zip(headers, col_w)):
        off = sum(col_w[:j])
        txt(s, hdr, hx+off+Inches(0.07), hy+Inches(0.06), cw-Inches(0.05), rh-Inches(0.06),
            size=11, bold=True, color=WHITE)

    for i, (rid, layer, sev, desc) in enumerate(rules):
        ry = hy + (i+1)*rh
        fill = SURFACE if i%2==0 else DARK
        box(s, Inches(0.45), ry, sum(col_w)+Inches(0.1), rh, fill=fill, line=None)
        vals = [rid, layer, sev, desc]
        vcols = [layer_col.get(layer, WHITE), layer_col.get(layer, WHITE),
                 sev_col.get(sev, WHITE), WHITE]
        for j, (val, vcol, cw) in enumerate(zip(vals, vcols, col_w)):
            off = sum(col_w[:j])
            txt(s, val, hx+off+Inches(0.07), ry+Inches(0.05), cw-Inches(0.05), rh-Inches(0.06),
                size=10, color=vcol)

def slide_14_summary(prs):
    s = add_slide(prs)
    bg(s, DARK)
    heading(s, "Summary & Roadmap")

    # Summary left
    card(s, Inches(0.5), Inches(1.35), Inches(5.8), Inches(5.8), border=GREEN)
    txt(s, "What We Built", Inches(0.65), Inches(1.42), Inches(5.5), Inches(0.52),
        size=16, bold=True, color=GREEN)
    summary = [
        "14 style rules across 3 layers + universal",
        "Four-stage pipeline: parse→detect→rules→AI",
        "watsonx Granite 13B AI narrative + suggestions",
        "0–100 patch quality score",
        "68-test suite · CI matrix Python 3.8–3.12",
        "pyproject.toml · pre-commit · GitHub Actions CI",
        "MIT license · CONTRIBUTING guide · CHANGELOG",
        "Scores: kernel 56  ·  QEMU 78  ·  libvirt 82",
    ]
    for i, l in enumerate(summary):
        txt(s, f"✓  {l}", Inches(0.65), Inches(2.05)+i*Inches(0.58),
            Inches(5.5), Inches(0.52), size=12, color=WHITE)

    # Roadmap right
    card(s, Inches(6.8), Inches(1.35), Inches(6.1), Inches(5.8), border=BLUE)
    txt(s, "Roadmap", Inches(6.95), Inches(1.42), Inches(5.8), Inches(0.52),
        size=16, bold=True, color=BLUE)
    roadmap = [
        ("v0.2", "Git hook integration (pre-push)"),
        ("v0.2", "IDE plugin (VS Code + vim)"),
        ("v0.3", "E-mail / Patchwork webhook"),
        ("v0.3", "Cover-letter quality check"),
        ("v0.4", "s390x-specific KVM rules"),
        ("v0.4", "Signed-off-by / Co-developed-by lint"),
        ("v1.0", "Gerrit / GitLab CI app"),
        ("v1.0", "Public release on PyPI"),
    ]
    for i, (ver, item) in enumerate(roadmap):
        ry = Inches(2.05) + i * Inches(0.58)
        txt(s, ver,  Inches(6.95), ry, Inches(0.7),  Inches(0.52),
            size=11, bold=True, color=BLUE)
        txt(s, item, Inches(7.75), ry, Inches(5.0),  Inches(0.52),
            size=12, color=WHITE)

    txt(s, "github.ibm.com/cheruiyo/Watsonx_challenge_2026  ·  pip install patchiq  (coming v1.0)",
        Inches(0.5), Inches(7.1), Inches(12.3), Inches(0.34),
        size=12, color=GREY, align=PP_ALIGN.CENTER)

# ── MAIN ───────────────────────────────────────────────────────────────────
def main():
    prs = Presentation()
    prs.slide_width  = SW
    prs.slide_height = SH

    slide_01_title(prs)
    slide_02_team(prs)
    slide_03_agenda(prs)
    slide_04_motivation(prs)
    slide_05_problem_solution(prs)
    slide_06_pipeline(prs)
    slide_07_tests(prs)
    slide_08_scores(prs)
    slide_09_kernel(prs)
    slide_10_qemu(prs)
    slide_11_libvirt(prs)
    slide_12_sashiko(prs)
    slide_13_rules(prs)
    slide_14_summary(prs)

    prs.save(OUT)
    print(f"Saved: {OUT}  ({len(prs.slides)} slides)")

if __name__ == "__main__":
    main()
