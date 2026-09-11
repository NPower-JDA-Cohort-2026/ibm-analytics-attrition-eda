"""Page assembly: header, the filter region, the stat-tile row and the six tabs.

Reading order is deliberate - the hero number and the tiles answer "how bad is it
in this slice", the tabs then answer "why", one analytical job per tab.
"""

from __future__ import annotations

from dash import dcc, html

import components as ui
import datamodel as dm

DIMENSION_OPTIONS = dm.grouped_options(dm.DIMENSIONS)
MEASURE_OPTIONS = dm.grouped_options(dm.MEASURES)
LIKERT_OPTIONS = [
    {"label": d.label, "value": d.key} for d in dm.DIMENSIONS if d.likert
]
CONDITION_OPTIONS = [{"label": c.label, "value": c.key} for c in dm.CONDITIONS]

#: Default set for the correlation views - the drivers the EDA notebooks land on.
DEFAULT_CORRELATION_KEYS = [
    "Age",
    "MonthlyIncome",
    "TotalWorkingYears",
    "YearsAtCompany",
    "YearsSinceLastPromotion",
    "JobLevel",
    "JobSatisfaction",
    "WorkLifeBalance",
    "StockOptionLevel",
    "DistanceFromHome",
]


def header() -> html.Header:
    return html.Header(
        [
            html.Div(
                [
                    html.P("IBM HR Analytics", className="eyebrow"),
                    html.H1("Employee attrition explorer", className="page-title"),
                    html.P(
                        "Filter the workforce by role, department, level and more - "
                        "every chart, statistic and table below re-reads the same slice.",
                        className="page-sub",
                    ),
                ],
                className="header-text",
            ),
            html.Div(
                [
                    html.Button(
                        "Dark mode",
                        id="theme-toggle",
                        n_clicks=0,
                        className="btn-ghost",
                        title="Switch between the light and dark palettes",
                    ),
                    html.Div(
                        [
                            html.Span("1,470 employees", className="meta-strong"),
                            html.Span(" · 35 attributes · fictional IBM sample dataset"),
                        ],
                        className="header-meta",
                    ),
                ],
                className="header-actions",
            ),
        ],
        className="page-header",
    )


def overview_tab() -> html.Div:
    return html.Div(
        [
            ui.chart_card(
                "Attrition rate by segment",
                "Sorted by rate, against the company-wide baseline",
                "fig-rate",
                controls=[
                    ui.select(
                        "ov-dim",
                        "Break down by",
                        DIMENSION_OPTIONS,
                        value="JobRole",
                        clearable=False,
                    )
                ],
                caption="Bars are labelled with their rate; headcount and the gap to the "
                "baseline are in the tooltip and the Tables tab.",
            ),
            ui.chart_card(
                "Risk grid",
                "Attrition rate across two dimensions at once",
                "fig-matrix",
                controls=[
                    ui.select(
                        "ov-row", "Rows", DIMENSION_OPTIONS, value="JobRole", clearable=False
                    ),
                    ui.select(
                        "ov-col",
                        "Columns",
                        DIMENSION_OPTIONS,
                        value="JobLevelLabel",
                        clearable=False,
                    ),
                ],
                caption="Cells are shaded by rate and labelled in whole percent. Blank "
                "cells fall below the minimum segment size set in the filter bar.",
            ),
            ui.table_card(
                "Segment detail",
                "The same numbers as the bar chart, sortable and exact",
                "tbl-segments",
            ),
        ],
        className="grid grid-2",
    )


def distribution_tab() -> html.Div:
    return html.Div(
        [
            ui.chart_card(
                "How one measure is distributed",
                "Share within each cohort, so the smaller leaver group stays visible",
                "fig-dist",
                controls=[
                    ui.select(
                        "dist-measure",
                        "Measure",
                        MEASURE_OPTIONS,
                        value="MonthlyIncome",
                        clearable=False,
                    ),
                    html.Div(
                        [
                            html.Label("Scale", className="ctl-label"),
                            dcc.RadioItems(
                                id="dist-norm",
                                options=[
                                    {"label": "Share of cohort", "value": "share"},
                                    {"label": "Employee count", "value": "count"},
                                ],
                                value="share",
                                className="ctl-radio",
                            ),
                        ],
                        className="ctl ctl-md",
                    ),
                ],
                caption="The box above each histogram marks the quartiles, the median and "
                "the mean. Counts are heavily imbalanced (1,233 stayers vs 237 leavers), "
                "which is why share is the default.",
            ),
            ui.chart_card(
                "Ordered-scale response",
                "Low answers to the left of centre, high answers to the right",
                "fig-likert",
                controls=[
                    ui.select(
                        "dist-likert",
                        "Scale",
                        LIKERT_OPTIONS,
                        value="JobSatisfactionLabel",
                        clearable=False,
                    )
                ],
                caption="Each row sums to 100% of that cohort. A leaver row leaning left "
                "means dissatisfaction is over-represented among people who left.",
            ),
            ui.chart_card(
                "Does the gap hold inside each segment?",
                "One box pair per category - stayers against leavers",
                "fig-boxes",
                controls=[
                    ui.select(
                        "dist-box-measure",
                        "Measure",
                        MEASURE_OPTIONS,
                        value="MonthlyIncome",
                        clearable=False,
                    ),
                    ui.select(
                        "dist-box-dim",
                        "Split by",
                        DIMENSION_OPTIONS,
                        value="JobLevelLabel",
                        clearable=False,
                    ),
                ],
                caption="A company-wide gap can be pure composition - a difference that "
                "survives inside every category is the more interesting finding.",
                wide=True,
            ),
        ],
        className="grid grid-7-5",
    )


