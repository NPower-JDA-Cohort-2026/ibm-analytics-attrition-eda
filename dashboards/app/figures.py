"""Figure builders - one function per chart on the dashboard.

Each builder takes the already-filtered frame plus the active theme tokens and
returns a ``go.Figure``. Chart forms follow the job the data has to do:

===================  ====================================  =========================
Job                  Form                                  Colour job
===================  ====================================  =========================
Comparison           horizontal bar + baseline reference   one hue (emphasis)
Comparison (split)   small multiples of the same bar       one hue per panel
Comparison (gap)     dumbbell                              one hue, two shades
Distribution         grouped histogram + marginal box       categorical (2 cohorts)
Distribution (scale) diverging stacked bar (Likert)        diverging
Relationship         scatter + least-squares trend          categorical (2 cohorts)
Correlation          heatmap, lower triangle               diverging (zero = grey)
Correlation (target) horizontal bar either side of zero    diverging
Composition          100% stacked bar / treemap            categorical / sequential
Magnitude grid       heatmap                               sequential (one hue)
===================  ====================================  =========================
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import datamodel as dm
import theme as th

# --- small colour utilities ---------------------------------------------------


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def rgba(hex_color: str, alpha: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha})"


def _relative_luminance(hex_color: str) -> float:
    def channel(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in _hex_to_rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def label_ink(fill_hex: str) -> str:
    """White or near-black - whichever clears contrast on this fill.

    A label set inside a coloured mark is the one place text may leave the text
    tokens, and it picks its colour from the fill's luminance.
    """
    return "#0b0b0b" if _relative_luminance(fill_hex) > 0.42 else "#ffffff"


def sample_scale(steps: tuple[str, ...], position: float) -> str:
    """Linear interpolation into a ramp, so tile/cell labels know their backdrop."""
    position = min(max(position, 0.0), 1.0)
    if len(steps) == 1:
        return steps[0]
    scaled = position * (len(steps) - 1)
    low = int(np.floor(scaled))
    high = min(low + 1, len(steps) - 1)
    frac = scaled - low
    c1, c2 = _hex_to_rgb(steps[low]), _hex_to_rgb(steps[high])
    blend = [round(a + (b - a) * frac) for a, b in zip(c1, c2)]
    return "#{:02x}{:02x}{:02x}".format(*blend)


def _bar_height(n_categories: int, per_row: int = 34, chrome: int = 132) -> int:
    """Size the card to include the axis band, never crop it into a scrollbar."""
    return int(min(max(n_categories * per_row + chrome, 260), 900))


def _pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


# --- comparison ---------------------------------------------------------------


def rate_bar(df: pd.DataFrame, dim: dm.Dimension, t: dict, min_n: int = 0) -> go.Figure:
    """Attrition rate per category, one hue, against the company baseline."""
    data = dm.rate_by_dimension(df, dim, min_n)
    if data.empty:
        return go.Figure(th.empty_figure(t))

    baseline = dm.baseline_rate()
    accent = t["series"][0]
    fig = go.Figure(
        go.Bar(
            x=data["rate"],
            y=data["category"],
            orientation="h",
            marker={"color": accent},
            width=0.55,
            text=[_pct(v, 1) for v in data["rate"]],
            textposition="outside",
            textfont={"size": 11, "color": t["ink_secondary"]},
            cliponaxis=False,
            customdata=np.stack(
                [data["headcount"], data["leavers"], data["lift"] * 100], axis=-1
            ),
            hovertemplate=(
                "<b>%{x:.1%}</b> attrition<br>%{y}<br>"
                "%{customdata[1]:,} of %{customdata[0]:,} employees left<br>"
                "%{customdata[2]:+.1f} pts vs company<extra></extra>"
            ),
            name="Attrition rate",
        )
    )

    top = float(data["rate"].max())
    layout = th.base_layout(t, height=_bar_height(len(data)))
    # leave room above the plot for the baseline annotation
    layout["margin"] = {**layout["margin"], "t": 30}
    fig.update_layout(
        **layout,
        showlegend=False,
        xaxis=th.axis(t, grid=True, tickformat=".0%", range=[0, max(top * 1.28, 0.08)]),
        yaxis=th.axis(t, categoryorder="array", categoryarray=data["category"].tolist()),
    )
    fig.add_vline(
        x=baseline,
        line={"color": t["axis"], "width": 1},
        annotation_text=f"Company {_pct(baseline, 1)}",
        annotation_position="top",
        annotation_font={"size": 10, "color": t["ink_muted"]},
    )
    return fig


def rate_small_multiples(
    df: pd.DataFrame,
    dim: dm.Dimension,
    split: dm.Dimension,
    t: dict,
    min_n: int = 0,
    max_panels: int = 4,
) -> go.Figure:
    """The same rate bar, faceted - the honest alternative to 4-series grouped bars."""
    if df.empty:
        return go.Figure(th.empty_figure(t))

    panels = [
        p
        for p in dm.category_order(df, split)
        if len(df.loc[df[split.key].eq(p)]) >= max(min_n, 1)
    ][:max_panels]
    if not panels:
        return go.Figure(th.empty_figure(t, "No segment is large enough to compare"))

    categories = dm.rate_by_dimension(df, dim, min_n)["category"].tolist()
    if not categories:
        return go.Figure(th.empty_figure(t))

    accent = t["series"][0]
    baseline = dm.baseline_rate()
    fig = make_subplots(
        rows=1,
        cols=len(panels),
        shared_yaxes=True,
        horizontal_spacing=0.045,
        subplot_titles=[f"{p}" for p in panels],
    )

    peak = 0.0
    for col, panel in enumerate(panels, start=1):
        slice_ = df.loc[df[split.key].eq(panel)]
        data = dm.rate_by_dimension(slice_, dim, min_n).set_index("category")
        data = data.reindex(categories)
        peak = max(peak, float(np.nan_to_num(data["rate"].max())))
        fig.add_trace(
            go.Bar(
                x=data["rate"],
                y=categories,
                orientation="h",
                marker={"color": accent},
                width=0.55,
                text=[("" if pd.isna(v) else _pct(v, 0)) for v in data["rate"]],
                textposition="outside",
                textfont={"size": 10, "color": t["ink_secondary"]},
                cliponaxis=False,
                customdata=np.stack(
                    [data["headcount"].fillna(0), data["leavers"].fillna(0)], axis=-1
                ),
                hovertemplate=(
                    f"<b>%{{x:.1%}}</b> attrition<br>%{{y}} · {panel}<br>"
                    "%{customdata[1]:,.0f} of %{customdata[0]:,.0f} left<extra></extra>"
                ),
                showlegend=False,
            ),
            row=1,
            col=col,
        )

    layout = th.base_layout(t, height=_bar_height(len(categories), 32, 164))
    # room for the per-panel titles
    layout["margin"] = {**layout["margin"], "t": 34}
    fig.update_layout(**layout, showlegend=False)
    for col in range(1, len(panels) + 1):
        fig.update_xaxes(
            th.axis(t, grid=True, tickformat=".0%", range=[0, max(peak * 1.35, 0.1)]),
            row=1,
            col=col,
        )
        fig.add_vline(
            x=baseline, line={"color": t["axis"], "width": 1}, row=1, col=col
        )
    fig.update_yaxes(
        th.axis(t, categoryorder="array", categoryarray=categories), row=1, col=1
    )
    for annotation in fig.layout.annotations:
        annotation.font = {"size": 11, "color": t["ink_secondary"], "family": th.FONT_STACK}
    return fig


def dumbbell(
    df: pd.DataFrame,
    dim: dm.Dimension,
    cond: dm.Dimension,
    t: dict,
    min_n: int = 0,
) -> go.Figure:
    """Attrition rate under two conditions per category - one hue, two shades."""
    if df.empty:
        return go.Figure(th.empty_figure(t))

    levels = [lv for lv in cond.order if lv in set(df[cond.key].dropna().unique())]
    if len(levels) < 2:
        return go.Figure(
            th.empty_figure(t, f"Both {cond.label} values are needed for this comparison")
        )
    low_level, high_level = levels[0], levels[-1]

    rows = []
    for category, chunk in df.groupby(dim.key, observed=True):
        a = chunk.loc[chunk[cond.key].eq(low_level), "AttritionFlag"]
        b = chunk.loc[chunk[cond.key].eq(high_level), "AttritionFlag"]
        if len(a) < max(min_n, 1) or len(b) < max(min_n, 1):
            continue
        rows.append(
            {
                "category": category,
                "low": float(a.mean()),
                "high": float(b.mean()),
                "n_low": int(len(a)),
                "n_high": int(len(b)),
            }
        )
    if not rows:
        return go.Figure(
            th.empty_figure(t, "No category has enough employees on both sides")
        )

    data = pd.DataFrame(rows)
    data["gap"] = data["high"] - data["low"]
    data = data.sort_values("gap")

    shades = t["sequential"]
    light, dark = (shades[1], shades[4]) if t["mode"] == "light" else (shades[5], shades[2])

    fig = go.Figure()
    for _, row in data.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["low"], row["high"]],
                y=[row["category"], row["category"]],
                mode="lines",
                line={"color": t["axis"], "width": 2},
                hoverinfo="skip",
                showlegend=False,
            )
        )
    for level, color, key, n_key in (
        (low_level, light, "low", "n_low"),
        (high_level, dark, "high", "n_high"),
    ):
        fig.add_trace(
            go.Scatter(
                x=data[key],
                y=data["category"],
                mode="markers+text",
                name=f"{cond.label.split(' (')[0]}: {level}",
                marker={
                    "size": 13,
                    "color": color,
                    "line": {"width": 2, "color": t["surface"]},
                },
                text=[_pct(v, 0) for v in data[key]],
                textposition="middle right" if key == "high" else "middle left",
                textfont={"size": 10, "color": t["ink_secondary"]},
                cliponaxis=False,
                customdata=data[n_key],
                hovertemplate=(
                    f"<b>%{{x:.1%}}</b> attrition<br>%{{y}} · {level}<br>"
                    "n=%{customdata:,}<extra></extra>"
                ),
            )
        )

    span = float(max(data["high"].max(), data["low"].max()))
    fig.update_layout(
        **th.base_layout(t, height=_bar_height(len(data), 36, 140)),
        xaxis=th.axis(t, grid=True, tickformat=".0%", range=[-0.06, max(span * 1.2, 0.12)]),
        yaxis=th.axis(t, categoryorder="array", categoryarray=data["category"].tolist()),
    )
    return fig


# --- magnitude grid -----------------------------------------------------------


def risk_matrix(
    df: pd.DataFrame,
    row_dim: dm.Dimension,
    col_dim: dm.Dimension,
    t: dict,
    min_n: int = 0,
) -> go.Figure:
    """Attrition rate across two dimensions - one hue, more is darker."""
    rates, counts = dm.rate_matrix(df, row_dim, col_dim, min_n)
    if rates.empty or rates.isna().all().all():
        return go.Figure(th.empty_figure(t, "Not enough employees per cell to show a rate"))

    steps = t["sequential"]
    z = rates.to_numpy(dtype=float)
    top = float(np.nanmax(z)) or 1.0

    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=[str(c) for c in rates.columns],
            y=[str(r) for r in rates.index],
            colorscale=th.colorscale(steps),
            zmin=0,
            zmax=top,
            xgap=2,
            ygap=2,
            hoverongaps=False,
            customdata=counts.to_numpy(dtype=float),
            hovertemplate=(
                "<b>%{z:.1f}%</b> attrition<br>%{y} · %{x}<br>"
                "n=%{customdata:,.0f}<extra></extra>"
            ),
            colorbar={
                "title": {"text": "Rate %", "font": {"size": 10, "color": t["ink_muted"]}},
                "thickness": 10,
                "len": 0.75,
                "outlinewidth": 0,
                "tickfont": {"size": 10, "color": t["ink_muted"]},
                "ticksuffix": "%",
            },
        )
    )

    # In-cell values as a text overlay so each label can pick its own ink.
    xs, ys, texts, colors = [], [], [], []
    for r, row_name in enumerate(rates.index):
        for c, col_name in enumerate(rates.columns):
            value = z[r, c]
            if np.isnan(value):
                continue
            xs.append(str(col_name))
            ys.append(str(row_name))
            # carry the unit, so a cell never reads as a headcount
            texts.append(f"{value:.0f}%")
            colors.append(label_ink(sample_scale(steps, value / top if top else 0)))
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="text",
            text=texts,
            textfont={"size": 10, "color": colors},
            hoverinfo="skip",
            showlegend=False,
        )
    )

    fig.update_layout(
        **th.base_layout(t, height=_bar_height(len(rates.index), 44, 150)),
        showlegend=False,
        xaxis=th.axis(t, side="top", tickangle=0),
        yaxis=th.axis(t, autorange="reversed"),
    )
    return fig


# --- distribution -------------------------------------------------------------


def distribution(
    df: pd.DataFrame, meas: dm.Measure, t: dict, normalize: bool = True
) -> go.Figure:
    """Grouped histogram of one measure per cohort, with a marginal box plot."""
    if df.empty:
        return go.Figure(th.empty_figure(t))

    colors = th.cohort_colors(t)
    fig = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.2, 0.8],
        shared_xaxes=True,
        vertical_spacing=0.04,
    )

    unit = f"{meas.prefix}%{{x:,.0f}}{meas.suffix}"
    for cohort in th.COHORT_ORDER:
        values = df.loc[df["Cohort"].eq(cohort), meas.key]
        if values.empty:
            continue
        color = colors[cohort]
        fig.add_trace(
            go.Box(
                x=values,
                name=cohort,
                orientation="h",
                marker={"color": color, "outliercolor": color, "size": 5},
                line={"color": color, "width": 2},
                fillcolor=rgba(color, 0.1),
                boxmean=True,
                hovertemplate=(
                    f"{cohort}<br>median {meas.prefix}%{{median:,.0f}}{meas.suffix}"
                    "<extra></extra>"
                ),
                showlegend=False,
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Histogram(
                x=values,
                name=cohort,
                marker={"color": color},
                histnorm="percent" if normalize else "",
                xbins={"size": meas.bin_size} if meas.bin_size else None,
                hovertemplate=(
                    f"<b>%{{y:.1f}}%</b> of {cohort.lower()} employees<br>{unit}"
                    "<extra></extra>"
                    if normalize
                    else f"<b>%{{y:,.0f}}</b> {cohort.lower()} employees<br>{unit}<extra></extra>"
                ),
            ),
            row=2,
            col=1,
        )

    layout = th.base_layout(t, height=420) | {"barmode": "group"}
    layout["legend"] = {**layout["legend"], "y": 1.06}
    fig.update_layout(**layout)
    fig.update_xaxes(th.axis(t, visible=False), row=1, col=1)
    fig.update_yaxes(th.axis(t, showticklabels=False), row=1, col=1)
    fig.update_xaxes(
        th.axis(t, grid=False, title=meas.label, tickprefix=meas.prefix), row=2, col=1
    )
    fig.update_yaxes(
        th.axis(
            t,
            grid=True,
            title="Share of cohort" if normalize else "Employees",
            ticksuffix="%" if normalize else "",
        ),
        row=2,
        col=1,
    )
    return fig


def measure_box_by_dimension(
    df: pd.DataFrame, meas: dm.Measure, dim: dm.Dimension, t: dict, min_n: int = 0
) -> go.Figure:
    """Does the gap hold *within* each category? One box pair per category."""
    if df.empty:
        return go.Figure(th.empty_figure(t))

    categories = [
        c
        for c in dm.category_order(df, dim)
        if len(df.loc[df[dim.key].eq(c)]) >= max(min_n, 1)
    ]
    if not categories:
        return go.Figure(th.empty_figure(t, "No category is large enough to show"))

    colors = th.cohort_colors(t)
    fig = go.Figure()
    for cohort in th.COHORT_ORDER:
        chunk = df.loc[df["Cohort"].eq(cohort) & df[dim.key].isin(categories)]
        if chunk.empty:
            continue
        color = colors[cohort]
        fig.add_trace(
            go.Box(
                x=chunk[meas.key],
                y=chunk[dim.key],
                name=cohort,
                orientation="h",
                marker={"color": color, "outliercolor": color, "size": 5},
                line={"color": color, "width": 2},
                fillcolor=rgba(color, 0.1),
                boxmean=True,
                hovertemplate=(
                    f"{cohort} · %{{y}}<br>median {meas.prefix}%{{median:,.0f}}{meas.suffix}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        **th.base_layout(t, height=_bar_height(len(categories), 62, 150)),
        boxmode="group",
        boxgap=0.35,
        boxgroupgap=0.15,
        xaxis=th.axis(t, grid=True, title=meas.label, tickprefix=meas.prefix),
        yaxis=th.axis(t, categoryorder="array", categoryarray=categories),
    )
    return fig


def likert_diverging(df: pd.DataFrame, dim: dm.Dimension, t: dict) -> go.Figure:
    """Ordered-scale share per cohort, centred on the middle of the scale."""
    data = dm.likert_shares(df, dim)
    if data.empty:
        return go.Figure(th.empty_figure(t))

    levels = [lv for lv in dim.order if lv in set(data["level"].dropna().unique())]
    if not levels:
        return go.Figure(th.empty_figure(t))

    mid = len(levels) // 2
    negative, positive = levels[:mid], levels[mid:]
    div = t["diverging"]
    # Strongest step at each end of the scale, fading toward the neutral middle:
    # the lowest level takes the outermost red, the highest the outermost blue.
    neg_colors = {lv: div[i] for i, lv in enumerate(negative)}
    pos_colors = {lv: div[len(div) - len(positive) + i] for i, lv in enumerate(positive)}

    pivot = data.pivot_table(
        index="cohort", columns="level", values="share", aggfunc="sum", observed=True
    ).reindex(index=list(th.COHORT_ORDER), columns=levels)
    counts = data.pivot_table(
        index="cohort", columns="level", values="headcount", aggfunc="sum", observed=True
    ).reindex(index=list(th.COHORT_ORDER), columns=levels)

    fig = go.Figure()
    ordered = list(reversed(negative)) + list(positive)
    for level in ordered:
        signed = -1 if level in negative else 1
        shares = pivot[level].fillna(0.0)
        color = neg_colors.get(level, pos_colors.get(level))
        labels = [
            f"{v * 100:.0f}%" if v >= 0.09 else "" for v in shares
        ]  # only label segments wide enough to hold the text
        fig.add_trace(
            go.Bar(
                x=shares * signed,
                y=pivot.index.astype(str),
                orientation="h",
                name=str(level),
                # stacking order runs outward from the centre; the legend still
                # reads in scale order
                legendrank=levels.index(level),
                marker={"color": color, "line": {"width": 2, "color": t["surface"]}},
                width=0.5,
                text=labels,
                textposition="inside",
                insidetextanchor="middle",
                constraintext="inside",
                textfont={"size": 10, "color": label_ink(color)},
                customdata=np.stack([shares * 100, counts[level].fillna(0)], axis=-1),
                hovertemplate=(
                    f"<b>%{{customdata[0]:.1f}}%</b> of cohort<br>{dim.label}: {level}"
                    "<br>%{customdata[1]:,.0f} employees<extra></extra>"
                ),
            )
        )

    span = float(max(pivot[negative].sum(axis=1).max(), pivot[positive].sum(axis=1).max()))
    span = max(span, 0.3) * 1.12
    ticks = [round(v, 2) for v in np.arange(-1, 1.01, 0.2) if abs(v) <= span]
    fig.update_layout(
        **th.base_layout(t, height=280),
        barmode="relative",
        xaxis=th.axis(
            t,
            grid=True,
            range=[-span, span],
            tickvals=ticks,
            ticktext=[f"{abs(v) * 100:.0f}%" for v in ticks],
            title=f"Share of cohort · left = lower {dim.label.lower()}",
        ),
        yaxis=th.axis(t),
    )
    fig.add_vline(x=0, line={"color": t["axis"], "width": 1})
    return fig


# --- relationship & correlation ----------------------------------------------


def relationship(
    df: pd.DataFrame,
    x_meas: dm.Measure,
    y_meas: dm.Measure,
    t: dict,
    trend: bool = True,
) -> go.Figure:
    """Two measures against each other, one mark per employee, split by cohort."""
    if df.empty:
        return go.Figure(th.empty_figure(t))

    colors = th.cohort_colors(t)
    rng = np.random.default_rng(7)
    fig = go.Figure()

    def jitter(series: pd.Series) -> np.ndarray:
        """Ordinal scales (1-5 codes) would otherwise stack into a few columns."""
        values = series.to_numpy(dtype=float)
        if series.nunique() > 10:
            return values
        spread = 0.16 * (np.nanmax(values) - np.nanmin(values) or 1) / max(series.nunique() - 1, 1)
        return values + rng.uniform(-spread, spread, size=values.shape)

    for cohort in th.COHORT_ORDER:
        chunk = df.loc[df["Cohort"].eq(cohort)]
        if chunk.empty:
            continue
        color = colors[cohort]
        fig.add_trace(
            go.Scatter(
                x=jitter(chunk[x_meas.key]),
                y=jitter(chunk[y_meas.key]),
                mode="markers",
                name=cohort,
                marker={
                    "size": 9,
                    "color": rgba(color, 0.78),
                    "line": {"width": 2, "color": t["surface"]},
                },
                customdata=np.stack(
                    [
                        chunk[x_meas.key],
                        chunk[y_meas.key],
                        chunk["JobRole"],
                        chunk["Department"],
                    ],
                    axis=-1,
                ),
                hovertemplate=(
                    f"<b>{x_meas.label}</b> {x_meas.prefix}%{{customdata[0]:,.0f}}{x_meas.suffix}"
                    f"<br><b>{y_meas.label}</b> {y_meas.prefix}%{{customdata[1]:,.0f}}{y_meas.suffix}"
                    f"<br>%{{customdata[2]}} · %{{customdata[3]}}<br>{cohort}<extra></extra>"
                ),
            )
        )
        if trend:
            fitted = dm.ols_line(chunk[x_meas.key], chunk[y_meas.key])
            if fitted is not None:
                xs, ys = fitted
                fig.add_trace(
                    go.Scatter(
                        x=xs,
                        y=ys,
                        mode="lines",
                        name=f"{cohort} trend",
                        line={"color": color, "width": 2},
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )

    fig.update_layout(
        **th.base_layout(t, height=470),
        hovermode="closest",
        hoverdistance=24,
        xaxis=th.axis(t, grid=True, title=x_meas.label, tickprefix=x_meas.prefix),
        yaxis=th.axis(t, grid=True, title=y_meas.label, tickprefix=y_meas.prefix),
    )
    return fig


def correlation_heatmap(df: pd.DataFrame, keys: list[str], t: dict) -> go.Figure:
    """Lower-triangle Pearson matrix - two hues either side of a grey zero."""
    matrix = dm.correlation_matrix(df, keys)
    if matrix.empty:
        return go.Figure(th.empty_figure(t, "Pick at least two measures to correlate"))

    labels = [dm.measure(k).label for k in matrix.columns]
    z = matrix.to_numpy(dtype=float).copy()
    z[np.triu_indices_from(z, k=0)] = np.nan  # keep the informative half only
    # The first row and last column of a masked triangle are entirely empty -
    # dropping them keeps the grid from carrying a blank rank and file.
    z = z[1:, :-1]
    row_labels, col_labels = labels[1:], labels[:-1]

    steps = t["diverging"]
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=col_labels,
            y=row_labels,
            colorscale=th.colorscale(steps),
            zmin=-1,
            zmax=1,
            zmid=0,
            xgap=2,
            ygap=2,
            hoverongaps=False,
            hovertemplate="<b>r = %{z:+.2f}</b><br>%{y}<br>vs %{x}<extra></extra>",
            colorbar={
                "title": {"text": "r", "font": {"size": 10, "color": t["ink_muted"]}},
                "thickness": 10,
                "len": 0.75,
                "outlinewidth": 0,
                "tickvals": [-1, -0.5, 0, 0.5, 1],
                "tickfont": {"size": 10, "color": t["ink_muted"]},
            },
        )
    )

    # Label only the pairs strong enough to be worth reading off the grid.
    xs, ys, texts, colors = [], [], [], []
    for r in range(z.shape[0]):
        for c in range(z.shape[1]):
            value = z[r, c]
            if np.isnan(value) or abs(value) < 0.3:
                continue
            xs.append(col_labels[c])
            ys.append(row_labels[r])
            texts.append(f"{value:+.2f}")
            colors.append(label_ink(sample_scale(steps, (value + 1) / 2)))
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="text",
            text=texts,
            textfont={"size": 10, "color": colors},
            hoverinfo="skip",
            showlegend=False,
        )
    )

    size = _bar_height(len(row_labels), 40, 190)
    fig.update_layout(
        **th.base_layout(t, height=size),
        showlegend=False,
        xaxis=th.axis(t, tickangle=-35),
        yaxis=th.axis(t, autorange="reversed"),
    )
    return fig


def attrition_correlation_bar(df: pd.DataFrame, keys: list[str], t: dict) -> go.Figure:
    """Each measure's correlation with leaving, either side of zero."""
    data = dm.attrition_correlations(df, keys)
    if data.empty:
        return go.Figure(
            th.empty_figure(t, "Both cohorts are needed to correlate against attrition")
        )

    steps = t["diverging"]
    negative, positive = steps[0], steps[-1]
    fig = go.Figure(
        go.Bar(
            x=data["corr"],
            y=data["label"],
            orientation="h",
            marker={"color": [negative if v < 0 else positive for v in data["corr"]]},
            width=0.55,
            text=[f"{v:+.2f}" for v in data["corr"]],
            textposition="outside",
            textfont={"size": 10, "color": t["ink_secondary"]},
            cliponaxis=False,
            hovertemplate="<b>r = %{x:+.2f}</b><br>%{y} vs leaving<extra></extra>",
            showlegend=False,
        )
    )
    span = float(np.abs(data["corr"]).max()) * 1.45 or 0.2
    fig.update_layout(
        **th.base_layout(t, height=_bar_height(len(data), 30, 120)),
        xaxis=th.axis(t, grid=True, range=[-span, span], title="Correlation with leaving"),
        yaxis=th.axis(t),
    )
    fig.add_vline(x=0, line={"color": t["axis"], "width": 1})
    return fig


