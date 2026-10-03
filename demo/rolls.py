"""Demo-Rollen: gezeichnete Kamerascans fuer die Screenshots (intern, nie Teil eines Releases).

``demo/start.sh`` legt damit zwei Filmrollen der gemeinsamen shrippen-Demowelt (Studio Weber,
siehe demo/world.json) als JPEGs an: heller Leuchttisch, schwarzer Filmstreifen mit
Perforation, darin ein gezeichnetes Motiv (Elbstrand Oevelgoenne, Fahrradwerkstatt). Jedes
Bild liegt etwas anders (Versatz, Drehung); ein paar sind absichtlich unterbelichtet,
damit die Erkennung alle drei Stufen zeigt. Danach laeuft der normale Weg ``kader open``.
Keine echten Fotos, deterministisch (fester Zufallssamen).
"""
import json
import math
import os
import random

import numpy as np

from PIL import Image, ImageDraw, ImageFilter

WORLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world.json")
W, H = 1333, 2000          # wie ein Hochformat-Kamerascan eines Kleinbildnegativs


def _sky_sea(d, box, rnd, dusk):
    x0, y0, x1, y1 = box
    horizon = y0 + int((y1 - y0) * rnd.uniform(0.48, 0.58))
    for y in range(y0, horizon):
        t = (y - y0) / max(1, horizon - y0)
        v = int(200 + 40 * t) if not dusk else int(150 + 90 * t)
        d.line([(x0, y), (x1, y)], fill=(v, v, v - 6))
    for y in range(horizon, y1):
        t = (y - horizon) / max(1, y1 - horizon)
        d.line([(x0, y), (x1, y)], fill=(int(110 + 60 * t),) * 3)
    for i in range(24):                       # Wellen
        yy = horizon + int((y1 - horizon) * (i / 24) ** 1.6)
        xs = rnd.randint(x0, x1 - 200)
        d.line([(xs, yy), (xs + rnd.randint(60, 260), yy)], fill=(215, 215, 210), width=2)
    return horizon


def _oevelgoenne(img, box, rnd, variant):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    horizon = _sky_sea(d, box, rnd, dusk=variant % 3 == 2)
    # Containerbruecken am anderen Ufer
    for i in range(4):
        cx = x0 + int((x1 - x0) * (0.15 + 0.22 * i + rnd.uniform(-0.03, 0.03)))
        top = horizon - rnd.randint(120, 200)
        d.rectangle([cx, top, cx + 14, horizon], fill=(70, 70, 72))
        d.rectangle([cx - 60, top, cx + 120, top + 16], fill=(70, 70, 72))
    # Strand im Vordergrund
    sand_top = y1 - int((y1 - y0) * rnd.uniform(0.18, 0.26))
    d.polygon([(x0, sand_top + 40), (x1, sand_top), (x1, y1), (x0, y1)], fill=(185, 180, 168))
    # Schiff
    sx = x0 + int((x1 - x0) * rnd.uniform(0.2, 0.55))
    sy = horizon - 8
    d.polygon([(sx, sy), (sx + 380, sy), (sx + 350, sy + 40), (sx + 20, sy + 40)], fill=(40, 40, 44))
    d.rectangle([sx + 220, sy - 70, sx + 320, sy], fill=(55, 55, 58))
    for k in range(5):
        d.rectangle([sx + 30 + k * 36, sy - 34, sx + 60 + k * 36, sy], fill=(90 + 20 * k, 80, 70))
    # Person am Strand
    px = x0 + int((x1 - x0) * rnd.uniform(0.55, 0.8))
    py = sand_top + 60
    d.ellipse([px - 22, py - 150, px + 22, py - 106], fill=(35, 35, 35))
    d.rectangle([px - 30, py - 105, px + 30, py], fill=(45, 45, 48))
    d.line([(px - 14, py), (px - 20, py + 110)], fill=(40, 40, 40), width=16)
    d.line([(px + 14, py), (px + 22, py + 110)], fill=(40, 40, 40), width=16)


