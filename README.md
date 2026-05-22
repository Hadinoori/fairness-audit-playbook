# Fairness Audit Playbook
### Operational Implementation — Vol. 01

**Author:** Hadi Noori  
**Regulatory basis:** EU AI Act Art. 6/9/10/13 · NIST AI RMF · EEOC 29 CFR § 1607  
**License:** CC BY-NC-ND 4.0

---

## What this is

A four-phase operational methodology for detecting, quantifying, and remediating bias
in high-stakes machine learning systems.

This repository is the **operational implementation** of the Fairness Audit Playbook (Vol. 01).
The full methodology — including governance framework, regulatory alignment, and trade-off
analysis — is in the Playbook PDF. This repository contains the code, audit artifacts,
and CI/CD integration that make the Playbook executable.

---

## The problem this solves

In 2016, ProPublica found COMPAS racially biased. Northpointe used the same data and
concluded it was fair. **Both were mathematically correct.**

The disagreement was not about the data. It was about which fairness metric to use —
and no one had made that decision before the model was deployed.

This Playbook makes that failure structurally impossible. **Phase 02 requires the fairness
metric to be selected, documented, and signed before any metric is computed.**

The COMPAS audit in this repository demonstrates what would have happened if this
Playbook had been in place at Northpointe:

1. **Phase 02 gate:** Deployment blocked — no metric selected and documented.
2. **Phase 04 gate:** Deployment blocked — FPR gap of 20.3% (threshold: ≤ 5%).

---

## Four-Phase Methodology

```
Phase 01 — Contextual Discovery (HCAT)
  Surface proxy variables. Run 80% Rule pre-check. Produce Data Card.

Phase 02 — Fairness Definition Selection
  Select primary metric via Decision Tree. Document trade-offs. Sign before computing.

Phase 03 — Bias Identification & Prioritization
  Classify disparities by Bias Taxonomy. Compute Priority Score.

Phase 04 — Metrics, Validation & Model Card
  Calculate SPD, EOD, AIR with 95% Bootstrap CI. Run Intersectional Scan. Sign Model Card.
```

---

## Repository Structure

```
fairness-audit-playbook/
├── src/
│   └── fairness_metrics.py      ← Core functions: importable, dependency-free
├── notebooks/
│   └── compas_audit.ipynb       ← Full four-phase audit on COMPAS data
├── artifacts/
│   ├── data_card_compas.md      ← Phase 01 output
│   └── model_card_compas.md     ← Phase 04 output — signed audit record
├── data/
│   └── compas-scores-two-years.csv
└── .github/workflows/
    └── fairness_gate.yaml       ← CI/CD block if any gate fails
```

---

## Quick Start

```python
from src.fairness_metrics import calculate_disparities, bootstrap_ci

metrics = calculate_disparities(
    data=df,
    sensitive_attr='race',
    majority_label='Caucasian',
    minority_label='African-American',
    target_label='two_year_recid',
    prediction='high_risk'
)

ci = bootstrap_ci(
    data=df,
    sensitive_attr='race',
    majority_label='Caucasian',
    minority_label='African-American',
    target_label='two_year_recid',
    prediction='high_risk'
)
```

No external fairness libraries required. Standard pandas/numpy only.

---

## COMPAS Audit Results

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| FPR — Caucasian (innocent, flagged) | 22.0% | — | — |
| FPR — African-American (innocent, flagged) | 42.3% | — | — |
| **FPR diff (primary metric)** | **20.3%** | **≤ 5%** | **⛔ FAIL** |
| EOD | 21.2% | ≤ 5% | ⛔ FAIL |
| Bootstrap 95% CI | [16.7%, 23.8%] | excludes zero | Significant |
| Worst intersectional group | AA × Male, FPR 43.7% | — | 2.2× gap |

**Deployment decision: ⛔ BLOCKED**