# --- composition --------------------------------------------------------------


def composition_stacked(
    df: pd.DataFrame, dim: dm.Dimension, split: dm.Dimension, t: dict
) -> go.Figure:
    """Part-to-whole: how each category of ``dim`` is made up of ``split`` values."""
    data = dm.composition(df, dim, split)
    if data.empty:
        return go.Figure(th.empty_figure(t))

    categories = dm.category_order(df, dim)
    segments = list(data["segment"].cat.categories)
    # Ordered segments (levels, bands, scales) get the ordinal ramp so the
    # order survives; unordered ones (roles, fields) get categorical hues.
    palette = (
        th.ordinal_ramp(t, len(segments))
        if dm.is_ordinal(split)
        else list(t["series"])
    )
    totals = data.groupby("category", observed=True)["headcount"].sum()

    fig = go.Figure()
    for index, segment in enumerate(segments):
        chunk = (
            data.loc[data["segment"].eq(segment)]
            .set_index("category")
            .reindex(categories)
        )
        # Colour follows the entity: slot index is the segment's position in the
        # declared order, so filtering never repaints the survivors.
        color = palette[index % len(palette)]
        fig.add_trace(
            go.Bar(
                x=chunk["share"].fillna(0),
                y=categories,
                orientation="h",
                name=str(segment),
                marker={"color": color, "line": {"width": 2, "color": t["surface"]}},
                width=0.55,
                text=[
                    f"{v * 100:.0f}%" if (v or 0) >= 0.09 else ""
                    for v in chunk["share"].fillna(0)
                ],
                textposition="inside",
                insidetextanchor="middle",
                constraintext="inside",
                textfont={"size": 10, "color": label_ink(color)},
                customdata=chunk["headcount"].fillna(0),
                hovertemplate=(
                    f"<b>%{{x:.1%}}</b> · {segment}<br>%{{y}}<br>"
                    "%{customdata:,.0f} employees<extra></extra>"
                ),
            )
        )

    layout = th.base_layout(t, height=_bar_height(len(categories), 38, 150))
    # Plotly reverses the legend on stacked bars; keep it in declared order.
    layout["legend"] = {**layout["legend"], "traceorder": "normal"}
    fig.update_layout(
        **layout,
        barmode="stack",
        xaxis=th.axis(t, grid=True, tickformat=".0%", range=[0, 1.14]),
        yaxis=th.axis(t, categoryorder="array", categoryarray=categories),
        annotations=[
            {
                "x": 1.005,
                "y": category,
                "xref": "x",
                "yref": "y",
                "text": f"n={int(totals.get(category, 0)):,}",
                "showarrow": False,
                "xanchor": "left",
                "font": {"size": 10, "color": t["ink_muted"]},
            }
            for category in categories
        ],
    )
    return fig


