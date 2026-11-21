# Model card: Raksham scam detector

Every figure below is copied from a file in this repository (`reports/*.md`, `reports/*.json`, `deploy/model/meta.json`, `README.md`) or from the code. Nothing here was measured separately for this card. If a number and a report disagree, the report wins.

## Summary

| | |
|---|---|
| Task | Binary text classification: scam or genuine message. A second model guesses the scam type for messages flagged as scams. |
| Input | Message text only, up to 2,000 characters (API limit). Sender, link and phone fields are not used. |
| Languages | English, Hindi (Devanagari), Hinglish (Hindi in Latin script). |
| Model | TF-IDF over word 1-2-grams and character 2-5-grams, then logistic regression. A second logistic regression picks one of 17 scam types. |
| Runtime | scikit-learn for training. The deployed app (`deploy/`) scores with NumPy only, from a model of about 1.8 MB stored as plain files in `deploy/model/`. |
| Output | `verdict`, `scam_probability`, `scam_type` (or `"uncertain"` when its confidence is below 0.5), `scam_type_confidence` and the words that pushed the score up. |
| Licence | Code: MIT (`LICENSE`). The data files are not covered and are not in this repository. |

## Intended use

Intended for:

- A first-pass signal in a demo, a research prototype or a personal tool that helps someone decide whether a message looks like an Indian SMS, WhatsApp, email or call-transcript scam.
- A baseline to compare better models against on unseen templates.
- Teaching: the model is small, readable and trained in about 25 seconds.

Not intended for:

- Blocking, deleting or reporting messages automatically. A verdict is not proof (see Limits).
- Any decision about a person, an account or a transaction without a human check.
- Languages other than English, Hindi and Hinglish. Other languages are not supported and are not detected, so they can silently score as genuine.
- Judging a message by its sender or links. Neither is an input.

## Training data

- **Raksham scam dataset**: 8,022 synthetic messages in 17 scam types plus genuine messages, written from 138 templates (82 scam, 56 genuine), about 50 near-copies per template. English 94 templates, Hindi 18, Hinglish 26. The file is not committed because its licence is not the repository owner's to grant.
- **External messages** (variant deployed on the site, `deploy/model/meta.json` says `"variant": "external"`): 8,198 extra messages at a quarter of the weight of a Raksham message, never scored. They come from the UCI SMS Spam Collection (5,160 unique messages after cleaning), 75% of the India Spam SMS Classification set (MIT) and 1,500 scam messages sampled from the IMC 2025 "Fishing for Smishing" dataset (CC BY 4.0). Sources, licences and the cleaning steps are in `data/external/README.md`. None of the data files are committed.
- The deployed model was fitted on all templates, including the dataset's own test split.

## Evaluation

The dataset is built from templates. A random split would let the model memorise templates and score near 100%, so all headline figures hold out whole templates: a template counts as caught or missed as a whole.

**Deployed variant (external data added)**, from `reports/metrics_external.md`. Balanced threshold 0.6, strict threshold 0.9.

Leave-templates-out cross-validation over all 138 templates (6 folds):

| | Scam templates caught | Genuine templates left alone | Message F1 | ROC AUC |
|---|---|---|---|---|
| All | 0.8659 | 0.875 | 0.92 | 0.976 |
| English | 0.8868 | 0.9024 | 0.9486 | 0.986 |
| Hindi | 0.9167 | 0.8333 | 0.8944 | 0.9963 |
| Hinglish | 0.7647 | 0.7778 | 0.8248 | 0.9163 |

Scam-type identification across unseen templates: accuracy 0.2669, macro F1 0.2182 over 17 types.

**Raksham-only variant (code default)**, from `reports/metrics.md`. Balanced threshold 0.71, strict threshold 0.93. Cross-validation over all templates: scam templates caught 0.9268, genuine templates left alone 0.8036, message F1 0.9404, ROC AUC 0.9752. On the dataset's own held-out test split (25 templates, none seen in training): recall 0.9291, false positive rate 0.0759, ROC AUC 0.9803 at the balanced threshold; at the strict threshold the false positive rate is 0.0 and recall falls to 0.6711.

**Real Indian SMS check** (README, "Real Indian SMS added"). On 513 real SMS held out from the India Spam SMS set, the Raksham-only model ranked messages worse than chance (AUC 0.39). The model deployed on the site scored AUC 0.999 on the same 513 messages, catching 167 of 187 scams with 0 of 326 genuine flagged at the strict threshold. The held-out messages come from the same collection as part of the training data, so this is an optimistic estimate of real-world accuracy.

## Limits and risks

- **Synthetic data.** The Raksham messages are template-written. Scores on them show how well the model separates this dataset's styles, not how well it works on real messages. The 0.39 AUC above is the clearest evidence of that gap.
- **Genuine messages are the weak spot.** There are fewer genuine templates than scam templates, and few cover payment confirmations such as salary, premiums or refunds. On 56 hand-written messages the deployed model gave 7 of 28 false alarms at the balanced threshold and 2 of 28 at the strict threshold (README).
- **Hinglish is the least reliable language.** In the deployed variant's cross-validation, Hinglish scam templates caught is 0.7647 against 0.8868 for English.
- **Scam type is a weak hint.** Each type has 3 to 6 templates and type accuracy on unseen templates is 0.2669. Use the verdict, not the type.
- **Vocabulary, not intent.** A bag-of-words model scores words. `docs/ARCHITECTURE_V2.md` lists measured failures: a real bank-style fraud alert scoring 0.960 (scam), a request for "the code I just texted you" scoring 0.040 (genuine), and a French scam scoring 0.337 (genuine).
- **Threshold trade-off.** The strict threshold keeps false alarms low on development data and misses more scams. Choose it on purpose, not by default.
- **Adversarial drift.** Scammers change wording. Short, unusual or very formal scams can score low. A fix for fancy Unicode letters (NFKC normalisation) exists, but other obfuscation is not covered.
- **Privacy.** Messages can contain personal details. The API scores them in memory and does not store them or log request bodies. Serve it over HTTPS and set `RAKSHAM_API_KEY` if it is not on a private network.

## Edge-case behaviour that is tested

`tests/test_edge_inputs.py` runs on the committed `deploy/model` (no dataset needed) and checks that blank text, a 100,000-character token, emoji, Hindi, Hinglish, Arabic, zero-width and control characters all return well-formed results, that scoring is deterministic and independent of batch order, and that the API length limit counts characters, not bytes. These tests check that the code behaves, not that the verdicts are right.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest                      # runs without the dataset; data-dependent tests skip
.venv/bin/raksham-train               # needs data/raksham_scam_dataset.csv; writes models/ and reports/
.venv/bin/raksham-train --external    # adds data/external/ files; writes reports/metrics_external.md
.venv/bin/raksham-export --external   # refreshes deploy/model/
```

## Citation and contact

Please cite the repository and, for the external data, the sources listed in `data/external/README.md`. Issues and pull requests are welcome; see `CONTRIBUTING.md` and `SECURITY.md`.
