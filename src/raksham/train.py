import argparse
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold

from . import data
from .model import (binary_metrics, candidates, pick_balanced_threshold, pick_threshold,
                    template_summary, type_model)

STRICT_FPR = 0.01  # the strict threshold lets through at most 1% of genuine messages as false alarms
EXTRA_WEIGHT = 0.25  # each external SMS counts a quarter of a Raksham message (see experiments/external_data.py)


def fit_detector(make, df, extra):
    """Fit on Raksham messages plus the down-weighted external data. External rows are only ever used for fitting, never scored."""
    X = pd.concat([df["text"], extra["text"]])
    y = np.r_[df["label"], extra["label"]]
    weights = np.r_[np.ones(len(df)), np.full(len(extra), EXTRA_WEIGHT)]
    model = make()
    model.fit(X, y, clf__sample_weight=weights)
    return model


def oof_probabilities(make, df, extra, folds: int) -> np.ndarray:
    """Out-of-fold scam probabilities. Folds are grouped by message template, so a template is never on both
    the fitting and the scoring side: this measures how the model copes with templates it has not seen."""
    prob = np.zeros(len(df))
    for fit_idx, score_idx in GroupKFold(n_splits=folds).split(df, df["label"], df["template_id"]):
        model = fit_detector(make, df.iloc[fit_idx], extra)
        prob[score_idx] = model.predict_proba(df.iloc[score_idx]["text"])[:, 1]
    return prob


def oof_scam_types(scam, folds: int) -> np.ndarray:
    pred = np.empty(len(scam), dtype=object)
    for fit_idx, score_idx in GroupKFold(n_splits=folds).split(scam, scam["scam_type"], scam["template_id"]):
        model = type_model().fit(scam.iloc[fit_idx]["text"], scam.iloc[fit_idx]["scam_type"])
        pred[score_idx] = model.predict(scam.iloc[score_idx]["text"])
    return pred


def scored(df, prob, threshold) -> dict:
    return {"messages": binary_metrics(df["label"], prob, threshold), "templates": template_summary(df, prob, threshold)}


def by_slice(df, prob, threshold, column) -> dict:
    return {str(v): scored(g, prob[g.index], threshold) for v, g in df.groupby(column)}


