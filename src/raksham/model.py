import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC


def features() -> FeatureUnion:
    """Word pairs catch phrases ("share otp"); character n-grams survive spelling noise, Hinglish and SMS shorthand."""
    return FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, sublinear_tf=True)),
    ])


def candidates() -> dict:
    return {
        "logreg": lambda: Pipeline([
            ("tfidf", features()),
            ("clf", LogisticRegression(C=10, max_iter=3000, class_weight="balanced")),
        ]),
        "calibrated_svc": lambda: Pipeline([
            ("tfidf", features()),
            ("clf", CalibratedClassifierCV(LinearSVC(C=0.5, class_weight="balanced"), method="sigmoid", cv=3)),
        ]),
    }


def type_model() -> Pipeline:
    return Pipeline([
        ("tfidf", features()),
        ("clf", LogisticRegression(C=10, max_iter=3000, class_weight="balanced")),
    ])


def explain(pipeline: Pipeline, text: str, k: int = 3) -> list[str]:
    """The words that pushed a logistic-regression score toward 'scam' the most."""
    tfidf, clf = pipeline.named_steps["tfidf"], pipeline.named_steps["clf"]
    names = tfidf.get_feature_names_out()
    row = tfidf.transform([text]).tocoo()
    words = [(names[j][len("word__"):], value * clf.coef_[0][j])
             for j, value in zip(row.col, row.data)
             if names[j].startswith("word__") and value * clf.coef_[0][j] > 0
             and not all(w in ENGLISH_STOP_WORDS or w.isdigit() for w in names[j][len("word__"):].split())]
    return [w for w, _ in sorted(words, key=lambda t: -t[1])[:k]]


def binary_metrics(y_true, prob, threshold: float) -> dict:
    """Scam is the positive class. False positives (a genuine message flagged) are reported on their own."""
    y_true = np.asarray(y_true)
    pred = (np.asarray(prob) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    div = lambda a, b: round(float(a) / b, 4) if b else None
    precision, recall = div(tp, tp + fp), div(tp, tp + fn)
    f1 = round(2 * precision * recall / (precision + recall), 4) if precision and recall else None
    out = {
        "n": int(len(y_true)), "threshold": round(float(threshold), 3),
        "accuracy": div(tp + tn, len(y_true)), "precision": precision, "recall": recall, "f1": f1,
        "false_positive_rate": div(fp, fp + tn), "false_negative_rate": div(fn, fn + tp),
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
    }
    if len(set(y_true.tolist())) == 2:
        out["roc_auc"] = round(float(roc_auc_score(y_true, prob)), 4)
    return out


def pick_threshold(y_true, prob, max_fpr: float = 0.01) -> float:
    """The lowest threshold that keeps genuine messages wrongly flagged at or under max_fpr, so recall is as high as that allows."""
    for t in np.round(np.arange(0.05, 0.96, 0.01), 2):
        m = binary_metrics(y_true, prob, t)
        if m["false_positive_rate"] is not None and m["false_positive_rate"] <= max_fpr:
            return float(t)
    return 0.5


def template_summary(df, prob, threshold: float) -> dict:
    """Scores per message template, because every template yields about 50 near-copies: a large template would
    otherwise decide the result. A template is flagged when its average scam probability reaches the threshold."""
    t = df.assign(p=np.asarray(prob)).groupby("template_id").agg(label=("label", "first"), p=("p", "mean"))
    scam, genuine = t[t["label"] == 1], t[t["label"] == 0]
    rate = lambda s: round(float(s.mean()), 4) if len(s) else None
    return {
        "scam_templates": int(len(scam)), "genuine_templates": int(len(genuine)),
        "scam_template_recall": rate(scam["p"] >= threshold),
        "genuine_template_specificity": rate(genuine["p"] < threshold),
    }


def pick_balanced_threshold(df, prob) -> float:
    """The threshold that does best on both scam templates caught and genuine templates left alone; ties go to the one nearest 0.5."""
    scored = []
    for t in np.round(np.arange(0.05, 0.96, 0.01), 2):
        s = template_summary(df, prob, t)
        scored.append((((s["scam_template_recall"] or 0) + (s["genuine_template_specificity"] or 0)) / 2, -abs(t - 0.5), float(t)))
    return max(scored)[2]
