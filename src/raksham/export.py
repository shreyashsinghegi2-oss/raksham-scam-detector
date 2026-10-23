"""Export the trained model to plain files for the Vercel deployment (deploy/model/).

The deployed function does not use scikit-learn or pickle. It reads vocabularies, inverse-document-frequency weights and
coefficients from these files and scores text with NumPy only (deploy/api/_lite.py). That keeps the function small and
removes the need to unpickle a file on a server.
"""
import json

import joblib
import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from .data import MODEL_PATH, REPORTS, ROOT

DEPLOY_MODEL = ROOT / "deploy" / "model"


def space(prefix: str, pipeline, arrays: dict, vocabs: dict) -> dict:
    """One feature space: a word vectoriser followed by a character vectoriser, as in features()."""
    union = pipeline.named_steps["tfidf"]
    spec, offset = {}, 0
    for name, vec in union.transformer_list:
        arrays[f"{prefix}_{name}_idf"] = vec.idf_.astype(np.float64)
        vocabs[f"{prefix}_{name}"] = {term: int(i) for term, i in vec.vocabulary_.items()}
        spec[name] = {"ngram": list(vec.ngram_range), "offset": offset, "size": len(vec.vocabulary_)}
        offset += len(vec.vocabulary_)
    spec["features"] = offset
    return spec


def main() -> None:
    bundle = joblib.load(MODEL_PATH)
    if bundle["detector_name"] != "logreg":
        raise SystemExit("Export supports the logistic-regression detector only.")
    arrays, vocabs = {}, {}
    detector = bundle["detector"]
    det_spec = space("det", detector, arrays, vocabs)
    kinds = bundle["type_model"]
    type_spec = space("type", kinds, arrays, vocabs)

    det_clf, explain_clf = detector.named_steps["clf"], bundle["explainer"].named_steps["clf"]
    if not np.allclose(det_clf.coef_, explain_clf.coef_, atol=1e-6):
        raise SystemExit("The detector and the explainer differ; export both before using this script.")
    arrays["det_coef"] = det_clf.coef_[0].astype(np.float64)
    arrays["type_coef"] = kinds.named_steps["clf"].coef_.astype(np.float64)
    arrays["type_intercept"] = kinds.named_steps["clf"].intercept_.astype(np.float64)

    metrics = json.loads((REPORTS / "metrics.json").read_text(encoding="utf-8"))
    cv = metrics["cross_validation"]
    meta = {
        "detector": bundle["detector_name"], "trained_on": bundle["trained_on"], "thresholds": bundle["thresholds"],
        "det_intercept": float(det_clf.intercept_[0]), "det_space": det_spec, "type_space": type_spec,
        "type_classes": [str(c) for c in kinds.named_steps["clf"].classes_],
        "stop_words": sorted(ENGLISH_STOP_WORDS),
        "evaluation": {
            "method": "leave-templates-out cross-validation over all templates",
            "scam_templates_caught": cv["overall"]["templates"]["scam_template_recall"],
            "genuine_templates_left_alone": cv["overall"]["templates"]["genuine_template_specificity"],
            "roc_auc": cv["overall"]["messages"]["roc_auc"],
            "scam_type_accuracy": cv["scam_type"]["accuracy"],
        },
    }
    DEPLOY_MODEL.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(DEPLOY_MODEL / "weights.npz", **arrays)
    (DEPLOY_MODEL / "vocab.json").write_text(json.dumps(vocabs, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (DEPLOY_MODEL / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    sizes = {p.name: p.stat().st_size for p in DEPLOY_MODEL.iterdir()}
    print(f"wrote {DEPLOY_MODEL}: " + ", ".join(f"{k} {v / 1e6:.1f} MB" for k, v in sizes.items()))
    print(f"detector features {det_spec['features']}, type features {type_spec['features']}, type classes {len(meta['type_classes'])}")


if __name__ == "__main__":
    main()