def write_report(r: dict) -> str:
    th = r["thresholds"]
    cv, ho = r["cross_validation"], r["held_out"]
    lines = [
        "# Results", "",
        f"Detector: `{r['detector']}` (TF-IDF word and character n-grams with logistic regression)" + (f", fitted on the Raksham messages plus {r['extra_rows']} external messages at a quarter weight (never scored)" if r["extra_rows"] else ", fitted on the Raksham messages only") + ". "
        f"Verdict threshold {th['balanced']} (balanced); strict threshold {th['strict']} (at most {STRICT_FPR:.0%} false alarms on development data).", "",
        "Every message in the dataset comes from one of {0} templates, about 50 near-copies each. All results below are therefore also given per template: "
        "a template counts as caught or missed as a whole. Messages from one template never appear on both sides of any split.".format(r["templates_total"]), "",
        "## 1. Cross-validation over all templates (leave-templates-out, 6 folds)", "",
        "This is the most stable estimate: every template is scored by a model that never saw it.", "",
        "| | Scam templates caught | Genuine templates left alone | Message accuracy | Message F1 | ROC AUC |", "|---|---|---|---|---|---|",
    ]
    c = cv["overall"]
    lines.append(f"| All ({c['templates']['scam_templates']} scam, {c['templates']['genuine_templates']} genuine templates) | {c['templates']['scam_template_recall']} | {c['templates']['genuine_template_specificity']} | {c['messages']['accuracy']} | {c['messages']['f1']} | {c['messages']['roc_auc']} |")
    for lang, m in cv["by_language"].items():
        lines.append(f"| {lang} ({m['templates']['scam_templates']} scam, {m['templates']['genuine_templates']} genuine) | {m['templates']['scam_template_recall']} | {m['templates']['genuine_template_specificity']} | {m['messages']['accuracy']} | {m['messages']['f1']} | {m['messages'].get('roc_auc')} |")
    lines += ["", f"Scam-type identification across unseen templates: accuracy {cv['scam_type']['accuracy']}, macro F1 {cv['scam_type']['macro_f1']} over {cv['scam_type']['classes']} types.", "",
              "## 2. The dataset's own held-out test split", "",
              f"A model fitted on train+val only ({r['dev_rows']} messages) and scored once on the test split ({ho['balanced']['messages']['n']} messages, {ho['balanced']['templates']['scam_templates'] + ho['balanced']['templates']['genuine_templates']} templates, none seen in training). "
              "The split has one test template per scam type and only 8 genuine templates, so treat each figure as coarse.", "",
              "| Threshold | Scam templates caught | Genuine templates left alone | Message recall | False positive rate | Message F1 | ROC AUC |", "|---|---|---|---|---|---|---|"]
    for name in ("balanced", "strict"):
        m = ho[name]
        lines.append(f"| {name} ({m['messages']['threshold']}) | {m['templates']['scam_template_recall']} | {m['templates']['genuine_template_specificity']} | {m['messages']['recall']} | {m['messages']['false_positive_rate']} | {m['messages']['f1']} | {m['messages']['roc_auc']} |")
    lines += ["", "Held-out test by language (balanced threshold):", "", "| Language | Scam templates caught | Genuine templates left alone |", "|---|---|---|"]
    for name, m in r["held_out_by_language"].items():
        lines.append(f"| {name} | {m['templates']['scam_template_recall']} | {m['templates']['genuine_template_specificity']} |")
    lines += ["", "Held-out test by scam type (one template each; balanced threshold):", "", "| Scam type | Messages flagged | Type identified |", "|---|---|---|"]
    for name, m in r["held_out_by_scam_type"].items():
        lines.append(f"| {name} | {m['flagged']} | {m['type_correct']} |")
    lines += ["", "## Limits", "",
              "- Every message is synthetic and written from templates. These scores show how well the model separates this dataset's scam and genuine styles on unseen templates. They do not measure accuracy on real messages.",
              "- Each scam type has 3 to 6 training templates, so the type label is a weak hint and is returned with its own confidence. The scam or genuine verdict is the reliable part.",
              "- Genuine messages that look like scams (money sent between family members, one-time-password notices) are the main false alarms. The deployed model is trained on all templates, including the test split, so the numbers in section 2 describe the earlier train+val model.",
              "- Only the message text is used. Sender, link and phone metadata are not available to the model."]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the scam detector.")
    parser.add_argument("--external", action="store_true", help="Also fit on the external data in data/external (not the default: see README).")
    args = parser.parse_args()
    suffix = "_external" if args.external else ""
    df = data.load()
    dev, test = data.dev_and_test(df)
    overlap = set(dev["template_id"]) & set(test["template_id"])
    assert not overlap, f"test templates also appear in development data: {sorted(overlap)[:5]}"
    extra = data.load_external(set(df["text"]))
    if not args.external:
        extra = extra.iloc[:0]  # same columns and types, no rows
    print(f"{len(df)} messages, {df['template_id'].nunique()} templates; development {len(dev)}, test {len(test)}, no shared templates; {len(extra)} external messages used for fitting only")

    # 1. Choose the model and thresholds on development data only.
    selection, oof = {}, {}
    for name, make in candidates().items():
        oof[name] = oof_probabilities(make, dev, extra, folds=5)
        selection[name] = binary_metrics(dev["label"], oof[name], 0.5)
        print(f"{name}: F1 {selection[name]['f1']}  AUC {selection[name]['roc_auc']}")
    best = max(selection, key=lambda n: (selection[n]["f1"], selection[n]["roc_auc"]))
    thresholds = {"balanced": pick_balanced_threshold(dev, oof[best]), "strict": pick_threshold(dev["label"], oof[best], STRICT_FPR)}
    print(f"selected {best}; thresholds {thresholds}")

    # 2. Score the held-out test split once.
    detector = fit_detector(candidates()[best], dev, extra)
    prob = detector.predict_proba(test["text"])[:, 1]
    kinds = type_model().fit(dev[dev["label"] == 1]["text"], dev[dev["label"] == 1]["scam_type"])
    scam_test = test[test["label"] == 1].copy()
    scam_test["predicted_type"] = kinds.predict(scam_test["text"])
    scam_test["flagged"] = prob[scam_test.index] >= thresholds["balanced"]
    held_out_types = {
        str(k): {"flagged": round(float(g["flagged"].mean()), 4), "type_correct": round(float((g["predicted_type"] == g["scam_type"]).mean()), 4)}
        for k, g in scam_test.groupby("scam_type")
    }

    # 3. Cross-validate over every template for the most stable estimate.
    prob_all = oof_probabilities(candidates()[best], df, extra, folds=6)
    scam_all = df[df["label"] == 1].reset_index(drop=True)
    types_all = oof_scam_types(scam_all, folds=6)
    cv = {
        "overall": scored(df, prob_all, thresholds["balanced"]),
        "by_language": by_slice(df, prob_all, thresholds["balanced"], "language"),
        "scam_type": {
            "accuracy": round(float(accuracy_score(scam_all["scam_type"], types_all)), 4),
            "macro_f1": round(float(f1_score(scam_all["scam_type"], types_all, average="macro")), 4),
            "classes": int(scam_all["scam_type"].nunique()),
        },
    }

    result = {
        "detector": best, "thresholds": thresholds, "dev_rows": int(len(dev)), "extra_rows": int(len(extra)), "templates_total": int(df["template_id"].nunique()),
        "selection": selection,
        "held_out": {k: scored(test, prob, t) for k, t in thresholds.items()},
        "held_out_by_language": by_slice(test, prob, thresholds["balanced"], "language"),
        "held_out_by_scam_type": held_out_types,
        "cross_validation": cv,
    }

    # 4. The deployed model learns from every template.
    final_detector = fit_detector(candidates()[best], df, extra)
    final_explainer = fit_detector(candidates()["logreg"], df, extra)
    final_types = type_model().fit(scam_all["text"], scam_all["scam_type"])
    model_path = data.MODEL_PATH.with_name(f"scam_detector{suffix}.joblib")
    model_path.parent.mkdir(exist_ok=True)
    joblib.dump({"detector": final_detector, "explainer": final_explainer, "type_model": final_types, "thresholds": thresholds,
                 "threshold": thresholds["balanced"], "detector_name": best, "trained_on": "all templates"}, model_path)
    data.REPORTS.mkdir(exist_ok=True)
    (data.REPORTS / f"metrics{suffix}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (data.REPORTS / f"metrics{suffix}.md").write_text(write_report(result), encoding="utf-8")

    o, h = cv["overall"], result["held_out"]["balanced"]
    print(f"CV (leave templates out): scam templates caught {o['templates']['scam_template_recall']}, genuine templates left alone {o['templates']['genuine_template_specificity']}, message F1 {o['messages']['f1']}, AUC {o['messages']['roc_auc']}")
    print(f"HELD-OUT TEST (balanced): recall {h['messages']['recall']}, false positive rate {h['messages']['false_positive_rate']}, F1 {h['messages']['f1']}, AUC {h['messages']['roc_auc']}")
    print(f"scam type (CV): accuracy {cv['scam_type']['accuracy']}, macro F1 {cv['scam_type']['macro_f1']}")
    print(f"saved {model_path.name} and reports/metrics{suffix}.md")


if __name__ == "__main__":
    main()
