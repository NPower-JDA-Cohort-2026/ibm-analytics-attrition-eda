"""Callback wiring.

Two stores carry shared state so no figure callback has to repeat the filter row:

* ``slice-store`` - the current filter selection plus the minimum segment size.
* ``theme-store`` - ``light`` or ``dark``, so the Plotly figures and the CSS
  always agree on which palette is on screen.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dash import Input, Output, State, dcc, html

import components as ui
import datamodel as dm
import figures as fg
import theme as th

FILTER_SPECS = dm.filter_specs()
FILTER_KEYS = [s.key for s in FILTER_SPECS]


def _slice_for(store: dict | None) -> tuple[pd.DataFrame, int]:
    store = store or {}
    frame = dm.apply_filters(dm.load_data(), store.get("filters"))
    return frame, int(store.get("min_n") or 0)


def register(app) -> None:
    # --- theme --------------------------------------------------------------
    app.clientside_callback(
        """
        function(boot, clicks, current) {
            const ctx = (dash_clientside.callback_context.triggered || []);
            const trigger = ctx.length ? ctx[0].prop_id : '';
            let mode = current || 'light';
            if (trigger.indexOf('theme-toggle') === 0) {
                mode = (mode === 'dark') ? 'light' : 'dark';
                try { window.localStorage.setItem('attrition-theme', mode); } catch (e) {}
            } else {
                try {
                    const saved = window.localStorage.getItem('attrition-theme');
                    if (saved === 'light' || saved === 'dark') {
                        mode = saved;
                    } else if (window.matchMedia &&
                               window.matchMedia('(prefers-color-scheme: dark)').matches) {
                        mode = 'dark';
                    }
                } catch (e) {}
            }
            document.documentElement.setAttribute('data-theme', mode);
            return [mode, mode === 'dark' ? 'Light mode' : 'Dark mode'];
        }
        """,
        Output("theme-store", "data"),
        Output("theme-toggle", "children"),
        Input("boot", "n_intervals"),
        Input("theme-toggle", "n_clicks"),
        State("theme-store", "data"),
        prevent_initial_call=True,
    )

    # --- filter region ------------------------------------------------------
    @app.callback(
        Output("slice-store", "data"),
        Output("filter-chips", "children"),
        Output("filter-count", "children"),
        [Input(f"f-{key}", "value") for key in FILTER_KEYS] + [Input("min-n", "value")],
    )
    def collect_filters(*values):
        selections = dict(zip(FILTER_KEYS, values[:-1]))
        min_n = values[-1] or 0
        frame = dm.apply_filters(dm.load_data(), selections)
        chips = dm.active_filter_summary(selections)

        chip_nodes = (
            [html.Span(text, className="chip") for text in chips]
            if chips
            else [html.Span("Whole company - no filters applied", className="chip chip-muted")]
        )
        total = len(dm.load_data())
        count = [
            html.Strong(f"{len(frame):,}"),
            html.Span(f" of {total:,} employees in view"),
        ]
        return {"filters": selections, "min_n": min_n}, chip_nodes, count

    @app.callback(
        [Output(f"f-{spec.key}", "value") for spec in FILTER_SPECS],
        Input("filter-reset", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_filters(_clicks):
        return [
            None if spec.kind == "multi" else list(dm.RANGE_BOUNDS[spec.key][:2])
            for spec in FILTER_SPECS
        ]

    @app.callback(
        Output("f-JobRole", "options"),
        Output("f-JobRole", "value", allow_duplicate=True),
        Input("f-Department", "value"),
        State("f-JobRole", "value"),
        prevent_initial_call=True,
    )
    def cascade_job_roles(departments, selected):
        """Job roles narrow to the chosen departments; impossible picks drop out."""
        frame = dm.load_data()
        if departments:
            frame = frame.loc[frame["Department"].isin(departments)]
        available = sorted(frame["JobRole"].unique().tolist())
        options = [{"label": role, "value": role} for role in available]
        kept = [role for role in (selected or []) if role in available]
        return options, (kept or None)

    # --- stat tiles ---------------------------------------------------------
    @app.callback(
        Output("kpi-row", "children"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
    )
    def render_kpis(store, mode):
        frame, _ = _slice_for(store)
        k = dm.kpi_summary(frame)
        baseline = k["baseline"]

        if not k["headcount"]:
            return [
                ui.hero_tile(
                    "Attrition rate in view",
                    "--",
                    footnote="No employees match the current filters",
                )
            ]

        gap = k["rate"] - baseline
        tiles = [
            ui.hero_tile(
                "Attrition rate in view",
                ui.pct(k["rate"]),
                delta=f"{ui.signed_points(gap)} vs company",
                delta_state="bad" if gap > 0.005 else "good" if gap < -0.005 else "neutral",
                footnote=f"Company baseline {ui.pct(baseline)}",
            ),
            ui.stat_tile(
                "Employees in view",
                f"{k['headcount']:,}",
                footnote=f"{ui.pct(k['share_of_company'], 0)} of the workforce",
                meter=k["share_of_company"],
            ),
            ui.stat_tile(
                "Employees who left",
                f"{k['leavers']:,}",
                footnote=f"of {k['headcount']:,} in this slice",
            ),
            ui.stat_tile(
                "Median monthly income",
                ui.compact(k["median_income"], "$"),
                delta=f"{k['median_income'] - k['median_income_baseline']:+,.0f} vs company",
                footnote=(
                    f"Leavers {ui.compact(abs(k['income_gap']), '$')} "
                    f"{'below' if k['income_gap'] < 0 else 'above'} stayers"
                    if k["income_gap"] is not None
                    else "One cohort only in this slice"
                ),
            ),
            ui.stat_tile(
                "Average tenure",
                f"{k['avg_tenure']:.1f} yrs",
                delta=f"{k['avg_tenure'] - k['avg_tenure_baseline']:+.1f} yrs vs company",
                footnote="Years at the company",
            ),
            ui.stat_tile(
                "Working overtime",
                ui.pct(k["overtime_share"], 0),
                delta=f"{ui.signed_points(k['overtime_share'] - k['overtime_baseline'], 0)} vs company",
                footnote="The strongest single driver in this dataset",
            ),
            ui.stat_tile(
                "Job-satisfaction gap",
                f"{k['sat_gap']:+.2f}" if k["sat_gap"] is not None else "--",
                footnote="Leavers minus stayers, on the 1-4 scale",
            ),
        ]
        return tiles

    # --- overview -----------------------------------------------------------
    @app.callback(
        Output("fig-rate", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("ov-dim", "value"),
    )
    def render_rate(store, mode, dim_key):
        frame, min_n = _slice_for(store)
        return fg.rate_bar(frame, dm.dimension(dim_key), th.tokens(mode), min_n)

    @app.callback(
        Output("fig-matrix", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("ov-row", "value"),
        Input("ov-col", "value"),
    )
    def render_matrix(store, mode, row_key, col_key):
        frame, min_n = _slice_for(store)
        row = dm.dimension(row_key)
        col = dm.dimension(col_key, "JobLevelLabel")
        if row.key == col.key:
            return th.empty_figure(
                th.tokens(mode), "Pick two different dimensions for the grid"
            )
        return fg.risk_matrix(frame, row, col, th.tokens(mode), min_n)

    @app.callback(
        Output("tbl-segments", "children"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("ov-dim", "value"),
    )
    def render_segment_table(store, mode, dim_key):
        frame, min_n = _slice_for(store)
        return _rate_table(frame, dm.dimension(dim_key), th.tokens(mode), min_n)

    # --- distribution -------------------------------------------------------
    @app.callback(
        Output("fig-dist", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("dist-measure", "value"),
        Input("dist-norm", "value"),
    )
    def render_distribution(store, mode, measure_key, norm):
        frame, _ = _slice_for(store)
        return fg.distribution(
            frame, dm.measure(measure_key), th.tokens(mode), normalize=(norm != "count")
        )

    @app.callback(
        Output("fig-likert", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("dist-likert", "value"),
    )
    def render_likert(store, mode, dim_key):
        frame, _ = _slice_for(store)
        return fg.likert_diverging(
            frame, dm.dimension(dim_key, "JobSatisfactionLabel"), th.tokens(mode)
        )

    @app.callback(
        Output("fig-boxes", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("dist-box-measure", "value"),
        Input("dist-box-dim", "value"),
    )
    def render_boxes(store, mode, measure_key, dim_key):
        frame, min_n = _slice_for(store)
        return fg.measure_box_by_dimension(
            frame,
            dm.measure(measure_key),
            dm.dimension(dim_key, "JobLevelLabel"),
            th.tokens(mode),
            min_n,
        )

    # --- relationship -------------------------------------------------------
    @app.callback(
        Output("fig-scatter", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("rel-x", "value"),
        Input("rel-y", "value"),
        Input("rel-trend", "value"),
    )
    def render_scatter(store, mode, x_key, y_key, trend):
        frame, _ = _slice_for(store)
        return fg.relationship(
            frame,
            dm.measure(x_key, "TotalWorkingYears"),
            dm.measure(y_key),
            th.tokens(mode),
            trend=bool(trend),
        )

    @app.callback(
        Output("fig-corrbar", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("corr-measures", "value"),
    )
    def render_corr_bar(store, mode, keys):
        frame, _ = _slice_for(store)
        return fg.attrition_correlation_bar(frame, _clean_keys(keys), th.tokens(mode))

    @app.callback(
        Output("fig-corr", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("corr-measures", "value"),
    )
    def render_corr_matrix(store, mode, keys):
        frame, _ = _slice_for(store)
        return fg.correlation_heatmap(frame, _clean_keys(keys), th.tokens(mode))

    # --- composition --------------------------------------------------------
    @app.callback(
        Output("fig-treemap", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
    )
    def render_treemap(store, mode):
        frame, min_n = _slice_for(store)
        return fg.workforce_treemap(frame, th.tokens(mode), min_n)

    @app.callback(
        Output("fig-compstack", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("comp-dim", "value"),
        Input("comp-split", "value"),
    )
    def render_composition(store, mode, dim_key, split_key):
        frame, _ = _slice_for(store)
        dim = dm.dimension(dim_key, "Department")
        split = dm.dimension(split_key, "JobLevelLabel")
        if dim.key == split.key:
            return th.empty_figure(
                th.tokens(mode), "Pick a different dimension for the segments"
            )
        return fg.composition_stacked(frame, dim, split, th.tokens(mode))

    @app.callback(
        Output("fig-cohortstack", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("comp-cohort-dim", "value"),
    )
    def render_cohort_stack(store, mode, dim_key):
        frame, _ = _slice_for(store)
        return fg.cohort_stacked(frame, dm.dimension(dim_key, "TenureGroup"), th.tokens(mode))

    # --- comparison ---------------------------------------------------------
    @app.callback(
        Output("fig-smallmult", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("cmp-dim", "value"),
        Input("cmp-split", "value"),
    )
    def render_small_multiples(store, mode, dim_key, split_key):
        frame, min_n = _slice_for(store)
        dim = dm.dimension(dim_key)
        split = dm.dimension(split_key, "OverTime")
        if dim.key == split.key:
            return th.empty_figure(
                th.tokens(mode), "Pick a different dimension for the panels"
            )
        return fg.rate_small_multiples(frame, dim, split, th.tokens(mode), min_n)

    @app.callback(
        Output("fig-dumbbell", "figure"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("cmp-dumbbell-dim", "value"),
        Input("cmp-cond", "value"),
    )
    def render_dumbbell(store, mode, dim_key, cond_key):
        frame, min_n = _slice_for(store)
        dim = dm.dimension(dim_key, "Department")
        cond = dm.condition(cond_key)
        if dim.key == cond.key:
            return th.empty_figure(
                th.tokens(mode), "Pick a dimension other than the condition itself"
            )
        return fg.dumbbell(frame, dim, cond, th.tokens(mode), min_n)

    # --- tables -------------------------------------------------------------
    @app.callback(
        Output("tbl-rates", "children"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("tbl-dim", "value"),
    )
    def render_rate_table(store, mode, dim_key):
        frame, min_n = _slice_for(store)
        return _rate_table(frame, dm.dimension(dim_key), th.tokens(mode), min_n)

    @app.callback(
        Output("tbl-measures", "children"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("tbl-measure-dim", "value"),
        Input("tbl-measure", "value"),
    )
    def render_measure_table(store, mode, dim_key, measure_key):
        frame, min_n = _slice_for(store)
        return _measure_table(
            frame,
            dm.dimension(dim_key, "JobLevelLabel"),
            dm.measure(measure_key),
            th.tokens(mode),
            min_n,
        )

    @app.callback(
        Output("tbl-corr", "children"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
        Input("tbl-corr-measures", "value"),
    )
    def render_corr_table(store, mode, keys):
        frame, _ = _slice_for(store)
        return _correlation_table(frame, _clean_keys(keys), th.tokens(mode))

    @app.callback(
        Output("tbl-records", "children"),
        Input("slice-store", "data"),
        Input("theme-store", "data"),
    )
    def render_records(store, mode):
        frame, _ = _slice_for(store)
        return _record_table(frame, th.tokens(mode))

    @app.callback(
        Output("download-csv", "data"),
        Input("download-btn", "n_clicks"),
        State("slice-store", "data"),
        prevent_initial_call=True,
    )
    def download_slice(_clicks, store):
        frame, _ = _slice_for(store)
        return dcc.send_data_frame(
            frame.to_csv, "attrition_slice.csv", index=False
        )


# --- table builders -----------------------------------------------------------


def _clean_keys(keys) -> list[str]:
    """Drop the non-selectable group headings the grouped dropdowns insert."""
    if not keys:
        return []
    if isinstance(keys, str):
        keys = [keys]
    return [k for k in keys if not str(k).startswith("__") and k in dm.MEASURE_BY_KEY]


def _rate_table(frame: pd.DataFrame, dim: dm.Dimension, t: dict, min_n: int):
    data = dm.rate_by_dimension(frame, dim, min_n)
    if data.empty:
        return html.P("No employees match the current filters.", className="empty-note")

    data = data.sort_values("rate", ascending=False)
    records = [
        {
            "segment": str(row.category),
            "headcount": int(row.headcount),
            "leavers": int(row.leavers),
            "rate": f"{row.rate * 100:.1f}%",
            "lift": f"{row.lift * 100:+.1f} pts",
        }
        for row in data.itertuples()
    ]
    columns = [
        {"name": dim.label, "id": "segment"},
        {"name": "Employees", "id": "headcount"},
        {"name": "Left", "id": "leavers"},
        {"name": "Attrition rate", "id": "rate"},
        {"name": "vs company", "id": "lift"},
    ]
    return ui.data_table(records, columns, t, page_size=12)


def _measure_table(
    frame: pd.DataFrame, dim: dm.Dimension, meas: dm.Measure, t: dict, min_n: int
):
    if frame.empty:
        return html.P("No employees match the current filters.", className="empty-note")

    rows = []
    for category in dm.category_order(frame, dim):
        chunk = frame.loc[frame[dim.key].eq(category)]
        if len(chunk) < max(min_n, 1):
            continue
        stayed = chunk.loc[chunk["Cohort"].eq("Stayed"), meas.key]
        left = chunk.loc[chunk["Cohort"].eq("Left"), meas.key]
        fmt = f"{{:{meas.fmt}}}"

        def show(series: pd.Series, stat: str) -> str:
            if series.empty:
                return "--"
            value = getattr(series, stat)()
            return f"{meas.prefix}{fmt.format(value)}{meas.suffix}"

        gap = (
            left.median() - stayed.median()
            if not left.empty and not stayed.empty
            else None
        )
        rows.append(
            {
                "segment": str(category),
                "n_stayed": int(len(stayed)),
                "n_left": int(len(left)),
                "median_stayed": show(stayed, "median"),
                "median_left": show(left, "median"),
                "gap": "--" if gap is None else f"{meas.prefix}{fmt.format(gap)}{meas.suffix}",
            }
        )
    if not rows:
        return html.P("No segment is large enough to summarise.", className="empty-note")

    columns = [
        {"name": dim.label, "id": "segment"},
        {"name": "Stayed (n)", "id": "n_stayed"},
        {"name": "Left (n)", "id": "n_left"},
        {"name": f"Median {meas.label.lower()} · stayed", "id": "median_stayed"},
        {"name": f"Median {meas.label.lower()} · left", "id": "median_left"},
        {"name": "Gap (left - stayed)", "id": "gap"},
    ]
    return ui.data_table(rows, columns, t, page_size=12)


def _correlation_table(frame: pd.DataFrame, keys: list[str], t: dict):
    if frame.empty or not keys:
        return html.P("Pick at least one measure.", className="empty-note")

    correlations = dm.attrition_correlations(frame, keys)
    if correlations.empty:
        return html.P(
            "Both cohorts are needed to correlate against attrition.",
            className="empty-note",
        )

    stayed = frame.loc[frame["Cohort"].eq("Stayed")]
    left = frame.loc[frame["Cohort"].eq("Left")]
    rows = []
    for row in correlations.sort_values("corr", key=np.abs, ascending=False).itertuples():
        meas = dm.measure(row.key)
        fmt = f"{{:{meas.fmt}}}"
        rows.append(
            {
                "measure": meas.label,
                "corr": f"{row.corr:+.3f}",
                "mean_stayed": f"{meas.prefix}{fmt.format(stayed[row.key].mean())}{meas.suffix}",
                "mean_left": f"{meas.prefix}{fmt.format(left[row.key].mean())}{meas.suffix}",
            }
        )
    columns = [
        {"name": "Measure", "id": "measure"},
        {"name": "r with leaving", "id": "corr"},
        {"name": "Mean · stayed", "id": "mean_stayed"},
        {"name": "Mean · left", "id": "mean_left"},
    ]
    return ui.data_table(rows, columns, t, page_size=14)


RECORD_COLUMNS = (
    ("Cohort", "Cohort"),
    ("Department", "Department"),
    ("JobRole", "Job role"),
    ("JobLevelLabel", "Level"),
    ("Age", "Age"),
    ("Gender", "Gender"),
    ("MaritalStatus", "Marital status"),
    ("MonthlyIncome", "Monthly income"),
    ("OverTime", "Overtime"),
    ("TravelLabel", "Travel"),
    ("YearsAtCompany", "Years at company"),
    ("YearsSinceLastPromotion", "Since promotion"),
    ("JobSatisfaction", "Job satisfaction"),
    ("WorkLifeBalance", "Work-life balance"),
    ("DistanceFromHome", "Distance"),
)


def _record_table(frame: pd.DataFrame, t: dict):
    if frame.empty:
        return html.P("No employees match the current filters.", className="empty-note")

    keys = [key for key, _ in RECORD_COLUMNS]
    records = frame[keys].to_dict("records")
    columns = [{"name": name, "id": key} for key, name in RECORD_COLUMNS]
    return html.Div(
        [
            html.P(
                f"{len(frame):,} employees · showing every filtered record",
                className="table-note",
            ),
            ui.data_table(records, columns, t, page_size=15),
        ]
    )
