import base64
import mimetypes
import re
from pathlib import Path
from typing import Literal

from diagrams.custom import Custom


def _find_icon_dir() -> Path:
    """Walk up from this file until an 'icons' folder is found."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "icons"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"No 'icons' folder found above {here}")


ICON_DIR = _find_icon_dir()


def Component(label="", icon: str = "", ext: Literal["png", "jpg", "svg"] = "png"):
    name = (icon or label).lower()
    if "." not in name:
        name = f"{name}.{ext}"
    path = ICON_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Icon not found: {path}")
    return Custom(label=label, icon_path=str(path))  # absolute path


get_filename = lambda x: str(Path(x).resolve().with_name("diagram"))

outformat = [
    "svg",
    "png",
    # "dot",
    # "jpg",
    # "pdf",
]
graph_attr = {
    "rankdir": "LR",
    "splines": "ortho",
    "nodesep": "1.0",
    "ranksep": "1.2",
    "pad": "0.5",
    "margin": "15",
    "compound": "true",
    # "bgcolor": "transparent",
}
edge_attr = {
    "fontsize": "10",
}


def inline_svg_images(svg_path):
    svg_path = Path(svg_path)
    text = svg_path.read_text(encoding="utf-8")

    def repl(m):
        img = Path(m.group(2))
        if not img.is_absolute():
            img = svg_path.parent / img
        if not img.exists():
            print("MISSING:", img)
            return m.group(0)
        mime = mimetypes.guess_type(img.name)[0] or "image/png"
        data = base64.b64encode(img.read_bytes()).decode()
        return f'{m.group(1)}"data:{mime};base64,{data}"'

    text = re.sub(r'((?:xlink:)?href=)"([^"]+\.(?:png|jpe?g|svg))"', repl, text)
    svg_path.write_text(text, encoding="utf-8")


def animate_svg(path):
    svg = Path(path).resolve().parent / "diagram.svg"
    css = """
    <style>
    .edge path { stroke-dasharray: 8 6; animation: flow 1s linear infinite; }
    @keyframes flow { to { stroke-dashoffset: -14; } }
    </style>
    """
    svg.write_text(re.sub(r"(<svg[^>]*>)", r"\1" + css, svg.read_text(), count=1))


def finalize_svg(path, animate=True):
    svg = Path(path).resolve().parent / "diagram.svg"
    inline_svg_images(svg)
    if animate:
        animate_svg(path)
