"""Data loading, feature derivation, the field registry and the filter/aggregation layer.

The dashboard reads the **raw** IBM extract so all 35 attributes stay available, then
re-derives the same grouped features the notebooks use (``AgeGroup``, ``TenureGroup``
share the bin edges defined in ``notebooks/04-data-wrangling.ipynb``) plus a few extra
bands the dashboard needs. Ordinal codes (1-4 satisfaction scales, education, job level)
are given their documented labels so nothing on screen reads as a bare integer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
WRANGLED_CSV = PROJECT_ROOT / "data" / "wrangled" / "HR_Employee_Attrition_Wrangled.csv"

# Columns with a single value across all 1,470 rows - they carry no information.
CONSTANT_COLUMNS = ("EmployeeCount", "Over18", "StandardHours")

SATISFACTION_LABELS = {1: "Low", 2: "Medium", 3: "High", 4: "Very High"}
SATISFACTION_ORDER = ("Low", "Medium", "High", "Very High")
WLB_LABELS = {1: "Bad", 2: "Good", 3: "Better", 4: "Best"}
WLB_ORDER = ("Bad", "Good", "Better", "Best")
EDUCATION_LABELS = {
    1: "Below College",
    2: "College",
    3: "Bachelor",
    4: "Master",
    5: "Doctor",
}
EDUCATION_ORDER = tuple(EDUCATION_LABELS.values())
TRAVEL_LABELS = {
    "Non-Travel": "No travel",
    "Travel_Rarely": "Rarely",
    "Travel_Frequently": "Frequently",
}
TRAVEL_ORDER = ("No travel", "Rarely", "Frequently")
STOCK_LABELS = {0: "None", 1: "Level 1", 2: "Level 2", 3: "Level 3"}
STOCK_ORDER = tuple(STOCK_LABELS.values())
PERFORMANCE_LABELS = {3: "Excellent", 4: "Outstanding"}
PERFORMANCE_ORDER = ("Excellent", "Outstanding")

AGE_GROUP_ORDER = ("Under 30", "30-39", "40-49", "50+")
TENURE_GROUP_ORDER = ("0-2 Years", "3-5 Years", "6-10 Years", "10+ Years")
INCOME_BAND_ORDER = ("Under $3K", "$3K-5K", "$5K-8K", "$8K-12K", "$12K+")
COMMUTE_ORDER = ("1-5", "6-10", "11-20", "21+")
PROMOTION_ORDER = ("Same year", "1 year", "2-3 years", "4-7 years", "7+ years")
COMPANIES_ORDER = ("First job", "1 before", "2-3 before", "4-5 before", "6+ before")
TRAINING_ORDER = ("0-1", "2-3", "4+")
JOB_LEVEL_ORDER = ("Level 1", "Level 2", "Level 3", "Level 4", "Level 5")

COHORT_ORDER = ("Stayed", "Left")


# --- registry types -----------------------------------------------------------


@dataclass(frozen=True)
class Dimension:
    """A categorical/ordinal column the user can break charts down by."""

    key: str
    label: str
    order: tuple[str, ...]
    group: str = "Other"
    #: ordinal scales can be drawn as a diverging stacked bar (Likert style)
    likert: bool = False


@dataclass(frozen=True)
class Measure:
    """A numeric column the user can distribute, correlate or plot."""

    key: str
    label: str
    group: str = "Other"
    fmt: str = ",.0f"
    prefix: str = ""
    suffix: str = ""
    #: histogram bin width; ``None`` lets Plotly choose
    bin_size: float | None = None


@dataclass(frozen=True)
class Filter:
    """A global filter control. ``kind`` is either ``multi`` or ``range``."""

    key: str
    label: str
    kind: str = "multi"
    options: tuple[str, ...] = field(default_factory=tuple)
    width: str = "md"


# --- load & derive ------------------------------------------------------------


def _band(series: pd.Series, bins, labels) -> pd.Series:
    return pd.cut(series, bins=bins, labels=list(labels)).astype("object")


@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    """Load the raw extract and attach the derived, human-readable features."""
    if not RAW_CSV.exists():  # pragma: no cover - deployment guard
        raise FileNotFoundError(
            f"Could not find {RAW_CSV}. Run the dashboard from the project checkout."
        )

    df = pd.read_csv(RAW_CSV)
    df = df.drop(columns=[c for c in CONSTANT_COLUMNS if c in df.columns])

    # Target, in both the label and the 0/1 forms the charts need.
    df["Cohort"] = np.where(df["Attrition"].eq("Yes"), "Left", "Stayed")
    df["AttritionFlag"] = df["Attrition"].eq("Yes").astype(int)

    # Grouped features - AgeGroup and TenureGroup use the notebook's bin edges.
    df["AgeGroup"] = _band(df["Age"], [0, 30, 40, 50, 100], AGE_GROUP_ORDER)
    df["TenureGroup"] = _band(
        df["YearsAtCompany"], [-1, 2, 5, 10, 100], TENURE_GROUP_ORDER
    )
    df["IncomeBand"] = _band(
        df["MonthlyIncome"], [0, 3000, 5000, 8000, 12000, np.inf], INCOME_BAND_ORDER
    )
    df["CommuteBand"] = _band(
        df["DistanceFromHome"], [0, 5, 10, 20, np.inf], COMMUTE_ORDER
    )
    df["PromotionWait"] = _band(
        df["YearsSinceLastPromotion"], [-1, 0, 1, 3, 7, np.inf], PROMOTION_ORDER
    )
    df["PriorCompanies"] = _band(
        df["NumCompaniesWorked"], [-1, 0, 1, 3, 5, np.inf], COMPANIES_ORDER
    )
    df["TrainingBand"] = _band(
        df["TrainingTimesLastYear"], [-1, 1, 3, np.inf], TRAINING_ORDER
    )

    # Ordinal codes -> documented labels.
    df["JobLevelLabel"] = "Level " + df["JobLevel"].astype(str)
    df["EducationLabel"] = df["Education"].map(EDUCATION_LABELS)
    df["TravelLabel"] = df["BusinessTravel"].map(TRAVEL_LABELS)
    df["StockOptionLabel"] = df["StockOptionLevel"].map(STOCK_LABELS)
    df["PerformanceLabel"] = df["PerformanceRating"].map(PERFORMANCE_LABELS)
    for col in (
        "JobSatisfaction",
        "EnvironmentSatisfaction",
        "RelationshipSatisfaction",
        "JobInvolvement",
    ):
        df[f"{col}Label"] = df[col].map(SATISFACTION_LABELS)
    df["WorkLifeBalanceLabel"] = df["WorkLifeBalance"].map(WLB_LABELS)

    return df


# --- registries ---------------------------------------------------------------

DIMENSIONS: tuple[Dimension, ...] = (
    Dimension("Department", "Department", (), "Role & org"),
    Dimension("JobRole", "Job role", (), "Role & org"),
    Dimension("JobLevelLabel", "Job level", JOB_LEVEL_ORDER, "Role & org"),
    Dimension("OverTime", "Overtime", ("No", "Yes"), "Role & org"),
    Dimension("TravelLabel", "Business travel", TRAVEL_ORDER, "Role & org"),
    Dimension("StockOptionLabel", "Stock option level", STOCK_ORDER, "Role & org"),
    Dimension("PerformanceLabel", "Performance rating", PERFORMANCE_ORDER, "Role & org"),
    Dimension("AgeGroup", "Age group", AGE_GROUP_ORDER, "Demographics"),
    Dimension("Gender", "Gender", ("Female", "Male"), "Demographics"),
    Dimension("MaritalStatus", "Marital status", ("Single", "Married", "Divorced"), "Demographics"),
    Dimension("EducationLabel", "Education", EDUCATION_ORDER, "Demographics"),
    Dimension("EducationField", "Education field", (), "Demographics"),
    Dimension("CommuteBand", "Distance from home", COMMUTE_ORDER, "Demographics"),
    Dimension("TenureGroup", "Tenure band", TENURE_GROUP_ORDER, "Tenure & pay"),
    Dimension("IncomeBand", "Monthly income band", INCOME_BAND_ORDER, "Tenure & pay"),
    Dimension("PromotionWait", "Years since promotion", PROMOTION_ORDER, "Tenure & pay"),
    Dimension("PriorCompanies", "Prior employers", COMPANIES_ORDER, "Tenure & pay"),
    Dimension("TrainingBand", "Trainings last year", TRAINING_ORDER, "Tenure & pay"),
    Dimension("JobSatisfactionLabel", "Job satisfaction", SATISFACTION_ORDER, "Sentiment", True),
    Dimension("EnvironmentSatisfactionLabel", "Environment satisfaction", SATISFACTION_ORDER, "Sentiment", True),
    Dimension("RelationshipSatisfactionLabel", "Relationship satisfaction", SATISFACTION_ORDER, "Sentiment", True),
    Dimension("JobInvolvementLabel", "Job involvement", SATISFACTION_ORDER, "Sentiment", True),
    Dimension("WorkLifeBalanceLabel", "Work-life balance", WLB_ORDER, "Sentiment", True),
)

MEASURES: tuple[Measure, ...] = (
    Measure("MonthlyIncome", "Monthly income", "Pay", ",.0f", "$", "", 1000),
    Measure("PercentSalaryHike", "Salary hike", "Pay", ".1f", "", "%", 1),
    Measure("DailyRate", "Daily rate", "Pay", ",.0f", "$", "", 100),
    Measure("HourlyRate", "Hourly rate", "Pay", ",.0f", "$", "", 5),
    Measure("MonthlyRate", "Monthly rate", "Pay", ",.0f", "$", "", 2000),
    Measure("Age", "Age", "Demographics", ".0f", "", " yrs", 2),
    Measure("DistanceFromHome", "Distance from home", "Demographics", ".0f", "", "", 2),
    Measure("TotalWorkingYears", "Total working years", "Experience", ".1f", "", " yrs", 2),
    Measure("YearsAtCompany", "Years at company", "Experience", ".1f", "", " yrs", 2),
    Measure("YearsInCurrentRole", "Years in current role", "Experience", ".1f", "", " yrs", 1),
    Measure("YearsSinceLastPromotion", "Years since promotion", "Experience", ".1f", "", " yrs", 1),
    Measure("YearsWithCurrManager", "Years with manager", "Experience", ".1f", "", " yrs", 1),
    Measure("NumCompaniesWorked", "Prior employers", "Experience", ".1f", "", "", 1),
    Measure("TrainingTimesLastYear", "Trainings last year", "Engagement", ".1f", "", "", 1),
    Measure("JobSatisfaction", "Job satisfaction (1-4)", "Engagement", ".2f", "", "", 1),
    Measure("EnvironmentSatisfaction", "Environment satisfaction (1-4)", "Engagement", ".2f", "", "", 1),
    Measure("RelationshipSatisfaction", "Relationship satisfaction (1-4)", "Engagement", ".2f", "", "", 1),
    Measure("JobInvolvement", "Job involvement (1-4)", "Engagement", ".2f", "", "", 1),
    Measure("WorkLifeBalance", "Work-life balance (1-4)", "Engagement", ".2f", "", "", 1),
    Measure("JobLevel", "Job level (1-5)", "Role & org", ".2f", "", "", 1),
    Measure("Education", "Education (1-5)", "Demographics", ".2f", "", "", 1),
    Measure("StockOptionLevel", "Stock option level (0-3)", "Role & org", ".2f", "", "", 1),
)

#: Two-level conditions usable as the two ends of a dumbbell comparison.
CONDITIONS: tuple[Dimension, ...] = (
    Dimension("OverTime", "Overtime (Yes vs No)", ("No", "Yes")),
    Dimension("Gender", "Gender", ("Female", "Male")),
    Dimension("PerformanceLabel", "Performance rating", PERFORMANCE_ORDER),
)

#: Dimensions whose categories carry a real order. These take a one-hue ordinal
#: ramp in composition charts; the rest take categorical hues. Declared here
#: rather than inferred from ``Dimension.order``, which also fixes the display
#: order of purely nominal fields like gender and marital status.
ORDINAL_DIMENSIONS = frozenset(
    {
        "JobLevelLabel",
        "OverTime",
        "TravelLabel",
        "StockOptionLabel",
        "PerformanceLabel",
        "AgeGroup",
        "EducationLabel",
        "CommuteBand",
        "TenureGroup",
        "IncomeBand",
        "PromotionWait",
        "PriorCompanies",
        "TrainingBand",
        "JobSatisfactionLabel",
        "EnvironmentSatisfactionLabel",
        "RelationshipSatisfactionLabel",
        "JobInvolvementLabel",
        "WorkLifeBalanceLabel",
    }
)


def is_ordinal(dim: Dimension) -> bool:
    return dim.key in ORDINAL_DIMENSIONS


DIMENSION_BY_KEY = {d.key: d for d in DIMENSIONS}
MEASURE_BY_KEY = {m.key: m for m in MEASURES}
CONDITION_BY_KEY = {c.key: c for c in CONDITIONS}


def dimension(key: str | None, fallback: str = "JobRole") -> Dimension:
    return DIMENSION_BY_KEY.get(key or "", DIMENSION_BY_KEY[fallback])


def measure(key: str | None, fallback: str = "MonthlyIncome") -> Measure:
    return MEASURE_BY_KEY.get(key or "", MEASURE_BY_KEY[fallback])


def condition(key: str | None, fallback: str = "OverTime") -> Dimension:
    return CONDITION_BY_KEY.get(key or "", CONDITION_BY_KEY[fallback])


def grouped_options(items) -> list[dict]:
    """Dropdown options with a non-selectable group heading per registry group."""
    options: list[dict] = []
    for group in dict.fromkeys(i.group for i in items):
        options.append({"label": f"--- {group} ---", "value": f"__{group}", "disabled": True})
        options.extend(
            {"label": i.label, "value": i.key} for i in items if i.group == group
        )
    return options


def category_order(df: pd.DataFrame, dim: Dimension) -> list[str]:
    """Declared order for ordinal dimensions; observed order otherwise."""
    if dim.order:
        present = set(df[dim.key].dropna().unique())
        return [c for c in dim.order if c in present]
    return sorted(df[dim.key].dropna().unique().tolist())


# --- filters ------------------------------------------------------------------


@lru_cache(maxsize=1)
def filter_specs() -> tuple[Filter, ...]:
    df = load_data()

    def opts(col: str, order: tuple[str, ...] = ()) -> tuple[str, ...]:
        values = df[col].dropna().unique().tolist()
        if order:
            return tuple(v for v in order if v in values)
        return tuple(sorted(values))

    return (
        Filter("Department", "Department", "multi", opts("Department"), "lg"),
        Filter("JobRole", "Job role", "multi", opts("JobRole"), "xl"),
        Filter("JobLevelLabel", "Job level", "multi", opts("JobLevelLabel", JOB_LEVEL_ORDER), "md"),
        Filter("OverTime", "Overtime", "multi", opts("OverTime", ("No", "Yes")), "sm"),
        Filter("TravelLabel", "Business travel", "multi", opts("TravelLabel", TRAVEL_ORDER), "md"),
        Filter("MaritalStatus", "Marital status", "multi", opts("MaritalStatus"), "md"),
        Filter("Gender", "Gender", "multi", opts("Gender"), "sm"),
        Filter("EducationField", "Education field", "multi", opts("EducationField"), "lg"),
        Filter("Age", "Age", "range", (), "md"),
        Filter("YearsAtCompany", "Years at company", "range", (), "md"),
        Filter("MonthlyIncome", "Monthly income", "range", (), "lg"),
    )


RANGE_BOUNDS = {
    "Age": (18, 60, 1),
    "YearsAtCompany": (0, 40, 1),
    "MonthlyIncome": (1000, 20000, 500),
}


def apply_filters(df: pd.DataFrame, selections: dict | None) -> pd.DataFrame:
    """Apply the global filter row. Empty / missing selections mean 'all'."""
    if not selections:
        return df

    mask = pd.Series(True, index=df.index)
    for spec in filter_specs():
        chosen = selections.get(spec.key)
        if spec.kind == "multi":
            if chosen:
                mask &= df[spec.key].isin(chosen)
        elif chosen and len(chosen) == 2:
            low, high = chosen
            lo, hi, _ = RANGE_BOUNDS[spec.key]
            if low > lo or high < hi:
                mask &= df[spec.key].between(low, high)
    return df.loc[mask]


def active_filter_summary(selections: dict | None) -> list[str]:
    """Human-readable chips describing what is currently scoping the view."""
    if not selections:
        return []
    chips: list[str] = []
    for spec in filter_specs():
        chosen = selections.get(spec.key)
        if spec.kind == "multi" and chosen:
            shown = ", ".join(chosen[:2])
            if len(chosen) > 2:
                shown += f" +{len(chosen) - 2}"
            chips.append(f"{spec.label}: {shown}")
        elif spec.kind == "range" and chosen and len(chosen) == 2:
            lo, hi, _ = RANGE_BOUNDS[spec.key]
            if chosen[0] > lo or chosen[1] < hi:
                chips.append(f"{spec.label}: {chosen[0]:,}-{chosen[1]:,}")
    return chips


# --- aggregation helpers ------------------------------------------------------


def baseline_rate() -> float:
    """Company-wide attrition rate, used as the reference on every rate chart."""
    return float(load_data()["AttritionFlag"].mean())


def rate_by_dimension(
    df: pd.DataFrame, dim: Dimension, min_n: int = 0
) -> pd.DataFrame:
    """Headcount, leavers and attrition rate per category of ``dim``."""
    if df.empty:
        return pd.DataFrame(columns=["category", "headcount", "leavers", "rate", "lift"])

    grouped = (
        df.groupby(dim.key, observed=True)["AttritionFlag"]
        .agg(headcount="size", leavers="sum")
        .reset_index()
        .rename(columns={dim.key: "category"})
    )
    grouped["rate"] = grouped["leavers"] / grouped["headcount"]
    grouped["lift"] = grouped["rate"] - baseline_rate()
    if min_n:
        grouped = grouped.loc[grouped["headcount"] >= min_n]

    if dim.order:
        rank = {c: i for i, c in enumerate(dim.order)}
        grouped = grouped.sort_values(
            "category", key=lambda s: s.map(rank).fillna(len(rank))
        )
    else:
        grouped = grouped.sort_values("rate")
    return grouped.reset_index(drop=True)


def rate_matrix(df: pd.DataFrame, row: Dimension, col: Dimension, min_n: int = 0):
    """Attrition-rate grid for ``row`` x ``col`` plus the matching headcounts."""
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    counts = df.pivot_table(
        index=row.key, columns=col.key, values="AttritionFlag", aggfunc="size"
    )
    leavers = df.pivot_table(
        index=row.key, columns=col.key, values="AttritionFlag", aggfunc="sum"
    )
    rates = (leavers / counts) * 100
    if min_n:
        rates = rates.where(counts >= min_n)

    rows = category_order(df, row)
    cols = category_order(df, col)
    rates = rates.reindex(index=rows, columns=cols)
    counts = counts.reindex(index=rows, columns=cols)
    return rates, counts


def composition(
    df: pd.DataFrame, dim: Dimension, split: Dimension, max_segments: int = 7
) -> pd.DataFrame:
    """Share of each ``split`` value inside each ``dim`` category.

    Segments past ``max_segments`` fold into "Other" rather than reaching for a
    ninth categorical hue.
    """
    if df.empty:
        return pd.DataFrame(columns=["category", "segment", "headcount", "share"])

    work = df[[dim.key, split.key]].copy()
    order = category_order(df, split)
    if len(order) > max_segments:
        keep = (
            work[split.key].value_counts().nlargest(max_segments).index.tolist()
        )
        keep = [c for c in order if c in keep]
        work[split.key] = work[split.key].where(work[split.key].isin(keep), "Other")
        order = keep + ["Other"]

    out = (
        work.groupby([dim.key, split.key], observed=True)
        .size()
        .reset_index(name="headcount")
        .rename(columns={dim.key: "category", split.key: "segment"})
    )
    totals = out.groupby("category", observed=True)["headcount"].transform("sum")
    out["share"] = out["headcount"] / totals
    out["segment"] = pd.Categorical(out["segment"], categories=order, ordered=True)
    return out.sort_values(["category", "segment"])


def likert_shares(df: pd.DataFrame, dim: Dimension) -> pd.DataFrame:
    """Share of each ordinal level within each cohort (for the diverging bar)."""
    if df.empty:
        return pd.DataFrame(columns=["cohort", "level", "headcount", "share"])

    out = (
        df.groupby(["Cohort", dim.key], observed=True)
        .size()
        .reset_index(name="headcount")
        .rename(columns={dim.key: "level"})
    )
    totals = out.groupby("Cohort", observed=True)["headcount"].transform("sum")
    out["share"] = out["headcount"] / totals
    out["cohort"] = pd.Categorical(out["Cohort"], categories=COHORT_ORDER, ordered=True)
    out["level"] = pd.Categorical(out["level"], categories=dim.order, ordered=True)
    return out.sort_values(["cohort", "level"])


def attrition_correlations(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Point-biserial correlation between each numeric measure and leaving."""
    if df.empty or df["AttritionFlag"].nunique() < 2:
        return pd.DataFrame(columns=["key", "label", "corr"])

    rows = []
    flag = df["AttritionFlag"]
    for key in keys:
        series = df[key]
        if series.nunique() < 2:
            continue
        rows.append({"key": key, "label": measure(key).label, "corr": float(series.corr(flag))})
    out = pd.DataFrame(rows)
    return out.sort_values("corr") if not out.empty else out


