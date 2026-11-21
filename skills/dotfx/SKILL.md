---
name: dotfx
description: Turn a photo or a video into LED dot-matrix, halftone, dither, duotone or pixel art. Use when the user asks for an LED, dot, halftone, dithered, pixel or "screen" look on an image, or types /dotfx.
---

# dotfx

Applies a dot-matrix style effect to an image with `scripts/dotfx.py` (Python 3, Pillow, NumPy).

## Presets

| Preset | Look |
|---|---|
| `led` | Round dots on black, like an LED screen |
| `soft-led` | Blurred first, soft glowing gradient through LED dots |
| `dither` | Small round dots, ordered dithering, grainy |
| `fine-dither` | Tiny square pixels, bright, full colour |
| `duotone` | Two colours only (blue and white by default), print-like |
| `pixel` | Square pixels with lit gaps instead of black |

## Steps

1. Find the user's image. Copy it to the working directory if the original is read-only.
2. Make sure the dependencies exist: `pip install pillow numpy` (add `--break-system-packages` if pip asks).
3. If the user did not name a style, run every preset so they can choose:
   `python scripts/dotfx.py INPUT --preset all -o dotfx_out`
   Otherwise run the one they asked for with `--preset NAME`.
4. Look at the results before sending. If an image is washed out or too dark, rerun with `--bright` or `--contrast`. Very bright photos often need `--bright 0.9` for `led` and `soft-led`.
5. Send the images back. Offer a tweak in one line: bigger or smaller dots, another shape, another background or other duotone colours.

## Overrides

Any preset value can be overridden:

- `--cell N` grid size in px (3 = fine, 14 = LED, 20+ = chunky)
- `--shape circle|square|line`
- `--dot 0.2–1.0` dot size inside its cell
- `--bg black|white|soft|#hex` (soft = blurred image shows through the gaps)
- `--blur PX` blur before the dots (gives the soft LED gradients)
- `--levels N` and `--bayer 2|4|8` for dithering (levels 0 = off)
- `--bright`, `--contrast`, `--sat` (1.0 = unchanged)
- `--glow 0–1` light bloom around the dots
- `--duo DARK LIGHT` two hex colours, e.g. `--duo "#1B1B1B" "#F4E3C1"`
- `--width PX` working width (default 1512)

Example: `python scripts/dotfx.py photo.jpg --preset duotone --duo "#C2185B" "#FFF3E0" --cell 4`

## Videos

The same script takes a video (mp4, mov, webm, gif): `python scripts/dotfx.py clip.mp4 --preset led -o dotfx_out`. It applies the effect to every frame, keeps the sound and writes `clip_led.mp4` (H.264, max 1080 px wide; `--width` to change). Videos default to one preset (`led`); `--preset all` renders all six and takes longer. Needs `ffmpeg`.
- Look at one frame first: render a still from the video with the image mode, tune the settings, then run the whole clip with the same flags.
- Dark night footage usually needs `--bright 1.2` to `1.4` with `led`.
- Ordered dithering is stable from frame to frame, so `dither` and `fine-dither` don't flicker.

## If the script is missing

Get it from the public repo: `git clone --depth 1 https://github.com/thibaud360/dotfx /tmp/dotfx` and use `/tmp/dotfx/skills/dotfx/scripts/dotfx.py`.