def relationship_tab() -> html.Div:
    return html.Div(
        [
            ui.chart_card(
                "Two measures against each other",
                "One mark per employee, coloured by cohort",
                "fig-scatter",
                controls=[
                    ui.select(
                        "rel-x", "X axis", MEASURE_OPTIONS, value="TotalWorkingYears", clearable=False
                    ),
                    ui.select(
                        "rel-y", "Y axis", MEASURE_OPTIONS, value="MonthlyIncome", clearable=False
                    ),
                    html.Div(
                        [
                            html.Label("Trend", className="ctl-label"),
                            dcc.Checklist(
                                id="rel-trend",
                                options=[{"label": "Least-squares fit", "value": "on"}],
                                value=["on"],
                                className="ctl-radio",
                            ),
                        ],
                        className="ctl ctl-md",
                    ),
                ],
                caption="Measures recorded on 1-5 codes get a small horizontal jitter so "
                "overlapping employees stay countable; the tooltip always reports the "
                "true values.",
            ),
            ui.chart_card(
                "What moves with leaving",
                "Point-biserial correlation between each measure and attrition",
                "fig-corrbar",
                caption="Positive means the measure runs higher among leavers. Ordinal "
                "1-5 codes are treated as numeric, which is a convenience, not a claim.",
            ),
            ui.chart_card(
                "Correlation matrix",
                "Pairwise Pearson r - blue moves together, red moves apart",
                "fig-corr",
                controls=[
                    ui.select(
                        "corr-measures",
                        "Measures",
                        MEASURE_OPTIONS,
                        value=DEFAULT_CORRELATION_KEYS,
                        multi=True,
                        width="xl",
                        placeholder="Pick at least two measures",
                    )
                ],
                caption="Only the lower triangle is drawn - the upper half is the same "
                "numbers mirrored. Cells reaching |r| >= 0.30 are labelled; the rest are in "
                "the tooltip and the Tables tab.",
                wide=True,
            ),
        ],
        className="grid grid-7-5",
    )


def composition_tab() -> html.Div:
    return html.Div(
        [
            ui.chart_card(
                "Where the workforce sits",
                "Area is headcount, shade is attrition rate",
                "fig-treemap",
                caption="Department to job role. Roles below the minimum segment size are "
                "left out of the tiling.",
            ),
            ui.chart_card(
                "Make-up of each segment",
                "Part-to-whole within every category",
                "fig-compstack",
                controls=[
                    ui.select(
                        "comp-dim", "Rows", DIMENSION_OPTIONS, value="Department", clearable=False
                    ),
                    ui.select(
                        "comp-split",
                        "Segments",
                        DIMENSION_OPTIONS,
                        value="JobLevelLabel",
                        clearable=False,
                    ),
                ],
                caption="Segments past the eighth fold into 'Other' rather than reaching "
                "for a ninth colour. Slices under 9% carry their value in the tooltip.",
            ),
            ui.chart_card(
                "Headcount split by cohort",
                "Absolute size of the stayer and leaver groups per category",
                "fig-cohortstack",
                controls=[
                    ui.select(
                        "comp-cohort-dim",
                        "Break down by",
                        DIMENSION_OPTIONS,
                        value="TenureGroup",
                        clearable=False,
                    )
                ],
                caption="Rates hide size. This is the same population as the rate chart, "
                "counted rather than normalised - useful for judging how much a high rate "
                "is actually worth acting on.",
                wide=True,
            ),
        ],
        className="grid grid-2",
    )


