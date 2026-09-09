"""Design tokens and Plotly chrome for the attrition dashboard.

Every colour the dashboard draws comes from this module, in one of four jobs:

* **categorical** - identity (cohorts, departments). Slots are assigned in a fixed
  order and never cycled or re-ranked.
* **sequential** - magnitude (attrition-rate heatmap, treemap). One hue, light to
  dark on the light surface, dark to light on the dark surface, so the step nearest
  the surface always means "near zero".
* **diverging** - polarity (correlations either side of zero). Two opposite hues
  with a neutral grey midpoint.
* **status** - state (good / warning / serious / critical). Reserved; never reused
  as a series colour.

The categorical slots, sequential blue ramp, surfaces and chrome are the validated
reference palette. To re-skin for another brand, substitute the values in
``LIGHT``/``DARK`` and re-run the palette validator against the new surfaces.

Validator results for the slots this dashboard actually puts on screen:

* 2 series (Stayed / Left), ``--pairs all``: PASS both modes (CVD dE 24.7 light,
  26.8 dark).
* 8 series (stacked composition), adjacent pairs: PASS both modes. Light mode
  raises a sub-3:1 contrast WARN on aqua / yellow / magenta, so the relief rule
  applies - those charts always ship a legend and a table view.
"""

from __future__ import annotations

FONT_STACK = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'

# --- chrome, ink and surfaces -------------------------------------------------

LIGHT: dict[str, object] = {
    "mode": "light",
    "surface": "#fcfcfb",
    "page": "#f9f9f7",
    "raised": "#ffffff",
    "ink": "#0b0b0b",
    "ink_secondary": "#52514e",
    "ink_muted": "#898781",
    "grid": "#e1e0d9",
    "axis": "#c3c2b7",
    "border": "rgba(11,11,11,0.10)",
    "wash": "rgba(11,11,11,0.04)",
    # de-emphasis fill for emphasis charts (one hue + grey)
    "deemphasis": "#c9c8c0",
    "series": (
        "#2a78d6",  # 1 blue
        "#eb6834",  # 2 orange
        "#1baf7a",  # 3 aqua
        "#eda100",  # 4 yellow
        "#e87ba4",  # 5 magenta
        "#008300",  # 6 green
        "#4a3aa7",  # 7 violet
        "#e34948",  # 8 red
    ),
    # one hue, near-zero step closest to the surface
    "sequential": (
        "#cde2fb",
        "#9ec5f4",
        "#6da7ec",
        "#3987e5",
        "#256abf",
        "#184f95",
        "#0d366b",
    ),
    # two opposite hues, neutral grey midpoint, four steps per arm
    "diverging": (
        "#bf3a30",
        "#e0645f",
        "#f4a8a3",
        "#fbd6d3",
        "#f0efec",
        "#cde2fb",
        "#9ec5f4",
        "#5598e7",
        "#256abf",
    ),
    "status": {
        "good": "#0ca30c",
        "warning": "#fab219",
        "serious": "#ec835a",
        "critical": "#d03b3b",
    },
    "delta_good": "#006300",
    "delta_bad": "#c0392b",
}

DARK: dict[str, object] = {
    "mode": "dark",
    "surface": "#1a1a19",
    "page": "#0d0d0d",
    "raised": "#212120",
    "ink": "#ffffff",
    "ink_secondary": "#c3c2b7",
    "ink_muted": "#898781",
    "grid": "#2c2c2a",
    "axis": "#383835",
    "border": "rgba(255,255,255,0.10)",
    "wash": "rgba(255,255,255,0.05)",
    "deemphasis": "#4c4c48",
    "series": (
        "#3987e5",
        "#d95926",
        "#199e70",
        "#c98500",
        "#d55181",
        "#008300",
        "#9085e9",
        "#e66767",
    ),
    "sequential": (
        "#104281",
        "#184f95",
        "#256abf",
        "#3987e5",
        "#6da7ec",
        "#9ec5f4",
        "#cde2fb",
    ),
    "diverging": (
        "#e66767",
        "#c85050",
        "#9b3a3a",
        "#6b3232",
        "#383835",
        "#2a4a75",
        "#1c5cab",
        "#2a78d6",
        "#3987e5",
    ),
    "status": {
        "good": "#0ca30c",
        "warning": "#fab219",
        "serious": "#ec835a",
        "critical": "#d03b3b",
    },
    "delta_good": "#0ca30c",
    "delta_bad": "#e66767",
}

THEMES = {"light": LIGHT, "dark": DARK}

# The two cohorts keep these hues everywhere in the app, in every chart, whatever
# the filter selection is - colour follows the entity, never its rank.
COHORT_ORDER = ("Stayed", "Left")