def correlation_matrix(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    usable = [k for k in keys if k in df.columns and df[k].nunique() > 1]
    if df.empty or len(usable) < 2:
        return pd.DataFrame()
    return df[usable].corr(numeric_only=True)


def ols_line(x: pd.Series, y: pd.Series) -> tuple[np.ndarray, np.ndarray] | None:
    """Least-squares fit for the scatter trend, computed without statsmodels."""
    ok = x.notna() & y.notna()
    if ok.sum() < 3 or x.loc[ok].nunique() < 2:
        return None
    slope, intercept = np.polyfit(x.loc[ok].to_numpy(float), y.loc[ok].to_numpy(float), 1)
    xs = np.linspace(float(x.loc[ok].min()), float(x.loc[ok].max()), 50)
    return xs, slope * xs + intercept


def kpi_summary(df: pd.DataFrame) -> dict[str, float | int | None]:
    """The numbers behind the stat-tile row."""
    full = load_data()
    if df.empty:
        return {
            "headcount": 0,
            "leavers": 0,
            "rate": None,
            "baseline": baseline_rate(),
            "median_income": None,
            "avg_tenure": None,
            "overtime_share": None,
            "share_of_company": 0.0,
            "income_gap": None,
            "sat_gap": None,
        }

    leavers = df.loc[df["AttritionFlag"].eq(1)]
    stayers = df.loc[df["AttritionFlag"].eq(0)]
    return {
        "headcount": int(len(df)),
        "leavers": int(len(leavers)),
        "rate": float(df["AttritionFlag"].mean()),
        "baseline": baseline_rate(),
        "median_income": float(df["MonthlyIncome"].median()),
        "median_income_baseline": float(full["MonthlyIncome"].median()),
        "avg_tenure": float(df["YearsAtCompany"].mean()),
        "avg_tenure_baseline": float(full["YearsAtCompany"].mean()),
        "overtime_share": float(df["OverTime"].eq("Yes").mean()),
        "overtime_baseline": float(full["OverTime"].eq("Yes").mean()),
        "share_of_company": len(df) / len(full),
        "income_gap": (
            float(leavers["MonthlyIncome"].median() - stayers["MonthlyIncome"].median())
            if len(leavers) and len(stayers)
            else None
        ),
        "sat_gap": (
            float(leavers["JobSatisfaction"].mean() - stayers["JobSatisfaction"].mean())
            if len(leavers) and len(stayers)
            else None
        ),
    }
