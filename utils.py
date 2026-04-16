# ── utils.py ──────────────────────────────────────────────────────────────────
# Functii utilitare: procesare imagini, download, rotunjire colturi
# ──────────────────────────────────────────────────────────────────────────────

import io
import urllib.request
from PIL import Image, ImageDraw, ImageTk


def round_image(img: Image.Image, radius: int = 16) -> Image.Image:
    """Rotunjeste colturile unei imagini PIL."""
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        [0, 0, img.size[0] - 1, img.size[1] - 1],
        radius=radius,
        fill=255
    )
    result = Image.new("RGBA", img.size, (0, 0, 0, 0))
    result.paste(img, mask=mask)
    return result


def fetch_image(url: str, size: tuple = (200, 200)) -> Image.Image:
    """Descarca o imagine de la URL, o redimensioneaza si ii rotunjeste colturile."""
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = r.read()
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        img = img.resize(size, Image.LANCZOS)
        return round_image(img, radius=12)
    except Exception:
        # Imagine placeholder daca download-ul esueaza
        img = Image.new("RGBA", size, (30, 30, 30, 255))
        return round_image(img, radius=12)


def make_placeholder_cover(size: tuple = (200, 200)) -> Image.Image:
    """Creeaza o coperta placeholder cu nota muzicala."""
    img = Image.new("RGBA", size, (30, 30, 30, 255))
    draw = ImageDraw.Draw(img)
    draw.text((size[0] // 2 - 15, size[1] // 2 - 15), "♪", fill=(80, 80, 80, 255))
    return round_image(img, radius=12)