def tokens(mode: str | None) -> dict:
    """Return the token set for ``light`` or ``dark`` (defaults to light)."""
    return THEMES.get(mode or "light", LIGHT)


def cohort_colors(t: dict) -> dict[str, str]:
    """Fixed hue per cohort: slot 1 for Stayed, slot 2 for Left."""
    series = t["series"]
    return {"Stayed": series[0], "Left": series[1]}


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def sample_scale(steps: tuple[str, ...], position: float) -> str:
    """Linear interpolation into a ramp."""
    position = min(max(position, 0.0), 1.0)
    if len(steps) == 1:
        return steps[0]
    scaled = position * (len(steps) - 1)
    low = int(scaled)
    high = min(low + 1, len(steps) - 1)
    frac = scaled - low
    c1, c2 = _hex_to_rgb(steps[low]), _hex_to_rgb(steps[high])
    return "#{:02x}{:02x}{:02x}".format(
        *(round(a + (b - a) * frac) for a, b in zip(c1, c2))
    )


def colorscale(steps: tuple[str, ...]) -> list[list]:
    """Turn an ordered list of hex steps into a Plotly colourscale."""
    last = len(steps) - 1
    return [[i / last, hex_] for i, hex_ in enumerate(steps)]


def sequential_scale(t: dict) -> list[list]:
    return colorscale(t["sequential"])


def diverging_scale(t: dict) -> list[list]:
    return colorscale(t["diverging"])


def ordinal_ramp(t: dict, count: int) -> list[str]:
    """``count`` steps of the one sequential hue, for *ordered* categories.

    Ordered categories (job levels, age bands, tenure bands) take a ramp rather
    than categorical hues - the order is the information, and eight unrelated
    hues throw it away. The sampled window stops short of the ramp's lightest
    step so every band still clears 2:1 against the surface, which is the
    ordinal rule rather than the sequential one.
    """
    steps = t["sequential"]
    last = len(steps) - 1
    # skip the two steps nearest the surface on light, the darkest on dark
    start = (2 / last) if t["mode"] == "light" else (1 / last)
    if count <= 1:
        return [sample_scale(steps, (start + 1) / 2)]
    return [
        sample_scale(steps, start + (1 - start) * i / (count - 1))
        for i in range(count)
    ]


def base_layout(t: dict, *, height: int | None = None) -> dict:
    """Shared Plotly layout: recessive hairline chrome, generous padding."""
    layout: dict[str, object] = {
        "paper_bgcolor": t["surface"],
        "plot_bgcolor": t["surface"],
        "font": {"family": FONT_STACK, "size": 12, "color": t["ink_secondary"]},
        "margin": {"l": 8, "r": 18, "t": 10, "b": 8},
        "hoverlabel": {
            "bgcolor": t["raised"],
            "bordercolor": t["axis"],
            "font": {"family": FONT_STACK, "size": 12, "color": t["ink"]},
            "align": "left",
        },
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "title": {"text": ""},
            "font": {"size": 11, "color": t["ink_secondary"]},
            "itemsizing": "constant",
        },
        "colorway": list(t["series"]),
        "separators": ".,",
        "dragmode": False,
        "bargap": 0.42,
        "bargroupgap": 0.12,
        # 4px rounded data-end, square at the baseline
        "barcornerradius": 4,
        "transition": {"duration": 0},
    }
    if height is not None:
        layout["height"] = height
    return layout


def axis(t: dict, *, grid: bool = False, title: str | None = None, **kwargs) -> dict:
    """Axis spec: solid hairline grid (never dashed), muted tick ink."""
    spec: dict[str, object] = {
        "showgrid": grid,
        "gridcolor": t["grid"],
        "gridwidth": 1,
        "griddash": "solid",
        "zeroline": False,
        "showline": False,
        "ticks": "",
        "tickfont": {"size": 11, "color": t["ink_muted"]},
        "title": {
            "text": title or "",
            "font": {"size": 11, "color": t["ink_muted"]},
            "standoff": 12,
        },
        "automargin": True,
    }
    spec.update(kwargs)
    return spec


def empty_figure(t: dict, message: str = "No employees match the current filters") -> dict:
    """A chart-shaped placeholder, so an empty slice never renders a broken axis."""
    return {
        "data": [],
        "layout": {
            **base_layout(t, height=260),
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "annotations": [
                {
                    "text": message,
                    "showarrow": False,
                    "font": {"size": 13, "color": t["ink_muted"], "family": FONT_STACK},
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                }
            ],
        },
    }
