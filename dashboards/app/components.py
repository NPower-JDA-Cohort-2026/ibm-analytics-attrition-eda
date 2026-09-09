"""Reusable UI pieces: stat tiles, the hero figure, chart cards, controls, tables.

Filters are ordinary HTML form controls styled to match the chart chrome - the
dataviz layer only decides *where* they sit (one region, above everything they
scope) and that every chart re-renders against the same slice.
"""

from __future__ import annotations

from dash import dash_table, dcc, html

import datamodel as dm

# --- formatting ---------------------------------------------------------------


def compact(value: float | int | None, prefix: str = "", digits: int = 1) -> str:
    """1,284 / 12.9K / $4.2M - stat tiles stay readable at any magnitude."""
    if value is None:
        return "--"
    value = float(value)
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= limit:
            return f"{prefix}{value / limit:.{digits}f}{suffix}"
    return f"{prefix}{value:,.0f}"


def pct(value: float | None, digits: int = 1) -> str:
    return "--" if value is None else f"{value * 100:.{digits}f}%"


def signed_points(value: float | None, digits: int = 1) -> str:
    return "--" if value is None else f"{value * 100:+.{digits}f} pts"


# --- figures as numbers -------------------------------------------------------


def hero_tile(
    label: str,
    value: str,
    delta: str | None = None,
    delta_state: str = "neutral",
    footnote: str | None = None,
) -> html.Div:
    """The one number the dashboard leads with - same sans as everything else."""
    children: list = [
        html.Div(label, className="tile-label"),
        html.Div(value, className="hero-value"),
    ]
    if delta:
        children.append(html.Div(delta, className=f"tile-delta delta-{delta_state}"))
    if footnote:
        children.append(html.Div(footnote, className="tile-foot"))
    return html.Div(children, className="tile tile-hero")


def stat_tile(
    label: str,
    value: str,
    delta: str | None = None,
    delta_state: str = "neutral",
    footnote: str | None = None,
    meter: float | None = None,
) -> html.Div:
    """label / value / optional delta. A meter replaces the sparkline: this is a
    cross-sectional snapshot, so there is no time axis to trend along."""
    children: list = [
        html.Div(label, className="tile-label"),
        html.Div(value, className="tile-value"),
    ]
    if delta:
        children.append(html.Div(delta, className=f"tile-delta delta-{delta_state}"))
    if meter is not None:
        children.append(
            html.Div(
                html.Div(
                    className="meter-fill",
                    style={"width": f"{max(min(meter, 1.0), 0.0) * 100:.1f}%"},
                ),
                className="meter",
                title=f"{meter * 100:.1f}% of the workforce",
            )
        )
    if footnote:
        children.append(html.Div(footnote, className="tile-foot"))
    return html.Div(children, className="tile")


# --- controls -----------------------------------------------------------------


def select(
    control_id: str,
    label: str,
    options,
    value=None,
    multi: bool = False,
    width: str = "md",
    placeholder: str = "All",
    clearable: bool = True,
) -> html.Div:
    return html.Div(
        [
            html.Label(label, htmlFor=control_id, className="ctl-label"),
            dcc.Dropdown(
                id=control_id,
                options=options,
                value=value,
                multi=multi,
                placeholder=placeholder,
                clearable=clearable,
                className="ctl-dropdown",
            ),
        ],
        className=f"ctl ctl-{width}",
    )


def range_control(spec: dm.Filter) -> html.Div:
    low, high, step = dm.RANGE_BOUNDS[spec.key]
    marks = {low: f"{low:,}", high: f"{high:,}"}
    return html.Div(
        [
            html.Label(spec.label, className="ctl-label"),
            dcc.RangeSlider(
                id=f"f-{spec.key}",
                min=low,
                max=high,
                step=step,
                value=[low, high],
                marks=marks,
                tooltip={"placement": "bottom", "always_visible": False},
                className="ctl-slider",
            ),
        ],
        className=f"ctl ctl-{spec.width}",
    )


