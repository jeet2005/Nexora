"""Generate preset avatar PNGs for Nexora (u1-u20 users, a1-a5 admins)."""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "avatars"

USER_PALETTE = [
    ("#6366F1", "#818CF8"), ("#8B5CF6", "#A78BFA"), ("#EC4899", "#F472B6"),
    ("#EF4444", "#F87171"), ("#F97316", "#FB923C"), ("#EAB308", "#FACC15"),
    ("#22C55E", "#4ADE80"), ("#14B8A6", "#2DD4BF"), ("#06B6D4", "#22D3EE"),
    ("#3B82F6", "#60A5FA"), ("#6366F1", "#A5B4FC"), ("#7C3AED", "#C4B5FD"),
    ("#DB2777", "#F9A8D4"), ("#DC2626", "#FCA5A5"), ("#EA580C", "#FDBA74"),
    ("#CA8A04", "#FDE047"), ("#16A34A", "#86EFAC"), ("#0D9488", "#5EEAD4"),
    ("#0284C7", "#7DD3FC"), ("#2563EB", "#93C5FD"),
]

ADMIN_PALETTE = [
    ("#1E293B", "#475569"), ("#7C2D12", "#C2410C"), ("#14532D", "#15803D"),
    ("#1E3A8A", "#2563EB"), ("#581C87", "#9333EA"),
]


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4))


def make_avatar(path: Path, label: str, c1: str, c2: str, size: int = 128) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for y in range(size):
        t = y / (size - 1)
        r = int(_hex(c1)[0] * (1 - t) + _hex(c2)[0] * t)
        g = int(_hex(c1)[1] * (1 - t) + _hex(c2)[1] * t)
        b = int(_hex(c1)[2] * (1 - t) + _hex(c2)[2] * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    margin = size // 8
    draw.ellipse([margin, margin, size - margin, size - margin], fill=(255, 255, 255, 40))

    text = label.upper()
    bbox = draw.textbbox((0, 0), text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) // 2, (size - th) // 2 - 4), text, fill=(255, 255, 255, 230))

    img.save(path, "PNG")


def main() -> None:
    for i, (c1, c2) in enumerate(USER_PALETTE, start=1):
        make_avatar(ROOT / "users" / f"u{i}.png", f"u{i}", c1, c2)
        print(f"Created u{i}.png")

    for i, (c1, c2) in enumerate(ADMIN_PALETTE, start=1):
        make_avatar(ROOT / "admins" / f"a{i}.png", f"a{i}", c1, c2)
        print(f"Created a{i}.png")

    print(f"Done — avatars saved to {ROOT}")


if __name__ == "__main__":
    main()
