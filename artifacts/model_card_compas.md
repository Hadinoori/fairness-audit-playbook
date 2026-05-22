# Model Card — COMPAS Recidivism Algorithm Audit
*Based on: Mitchell et al. (2019), Model Cards for Model Reporting*  
*Fairness Audit Playbook v3.0 — Phase 04 Output*

---

## Model Identity

| Field | Value |
|-------|-------|
| **Model** | COMPAS Recidivism Scoring Algorithm |
| **Vendor** | Northpointe (now Equivant) |
| **Output** | decile_score (1–10) → high_risk (≥5) |
| **Decision context** | Pretrial detention, bail, parole recommendations |
| **Risk Tier** | T-1 — Criminal Justice (EU AI Act Annex III §1) |
| **Audit date** | 2026 |
| **Auditor** | Hadi Noori |

---

## Phase 02 — Fairness Definition Rationale

**Selected metric: Predictive Equality (FPR Parity)**

| Decision Tree Question | Answer | Basis |
|----------------------|--------|-------|
| Base rates equal across groups? | No | Measured on dataset |
| FN harm more severe than FP harm? | **No** | Normative judgment — documented below |

**Normative justification:**  
COMPAS is a punitive system. Its outputs influence pretrial detention and parole decisions.
A False Positive (flagging an innocent person as high-risk) results in potential wrongful
detention — a direct violation of liberty. A False Negative (missing a true reoffender)
results in a person being released who later reoffends.

In a legal system built on the presumption of innocence, FP harm outweighs FN harm.
Therefore Predictive Equality (FPR Parity) is the primary metric.

**Trade-off accepted:** A TPR gap may persist. This is a deliberate policy choice.
The TPR gap is documented in this Model Card and must be reviewed at each audit cycle.

*This rationale was documented before any metrics were computed — Phase 02 requirement.*

---

## Phase 04 — Disparity Report

### Single-Axis Analysis: Race

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| FPR — Caucasian | 22.0% | — | — |
| FPR — African-American | 42.3% | — | — |
| **FPR diff (primary)** | **20.3%** | **≤ 5%** | **⛔ FAIL** |
| EOD (abs) | 21.2% | ≤ 5% | ⛔ FAIL |
| AIR | 1.74 | ≤ 1.25 | ⛔ FAIL |
| Bootstrap CI (FPR diff, 95%) | [16.7%, 23.8%] | excludes zero | Significant ✓ |
| CI Width | 7.1% | ≤ 10% | ✓ PASS |

**Interpretation:**  
Of every 100 innocent African-Americans, 42 were flagged high-risk.  
Of every 100 innocent Caucasians, 22 were flagged high-risk.  
The disparity is 20.3 percentage points. The 95% Bootstrap CI [16.7%, 23.8%]
excludes zero, confirming this is not a sampling artifact.

### Intersectional Analysis: Race × Sex

| Group | N | FPR | TPR | High-Risk Rate |
|-------|---|-----|-----|----------------|
| African-American × Male | 2,626 | **43.7%** | — | 59.3% |
| African-American × Female | 549 | 37.9% | — | 49.5% |
| Caucasian × Female | 482 | 28.8% | — | 38.2% |
| Caucasian × Male | 1,621 | 19.8% | — | 31.6% |

**Worst-off group: African-American × Male**  
FPR ratio vs. Caucasian × Male: 43.7% ÷ 19.8% = **2.2×**  
An innocent Black man is 2.2× more likely to be flagged high-risk than an innocent White man.

---

## Deployment Decision

**⛔ BLOCKED**

Three of six deployment gates failed. Under the Fairness Audit Playbook (Section 1.4),
if any single metric breaches its threshold, the model does not ship.

The team has 5 business days to remediate or accept the risk in writing.
Product Manager sign-off is required for any risk acceptance.

---

## Residual Risk Statement

| Risk | Description | Status |
|------|-------------|--------|
| Feedback Loop | priors_count encodes over-policing history | Unresolved — Exploration Budget recommended |
| Intersectional harm | AA × Male FPR 2.2× higher than Caucasian × Male | Unresolved — binding constraint |
| Scope limitation | Broward County 2013–2014 only | Documented — do not generalize |
| TPR gap | Accepted trade-off from FPR Parity selection | Documented and signed |

---

## Key Finding

> If this Playbook had been in place at Northpointe before COMPAS deployment,
> the model would have been **blocked at two points**:
>
> 1. **Phase 02:** No fairness metric had been selected and documented before deployment.
>    The Playbook makes this a hard gate — no metric selection, no deployment.
>
> 2. **Phase 04:** The 20.3% FPR gap would have triggered an automatic CI/CD block.
>
> The ProPublica–Northpointe disagreement was not a technical disagreement about data.
> It was a governance failure: no one had decided what "fair" meant before the model shipped.
> This Playbook makes that failure structurally impossible.

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Fairness Champion | Hadi Noori | 2026 | ✓ |
| Product Manager | — | — | Required before deployment |
| Legal (Consulted) | — | — | Required for T-1 systems |

*Retain for minimum 10 years per EU AI Act Art. 18(1).*
