"""Does the external SMS data help on templates the model has not seen?

Compares fitting on Raksham only with fitting on Raksham plus the external data (weight 0.25), using
leave-templates-out cross-validation over five random assignments of templates to folds. External messages are
only ever fitted, never scored. Run from the project root:  python experiments/external_data.py
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from raksham import data
from raksham.model import candidates, pick_balanced_threshold, template_summary
from raksham.train import EXTRA_WEIGHT, fit_detector

FOLDS, SEEDS = 6, 5


def run(df, extra, seed):
    templates = df["template_id"].unique()
    rng = np.random.default_rng(seed)
    fold_of = dict(zip(rng.permutation(templates), np.arange(len(templates)) % FOLDS))
    fold = df["template_id"].map(fold_of).to_numpy()
    prob = np.zeros(len(df))
    for k in range(FOLDS):
        fit_idx, score_idx = np.where(fold != k)[0], np.where(fold == k)[0]
        model = fit_detector(candidates()["logreg"], df.iloc[fit_idx], extra)
        prob[score_idx] = model.predict_proba(df.iloc[score_idx]["text"])[:, 1]
    threshold = pick_balanced_threshold(df, prob)
    overall = template_summary(df, prob, threshold)
    hinglish = df[df["language"] == "hinglish"]
    return [roc_auc_score(df["label"], prob), overall["scam_template_recall"], overall["genuine_template_specificity"],
            template_summary(hinglish, prob[hinglish.index], threshold)["genuine_template_specificity"]]


def main() -> None:
    df = data.load()
    extra = data.load_external(set(df["text"]))
    none = extra.iloc[:0]
    print(f"{len(extra)} external messages, weight {EXTRA_WEIGHT}")
    base, with_extra = [], []
    for seed in range(SEEDS):
        base.append(run(df, none, seed))
        with_extra.append(run(df, extra, seed))
        print(f"seed {seed}: base {np.round(base[-1], 3)}  with external {np.round(with_extra[-1], 3)}")
    cols = ["ROC AUC", "scam templates caught", "genuine templates left alone", "Hinglish genuine left alone"]
    table = pd.DataFrame({"Raksham only": np.mean(base, axis=0), "+ external": np.mean(with_extra, axis=0)}, index=cols).round(3)
    print(f"\nMean over {SEEDS} random template splits:\n{table}")


if __name__ == "__main__":
    main()