def workforce_treemap(df: pd.DataFrame, t: dict, min_n: int = 0) -> go.Figure:
    """Headcount as area, attrition rate as one-hue depth, department to role."""
    if df.empty:
        return go.Figure(th.empty_figure(t))

    steps = t["sequential"]
    ids, labels, parents, values, colors, counts, rates = [], [], [], [], [], [], []

    for dept, dept_rows in df.groupby("Department", observed=True):
        dept_rate = float(dept_rows["AttritionFlag"].mean())
        ids.append(dept)
        labels.append(dept)
        parents.append("")
        values.append(0)
        colors.append(dept_rate)
        counts.append(len(dept_rows))
        rates.append(dept_rate)
        for role, role_rows in dept_rows.groupby("JobRole", observed=True):
            if len(role_rows) < min_n:
                continue
            role_rate = float(role_rows["AttritionFlag"].mean())
            ids.append(f"{dept}/{role}")
            labels.append(role)
            parents.append(dept)
            values.append(len(role_rows))
            colors.append(role_rate)
            counts.append(len(role_rows))
            rates.append(role_rate)

    if len(ids) <= len(df["Department"].unique()):
        return go.Figure(th.empty_figure(t, "No role is large enough to show"))

    top = max(max(colors), 1e-9)
    fig = go.Figure(
        go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="remainder",
            marker={
                "colors": colors,
                "colorscale": th.colorscale(steps),
                "cmin": 0,
                "cmax": top,
                "line": {"width": 2, "color": t["surface"]},
                "colorbar": {
                    "title": {
                        "text": "Rate",
                        "font": {"size": 10, "color": t["ink_muted"]},
                    },
                    "thickness": 10,
                    "len": 0.7,
                    "outlinewidth": 0,
                    "tickformat": ".0%",
                    "tickfont": {"size": 10, "color": t["ink_muted"]},
                },
            },
            textfont={
                "size": 12,
                "color": [label_ink(sample_scale(steps, c / top)) for c in colors],
            },
            texttemplate="%{label}<br>%{customdata[0]:,} · %{customdata[1]:.0%}",
            customdata=np.stack([counts, rates], axis=-1),
            hovertemplate=(
                "<b>%{label}</b><br>%{customdata[0]:,} employees<br>"
                "%{customdata[1]:.1%} attrition<extra></extra>"
            ),
            tiling={"pad": 2},
            pathbar={"visible": False},
            # without this the implicit root tile paints itself near-black
            root={"color": t["surface"]},
        )
    )
    layout = th.base_layout(t, height=430)
    layout["margin"] = {"l": 4, "r": 4, "t": 4, "b": 4}
    # Drop a tile's label rather than shrinking it into illegibility.
    layout["uniformtext"] = {"minsize": 10, "mode": "hide"}
    fig.update_layout(**layout)
    return fig


