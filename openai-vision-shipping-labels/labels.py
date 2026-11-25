"""Six fictional shipping labels, drawn with Pillow, plus the ground truth for each.

The labels are rendered fresh on every run (deterministic: same pixels each
time), so the expected values below always match the images. Four are clean
enough for any vision model; two are built to be hard: a faded thermal print
with confusable characters, and a weight that was struck out and rewritten.
"""

import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pydantic import BaseModel, ConfigDict

LABELS_DIR = Path(__file__).parent / "labels"
W, H = 600, 900


class LabelFields(BaseModel):
    """The typed record we want back from every label."""

    model_config = ConfigDict(extra="forbid")  # strict JSON schema needs additionalProperties=false

    tracking_number: str
    carrier: str
    recipient_name: str
    postal_code: str
    weight_kg: float
    service_level: Literal["Economy", "Standard", "Express"]
    fragile: bool


@dataclass(frozen=True)
class LabelSpec:
    file: str
    kind: str
    expected: LabelFields
    street: str
    city: str
    # How the label is drawn
    scale: float = 1.0  # < 1 shrinks the type, packing the label
    ink: int = 15  # text grey level, 0 = black; high values = faded print
    paper: int = 252
    blur: float = 0.0
    noise: int = 0
    rotate: int = 0  # degrees counter-clockwise applied to the finished label
    weight_text: str | None = None  # how the weight is printed, when not "<x> KG"
    struck_weight: str | None = None  # a printed weight that was crossed out
    extra_lines: list[str] = field(default_factory=list)  # distractor numbers


SPECS = [
    LabelSpec(
        file="label_01_clean.png",
        kind="clean carrier label, big type",
        expected=LabelFields(
            tracking_number="NWP 4821 7730 19", carrier="Northwind Parcel",
            recipient_name="Maren Olsvik", postal_code="20457", weight_kg=4.20,
            service_level="Standard", fragile=False),
        street="Kaiserkai 12", city="Hamburg",
    ),
    LabelSpec(
        file="label_02_dense.png",
        kind="dense label with pounds, order numbers and a fragile stamp",
        expected=LabelFields(
            tracking_number="QP-7731-0482-ZK", carrier="Quokka Post",
            recipient_name="Tobias Brenner-Albrecht", postal_code="01067", weight_kg=12.75,
            service_level="Express", fragile=True),
        street="Wallstrasse 48b", city="Dresden", scale=0.78,
        weight_text="12.75 KG / 28.1 LB",
        extra_lines=["ORDER 55-20931-77", "REF PO-884120", "CUSTOMS CN22 / 0394", "PKG 2 OF 3"],
    ),
    LabelSpec(
        file="label_03_rotated.png",
        kind="label photographed sideways (rotated 90 degrees)",
        expected=LabelFields(
            tracking_number="TWC-90314-5527", carrier="Tidewater Couriers",
            recipient_name="Ines Carvalho", postal_code="4050-123", weight_kg=0.85,
            service_level="Economy", fragile=False),
        street="Rua das Flores 207", city="Porto", rotate=90,
    ),
    LabelSpec(
        file="label_04_faded.png",
        kind="faded, noisy thermal print with confusable characters",
        expected=LabelFields(
            tracking_number="QP-O8B1-I1O0-S5Z2", carrier="Quokka Post",
            recipient_name="Zoë Lindgren", postal_code="75011", weight_kg=3.10,
            service_level="Standard", fragile=False),
        street="12 Rue Oberkampf", city="Paris", ink=150, paper=226, blur=0.9, noise=22,
    ),
    LabelSpec(
        file="label_05_struck_weight.png",
        kind="printed weight crossed out and rewritten by hand",
        expected=LabelFields(
            tracking_number="NWP 6150 2284 03", carrier="Northwind Parcel",
            recipient_name="Gustavo Peñaranda", postal_code="08001", weight_kg=11.30,
            service_level="Express", fragile=True),
        street="Carrer del Carme 55", city="Barcelona", struck_weight="9.80",
    ),
    LabelSpec(
        file="label_06_swift.png",
        kind="clean label from a second carrier, different layout colours",
        expected=LabelFields(
            tracking_number="SAF 3306 9918 42", carrier="SwiftArrow Freight",
            recipient_name="Dmitri Volkov", postal_code="10115", weight_kg=7.60,
            service_level="Express", fragile=False),
        street="Invalidenstrasse 91", city="Berlin", paper=240,
    ),
]

