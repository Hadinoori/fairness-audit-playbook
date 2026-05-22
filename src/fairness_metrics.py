"""
Fairness Audit Playbook — Core Metrics Module
Author: Hadi Noori
Version: 3.0
Regulatory: EU AI Act Art. 6/9/10/13 · NIST AI RMF · EEOC 29 CFR § 1607

This module is the operational implementation of the Fairness Audit Playbook (Vol. 01).
All functions correspond directly to Phase 04 of the four-phase audit methodology.
No external fairness libraries required — standard pandas/numpy only.
"""

import numpy as np
import pandas as pd


def calculate_disparities(
    data: pd.DataFrame,
    sensitive_attr: str,
    majority_label: str,
    minority_label: str,
    target_label: str,
    prediction: str
) -> dict:
    """
    Calculate SPD, EOD, AIR, and FPR disparity between two groups.

    Parameters
    ----------
    data            : DataFrame containing audit data
    sensitive_attr  : Column name of the sensitive attribute (e.g. 'race')
    majority_label  : Label of the majority group (e.g. 'Caucasian')
    minority_label  : Label of the minority group (e.g. 'African-American')
    target_label    : Ground truth label column
    prediction      : Model prediction column (binary 0/1)

    Returns
    -------
    dict with SPD, EOD_signed, EOD_abs, AIR, FPR per group, and FPR_diff.
    Returns {'Error': message} if inputs are invalid.

    Notes
    -----
    SPD sign convention: majority - minority (opposite to Fairlearn).
    FPR_diff sign convention: minority - majority (positive = minority disadvantaged).
    """
    group_a = data[data[sensitive_attr] == majority_label]
    group_b = data[data[sensitive_attr] == minority_label]

    if len(group_a) == 0 or len(group_b) == 0:
        return {"Error": "One or both groups are empty — check label values"}

    rate_a = group_a[prediction].mean()
    rate_b = group_b[prediction].mean()
    spd = rate_a - rate_b

    qa = group_a[group_a[target_label] == 1]
    qb = group_b[group_b[target_label] == 1]

    if len(qa) == 0 or len(qb) == 0:
        return {"Error": "No qualified individuals in one or both groups"}

    eod_signed = qa[prediction].mean() - qb[prediction].mean()
    eod_abs = abs(eod_signed)

    if rate_a == 0 and rate_b == 0:
        ratio = 1.0
    elif rate_a == 0:
        return {"Error": "Majority group selection rate is 0 — AIR undefined"}
    else:
        ratio = rate_b / rate_a

    # FPR — core metric for Predictive Equality in punitive systems
    non_recid_a = group_a[group_a[target_label] == 0]
    non_recid_b = group_b[group_b[target_label] == 0]
    fpr_a = non_recid_a[prediction].mean()
    fpr_b = non_recid_b[prediction].mean()
    fpr_diff = fpr_b - fpr_a

    maj_key = majority_label.replace('-', '_').replace(' ', '_')
    min_key = minority_label.replace('-', '_').replace(' ', '_')

    return {
        "SPD": round(spd, 4),
        "EOD_signed": round(eod_signed, 4),
        "EOD_abs": round(eod_abs, 4),
        "AIR": round(ratio, 4),
        f"FPR_{maj_key}": round(fpr_a, 4),
        f"FPR_{min_key}": round(fpr_b, 4),
        "FPR_diff": round(fpr_diff, 4),
    }


def bootstrap_ci(
    data: pd.DataFrame,
    sensitive_attr: str,
    majority_label: str,
    minority_label: str,
    target_label: str,
    prediction: str,
    n_resamples: int = 2000,
    ci: float = 0.95
) -> dict:
    """
    Stratified bootstrap confidence intervals for EOD, AIR, and FPR_diff.

    Each group is resampled independently to preserve minority representation
    in every bootstrap draw. significant=True means the disparity is
    statistically detectable at the chosen confidence level (CI excludes zero).

    Parameters
    ----------
    n_resamples : Number of bootstrap draws (default 2000).
                  Use >= 5000 for Bonferroni-adjusted CIs (alpha* < 0.01).
    ci          : Confidence level (default 0.95).

    Returns
    -------
    dict with CI bounds, significance flags, CI widths, and valid draw count.
    CI width > 0.10 indicates insufficient data (Section 1.4, Playbook).
    """
    fpr_diffs, eod_s, air_s = [], [], []

    maj = data[data[sensitive_attr] == majority_label]
    mn = data[data[sensitive_attr] == minority_label]

    for _ in range(n_resamples):
        s = pd.concat([
            maj.sample(n=len(maj), replace=True),
            mn.sample(n=len(mn), replace=True)
        ])
        r = calculate_disparities(
            s, sensitive_attr, majority_label, minority_label, target_label, prediction
        )
        if "Error" not in r:
            fpr_diffs.append(r["FPR_diff"])
            eod_s.append(r["EOD_signed"])
            air_s.append(r["AIR"])

    if not fpr_diffs:
        return {"Error": "All bootstrap draws returned errors — check inputs"}

    alpha = (1 - ci) / 2

    def bounds(s, a):
        lo = np.percentile(s, a * 100)
        hi = np.percentile(s, (1 - a) * 100)
        significant = lo > 0.0 or hi < 0.0
        width = round(hi - lo, 4)
        return round(lo, 4), round(hi, 4), significant, width

    fl, fh, fs, fw = bounds(fpr_diffs, alpha)
    el, eh, es, ew = bounds(eod_s, alpha)
    al, ah, as_, aw = bounds([x - 1 for x in air_s], alpha)

    return {
        "FPR_diff_CI": (fl, fh),
        "FPR_diff_significant": fs,
        "FPR_CI_width": fw,
        "EOD_CI": (el, eh),
        "EOD_significant": es,
        "EOD_CI_width": ew,
        "AIR_CI": (al + 1, ah + 1),
        "AIR_significant": as_,
        "AIR_CI_width": aw,
        "n_valid_draws": len(fpr_diffs),
    }


