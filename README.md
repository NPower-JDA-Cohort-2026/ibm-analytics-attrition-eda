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

## IBM Attrition Explorer Dashboard

An interactive Dash app over the IBM HR Analytics dataset. Filter the workforce by
job role, department, level and seven other attributes; every statistic, chart and
table below the filter row re-reads the same slice.

Libraries `dash` and `plotty` were added on top of the project's existing `requirements.txt`.
Install the required libraries:

```bash
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

```bash
# from the project root type
(.venv) PS [YOUR WORK DIRECTORY]> python dashboards/app/app.py          # http://127.0.0.1:8050
```

Once Dash is running, open http://127.0.0.1:8050/ in your web browser to access the dashboard

### What it shows

The app reads **`data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv`** so all 35
attributes stay available, drops the three constant columns (`EmployeeCount`,
`Over18`, `StandardHours`), and re-derives the grouped features the notebooks use.
`AgeGroup` and `TenureGroup` share the exact bin edges from
`notebooks/04-data-wrangling.ipynb`, so a number here matches a number there.

---

## Roadmap

| Phase | Deliverable                                           | Status  |
| :---- | :---------------------------------------------------- | :------ |
| 00    | Exploring IBM HR Analytics Employee Attrition Dataset | ✅ Done |
| 01    | Handling duplicates values                            | ✅ Done |
| 02    | Handling missing values                               | ✅ Done |
| 03    | Normalizing Data                                      | ✅ Done |
| 04    | Data wrangling                                        | ✅ Done |
| 05    | Exploratory Data Analysis                             | ✅ Done |
| 06    | Finding how data is distributed                       | ✅ Done |
| 07    | Finding outliers                                      | ✅ Done |
| 08    | Finding correlation                                   | ✅ Done |
| 09    | Visualizing distribution                              | ✅ Done |
| 10    | Regression Model                                      | ✅ Done |

---

## Repository Structure

Planned layout; directories appear as each phase lands.

```
ibm-analytics-attrition-eda/
├── data/
│   ├── raw/                  # IBM HR Analytics Employee Attrition & Performance CSV file
│   └── processed/            # Cleaned, decoded outputs
├── notebooks/
│   ├── 00-exploring-the-dataset.ipynb
│   ├── 01-handling-duplicates.ipynb
│   ├── 02-handling-missing-values.ipynb
│   ├── 03-normalizing-data.ipynb
│   ├── 04-data-wrangling.ipynb
│   ├── 05-exploratory-data-analysis.ipynb
│   ├── 06-finding-how-data-distributed.ipynb
│   ├── 07-finding-outliers.ipynb
│   ├── 08-finding-correlation.ipynb
│   ├── 09-visualizing-distribution.ipynb
│   └── 10-regression-model.ipynb
├── dashboards/
│   └── app/                  # Dash application
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

## When something goes wrong with Git

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

| Author                   | GitHub                                                                                                                                   |
| :----------------------- | :--------------------------------------------------------------------------------------------------------------------------------------- |
| **Amruta Atul**          | [![GitHub](https://img.shields.io/badge/GitHub-@amrutaatul2000-181717?style=flat-square&logo=github)](https://github.com/amrutaatul2000) |
| **Asif Hassan**          | [![GitHub](https://img.shields.io/badge/GitHub-@asifhassan07-181717?style=flat-square&logo=github)](https://github.com/asifhassan07)     |
| **Dhanan Thannoo**       | [![GitHub](https://img.shields.io/badge/GitHub-@ThannooDhanan-181717?style=flat-square&logo=github)](https://github.com/ThannooDhanan)   |
| **Yunseo Jang**          | [![GitHub](https://img.shields.io/badge/GitHub-@Solcratic-181717?style=flat-square&logo=github)](https://github.com/Solcratic)           |
| **Moustafa Ismail**      | [![GitHub](https://img.shields.io/badge/GitHub-@mismail115-181717?style=flat-square&logo=github)](https://github.com/mismail115)         |
| **Pablo Fiterman**       | [![GitHub](https://img.shields.io/badge/GitHub-@pfiterman-181717?style=flat-square&logo=github)](https://github.com/pfiterman)           |
| **Stephanie Jivoderova** | [![GitHub](https://img.shields.io/badge/GitHub-@therealstephj-181717?style=flat-square&logo=github)](https://github.com/therealstephj)   |
| **Tanvi Varshney**       | [![GitHub](https://img.shields.io/badge/GitHub-tanvivarshney7-181717?style=flat-square&logo=github)](https://github.com/tanvivarshney7)  |

<div align="center">

---

⭐ If this analysis is useful to your own work, consider starring the repository.

</div>