# Candidate fonts, best first; Pillow's built-in font is the fallback.
_FONTS = {
    "sans": ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "mono": ["/System/Library/Fonts/Supplemental/Courier New Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"],
    "hand": ["/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf", "/System/Library/Fonts/MarkerFelt.ttc"],
}


def _font(kind: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONTS[kind]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def render_label(spec: LabelSpec) -> Image.Image:
    e = spec.expected
    rng = random.Random(spec.file)  # per-label seed: identical pixels every run
    img = Image.new("L", (W, H), spec.paper)
    d = ImageDraw.Draw(img)
    ink, s = spec.ink, spec.scale

    def sz(n: int) -> int:
        return max(10, round(n * s))

    # Carrier banner: white-on-dark, with the service level in a box
    banner = 30 if ink < 100 else 90
    d.rectangle([0, 0, W, 110], fill=banner)
    d.text((24, 30), e.carrier.upper(), font=_font("bold", sz(30)), fill=255)
    d.rectangle([W - 150, 25, W - 20, 85], outline=255, width=3)
    d.text((W - 140, 42), e.service_level.upper(), font=_font("bold", sz(24)), fill=255)

    y = 135
    d.text((24, y), "SHIP TO", font=_font("sans", sz(20)), fill=ink + 40)
    y += round(34 * s)
    d.text((24, y), e.recipient_name, font=_font("bold", sz(44)), fill=ink)
    y += round(62 * s)
    d.text((24, y), spec.street, font=_font("sans", sz(32)), fill=ink)
    y += round(46 * s)
    d.text((24, y), f"{e.postal_code} {spec.city.upper()}", font=_font("bold", sz(38)), fill=ink)
    y += round(70 * s)

    for line in spec.extra_lines:
        d.text((24, y), line, font=_font("mono", sz(26)), fill=ink + 30)
        y += round(36 * s)
    y += round(10 * s)

    # Weight row
    d.line([24, y, W - 24, y], fill=ink + 60, width=2)
    y += 18
    d.text((24, y), "WEIGHT", font=_font("sans", sz(20)), fill=ink + 40)
    wx, wy = 24, y + round(28 * s)
    if spec.struck_weight:
        old = f"{spec.struck_weight} KG"
        d.text((wx, wy), old, font=_font("bold", sz(46)), fill=ink)
        width = d.textlength(old, font=_font("bold", sz(46)))
        d.line([wx - 6, wy + 30, wx + width + 6, wy + 30], fill=ink, width=5)  # the strike-through
        d.text((wx + width + 40, wy - 8), f"{e.weight_kg:.2f}", font=_font("hand", 58), fill=40)
    else:
        text = spec.weight_text or f"{e.weight_kg:.2f} KG"
        d.text((wx, wy), text, font=_font("bold", sz(46)), fill=ink)
    y = wy + round(80 * s)

    if e.fragile:
        d.rectangle([W - 250, y, W - 24, y + 74], outline=ink, width=5)
        d.text((W - 238, y + 12), "FRAGILE", font=_font("bold", sz(38)), fill=ink)

    # Barcode (decorative bars) with the human-readable tracking number under it
    y = max(y + 110, H - 250)
    x = 40
    while x < W - 40:
        bar = rng.choice([2, 3, 5, 8])
        d.rectangle([x, y, x + bar, y + 120], fill=ink)
        x += bar + rng.choice([3, 4, 6])
    d.text((40, y + 134), "TRACKING", font=_font("sans", sz(18)), fill=ink + 40)
    d.text((40, y + 158), e.tracking_number, font=_font("mono", sz(40)), fill=ink)

    if spec.noise:
        px = img.load()
        for _ in range(W * H // 6):
            x, yy = rng.randrange(W), rng.randrange(H)
            px[x, yy] = max(0, min(255, px[x, yy] + rng.randint(-spec.noise, spec.noise)))
    if spec.blur:
        img = img.filter(ImageFilter.GaussianBlur(spec.blur))
    if spec.rotate:
        img = img.rotate(spec.rotate, expand=True, fillcolor=spec.paper)
    return img


def generate_labels(directory: Path = LABELS_DIR) -> list[Path]:
    """Render every label PNG into `directory` and return the paths in spec order."""
    directory.mkdir(exist_ok=True)
    paths = []
    for spec in SPECS:
        path = directory / spec.file
        render_label(spec).convert("RGB").save(path)
        paths.append(path)
    return paths