def filter_bar() -> html.Div:
    """One region above the charts. Everything below re-renders against it."""
    specs = dm.filter_specs()
    multi = [s for s in specs if s.kind == "multi"]
    ranges = [s for s in specs if s.kind == "range"]

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Filters", className="bar-title"),
                            html.Span(
                                "scope every chart, stat and table below",
                                className="bar-hint",
                            ),
                        ],
                        className="bar-heading",
                    ),
                    html.Div(
                        [
                            html.Div(id="filter-count", className="bar-count"),
                            html.Button(
                                "Reset all",
                                id="filter-reset",
                                n_clicks=0,
                                className="btn-ghost",
                            ),
                        ],
                        className="bar-actions",
                    ),
                ],
                className="bar-top",
            ),
            html.Div(
                [
                    select(
                        f"f-{spec.key}",
                        spec.label,
                        [{"label": o, "value": o} for o in spec.options],
                        multi=True,
                        width=spec.width,
                    )
                    for spec in multi
                ],
                className="ctl-row",
            ),
            html.Div(
                [range_control(spec) for spec in ranges]
                + [
                    select(
                        "min-n",
                        "Hide segments smaller than",
                        [
                            {"label": "Show every segment", "value": 0},
                            {"label": "10 employees", "value": 10},
                            {"label": "20 employees", "value": 20},
                            {"label": "30 employees", "value": 30},
                        ],
                        value=10,
                        width="md",
                        clearable=False,
                    )
                ],
                className="ctl-row ctl-row-wide",
            ),
            html.Div(id="filter-chips", className="chip-row"),
        ],
        className="filter-bar",
    )


# --- cards --------------------------------------------------------------------


def chart_card(
    title: str,
    subtitle: str,
    graph_id: str,
    controls: list | None = None,
    caption: str | None = None,
    wide: bool = False,
) -> html.Div:
    """A chart plus its encoding controls.

    The selectors in a card header choose *what is plotted* (which dimension,
    which measure) - they never slice the data. Data filters live in the one
    filter region above, so every card always shows the same population.
    """
    header: list = [
        html.Div(
            [html.H3(title, className="card-title"), html.P(subtitle, className="card-sub")],
            className="card-heading",
        )
    ]
    if controls:
        header.append(html.Div(controls, className="card-controls"))

    body: list = [
        html.Div(header, className="card-header"),
        dcc.Loading(
            dcc.Graph(
                id=graph_id,
                config={
                    "displayModeBar": False,
                    "responsive": True,
                    "doubleClick": False,
                },
                className="graph",
            ),
            # Refetch keeps the frame: hold the previous render, dimmed.
            overlay_style={"visibility": "visible", "opacity": 0.45},
            delay_show=180,
            type="default",
            color="#898781",
        ),
    ]
    if caption:
        body.append(html.P(caption, className="card-caption"))
    return html.Div(body, className=f"card{' card-wide' if wide else ''}")


def table_card(
    title: str, subtitle: str, container_id: str, controls: list | None = None
) -> html.Div:
    header: list = [
        html.Div(
            [html.H3(title, className="card-title"), html.P(subtitle, className="card-sub")],
            className="card-heading",
        )
    ]
    if controls:
        header.append(html.Div(controls, className="card-controls"))

    return html.Div(
        [
            html.Div(header, className="card-header"),
            dcc.Loading(
                html.Div(id=container_id, className="table-wrap"),
                overlay_style={"visibility": "visible", "opacity": 0.45},
                delay_show=180,
                type="default",
                color="#898781",
            ),
        ],
        className="card card-wide",
    )


def data_table(records: list[dict], columns: list[dict], t: dict, page_size: int = 12):
    """The table view every chart is twinned with - the WCAG-clean equivalent."""
    if not records:
        return html.P("No employees match the current filters.", className="empty-note")

    return dash_table.DataTable(
        data=records,
        columns=columns,
        page_size=page_size,
        sort_action="native",
        style_as_list_view=True,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": t["surface"],
            "color": t["ink_secondary"],
            "fontWeight": "600",
            "fontSize": "11px",
            "textTransform": "uppercase",
            "letterSpacing": "0.04em",
            "border": "none",
            "borderBottom": f"1px solid {t['axis']}",
        },
        style_cell={
            "backgroundColor": t["surface"],
            "color": t["ink"],
            "fontFamily": "system-ui, -apple-system, 'Segoe UI', sans-serif",
            "fontSize": "12px",
            "fontVariantNumeric": "tabular-nums",
            "padding": "9px 14px",
            "border": "none",
            "borderBottom": f"1px solid {t['grid']}",
            "textAlign": "right",
        },
        style_cell_conditional=[
            {"if": {"column_id": columns[0]["id"]}, "textAlign": "left"}
        ],
        style_data_conditional=[
            {"if": {"state": "active"}, "backgroundColor": t["wash"], "border": "none"},
            {"if": {"state": "selected"}, "backgroundColor": t["wash"], "border": "none"},
        ],
    )
