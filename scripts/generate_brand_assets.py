from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "assets" / "logo.png"
NAVY = (16, 42, 67)
GOLD = (197, 160, 82)
IVORY = (255, 253, 248)
TEXT = (30, 53, 73)


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    copy = image.copy()
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    return copy


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def main() -> None:
    logo = Image.open(LOGO).convert("RGBA")
    quarter = logo.crop((0, 0, int(logo.width * 0.26), logo.height))
    bbox = quarter.getchannel("A").getbbox()
    emblem = quarter.crop(bbox) if bbox else quarter

    icon = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    mark = contain(emblem, (460, 460))
    icon.alpha_composite(mark, ((512 - mark.width) // 2, (512 - mark.height) // 2))
    icon.save(ROOT / "assets" / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    large = Image.new("RGB", (164, 314), IVORY)
    draw = ImageDraw.Draw(large)
    draw.rectangle((0, 0, 163, 114), fill=NAVY)
    large_mark = contain(emblem, (92, 92))
    large.paste(large_mark, ((164 - large_mark.width) // 2, 11), large_mark)
    draw.rectangle((24, 135, 140, 138), fill=GOLD)
    draw.text((82, 154), "CORDÓN", font=font(18, True), fill=TEXT, anchor="mm")
    draw.text((82, 177), "DE ORO", font=font(18, True), fill=TEXT, anchor="mm")
    draw.text((82, 202), "E.I.R.L.", font=font(10, True), fill=(130, 105, 54), anchor="mm")
    draw.multiline_text((82, 244), "Sistema de Gestión\nEmpresarial", font=font(10), fill=(88, 103, 117), anchor="mm", align="center", spacing=4)
    large.save(ROOT / "installer" / "wizard-large.bmp")

    small = Image.new("RGB", (55, 58), NAVY)
    small_mark = contain(emblem, (46, 46))
    small.paste(small_mark, ((55 - small_mark.width) // 2, (58 - small_mark.height) // 2), small_mark)
    small.save(ROOT / "installer" / "wizard-small.bmp")


if __name__ == "__main__":
    main()

