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
> This dataset is **fictional**, created by IBM data scientists to demonstrate HR analytics. It does not describe real employees and its rates are not industry benchmarks. Findings here demonstrate _method_ — they are not transferable HR conclusions.

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

Open the terminal and type in your ibm-analytics-attrition-eda root directory:

```bash
# from the project root type
(.venv) PS [PROJECT ROOT DIRECTORY]> python dashboards/app/app.py          # http://127.0.0.1:8050
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

In your work directory type:

```bash
git clone https://github.com/NPower-JDA-Cohort-2026/ibm-analytics-attrition-eda.git
cd ibm-analytics-attrition-eda

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Notebooks are numerically prefixed and intended to be run in order.

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