Full audit: [`notebooks/compas_audit.ipynb`](notebooks/compas_audit.ipynb)  
Data Card: [`artifacts/data_card_compas.md`](artifacts/data_card_compas.md)  
Model Card: [`artifacts/model_card_compas.md`](artifacts/model_card_compas.md)

---

## Using This in Your Own Project

This repository is designed to be adapted to any ML system in any organization.
COMPAS is the reference case study — your model replaces it.

### Step 1 — Install

```bash
git clone https://github.com/Hadinoori/fairness-audit-playbook.git
cd fairness-audit-playbook
pip install -r requirements.txt
```

### Step 2 — Run the audit on your model

Replace the COMPAS data and labels with your own:

```python
from src.fairness_metrics import calculate_disparities, bootstrap_ci, check_deployment_gates

# Your data — must have: sensitive attribute, ground truth, model prediction
metrics = calculate_disparities(
    data=your_df,
    sensitive_attr='gender',        # your sensitive attribute column
    majority_label='Male',          # majority group label
    minority_label='Female',        # minority group label
    target_label='hired',           # ground truth (1 = positive outcome)
    prediction='model_output'       # model prediction (binary 0/1)
)

ci = bootstrap_ci(
    data=your_df,
    sensitive_attr='gender',
    majority_label='Male',
    minority_label='Female',
    target_label='hired',
    prediction='model_output'
)

gates = check_deployment_gates(metrics, ci)
print(gates['OVERALL'])
```

### Step 3 — Adapt the CI/CD gate

Copy `.github/workflows/fairness_gate.yaml` into your repository.
Edit the data loading section to point to your model and data pipeline.
The gate thresholds (FPR diff ≤ 0.05, EOD ≤ 0.05, AIR ≤ 1.25) can be adjusted
to match your regulatory context — document any change in your Model Card.

### Step 4 — Follow the four-phase methodology

Before running any code, complete Phase 01 and Phase 02:
- Fill in the Data Card template (see `artifacts/data_card_compas.md` as reference)
- Select and document your fairness metric via the Decision Tree (Phase 02)
- Get the Data Card signed before proceeding to Phase 04

Skipping Phase 02 is the exact governance failure that produced the
ProPublica–Northpointe disagreement. The metric must be chosen before results are computed.

For the complete methodology:  
**→ Fairness Audit Playbook PDF (Vol. 01)**

---

## CI/CD Integration

The `fairness_gate.yaml` workflow runs automatically on every push to `src/`.
If any deployment gate fails, the build is blocked and the model cannot be deployed.

```yaml
# Triggers on push to main when src/ changes
# Downloads COMPAS data automatically from ProPublica's public repository
# Fails build if: FPR diff > 0.05, EOD > 0.05, AIR > 1.25, or CI width > 0.10
```

---

## Scope & Limitations

This Playbook addresses **disparate impact** (group fairness) only.
Three boundaries apply:

1. It does not resolve which disparities are normatively acceptable — that is a values decision.
2. Disparate treatment (direct use of protected attributes) requires a different analytical approach.
3. Individual fairness (Dwork et al., 2012) is not addressed.

The COMPAS dataset covers Broward County, Florida, 2013–2014.
Results must not be generalized to other jurisdictions or time periods.

For the complete methodology, governance framework, and regulatory alignment:
**→ Fairness Audit Playbook PDF (Vol. 01)**

---

## References

- Barocas, Hardt & Narayanan (2023). *Fairness and Machine Learning.* MIT Press.
- Buolamwini & Gebru (2018). Gender Shades. PMLR Vol. 81.
- Chouldechova (2017). Fair prediction with disparate impact. *Big Data.*
- Kleinberg et al. (2017). Inherent trade-offs in fair risk scores. ITCS.
- Mitchell et al. (2019). Model Cards for Model Reporting. FAccT.
- ProPublica (2016). How We Analyzed the COMPAS Recidivism Algorithm.
- Regulation (EU) 2024/1689 — AI Act.
- NIST AI RMF 1.0 (2023).