def cohort_stacked(df: pd.DataFrame, dim: dm.Dimension, t: dict) -> go.Figure:
    """Absolute headcount per category, split into stayers and leavers."""
    if df.empty:
        return go.Figure(th.empty_figure(t))

    categories = dm.category_order(df, dim)
    colors = th.cohort_colors(t)
    counts = (
        df.groupby([dim.key, "Cohort"], observed=True)
        .size()
        .unstack("Cohort")
        .reindex(index=categories)
        .reindex(columns=list(th.COHORT_ORDER))
        .fillna(0)
    )

    fig = go.Figure()
    for cohort in th.COHORT_ORDER:
        color = colors[cohort]
        fig.add_trace(
            go.Bar(
                x=counts[cohort],
                y=categories,
                orientation="h",
                name=cohort,
                marker={"color": color, "line": {"width": 2, "color": t["surface"]}},
                width=0.55,
                hovertemplate=(
                    f"<b>%{{x:,.0f}}</b> {cohort.lower()}<br>%{{y}}<extra></extra>"
                ),
            )
        )
    layout = th.base_layout(t, height=_bar_height(len(categories), 38, 150))
    layout["legend"] = {**layout["legend"], "traceorder": "normal"}
    fig.update_layout(
        **layout,
        barmode="stack",
        xaxis=th.axis(t, grid=True, title="Employees"),
        yaxis=th.axis(t, categoryorder="array", categoryarray=categories),
    )
    return fig
