"""Génère l'image de présentation Play Store 1024×500 à partir de l'icône Booktime."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "frontend" / "public" / "icon-512.png"
OUT = ROOT / "frontend" / "public" / "play-store" / "feature-graphic.png"

W, H = 1024, 500
GREEN = (34, 166, 62)  # #22a63e — vert icône
GREEN_DARK = (22, 140, 48)
WHITE = (255, 255, 255)
SOFT = (232, 252, 237)


def find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), GREEN)
    draw = ImageDraw.Draw(img)

    # Bandeau / profondeur légère à droite
    draw.polygon([(620, 0), (W, 0), (W, H), (520, H)], fill=GREEN_DARK)

    icon = Image.open(ICON).convert("RGBA").resize((260, 260), Image.Resampling.LANCZOS)
    # Plaque claire pour détacher l'icône du fond vert
    plate = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    plate_draw = ImageDraw.Draw(plate)
    plate_draw.rounded_rectangle((0, 0, 299, 299), radius=64, fill=(255, 255, 255, 235))
    plate.paste(icon, (20, 20), icon)
    icon_x, icon_y = 64, (H - 300) // 2
    img.paste(plate, (icon_x, icon_y), plate)

    title_font = find_font(72)
    tag_font = find_font(28)

    title = "Booktime"
    tag = "Ta bibliothèque, toujours avec toi"

    # Texte à droite de l'icône
    tx = 420
    draw.text((tx, 160), title, font=title_font, fill=WHITE)
    draw.text((tx, 250), tag, font=tag_font, fill=SOFT)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"OK {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
