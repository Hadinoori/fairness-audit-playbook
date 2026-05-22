# Data Card — COMPAS Recidivism Dataset
*Based on: Gebru et al. (2021), Datasheets for Datasets*  
*Fairness Audit Playbook v3.0 — Phase 01 Output*

---

## Dataset Identity

| Field | Value |
|-------|-------|
| **Name** | COMPAS Recidivism Scores — Two Year |
| **Source** | ProPublica, 2016 |
| **Original collector** | Broward County Sheriff's Office |
| **Geography** | Broward County, Florida, USA |
| **Time period** | 2013–2014 |
| **Records (raw)** | 7,214 |
| **Records (filtered)** | 6,172 |
| **Filter applied** | ProPublica standard filter (days_b_screening_arrest ±30, is_recid ≠ -1) |

---

## Protected Attributes

| Attribute | Values | Distribution |
|-----------|--------|--------------|
| race | African-American, Caucasian, Hispanic, Other, Asian, Native American | AA: 51.4%, Caucasian: 34.1% |
| sex | Male, Female | Male: 80.8%, Female: 19.2% |

---

## Proxy Variables Identified (HCAT Step 1.2)

| Feature | Proxy for | Association | Action |
|---------|-----------|-------------|--------|
| priors_count | Race (over-policing) | Moderate-High | **Retained** — Business Necessity (core predictive signal). Flagged for intersectional monitoring. Feedback loop risk documented in Model Card. |
| age | Race (structural) | Moderate | Monitored |

---

## Feedback Loop Risk (HCAT Step 1.3)

**priors_count** encodes prior arrests, which reflect exposure to the criminal justice system,
not criminal propensity. Decades of over-policing in minority communities produce more arrest
records for the same underlying behavior. This is a Feedback Loop bias — the model's outputs
(high-risk scores) influence future policing decisions, which produce more arrests, which
increase future priors_count values. An Exploration Budget (ε = 5%) is recommended
for any live deployment.

---

## 80% Rule Pre-Check (HCAT Step 1.4)

| Group | High-Risk Rate | AIR |
|-------|---------------|-----|
| Caucasian (majority) | 33.1% | — |
| African-American (minority) | 57.6% | 1.74 |

AIR > 1.0 means the minority group is flagged at a *higher* rate.
In a punitive system, this is the inverse of the standard EEOC framing
(which applies to selection/hiring). The disparity is flagged for Phase 04 analysis.

---

## Critical Limitation

**This dataset covers Broward County, Florida, 2013–2014 only.**

Results must not be generalized to:
- Other counties or states
- Other time periods
- Other demographic compositions

Any deployment of this audit methodology in a different context requires
independent data collection and a full four-phase audit from Phase 01.

---

## Sign-Off

| Role | Name | Date |
|------|------|------|
| Data Scientist | Hadi Noori | 2026 |
| Legal (Consulted) | — | — |

*Phase 02 may proceed.*
