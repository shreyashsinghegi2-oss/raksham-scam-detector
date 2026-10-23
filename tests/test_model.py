import pandas as pd

from raksham.model import binary_metrics, pick_balanced_threshold, pick_threshold, template_summary


def test_binary_metrics_on_a_known_case():
    m = binary_metrics([1, 1, 0, 0], [0.9, 0.4, 0.2, 0.6], 0.5)
    assert (m["tp"], m["fn"], m["tn"], m["fp"]) == (1, 1, 1, 1)
    assert m["accuracy"] == m["precision"] == m["recall"] == m["f1"] == m["false_positive_rate"] == 0.5


def test_template_summary_scores_whole_templates():
    df = pd.DataFrame({"template_id": ["a", "a", "b", "b"], "label": [1, 1, 0, 0]})
    assert template_summary(df, [0.9, 0.8, 0.1, 0.3], 0.5)["genuine_template_specificity"] == 1.0
    assert template_summary(df, [0.9, 0.8, 0.9, 0.7], 0.5)["genuine_template_specificity"] == 0.0
    assert template_summary(df, [0.9, 0.8, 0.1, 0.3], 0.5)["scam_template_recall"] == 1.0


def test_thresholds_separate_clean_scores():
    df = pd.DataFrame({"template_id": list("aabb"), "label": [1, 1, 0, 0]})
    prob = [0.95, 0.9, 0.1, 0.2]
    assert 0.2 < pick_balanced_threshold(df, prob) <= 0.9
    assert pick_threshold(df["label"], prob, max_fpr=0.0) > 0.2