def comparison_tab() -> html.Div:
    return html.Div(
        [
            ui.chart_card(
                "Same comparison, one panel per group",
                "Small multiples instead of a four-series grouped bar",
                "fig-smallmult",
                controls=[
                    ui.select(
                        "cmp-dim", "Compare", DIMENSION_OPTIONS, value="JobRole", clearable=False
                    ),
                    ui.select(
                        "cmp-split",
                        "One panel per",
                        DIMENSION_OPTIONS,
                        value="OverTime",
                        clearable=False,
                    ),
                ],
                caption="Panels share one x scale, so bar lengths are comparable across "
                "them. At most four panels are drawn; the vertical rule in each is the "
                "company baseline.",
                wide=True,
            ),
            ui.chart_card(
                "The gap a single condition makes",
                "Two dots per category, connected by the size of the gap",
                "fig-dumbbell",
                controls=[
                    ui.select(
                        "cmp-dumbbell-dim",
                        "Compare",
                        DIMENSION_OPTIONS,
                        value="Department",
                        clearable=False,
                    ),
                    ui.select(
                        "cmp-cond", "Condition", CONDITION_OPTIONS, value="OverTime", clearable=False
                    ),
                ],
                caption="Sorted by gap, widest at the top. Both ends are labelled, so the "
                "lighter shade never has to be read by colour alone.",
                wide=True,
            ),
        ],
        className="grid grid-1",
    )


def tables_tab() -> html.Div:
    return html.Div(
        [
            ui.table_card(
                "Attrition by segment",
                "The table twin of the Overview bar chart and the risk grid",
                "tbl-rates",
                controls=[
                    ui.select(
                        "tbl-dim",
                        "Break down by",
                        DIMENSION_OPTIONS,
                        value="JobRole",
                        clearable=False,
                    )
                ],
            ),
            ui.table_card(
                "Measure summary by cohort",
                "The table twin of the histogram, the boxes and the scatter",
                "tbl-measures",
                controls=[
                    ui.select(
                        "tbl-measure-dim",
                        "Rows",
                        DIMENSION_OPTIONS,
                        value="JobLevelLabel",
                        clearable=False,
                    ),
                    ui.select(
                        "tbl-measure",
                        "Measure",
                        MEASURE_OPTIONS,
                        value="MonthlyIncome",
                        clearable=False,
                    ),
                ],
            ),
            ui.table_card(
                "Correlation table",
                "The table twin of the correlation matrix and the driver bars",
                "tbl-corr",
                controls=[
                    ui.select(
                        "tbl-corr-measures",
                        "Measures",
                        MEASURE_OPTIONS,
                        value=DEFAULT_CORRELATION_KEYS,
                        multi=True,
                        width="xl",
                    )
                ],
            ),
            ui.table_card(
                "Employee records in the current slice",
                "The filtered rows themselves, sortable and paged",
                "tbl-records",
                controls=[
                    html.Div(
                        [
                            html.Button(
                                "Download slice as CSV",
                                id="download-btn",
                                n_clicks=0,
                                className="btn-ghost",
                            ),
                            dcc.Download(id="download-csv"),
                        ],
                        className="ctl ctl-md",
                    )
                ],
            ),
        ],
        className="grid grid-1",
    )


def footer() -> html.Footer:
    return html.Footer(
        [
            html.P(
                [
                    html.Strong("This dataset is fictional. "),
                    "IBM created it to demonstrate HR analytics; its rates are not "
                    "industry benchmarks and nothing here describes real employees. "
                    "The charts demonstrate method, not transferable HR conclusions.",
                ],
                className="footer-note",
            ),
            html.P(
                "Source: data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv · grouped "
                "features re-derived with the bin edges from notebook 04.",
                className="footer-meta",
            ),
        ],
        className="page-footer",
    )


def build_layout() -> html.Div:
    return html.Div(
        [
            dcc.Store(id="theme-store", data="light"),
            dcc.Store(id="slice-store", data={"filters": {}, "min_n": 10}),
            dcc.Interval(id="boot", interval=40, max_intervals=1),
            header(),
            ui.filter_bar(),
            html.Div(id="kpi-row", className="kpi-row"),
            dcc.Tabs(
                id="tabs",
                value="overview",
                className="tabs",
                parent_className="tabs-parent",
                children=[
                    dcc.Tab(
                        label="Overview",
                        value="overview",
                        children=overview_tab(),
                        className="tab",
                        selected_className="tab-selected",
                    ),
                    dcc.Tab(
                        label="Distribution",
                        value="distribution",
                        children=distribution_tab(),
                        className="tab",
                        selected_className="tab-selected",
                    ),
                    dcc.Tab(
                        label="Relationship",
                        value="relationship",
                        children=relationship_tab(),
                        className="tab",
                        selected_className="tab-selected",
                    ),
                    dcc.Tab(
                        label="Composition",
                        value="composition",
                        children=composition_tab(),
                        className="tab",
                        selected_className="tab-selected",
                    ),
                    dcc.Tab(
                        label="Comparison",
                        value="comparison",
                        children=comparison_tab(),
                        className="tab",
                        selected_className="tab-selected",
                    ),
                    dcc.Tab(
                        label="Tables",
                        value="tables",
                        children=tables_tab(),
                        className="tab",
                        selected_className="tab-selected",
                    ),
                ],
            ),
            footer(),
        ],
        className="page",
    )
