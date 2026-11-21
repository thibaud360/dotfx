#!/usr/bin/env python3
"""dotfx: turn any image into LED dots, halftone, dither or pixel art.
Usage: python dotfx.py IMAGE [--preset NAME|all] [-o OUTDIR] [overrides]"""
import argparse, os
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

PRESETS = {
    "led":         dict(cell=14, shape="circle", dot=0.80, bg="black", blur=0,  sat=1.2,  bright=0.92, contrast=1.25, glow=0.12),
    "soft-led":    dict(cell=18, shape="circle", dot=0.80, bg="black", blur=18, sat=1.3,  bright=0.90, contrast=1.25, glow=0.20),
    "dither":      dict(cell=6,  shape="circle", dot=0.90, bg="black", levels=3, bayer=4, sat=1.3, contrast=1.25),
    "fine-dither": dict(cell=3,  shape="square", dot=1.00, levels=3, bayer=8, sat=1.3, bright=1.15, contrast=1.1),
    "duotone":     dict(cell=3,  shape="square", dot=1.00, levels=2, bayer=8, duo=("#2B45D6", "#FFFFFF"), stretch=True, contrast=1.1),
    "pixel":       dict(cell=9,  shape="square", dot=0.78, bg="soft", levels=6, bayer=4, sat=0.75, bright=1.05, contrast=1.1),
}
DEFAULTS = dict(cell=12, shape="circle", dot=0.8, bg="black", blur=0, sat=1.0, bright=1.0, contrast=1.0,
                glow=0.0, levels=0, bayer=8, duo=None, stretch=False, width=1512)

def bayer(n):
    m = np.array([[0]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return m.astype(np.float32) / (n * n) - 0.5 + 0.5 / (n * n)

def cell_mask(cell, frac, shape, ss=4):
    n = cell * ss
    y, x = np.mgrid[0:n, 0:n] + 0.5
    c, r = n / 2, frac * n / 2
    if shape == "circle":
        m = (x - c) ** 2 + (y - c) ** 2 <= r * r
    elif shape == "line":
        m = abs(y - c) <= r * 0.5
    else:
        m = (abs(x - c) <= r) & (abs(y - c) <= r)
    return m.astype(np.float32).reshape(cell, ss, cell, ss).mean(axis=(1, 3))

def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255

def apply(img, **o):
    p = {**DEFAULTS, **{k: v for k, v in o.items() if v is not None}}
    img = img.convert("RGB")
    if p["width"] and img.width > p["width"]:
        img = img.resize((p["width"], round(img.height * p["width"] / img.width)), Image.LANCZOS)
    if p["blur"]:
        img = img.filter(ImageFilter.GaussianBlur(p["blur"]))
    img = ImageEnhance.Color(img).enhance(p["sat"])
    img = ImageEnhance.Brightness(img).enhance(p["bright"])
    img = ImageEnhance.Contrast(img).enhance(p["contrast"])
    cell = max(1, int(p["cell"]))
    gw, gh = img.width // cell, img.height // cell
    g = np.asarray(img.resize((gw, gh), Image.BOX), np.float32) / 255
    t = np.tile(bayer(p["bayer"]), (gh // p["bayer"] + 1, gw // p["bayer"] + 1))[:gh, :gw, None]
    L = p["levels"] - 1
    if p["duo"]:
        lum = (g @ np.array([.299, .587, .114], np.float32))[..., None]
        if p["stretch"]:
            lo, hi = np.percentile(lum, [3, 97])
            lum = np.clip((lum - lo) / (hi - lo + 1e-6), 0, 1) ** 1.6
        if L > 0:
            lum = np.clip(np.round(lum * L + t), 0, L) / L
        d, l = (hex_rgb(c) for c in p["duo"])
        g = d + (l - d) * lum
    elif L > 0:
        g = np.clip(np.round(g * L + t), 0, L) / L
    col = np.repeat(np.repeat(g, cell, 0), cell, 1)
    m = np.tile(cell_mask(cell, p["dot"], p["shape"]), (gh, gw))[..., None]
    if p["bg"] == "soft":
        b = np.asarray(img.filter(ImageFilter.GaussianBlur(cell * 1.5)).crop((0, 0, gw * cell, gh * cell)), np.float32) / 255
        b = np.clip(b * 1.12 + 0.06, 0, 1)
    elif p["bg"] == "white":
        b = np.ones_like(col)
    elif p["bg"].startswith("#"):
        b = np.ones_like(col) * hex_rgb(p["bg"])
    else:
        b = np.zeros_like(col)
    out = Image.fromarray((np.clip(b * (1 - m) + col * m, 0, 1) * 255).astype(np.uint8))
    if p["glow"]:
        gl = np.asarray(out.filter(ImageFilter.GaussianBlur(cell * 0.8)), np.float32)
        out = Image.fromarray(np.clip(np.asarray(out, np.float32) + gl * p["glow"], 0, 255).astype(np.uint8))
    return out

def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("image")
    a.add_argument("--preset", default="all", help="all, " + ", ".join(PRESETS))
    a.add_argument("-o", "--out", default="dotfx_out")
    for k in ("cell", "levels", "bayer", "width"):
        a.add_argument("--" + k, type=int)
    for k in ("dot", "blur", "sat", "bright", "contrast", "glow"):
        a.add_argument("--" + k, type=float)
    a.add_argument("--shape", choices=["circle", "square", "line"])
    a.add_argument("--bg", help="black, white, soft or #hex")
    a.add_argument("--duo", nargs=2, metavar=("DARK", "LIGHT"), help="two hex colors")
    args = vars(a.parse_args())
    src, name = Image.open(args.pop("image")), None
    os.makedirs(args["out"], exist_ok=True)
    names = list(PRESETS) if args["preset"] == "all" else [args["preset"]]
    out, base = args.pop("out"), os.path.splitext(os.path.basename(src.filename))[0]
    args.pop("preset")
    for n in names:
        res = apply(src, **{**PRESETS[n], **{k: v for k, v in args.items() if v is not None}})
        path = os.path.join(out, f"{base}_{n}.jpg")
        res.save(path, quality=92)
        print(path)

if __name__ == "__main__":
    main()