def _werkstatt(img, box, rnd, variant):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    for y in range(y0, y1):                   # Werkstattwand mit Licht von links
        t = (y - y0) / max(1, y1 - y0)
        d.line([(x0, y), (x1, y)], fill=(int(150 - 40 * t),) * 3)
    for i in range(0, x1 - x0, 90):           # Holzlatten
        d.line([(x0 + i, y0), (x0 + i, y1)], fill=(120, 120, 118), width=3)
    floor = y0 + int((y1 - y0) * 0.72)
    d.rectangle([x0, floor, x1, y1], fill=(95, 92, 88))
    # Werkbank
    d.rectangle([x0 + 40, floor - 180, x1 - 40, floor - 150], fill=(60, 55, 50))
    d.rectangle([x0 + 70, floor - 150, x0 + 100, floor], fill=(60, 55, 50))
    d.rectangle([x1 - 100, floor - 150, x1 - 70, floor], fill=(60, 55, 50))
    # Fahrrad(er)
    for n in range(1 + variant % 2):
        cx = x0 + int((x1 - x0) * (0.3 + 0.35 * n)) + rnd.randint(-40, 40)
        cy = floor + 40 - n * 380
        r = 150 - n * 30
        for wx in (cx - r - 40, cx + r + 40):
            d.ellipse([wx - r, cy - r, wx + r, cy + r], outline=(30, 30, 30), width=12)
            for a in range(0, 360, 20):
                d.line([(wx, cy), (wx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))],
                       fill=(80, 80, 80), width=2)
        d.line([(cx - r - 40, cy), (cx, cy - r), (cx + r + 40, cy)], fill=(200, 200, 205), width=14)
        d.line([(cx, cy - r), (cx - 60, cy - r - 120)], fill=(200, 200, 205), width=12)
    # Werkzeugwand
    for k in range(7):
        tx = x0 + 80 + k * ((x1 - x0 - 160) // 7)
        d.rectangle([tx, y0 + 140, tx + 18, y0 + 140 + rnd.randint(120, 260)], fill=(45, 45, 48))


def _scan(motif, rnd, variant, difficult):
    """Ein Kamerascan: Leuchttisch, Filmstreifen, Bildfeld mit Motiv."""
    bg = 245 if not difficult else 205
    img = Image.new("RGB", (W, H), (bg, bg, bg - 2))
    d = ImageDraw.Draw(img)
    # Filmstreifen (Hochformat, 24x36 mm): Bildfeld fast so breit wie der Scan, die Perforation
    # (Takt 4,75 mm) liegt am Rand; Masse wie bei einem echten Kamerascan, damit der
    # Perforations-Massstab der Erkennung stimmt.
    fx0, fx1 = rnd.randint(-8, 6), W - rnd.randint(-6, 8)
    fy0, fy1 = int(H * 0.008), int(H * 0.992)
    d.rectangle([fx0, fy0, fx1, fy1], fill=(18, 18, 20))
    frame_h = 1822
    pitch = frame_h * 4.75 / 36
    for side in (fx0 + 14, fx1 - 50):
        y = fy0 + rnd.uniform(0, pitch)
        while y < fy1 - 50:
            d.rounded_rectangle([side, int(y), side + 36, int(y) + 44], radius=5, fill=(bg, bg, bg))
            y += pitch
    ix0 = (W - 1200) // 2 + rnd.randint(-10, 10)
    iy0 = (H - frame_h) // 2 + rnd.randint(-14, 14)
    ix1, iy1 = ix0 + 1200, iy0 + frame_h
    frame = Image.new("RGB", (ix1 - ix0, iy1 - iy0), (128, 128, 128))
    motif(frame, (0, 0, ix1 - ix0, iy1 - iy0), rnd, variant)
    frame = frame.filter(ImageFilter.GaussianBlur(1.2))
    if difficult:                              # unterbelichtet: kaum Kontrast zum Rand
        frame = Image.blend(frame, Image.new("RGB", frame.size, (22, 22, 24)), difficult)
    img.paste(frame, (ix0, iy0))
    # Korn und leichte Drehung wie beim Abfotografieren
    grain = np.random.default_rng(rnd.randint(0, 2**32 - 1)).normal(0, 6, (H, W, 1))
    img = Image.fromarray(np.clip(np.asarray(img, dtype=np.float32) + grain, 0, 255).astype(np.uint8))
    angle = rnd.uniform(-1.2, 1.2) if not difficult else rnd.uniform(2.5, 3.5)
    img = img.rotate(angle, resample=Image.BICUBIC, fillcolor=(bg, bg, bg - 2))
    return img


ROLLS = [(_oevelgoenne, 0), (_werkstatt, 1)]


def generate(folder, seed=3):
    """Legt die Demo-Rollen unter ``folder`` an (vorhandene Bilder bleiben). Rueckgabe: Anzahl Bilder."""
    with open(WORLD, encoding="utf-8") as f:
        rolls = json.load(f)["media"]["film_rolls"]
    count = 0
    for (motif, idx), roll in zip(ROLLS, rolls):
        d = os.path.join(folder, roll["name"])
        os.makedirs(d, exist_ok=True)
        for i in range(roll["frames"]):
            path = os.path.join(d, f"{idx + 3:02d}_{i + 1:02d}.jpg")
            count += 1
            if os.path.exists(path):
                continue
            rnd = random.Random(seed * 1000 + idx * 100 + i)
            # unterbelichtete Bilder (Anteil Schwarz, Bildnummer ab 1 aus der Welt): landen in Gruen, Gelb und Rot
            difficult = roll.get("underexposed", {}).get(str(i + 1), 0)
            _scan(motif, rnd, i, difficult).save(path, quality=90)
    return count


def before_after(out, seed=3):
    """Landing-page picture: a demo scan (left) and the frame Kader cut from it (right).

    Runs the real detection on one demo roll and uses its crop. ``out`` is the image file."""
    import tempfile

    import kader as acn

    with tempfile.TemporaryDirectory() as tmp:
        generate(tmp, seed)
        roll = sorted(d for d in os.listdir(tmp) if os.path.isdir(os.path.join(tmp, d)))[0]
        paths = sorted(os.path.join(tmp, roll, f) for f in os.listdir(os.path.join(tmp, roll)))
        batch = acn.compute_batch(paths, 0.3, False, "35mm", report=lambda msg: None)
        result = next(r for r in batch["results"] if os.path.basename(r["input_file"]) == os.path.basename(paths[0]))
        scan = Image.open(paths[0]).convert("RGB")
    x, y, w, h = (int(result[k]) for k in ("x", "y", "width", "height"))
    frame = scan.crop((x, y, x + w, y + h))
    # Kante colours: dark ground, the crop marked in yellow on the scan.
    height = 900
    left = scan.resize((round(scan.width * height / scan.height), height))
    s = height / scan.height
    d = ImageDraw.Draw(left)
    d.rectangle([x * s, y * s, (x + w) * s, (y + h) * s], outline=(250, 189, 47), width=5)
    right = frame.resize((round(frame.width * height / frame.height), height))
    gap, pad, arrow = 150, 40, (250, 189, 47)
    canvas = Image.new("RGB", (left.width + gap + right.width + 2 * pad, height + 2 * pad), (29, 32, 33))
    canvas.paste(left, (pad, pad))
    canvas.paste(right, (pad + left.width + gap, pad))
    d = ImageDraw.Draw(canvas)
    ax, ay = pad + left.width + 30, pad + height // 2
    d.line([(ax, ay), (ax + gap - 60, ay)], fill=arrow, width=8)
    d.polygon([(ax + gap - 60, ay - 22), (ax + gap - 30, ay), (ax + gap - 60, ay + 22)], fill=arrow)
    canvas.save(out, quality=88)
    return result.get("confidence")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # kader.py
    if len(sys.argv) == 3 and sys.argv[1] == "rolls":
        print(generate(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == "before-after":
        print("confidence", before_after(sys.argv[2]))
    else:
        sys.exit("usage: demo/rolls.py rolls FOLDER | before-after OUT.webp")
