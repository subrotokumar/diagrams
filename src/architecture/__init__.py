from typing import Literal

from diagrams.custom import Custom


def Component(label="", icon: str = "", ext: Literal["png", "jpg", "svg"] = "png"):
    if icon == "":
        icon = f"../icons/{label.lower()}.{ext}"
    elif "." in icon:
        icon = f"../icons/{icon.lower()}"
    else:
        icon = f"../icons/{icon.lower()}.{ext}"
    return Custom(label=label, icon_path=icon)


graph_attr = {
    "rankdir": "LR",
    "splines": "ortho",
    "nodesep": "1.0",
    "ranksep": "1.2",
    "pad": "0.5",
    "margin": "15",
    "compound": "true",
}
edge_attr = {
    "fontsize": "10",
}

__init__ = []
