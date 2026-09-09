# Employee attrition explorer

An interactive Dash app over the IBM HR Analytics dataset. Filter the workforce by
job role, department, level and seven other attributes; every statistic, chart and
table below the filter row re-reads the same slice.

```bash
# from the project root
.venv/Scripts/python dashboards/app/app.py          # http://127.0.0.1:8050
.venv/Scripts/python dashboards/app/app.py --debug  # hot reload
.venv/Scripts/python dashboards/app/smoke_test.py   # exercise every callback
```

Requires `dash` on top of the project's existing `requirements.txt`
(`pandas`, `numpy`, `plotly`):

```bash
.venv/Scripts/python -m pip install dash
```

---

## What it shows

The app reads **`data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv`** so all 35
attributes stay available, drops the three constant columns (`EmployeeCount`,
`Over18`, `StandardHours`), and re-derives the grouped features the notebooks use.
`AgeGroup` and `TenureGroup` share the exact bin edges from
`notebooks/04-data-wrangling.ipynb`, so a number here matches a number there.

### Filters — what you asked for, plus what the data rewards

`JobRole`, `Department` and `JobLevel` were the requested three. Attrition in this
dataset is concentrated by conditions that cut *across* role and level, so the
filter row also carries the ones that actually move the rate:

| Filter | Why it earns a slot |
| :--- | :--- |
| **Overtime** | The single strongest split in the dataset — 30.5% vs 10.4% |
| **Business travel** | Frequent travellers leave at roughly twice the rate of non-travellers |
| **Marital status** | Single employees are the most over-represented demographic among leavers |
| **Gender**, **Education field** | Fairness checks — does a finding hold across groups, or is it one group? |
| **Age**, **Years at company**, **Monthly income** | Range sliders, because the risk is concentrated at the *young / new / low-paid* end rather than in any one band |

Two behaviours worth knowing:

- **Job role narrows to the departments you pick.** Choosing "Sales" leaves the
  three Sales roles selectable; impossible combinations drop out of your selection
  rather than silently returning zero rows.
- **"Hide segments smaller than"** (default: 10 employees) suppresses categories
  too small to carry a believable rate. A 100% attrition rate on two people is
  noise, and on a 1,470-row dataset sliced four ways that happens constantly.

### Tabs — one analytical job each

| Tab | Charts | The question |
| :--- | :--- | :--- |
| **Overview** | Rate bar vs baseline · risk grid heatmap · segment table | Where is attrition concentrated? |
| **Distribution** | Grouped histogram + marginal box · diverging Likert bar · box pairs per segment | How does a measure spread, and do leavers sit elsewhere in it? |
| **Relationship** | Scatter + least-squares fit · driver correlation bars · correlation matrix | What moves with what? |
| **Composition** | Treemap · 100% stacked bars · cohort headcount stack | What is this workforce made of? |
| **Comparison** | Small multiples · dumbbell | Does a gap hold across groups? |
| **Tables** | Four table twins + CSV export | The exact numbers |

Every selector in a **card header** chooses *what is plotted* — a dimension, a
measure. Every control in the **filter row** chooses *which employees* are plotted.
Keeping those two jobs in separate places is why the numbers across cards always
agree.

---

## Design notes

Charts follow the form-first method in the `dataviz` skill: pick the form from the
data's job, assign colour by the job it does, then validate.

**Forms.** Rate comparisons are horizontal bars against a baseline rule — nominal
categories get one hue, never a value-ramp, because bar length already encodes the
magnitude. Ordinal scales (the 1–4 satisfaction and work-life questions) get a
**diverging stacked bar** centred between the middle two levels, so a cohort leaning
left reads as dissatisfaction at a glance. The "compare across a second dimension"
job is served by **small multiples** rather than a four-series grouped bar, which
avoids both a label flood and a legend nobody reads. There is **no dual-axis chart**
anywhere.

**Colour.** Four jobs, four palettes: categorical for identity (the two cohorts hold
slot 1 and slot 2 *everywhere*, so filtering never repaints them), one-hue sequential
for magnitude, blue↔red diverging with a grey midpoint for correlations, and a
reserved status palette that is never used as a series colour. The categorical slots
were validated with the skill's checker rather than eyeballed:

| Palette in use | Mode | Result |
| :--- | :--- | :--- |
| 2 cohorts, all-pairs | light / dark | PASS — CVD ΔE 24.7 / 26.8 |
| 8 stacked segments, adjacent | dark | PASS on every gate |
| 8 stacked segments, adjacent | light | PASS, with a sub-3:1 contrast WARN on aqua / yellow / magenta |

That light-mode WARN triggers the **relief rule**, which is why the stacked charts
always ship a legend, in-segment value labels, and a table twin in the Tables tab.

**Marks.** Bars cap at ~18px with 4px rounded data-ends and square baselines; lines
are 2px; markers are 9px with a 2px surface ring; gridlines are solid hairlines one
step off the surface, never dashed. Touching fills are separated by a 2px gap in the
surface colour rather than a stroke. Labels ride the marks selectively — a bar's
value at its tip, and in-segment labels only where the text actually fits (segments
under 9% send their value to the tooltip and the table instead of being clipped).
Chart containers are sized from their category count so the x-axis band is always
inside the card.

**Dark mode is selected, not flipped.** The dark column is its own set of steps
chosen against the dark surface. The CSS is keyed only on `[data-theme]` — never on
`prefers-color-scheme` alone — because Plotly figures are coloured server-side from
the same token set, and a media query would let the CSS and the charts disagree about
which mode is on screen. A boot script seeds the attribute from `localStorage`, else
the OS preference, before first paint.

**No sparklines in the stat tiles.** The dataset is a cross-sectional snapshot with
no date column, so there is no trend to draw. The headcount tile carries a **meter**
(share of the workforce in view) instead, which is a ratio the data can actually
support.

---

## Files

| File | Contents |
| :--- | :--- |
| `app.py` | Dash app factory, index template, CLI entry point |
| `datamodel.py` | Loading, derived features, the dimension/measure registry, filters, aggregations |
| `figures.py` | One builder per chart |
| `theme.py` | Light and dark tokens, Plotly chrome, colourscales |
| `components.py` | Stat tiles, hero figure, chart cards, controls, tables |
| `layout.py` | Page assembly and the six tabs |
| `callbacks.py` | Callback wiring and the table builders |
| `assets/dashboard.css` | UI shell; tokens mirror `theme.py` |
| `smoke_test.py` | Fires every server-side callback across five filter scenarios |

Adding a dimension or measure means appending one entry to `DIMENSIONS` or
`MEASURES` in `datamodel.py` — every selector in the app is built from those
registries, so it appears everywhere at once.

---

## Caveats

- **The dataset is fictional.** IBM built it to demonstrate HR analytics. Its rates
  are not benchmarks and no row describes a real person. Everything here
  demonstrates method.
- **The framing is diagnostic, not predictive.** The app reports which conditions
  are over-represented among leavers and by how much. It does not score individuals,
  and it should not be used to.
- **Correlations on ordinal codes are a convenience.** The 1–5 satisfaction and
  education codes are treated as numeric in the correlation views. That is
  conventional and useful for ranking drivers, but the spacing between codes is
  assumed, not measured.
- **Small slices lie.** With 1,470 rows, a few filters can leave a handful of
  employees. The minimum-segment-size control exists for exactly this, and every
  tooltip reports its `n`.
