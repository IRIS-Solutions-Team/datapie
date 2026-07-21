r"""
"""


#[

from __future__ import annotations

import re

#]


__all__ = (
    "rgba_from_string",
    "string_from_rgba",
    "generate_opaque_shades",
)


_HEX_PATTERN = re.compile(
    r"#([0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})",
    re.IGNORECASE,
)

_RGB_PATTERN = re.compile(
    r"rgb\((\d+),(\d+),(\d+)\)",
    re.IGNORECASE,
)

_RGBA_PATTERN = re.compile(
    r"rgba\((\d+),(\d+),(\d+),([01](?:\.\d+)?|\.\d+)\)",
    re.IGNORECASE,
)


def rgba_from_string(
    color: str | tuple[float, float, float] | tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    """
    Convert a color specification to an RGBA tuple of floats.

    Accepted string formats:
        #RGB
        #RGBA
        #RRGGBB
        #RRGGBBAA
        rgb(r,g,b)
        rgba(r,g,b,a)

    If `color` is already an RGBA tuple, it is returned unchanged (after
    converting its elements to float).
    """
    if isinstance(color, tuple):
        if len(color) == 3:
            return tuple(float(x) for x in color + (1.0, ))
        if len(color) == 4:
            return tuple(float(x) for x in color)
        raise ValueError("RGBA tuple must have exactly three or four elements")

    color = "".join(color.split())

    m = _HEX_PATTERN.fullmatch(color)
    if m:
        hex_ = m.group(1)

        if len(hex_) in (3, 4):
            hex_ = "".join(2 * c for c in hex_)

        if len(hex_) == 6:
            hex_ += "ff"

        return (
            int(hex_[0:2], 16) / 255,
            int(hex_[2:4], 16) / 255,
            int(hex_[4:6], 16) / 255,
            int(hex_[6:8], 16) / 255,
        )

    m = _RGBA_PATTERN.fullmatch(color)
    if m:
        r, g, b = (int(x) / 255 for x in m.groups()[:3])
        a = float(m.group(4))
        return r, g, b, a

    m = _RGB_PATTERN.fullmatch(color)
    if m:
        r, g, b = (int(x) / 255 for x in m.groups())
        return r, g, b, 1.0

    raise ValueError(f"Unsupported color format: {color!r}")


def string_from_rgba(
    rgba: tuple[float, float, float, float],
) -> str:
    """
    Convert an RGBA tuple of floats to an rgba(...) string.
    """
    r, g, b, a = rgba
    return (
        f"rgba("
        f"{round(255 * r)},"
        f"{round(255 * g)},"
        f"{round(255 * b)},"
        f"{a:g}"
        f")"
    )


_DEFAULT_SHADING_BACKGROUND_RGBA = (1.0, 1.0, 1.0, 1.0, )


def generate_opaque_shades(
    base_rgba: tuple[float, float, float, float],
    num_bands: int,
    #
    weights: Iterable[float, ...] | None = None,
    background_rgba: tuple[float, float, float, float] | None = None,
    min_weight: float = 0.30,
    max_weight: float = 0.60,
) -> tuple[tuple[float, float, float, float], ...]:
    r"""
    """
    if background_rgba is None:
        background_rgba = _DEFAULT_SHADING_BACKGROUND_RGBA
    if weights is None:
        weights = _generate_weights(
            num_bands,
            min_weight=min_weight,
            max_weight=max_weight,
        )
    return [
        _calculate_opaque_shade(base_rgba, w, background_rgba, )
        for w in weights
    ]


def _calculate_opaque_shade(
    base_rgba: tuple[float, float, float, float],
    weight: float,
    background_rgba: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    r"""
    """
    r, g, b, a, = base_rgba
    bg_r, bg_g, bg_b, bg_a, = background_rgba
    new_r = (1 - weight) * bg_r + weight * r
    new_g = (1 - weight) * bg_g + weight * g
    new_b = (1 - weight) * bg_b + weight * b
    new_a = 1
    return new_r, new_g, new_b, new_a,


def _generate_weights(
    num_bands: int,
    min_weight: float,
    max_weight: float,
) -> tuple[float, ...]:
    r"""
    """
    if num_bands < 1:
         return ()
    if num_bands == 1:
        return ((min_weight + max_weight) / 2,)
    return tuple(
        min_weight + i * (max_weight - min_weight) / (num_bands - 1)
        for i in range(num_bands)
    )

