from dataclasses import dataclass, field
from typing import ClassVar


@dataclass(frozen=True)
class ColorTokens:
    root_bg: str = "#020703"
    deep_bg: str = "#030A05"
    panel: str = "#061108"
    raised_panel: str = "#09180D"
    input_bg: str = "#020805"
    hover_surface: str = "#0B2413"
    selected_surface: str = "#0D3219"
    primary_green: str = "#00F56A"
    bright_green: str = "#1CFF7A"
    medium_green: str = "#00C853"
    green_border: str = "#087A38"
    muted_green: str = "#46A568"
    dim_green: str = "#1D5C34"
    info: str = "#18C8FF"
    warning: str = "#FFB300"
    danger: str = "#FF1744"
    recovered: str = "#B86CFF"
    inferred: str = "#00C2D7"
    manual: str = "#F5D547"
    primary_text: str = "#EAF7EE"
    secondary_text: str = "#A9C7B2"
    muted_text: str = "#6E9278"
    disabled_text: str = "#42604A"

    @classmethod
    def high_contrast(cls) -> "ColorTokens":
        return cls(
            root_bg="#000000",
            deep_bg="#000000",
            panel="#0A0A0A",
            raised_panel="#141414",
            input_bg="#000000",
            hover_surface="#1A1A1A",
            selected_surface="#222222",
            primary_green="#00FF66",
            bright_green="#33FF88",
            medium_green="#00CC44",
            green_border="#00FF66",
            muted_green="#66FF99",
            dim_green="#33AA55",
            info="#44CCFF",
            warning="#FFCC00",
            danger="#FF3333",
            recovered="#CC77FF",
            inferred="#33DDEE",
            manual="#FFDD44",
            primary_text="#FFFFFF",
            secondary_text="#CCCCCC",
            muted_text="#999999",
            disabled_text="#555555",
        )
