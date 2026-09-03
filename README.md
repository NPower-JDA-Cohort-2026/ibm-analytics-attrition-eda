<div align="center">

# IBM HR Analytics — Employee Attrition EDA

**An end-to-end exploratory analysis of employee attrition: which people leave, which conditions travel with them, and what an HR team could act on.**

Exploratory data analysis · KPI design · data visualization · dashboard prototypes

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](#technologies)
[![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=flat-square&logo=jupyter&logoColor=white)](#technologies)
[![pandas](https://img.shields.io/badge/pandas-150458?style=flat-square&logo=pandas&logoColor=white)](#technologies)
[![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white)](#technologies)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=flat-square)](#technologies)
[![seaborn](https://img.shields.io/badge/seaborn-4C72B0?style=flat-square)](#technologies)
[![Excel](https://img.shields.io/badge/Excel-217346?style=flat-square&logo=microsoftexcel&logoColor=white)](#technologies)

[![Records](https://img.shields.io/badge/records-1%2C470-informational?style=flat-square)](#dataset)
[![Features](https://img.shields.io/badge/features-35-informational?style=flat-square)](#schema)
[![Attrition rate](https://img.shields.io/badge/attrition-16.1%25-orange?style=flat-square)](#class-balance)
[![Status](https://img.shields.io/badge/status-in%20progress-yellow?style=flat-square)](#roadmap)

</div>

---

## Overview

Attrition is expensive and mostly invisible until it has already happened. Replacing a mid-level employee costs a meaningful multiple of their salary once recruiting, onboarding, lost productivity, and institutional knowledge are counted — and the signals that precede a resignation are usually sitting in HR data that nobody has cross-tabulated.

This project takes IBM's HR Analytics dataset — 1,470 employee records across 35 attributes — and works it end to end: profiling and cleaning, univariate and bivariate exploration, segment-level attrition rates, and a set of visualizations and dashboard prototypes designed to be read by someone who does not know pandas.

The framing is deliberately **diagnostic rather than predictive**. The primary question is not "can we guess who quits" but "which conditions are over-represented among leavers, by how much, and is the gap large enough to act on."

> [!IMPORTANT]
> This dataset is **fictional**, created by IBM data scientists to demonstrate HR analytics. It does not describe real employees and its rates are not industry benchmarks. Findings here demonstrate _method_ — they are not transferable HR conclusions. See [Caveats and Ethics](#caveats-and-ethics).

---

## Dataset

|                    |                                                                                                                                                     |
| :----------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Source**         | [IBM HR Analytics Employee Attrition & Performance](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset/data) — Kaggle |
| **Publisher**      | `pavansubhasht`, originally authored by IBM                                                                                                         |
| **File**           | `WA_Fn-UseC_-HR-Employee-Attrition.csv` — a single flat table, commonly opened and analysed in Excel                                                |
| **Shape**          | 1,470 rows × 35 columns; one row per employee                                                                                                       |
| **Grain**          | Cross-sectional snapshot — **no date or event-timestamp column**                                                                                    |
| **Target**         | `Attrition` — `Yes` / `No`                                                                                                                          |
| **Missing values** | None                                                                                                                                                |
| **License**        | Kaggle lists the dataset under an open database licence; confirm the current terms on the dataset page before redistributing the raw file           |

### Schema

35 columns, grouped by what they are for rather than by dtype.

| Group                | Columns                                                                                                                                                       |
| :------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Target**           | `Attrition`                                                                                                                                                   |
| **Demographics**     | `Age`, `Gender`, `MaritalStatus`, `Education`, `EducationField`, `DistanceFromHome`                                                                           |
| **Role & org**       | `Department`, `JobRole`, `JobLevel`, `BusinessTravel`, `OverTime`                                                                                             |
| **Compensation**     | `MonthlyIncome`, `HourlyRate`, `DailyRate`, `MonthlyRate`, `PercentSalaryHike`, `StockOptionLevel`                                                            |
| **Tenure & history** | `YearsAtCompany`, `TotalWorkingYears`, `YearsInCurrentRole`, `YearsSinceLastPromotion`, `YearsWithCurrManager`, `NumCompaniesWorked`, `TrainingTimesLastYear` |
| **Survey / ordinal** | `JobSatisfaction`, `EnvironmentSatisfaction`, `RelationshipSatisfaction`, `JobInvolvement`, `WorkLifeBalance`, `PerformanceRating`                            |
| **Identifier**       | `EmployeeNumber`                                                                                                                                              |
| **Constant — drop**  | `EmployeeCount` (always 1), `StandardHours` (always 80), `Over18` (always `Y`)                                                                                |

**Ordinal codebook.** Survey fields arrive as integers with no labels attached; decoding them is a required cleaning step, not a nicety, because unlabelled `1–4` axes are unreadable on a dashboard.

| Field                                                                                      | Scale                                                          |
| :----------------------------------------------------------------------------------------- | :------------------------------------------------------------- |
| `Education`                                                                                | 1 Below College · 2 College · 3 Bachelor · 4 Master · 5 Doctor |
| `JobSatisfaction`, `EnvironmentSatisfaction`, `RelationshipSatisfaction`, `JobInvolvement` | 1 Low · 2 Medium · 3 High · 4 Very High                        |
| `WorkLifeBalance`                                                                          | 1 Bad · 2 Good · 3 Better · 4 Best                             |
| `PerformanceRating`                                                                        | 1 Low · 2 Good · 3 Excellent · 4 Outstanding                   |
| `JobLevel`                                                                                 | 1 (entry) → 5 (senior)                                         |
| `StockOptionLevel`                                                                         | 0 (none) → 3                                                   |

### Data quality notes to verify during profiling

These are the checks worth running first, because each one changes how a later chart must be built:

1. **Three constant columns** carry zero information — drop them and say so in the notebook.
2. **`PerformanceRating` is effectively binary** — only the top two values appear in practice, so "performance" here is a coarse high/very-high split, not a 4-point scale. Any "do we lose our top performers" KPI must be framed around that limitation.
3. **Four separate rate fields** (`HourlyRate`, `DailyRate`, `MonthlyRate`, `MonthlyIncome`) are not mutually consistent — they do not reconcile arithmetically. Check their correlation with `MonthlyIncome` and pick one compensation measure to standardise on rather than plotting all four.
4. **`EmployeeNumber` is a sparse identifier**, not a feature — exclude it from every correlation matrix and model.
5. **`MonthlyIncome` is right-skewed** and tightly coupled to `JobLevel` and `JobRole`. Comparing raw income between leavers and stayers company-wide confounds pay with seniority; compare **within** role and level.
6. **Collinear tenure block** — the five `Years*` fields plus `Age` move together. Expect a dense corner in the correlation matrix and treat it as one construct.

---

## Analysis Questions

Grouped by the decision each one would inform.

**Where is attrition concentrated?**

- Which job roles, departments, and job levels exceed the 16.1% baseline, and by enough to matter given their headcount?
- Is attrition an early-tenure phenomenon, a mid-career phenomenon, or both?

**What conditions travel with leaving?**

- How much does `OverTime` shift the rate, and does it survive controlling for role and level?
- Does travel frequency carry an independent signal, or is it a proxy for sales roles?
- Do commute distance, promotion stagnation, and manager tenure each move the needle on their own?

**Does compensation explain it?**

- Within the same role and level, do leavers earn less than stayers?
- Do salary hike and stock option level behave like retention levers, or are they confounded by performance and seniority?

**Does the survey data see it coming?**

- Which of the four satisfaction dimensions separates leavers from stayers most cleanly?
- Is low satisfaction concentrated in the same segments as high attrition, or are they different populations?

**Is the attrition costly or benign?**

- What share of leavers are high performers at senior levels — the losses actually worth spending money to prevent?

---

## KPI Ideas

Candidate metrics for the analysis and the dashboards. Each is computable from this dataset _except_ where marked, and each names its denominator — an attrition "rate" with an unstated denominator is the fastest way to mislead a stakeholder.

### Tier 1 — Headline

| KPI                          | Definition                                                              | Why it earns a slot                                             |
| :--------------------------- | :---------------------------------------------------------------------- | :-------------------------------------------------------------- |
| **Attrition rate**           | Leavers ÷ total headcount                                               | The anchor number every other figure is compared against        |
| **Headcount**                | Row count                                                               | Denominator context; prevents over-reading thin segments        |
| **Early attrition rate**     | Leavers with `YearsAtCompany ≤ 2` ÷ employees with `YearsAtCompany ≤ 2` | Isolates hiring/onboarding failure from long-term disengagement |
| **Regretted attrition rate** | Leavers with top `PerformanceRating` ÷ all top-rated employees          | Not all attrition is a loss — this separates the expensive kind |
| **Senior attrition rate**    | Leavers at `JobLevel ≥ 3` ÷ employees at `JobLevel ≥ 3`                 | Weights the metric by replacement difficulty                    |
| **Median tenure at exit**    | Median `YearsAtCompany` among leavers                                   | Tells you _when_ in the lifecycle to intervene                  |

### Tier 2 — Driver / diagnostic

| KPI                                 | Definition                                                                            | Reads as                                                           |
| :---------------------------------- | :------------------------------------------------------------------------------------ | :----------------------------------------------------------------- |
| **Overtime attrition lift**         | Rate(`OverTime=Yes`) ÷ Rate(`OverTime=No`)                                            | A multiplier — the single most quotable diagnostic in this dataset |
| **Segment lift vs baseline**        | Rate(segment) − 16.1%, in percentage points                                           | Signed gap; the input to every diverging chart below               |
| **Within-band pay gap**             | Median `MonthlyIncome` of stayers − leavers, computed _within_ `JobRole` × `JobLevel` | Whether pay is a driver once seniority is held constant            |
| **Promotion stagnation rate**       | Attrition rate by `YearsSinceLastPromotion` band (0–1, 2–3, 4–7, 8+)                  | Whether the pipeline is stalling                                   |
| **Manager-tenure effect**           | Attrition rate by `YearsWithCurrManager` band                                         | Isolates a lever a company can actually pull                       |
| **Commute sensitivity**             | Attrition rate by `DistanceFromHome` band                                             | Cheap to act on (hybrid policy, site assignment)                   |
| **Composite satisfaction index**    | Mean of the four satisfaction fields, 1–4                                             | One readable number instead of four correlated ones                |
| **Role mobility ratio**             | `YearsInCurrentRole` ÷ `YearsAtCompany`                                               | High and rising = stuck in seat                                    |
| **Job-hopping propensity**          | `NumCompaniesWorked` ÷ `TotalWorkingYears`                                            | Prior mobility as a behavioural prior                              |
| **Training coverage**               | Attrition rate by `TrainingTimesLastYear`                                             | Tests whether investment tracks retention                          |
| **Stock option retention gradient** | Attrition rate by `StockOptionLevel` (0–3)                                            | A monotonic gradient here is a direct policy argument              |

### Tier 3 — Modelled or assumption-driven

Flagged separately because they depend on inputs the dataset does not contain. State the assumption on the chart itself, in the visible caption — not in a footnote.

| KPI                             | Notes                                                                                                                                                                                              |
| :------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Estimated cost of attrition** | Σ (leaver `MonthlyIncome` × 12 × replacement-cost multiplier). Requires an assumed multiplier — expose it as a **user-adjustable input**, not a hardcoded constant, and show the number as a range |
| **Flight-risk score**           | Predicted probability from a classifier; see [Modelling Extension](#modelling-extension)                                                                                                           |
| **Watchlist precision@k**       | Of the top _k_ highest-risk employees, the share who actually left — the only score metric an HR partner cares about                                                                               |
| **Retention ROI**               | Cost avoided ÷ cost of intervention, at a chosen risk threshold                                                                                                                                    |

### KPIs this dataset cannot support

Stating these explicitly is part of the deliverable — it demonstrates knowing the difference between a metric that is hard and one that is impossible.

- ❌ Monthly / quarterly / rolling attrition trend, YoY change, seasonality — **no date column**
- ❌ Voluntary vs involuntary split — `Attrition` is undifferentiated
- ❌ Time-to-fill, offer acceptance, absenteeism, internal transfer rate — not collected
- ❌ Exit reason analysis — no free-text or reason code
- ❌ True survival / hazard curves — no observation window or censoring information

---

## Visualization Ideas

### Core charts

| Job the reader must do                              | Form                                                                                                  | Colour                              |
| :-------------------------------------------------- | :---------------------------------------------------------------------------------------------------- | :---------------------------------- |
| Rank attrition across 9 job roles                   | **Horizontal bar**, sorted descending — long names need the horizontal axis                           | Sequential, one hue                 |
| See who is above / below the 16.1% baseline         | **Diverging bar** of signed lift in percentage points, centred on zero                                | Diverging, two hues + grey midpoint |
| Read attrition across two dimensions at once        | **Heatmap** — `JobRole` × `OverTime`, or `Department` × `JobLevel`, cells annotated with rate _and_ n | Sequential, one hue                 |
| Compare survey distributions for leavers vs stayers | **Diverging stacked bar**, centred on the neutral point of the 1–4 scale                              | Diverging                           |
| Show the pay gap per role                           | **Dumbbell** — median income of stayers vs leavers, one row per role                                  | One hue, two shades                 |
| Make the overtime finding unmissable                | **Emphasis** — overtime cohort in the accent hue, everything else grey                                | 1 hue + grey                        |
| Compare age / income / tenure shapes                | **Overlaid histogram or box plot** by attrition status                                                | 2 categorical                       |
| Show attrition across the tenure axis               | **Line** over `YearsAtCompany` bands, explicitly captioned as workforce composition                   | Sequential                          |
| Show the numeric feature relationships              | **Correlation heatmap**, diverging around zero, tenure block grouped                                  | Diverging                           |
| Break a driver down by department                   | **Small multiples** — tenure-band attrition, one panel per department                                 | 1 hue across panels                 |
| Present all 9 roles × 6 metrics                     | **Table** with inline bars — past ~7 categories a table beats more colour                             | Ink, not hue                        |

### Accessibility requirements

Non-negotiable for anything that goes in the portfolio:

- Categorical palettes **validated for colour-vision deficiency**, computed rather than eyeballed.
- **Dark mode selected**, not auto-inverted — its own steps from the same ramps.
- A **table view** available behind every chart.
- Hover tooltip on every interactive mark; crosshair on line charts.
- Every axis labelled with units; every rate paired with its denominator.

---

## Dashboard Concepts

Four prototypes, ordered by audience. Each answers a different question and stands alone — a single dashboard trying to serve all four audiences serves none.

### 1 · Executive Overview — _"How bad is it and where?"_

Audience: HR director. One screen, no scrolling, readable in thirty seconds.

```
┌──────────────────────────────────────────────────────────────┐
│  [ filters: Department · Job Level · Overtime ]              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│      16.1%          ┌─── KPI row ─────────────────────┐      │
│    ATTRITION        │ 1,470 head · 237 left           │      │
│    RATE             │ early 27%* · regretted 15%*     │      │
│   (hero figure)     │ median tenure at exit: 3 yrs*   │      │
│                     └─────────────────────────────────┘      │
├───────────────────────────────┬──────────────────────────────┤
│  Attrition rate by job role   │  Lift vs baseline            │
│  (horizontal bar, sorted, n)  │  (diverging bar, ±pp)        │
├───────────────────────────────┴──────────────────────────────┤
│  Top risk segments — role × condition, rate, n, lift (table) │
└──────────────────────────────────────────────────────────────┘
                                        * to be computed
```

### 2 · Driver Diagnostics — _"Why are they leaving?"_

Audience: HR business partner. One panel per hypothesis, each with the baseline drawn on it.

- **Overtime** — emphasis bar, the lift multiplier called out as a large number
- **Travel** — attrition rate by `BusinessTravel`, faceted by department to expose the sales confound
- **Promotion stagnation** — rate by `YearsSinceLastPromotion` band
- **Manager tenure** — rate by `YearsWithCurrManager` band
- **Commute** — rate by `DistanceFromHome` band
- **Satisfaction** — diverging stacked bars, four dimensions, leavers vs stayers side by side
- **Tenure composition** — line over `YearsAtCompany`, captioned for what it is

### 3 · Compensation & Equity — _"Is this a pay problem?"_

Audience: comp & benefits. Every view controls for seniority — that is the entire point of the tab.

- Dumbbell: median income, stayers vs leavers, **within** each `JobRole`
- Heatmap: attrition rate across `JobLevel` × income quartile
- `PercentSalaryHike` band vs attrition rate, split by `PerformanceRating`
- `StockOptionLevel` gradient — the cleanest policy argument available here
- **Pay-band distribution by gender within role and level**, presented as a descriptive observation with explicit sample sizes and confidence caveats. This is a fairness _audit_ view, not an input to any decision about an individual.

### 4 · Retention Risk Explorer — _"Who, and what would it cost?"_

Audience: analytics team. Model-backed, and the only tab where individual-level scores appear.

- Flight-risk score distribution, with the decision threshold as a movable line
- Feature contribution bar chart — global importance, honest about collinearity in the tenure block
- Watchlist table above the threshold: role, level, tenure, top contributing factors, score
- Precision / recall at threshold, plus a confusion matrix
- **Cost calculator** — replacement multiplier and intervention cost as visible inputs, outputting a range

> [!CAUTION]
> A watchlist of named individuals is the point at which an analytics exercise becomes an HR decision system. Even on fictional data, build it with the guardrails the real thing would need: no protected attributes as predictors, a documented threshold rationale, and a stated human-review requirement. See [Caveats and Ethics](#caveats-and-ethics).

### Implementation options

| Tool                        | Fit                                                                                                                                                |
| :-------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Excel**                   | Pivot tables, slicers, and a linked dashboard sheet — the fastest credible prototype, and it keeps the analysis legible to non-technical reviewers |
| **Power BI / Tableau**      | Cross-filtering, drill-through, and calculated measures; the closest to what an HR team would actually receive                                     |
| **Plotly Dash / Streamlit** | Python-native, version-controllable, and the natural home for the live cost calculator and model threshold slider                                  |
| **Static HTML**             | A single self-contained file — the most reliable thing to link from a portfolio, since it renders anywhere with no runtime                         |

> [!TIP]
> Building the **same** dashboard in two tools — Excel and one code-based option — is a stronger portfolio piece than two different dashboards. It demonstrates tool judgement rather than tool count.

---

## Modelling Extension

Optional, and secondary to the EDA. If included, the point is **interpretability**, not leaderboard score.

- **Baseline first** — always predict "stays" scores ≈83.9% accuracy. Any model must beat that or be discarded, which is exactly why accuracy is the wrong metric here.
- **Report precision, recall, and PR-AUC.** With a 16% positive class, ROC-AUC flatters a model that finds almost nobody. Precision@k mirrors how a watchlist is actually used.
- **Logistic regression as the primary model** — coefficients and odds ratios are directly quotable to a stakeholder. Gradient boosting only as a benchmark to show what accuracy is being traded away.
- **Handle imbalance explicitly** — class weights over synthetic oversampling, and never resample before the split.
- **Exclude `Gender`, `Age`, `MaritalStatus`** from any model producing individual-level scores, and document the exclusion. Keep them in the _descriptive_ analysis where fairness auditing requires them.
- **Split before anything else.** Encode, scale, and bin inside a pipeline fitted on train only.

---

## Roadmap

| Phase | Deliverable                                                                       | Status     |
| :---- | :-------------------------------------------------------------------------------- | :--------- |
| 00    | Understanding IBM HR Analytics Employee Attrition Dataset                         | ⏳ Planned |
| 01    | Data acquisition and profiling — dtypes, constants, distributions, quality checks | ⏳ Planned |
| 02    | Cleaning and feature prep — drop constants, decode ordinals, derive tenure bands  | ⏳ Planned |
| 03    | Univariate exploration — distributions and category frequencies                   | ⏳ Planned |
| 04    | Bivariate analysis — segment attrition rates against the baseline, with n         | ⏳ Planned |
| 05    | Driver deep-dives — overtime, compensation, promotion, manager, commute           | ⏳ Planned |
| 06    | Visualization pass — final figures, validated palette, light and dark             | ⏳ Planned |
| 07    | Dashboard build — Excel prototype, then a code-based version                      | ⏳ Planned |
| 08    | Optional model — interpretable classifier and risk explorer                       | ⏳ Planned |
| 09    | Findings write-up — one page, ranked by actionability                             | ⏳ Planned |

---

## Repository Structure

Planned layout; directories appear as each phase lands.

```
ibm-analytics-attrition-eda/
├── data/
│   ├── raw/                  # IBM HR Analytics Employee Attrition & Performance CSV file
│   └── processed/            # Cleaned, decoded outputs
├── notebooks/
│   ├── 00-understanding-data.ipynb
│   ├── 01-data-profiling.ipynb
│   ├── 02-cleaning-feature-prep.ipynb
│   ├── 03-univariate-exploration.ipynb
│   ├── 04-attrition-by-segment.ipynb
│   ├── 05-driver-deep-dives.ipynb
│   └── 06-final-figures.ipynb
├── dashboards/
│   ├── excel/                # Workbook with pivots and slicers
│   └── app/                  # Dash / Streamlit application
├── reports/
│   ├── figures/              # Exported charts, light and dark
│   └── findings.md           # Ranked conclusions with caveats
├── requirements.txt
└── README.md
```

---

## Getting Started

**Clone and set up the environment.**

```bash
git clone https://github.com/NPower-JDA-Cohort-2026/ibm-analytics-attrition-eda.git
cd [Work_Directory]/ibm-analytics-attrition-eda

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Notebooks are numerically prefixed and intended to be run in order.

---

## Run in Google Colab

No local install, no virtual environment, no VS Code. Colab gives every team member the same Python environment in the browser, which makes it the fastest way to read, run, or review a notebook — and the easiest way to help a teammate who is stuck on a setup problem.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NPower-JDA-Cohort-2026/ibm-analytics-attrition-eda/blob/main/notebooks/00-understanding-data.ipynb)

### Open a notebook

**Option A — the badge.** Click the badge above. It opens `00-understanding-data.ipynb` from the `main` branch directly.

**Option B — the URL pattern.** Any notebook in the repository can be opened by swapping the filename:

```
https://colab.research.google.com/github/NPower-JDA-Cohort-2026/ibm-analytics-attrition-eda/blob/main/notebooks/<NOTEBOOK-NAME>.ipynb
```

**Option C — the Colab file picker.** In Colab, go to **File → Open notebook → GitHub**, paste `NPower-JDA-Cohort-2026/ibm-analytics-attrition-eda`, and pick the notebook from the list. Tick **Include private repos** and authorise GitHub if the repository is not public for you yet.

> [!IMPORTANT]
> Opening a notebook this way gives you a **scratch copy**. Editing it does **not** change the repository, and closing the tab loses your work unless you save it. Use **File → Save a copy in Drive** to keep it, or see [Saving your work back to GitHub](#saving-your-work-back-to-github) below.

### Install the dependencies

Colab ships with pandas, NumPy, Matplotlib, and seaborn already installed, so most notebooks run as-is. To match the exact versions this project was built against, run this as the first cell:

```python
!pip install -q -r https://raw.githubusercontent.com/NPower-JDA-Cohort-2026/ibm-analytics-attrition-eda/main/requirements.txt
```

If that pull is slow or a pin conflicts with Colab's preinstalled stack, install only what the notebooks actually import:

```python
!pip install -q pandas numpy matplotlib seaborn plotly
```

### Get the data into the session

Colab runtime starts empty. Pick one of the two routes below.

**1 · Manual upload — simplest, fine for a one-off session.**

```python
from google.colab import files
import pathlib

pathlib.Path("data/raw").mkdir(parents=True, exist_ok=True)
uploaded = files.upload()          # choose WA_Fn-UseC_-HR-Employee-Attrition.csv

for name in uploaded:
    pathlib.Path(name).rename(f"data/raw/{name}")
```

**2 · Google Drive — best if you will run notebooks more than once.** Upload the CSV to your Drive once, then mount it in every session:

```python
from google.colab import drive
import pathlib, shutil

drive.mount("/content/drive")

pathlib.Path("data/raw").mkdir(parents=True, exist_ok=True)
shutil.copy(
    "/content/drive/MyDrive/ibm-hr-attrition/WA_Fn-UseC_-HR-Employee-Attrition.csv",
    "data/raw/",
)
```

### Keep the file paths working

Notebooks read the data with a relative path such as `data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv`. Locally that resolves because the notebook lives in `notebooks/`; in Colab the working directory is `/content`. The snippets above already write to `/content/data/raw/`, which is why they use `data/raw` and not `../data/raw`. If a notebook fails with `FileNotFoundError`, check where the file actually landed:

```python
import os
print(os.getcwd())
!ls -R data
```

### Saving your work back to GitHub

Colab can commit for you: **File → Save a copy in GitHub**. It asks for the repository, the branch, and a commit message, and it pushes the notebook as one commit.

Two rules for the team when using it:

- **Never save to `main` from Colab.** Type a feature branch name in the branch field — Colab creates it if it does not exist. See [Team Git Workflow](#team-git-workflow).
- **Write the commit message properly.** The dialog is a normal commit message box, so the [Conventional Commits](#commit-message-convention) format applies there too.

> [!TIP]
> Colab notebooks carry heavy execution metadata and can generate large, unreviewable diffs. Before saving back to GitHub, **Runtime → Restart and run all** so the outputs are clean and in order, and mention in the commit body that the notebook was run top to bottom.

### What Colab will not do for you

| Limitation                   | What it means for this project                                                                                  |
| :--------------------------- | :-------------------------------------------------------------------------------------------------------------- |
| Runtime is temporary         | Files, installs, and the mounted CSV vanish when the session disconnects — re-run the setup cells each time     |
| Idle disconnect              | Long unattended runs get dropped; keep notebooks quick and restartable                                          |
| No project virtual env       | Package versions are Colab's unless you pin them with the `requirements.txt` cell above                         |
| Excel dashboards do not open | Phase 07's Excel workbook needs a desktop spreadsheet application                                               |
| Dash / Streamlit apps        | Runnable only with a tunnel workaround; treat the local environment as the supported path for `dashboards/app/` |

---

## Team Git Workflow

### The loop

**1 · Update `main` before starting.** - Before starting new work, make sure your local main is up to date.

```bash
git switch main
git pull origin main
```

`--rebase` replays your local commits on top of the remote instead of manufacturing a "Merge branch 'main'" commit, which keeps the shared history readable.

**2 · Branch for your work.** Do not commit directly to `main`.

```bash
git switch -c feat/04-attrition-by-segment
```

Branch naming mirrors the commit types below: `feat/…`, `fix/…`, `docs/…`, `chore/…`. Include the notebook or phase number when the work maps to one.

**3 · Make your change on your branch.** Keep each branch focused on one task.

For example:

Good: Add attrition analysis by job role
Avoid: Add attrition analysis + redesign README + update dependencies

**4 · Stage the files you want to commit.** Add only the files related to your task.

```bash
git add notebooks/04-attrition-by-segment.ipynb
git add reports/figures/attrition-by-role.png

git diff --staged        # last look at exactly what will be committed
```

**5 · Commit with a real message.** Format and rationale in [Commit Message Convention](#commit-message-convention).

```bash
git commit -m "feat(04): add attrition rate by job role and level"
```

Commit in small, working steps. Several focused commits are easier to review — and to revert.

**6 · Pull once more, then push.** Someone almost certainly pushed while you were working.

```bash
git pull origin main
git push -u origin feat/04-attrition-by-segment
```

**7 · Open a pull request** against `main`, describe what changed. Merge after approval, then clean up:

```bash
git switch main
git pull origin main
git branch -d feat/04-attrition-by-segment
```

### When something goes wrong

| Situation                             | Command                                                                                      |
| :------------------------------------ | :------------------------------------------------------------------------------------------- |
| Push rejected — remote has new work   | `git pull --rebase origin main`, resolve, then push again                                    |
| Staged a file by mistake              | `git restore --staged <file>` — unstages it, keeps your edits                                |
| Discard uncommitted edits to a file   | `git restore <file>` — **destructive**, the edits are gone                                   |
| Wrong commit message, not pushed yet  | `git commit --amend -m "<correct message>"`                                                  |
| Undo the last commit, keep the work   | `git reset --soft HEAD~1`                                                                    |
| Need to switch branches mid-change    | `git stash` → switch → `git stash pop`                                                       |
| Notebook conflict you cannot untangle | Keep one version: `git checkout --theirs <notebook>` or `--ours`, re-run it, commit, explain |

---

## Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/). The point is not ceremony — it is that `git log --oneline` becomes a readable changelog, and a reviewer can tell what a commit does before opening it.

```
<type>(<scope>): <short summary in the imperative mood>

<optional body — why the change was made, not what it did>
```

Rules that make the format worth following:

- **Type is lower-case and required.** Scope is optional but strongly encouraged — use the notebook number (`04`), the directory (`dashboards`), or the area (`readme`).
- **Summary is imperative and under ~72 characters.** "add segment rates", not "added" or "adds".
- **No trailing period.** No capital letter after the colon.
- **One logical change per commit.** If the summary needs "and", split it.
- **Use the body for the _why_.** The diff already shows what changed; it cannot show what you were thinking.

### Types used by this team

| Type       | Use it for                                                   | Example                                                         |
| :--------- | :----------------------------------------------------------- | :-------------------------------------------------------------- |
| `feat`     | New analysis, notebook, chart, KPI, or dashboard view        | `feat(05): add overtime attrition lift with baseline reference` |
| `fix`      | Correcting a wrong result, broken code, or bad calculation   | `fix(04): use segment denominator instead of total headcount`   |
| `docs`     | README, findings write-up, markdown cells, docstrings        | `docs(readme): add Google Colab setup instructions`             |
| `refactor` | Restructuring code with no change to the output              | `refactor(02): extract ordinal decoding into a helper function` |
| `style`    | Formatting, palette, labels, layout — nothing behavioural    | `style(06): apply colour-vision-safe palette to role charts`    |
| `chore`    | Dependencies, `.gitignore`, repo scaffolding, housekeeping   | `chore: pin pandas to 3.0.5 in requirements.txt`                |
| `data`     | Data acquisition, cleaning outputs, schema or codebook edits | `data(02): drop constant columns and write processed snapshot`  |
| `test`     | Validation checks and assertions on the analysis             | `test(04): assert segment rates sum to the overall baseline`    |
| `perf`     | Making something meaningfully faster                         | `perf(03): vectorise tenure banding instead of iterating rows`  |
| `revert`   | Undoing a previous commit                                    | `revert: feat(08) flight-risk score prototype`                  |

### Worked examples

Good — scoped, imperative, one idea, and the body carries the reasoning:

```
feat(05): add within-role pay gap dumbbell chart

Company-wide income comparison confounds pay with seniority, so the
gap is computed inside each JobRole x JobLevel cell. Cells with fewer
than 20 employees are flagged rather than plotted.
```

```
fix(04): correct attrition rate denominator for job role

Rates were dividing by total headcount instead of the role's own
headcount, which understated every role. Sales Representative moves
from 6.5% to 39.8%.
```

```
docs(readme): document Colab data-loading routes
```

> [!TIP]
> Before committing, read your message back as the sentence _"This commit will \_\_\_."_ If it does not complete that sentence, rewrite it.

---

## Technologies

| Technology                           | Role                                                   |
| :----------------------------------- | :----------------------------------------------------- |
| **Python**                           | Analysis language                                      |
| **pandas**                           | Loading, cleaning, grouping, cross-tabulation          |
| **NumPy**                            | Numeric operations and binning                         |
| **Matplotlib**                       | Figure composition and export                          |
| **seaborn**                          | Statistical plots and distribution comparison          |
| **Jupyter Lab**                      | Exploratory environment                                |
| **Microsoft Excel**                  | Pivot-table analysis and the first dashboard prototype |
| **Plotly / Dash** _or_ **Streamlit** | Interactive dashboard and risk explorer                |
| **scikit-learn**                     | Optional interpretable classifier                      |

---

## Caveats and Ethics

**The data is fictional.** IBM authored it as a teaching set. Nothing here describes real people, and no rate in it should be cited as an industry benchmark. Any conclusion stated in this repository is a statement about _this dataset_ and about the method used on it.

**Correlation is not cause.** Overtime co-occurring with attrition does not establish that overtime causes attrition. With a single cross-sectional snapshot and no experiment, the honest ceiling is "this condition is over-represented among leavers by _n_ percentage points." Findings are worded that way throughout.

**Attrition modelling on people is consequential.** Even as a portfolio exercise, an individual-level risk score is the kind of artefact that, in production, shapes who gets promoted, invested in, or quietly written off. This project therefore:

- keeps `Gender`, `Age`, and `MaritalStatus` out of any model that scores individuals — using protected or proxy attributes to predict who might leave is both legally fraught and self-fulfilling;
- retains those attributes in the **descriptive** analysis, because you cannot audit for disparity in a variable you refused to look at;
- treats every score as an input to a conversation with a human, never as a decision;
- reports segment sizes on every rate, so a finding built on eight people cannot masquerade as a pattern.

**Reproducibility.** The raw CSV is not redistributed. Notebooks are committed with outputs so they can be read on GitHub, and every derived table is regenerable from `data/raw/` by running the notebooks in order.

---

## License

No license file is currently present in this repository.

Code and analysis are shared for educational reference. The underlying dataset remains subject to the terms published on its [Kaggle page](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset/data) and is credited to IBM; it is not redistributed here.

---

## Author(S)

| Author              | GitHub                                                                                                                                  |
| :------------------ | :-------------------------------------------------------------------------------------------------------------------------------------- |
| **Amruta Atul**     | [GitHub](https://github.com/username)                                                                                                   |
| **Asif Hassan**     | [GitHub](https://github.com/username)                                                                                                   |
| **Dhanan Thannoo**  | [![GitHub](https://img.shields.io/badge/GitHub-@ThannooDhanan-181717?style=flat-square&logo=github)](https://github.com/ThannooDhanan)  |
| **Yunseo Jang**     | [![GitHub](https://img.shields.io/badge/GitHub-@Solcratic-181717?style=flat-square&logo=github)](https://github.com/Solcratic)          |
| **Moustafa Ismail** | [![GitHub](https://img.shields.io/badge/GitHub-@mismail115-181717?style=flat-square&logo=github)](https://github.com/mismail115)        |
| **Pablo Fiterman**  | [![GitHub](https://img.shields.io/badge/GitHub-@pfiterman-181717?style=flat-square&logo=github)](https://github.com/pfiterman)          |
| **Tanvi Varshney**  | [![GitHub](https://img.shields.io/badge/GitHub-tanvivarshney7-181717?style=flat-square&logo=github)](https://github.com/tanvivarshney7) |

<div align="center">

---

⭐ If this analysis is useful to your own work, consider starring the repository.

</div>