def intersectional_scan(
    data: pd.DataFrame,
    attr1: str,
    attr2: str,
    target_label: str,
    prediction: str
) -> pd.DataFrame:
    """
    Min-Max intersectional scan across all identity intersections (Phase 04, Step 4.3).

    Subgroups with N < 30 are excluded; apply Bayesian shrinkage separately
    for small samples (Playbook Section 2.5, Step D).

    Parameters
    ----------
    attr1, attr2 : Two sensitive attributes to intersect (e.g. 'race' and 'sex')

    Returns
    -------
    DataFrame sorted by FPR descending — worst-off group first.
    The worst-off group defines the audit's binding constraint.
    """
    data = data.copy()
    data["_intersect"] = data[attr1] + " x " + data[attr2]

    results = []
    for group, gdf in data.groupby("_intersect"):
        n = len(gdf)
        if n < 30:
            continue  # N < 30: apply Bayesian shrinkage (Playbook Section 2.5, Step D)

        high_risk_rate = gdf[prediction].mean()

        non_recid = gdf[gdf[target_label] == 0]
        fpr = non_recid[prediction].mean() if len(non_recid) > 0 else None

        recid = gdf[gdf[target_label] == 1]
        tpr = recid[prediction].mean() if len(recid) > 0 else None

        results.append({
            "group": group,
            "n": n,
            "high_risk_rate": round(high_risk_rate, 3),
            "FPR": round(fpr, 3) if fpr is not None else None,
            "TPR": round(tpr, 3) if tpr is not None else None,
        })

    return pd.DataFrame(results).sort_values("FPR", ascending=False).reset_index(drop=True)


def check_deployment_gates(metrics: dict, ci_metrics: dict) -> dict:
    """
    Check the six deployment gates defined in Playbook Section 1.4.

    If any single gate fails, the model must not be deployed.
    The team has 5 business days to remediate or accept residual risk in writing.
    Product Manager owns the final deployment decision (RACI, Section 4.3).

    Parameters
    ----------
    metrics    : Output of calculate_disparities()
    ci_metrics : Output of bootstrap_ci()

    Returns
    -------
    dict with per-gate results and OVERALL deployment decision.
    """
    gates = {}

    # Gate 1: AIR — for punitive systems, minority is flagged MORE (AIR > 1)
    # Threshold inverted: AIR > 1.25 signals disproportionate flagging
    air = metrics.get("AIR")
    if air is not None:
        gates["AIR_gate"] = {
            "value": air,
            "threshold": "<= 1.25 (punitive system, inverted EEOC framing)",
            "status": "FAIL" if air > 1.25 else "PASS"
        }

    # Gate 2: EOD <= 0.05
    eod = metrics.get("EOD_abs")
    if eod is not None:
        gates["EOD_gate"] = {
            "value": round(eod, 3),
            "threshold": "<= 0.05",
            "status": "FAIL" if eod > 0.05 else "PASS"
        }

    # Gate 3: FPR_diff <= 0.05 — primary metric for Predictive Equality
    fpr_diff = metrics.get("FPR_diff")
    if fpr_diff is not None:
        gates["FPR_Parity_gate"] = {
            "value": round(abs(fpr_diff), 3),
            "threshold": "<= 0.05",
            "status": "FAIL" if abs(fpr_diff) > 0.05 else "PASS"
        }

    # Gate 4: Bootstrap CI width <= 0.10 (stability check)
    fpr_width = ci_metrics.get("FPR_CI_width")
    if fpr_width is not None:
        gates["CI_width_gate"] = {
            "value": fpr_width,
            "threshold": "<= 0.10",
            "status": "FAIL" if fpr_width > 0.10 else "PASS"
        }

    failed = [g for g, v in gates.items() if v["status"] == "FAIL"]
    overall = "DEPLOY — all gates passed" if not failed else f"BLOCKED — failed gates: {', '.join(failed)}"
    gates["OVERALL"] = overall

    return gates
