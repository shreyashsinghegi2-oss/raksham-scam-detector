# Raksham Scam Detector

A text classifier that tells scam messages from genuine ones in Indian SMS, WhatsApp, email and call transcripts (English, Hindi and Hinglish). Trained on the Raksham scam dataset (8,022 messages, 17 scam types).

It returns a verdict and a scam probability. For scams it also returns a likely scam type with its confidence, and the words that pushed the score up.

## Data (not in this repository)

The training dataset (`data/raksham_scam_dataset.csv`) and the external SMS file (`data/external/uci_sms_spam.tsv`) are not committed, because their licences are not mine to grant. To retrain, put your copy of the Raksham dataset at `data/raksham_scam_dataset.csv`; see `data/external/README.md` for the optional external file. The trained model that the website needs is committed as plain files in `deploy/model/`, so the site deploys without any data. Tests that need the data skip themselves when it is missing.

## Use it

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/raksham-train                       # about 25 seconds; writes models/ and reports/
.venv/bin/raksham-predict "Your KYC has expired. Share the OTP now or your account will be blocked."
.venv/bin/raksham-predict --strict "..."      # fewer false alarms, more missed scams
.venv/bin/raksham-eval                        # 24 hand-written messages that are not from the dataset
.venv/bin/pytest
```

Example output:

```json
{
  "text": "Your KYC has expired. Share the OTP now or your account will be blocked.",
  "verdict": "scam",
  "scam_probability": 0.977,
  "scam_type": "kyc_account_block",
  "scam_type_guess": "kyc_account_block",
  "scam_type_confidence": 0.576,
  "signals": ["the otp", "account", "your account"]
}
```

When the scam-type confidence is below 0.5, `scam_type` is `"uncertain"` and `scam_type_guess` holds the best guess.

## Deploy it

**Vercel:** `deploy/` is a ready-to-deploy, NumPy-only app (no scikit-learn, 1.8 MB model). Run `raksham-export` after training to refresh `deploy/model/`, then follow `deploy/DEPLOY.md`.

**Anywhere else:** the model is also served by a FastAPI app (`src/raksham/api.py`).

The model is served by a small web API (`src/raksham/api.py`).

```bash
.venv/bin/pip install -e ".[serve]"
.venv/bin/raksham-train                                   # once, to create models/
RAKSHAM_API_KEY=choose-a-long-secret .venv/bin/uvicorn raksham.api:app --host 0.0.0.0 --port 8000
```

```bash
curl localhost:8000/health
curl -X POST localhost:8000/predict -H "x-api-key: choose-a-long-secret" -H "content-type: application/json" \
  -d '{"messages": ["Your KYC has expired. Share the OTP now."], "strict": false}'
```

- `POST /predict` takes 1 to 50 messages of up to 2,000 characters and returns one result per message, in order, without echoing the text.
- Set `RAKSHAM_API_KEY` to require an `x-api-key` header. Without it the endpoint is open, so do that only on a private network.
- Messages are scored in memory. The app does not store them and does not log request bodies. Put the service behind HTTPS (your host or a proxy) because messages can contain personal details.
- Container: `docker build -t raksham-scam-detector .` trains the model during the build, so the image is self-contained. It runs as a non-root user and listens on port 8000. The Dockerfile has not been built in this repository's sandbox because the Docker daemon was not running there; run the build once before relying on it.
- Any host that runs a container works (Cloud Run, Fly.io, Render, a VM). One small instance is enough: scoring takes milliseconds.

## How it works

- Features: TF-IDF over word pairs and over character 2-5-grams (the second survives spelling noise, SMS shorthand and Hinglish).
- Model: logistic regression, chosen over a calibrated linear SVM on cross-validation. A second logistic regression picks the scam type among scam messages.
- Input: message text only. The dataset's sender, link and phone columns are not used, because a message you check will not come with them.
- Two thresholds: **balanced** (0.71) is the default; **strict** (0.93) keeps false alarms on development data at or under 1%.

## How good is it

Every message in the dataset comes from one of 138 templates, about 50 near-copies each. Splitting messages at random would let the model memorise templates and report scores near 100%, so every figure here is measured on templates the model has not seen. Full tables are in `reports/metrics.md`.

Leave-templates-out cross-validation over all 138 templates (the most stable estimate):

| | Scam templates caught | Genuine templates left alone |
|---|---|---|
| All | 93% | 80% |
| English | 94% | 85% |
| Hindi | 100% | 83% |
| Hinglish | 82% | 56% |

Message-level: F1 0.94, ROC AUC 0.975. On the dataset's own held-out test split (25 templates the model never saw): recall 93%, false positive rate 7.6%, ROC AUC 0.98. At the strict threshold, false alarms on that split are 0% but recall falls to 67%.

On 24 messages written separately from the dataset: all 12 scams caught at the default threshold, and 2 of 12 genuine messages wrongly flagged ("premium received", "salary credited"). At the strict threshold, no genuine message is flagged and 2 scams are missed. This set is tiny and written by the project author; it shows behaviour, not accuracy.

## More data

I looked for more data to improve the model. Most Indian, Hindi, Hinglish and smishing datasets are on Hugging Face, Mendeley and IEEE DataPort, which the build sandbox could not reach. The one usable source was the English SMS Spam Collection (UCI, 5,160 unique messages after cleaning), now in `data/external/` with its citation. A Nigerian SMS set was rejected: no licence, and it contains personal messages.

`experiments/external_data.py` tests whether adding it helps on templates the model has not seen (6-fold leave-templates-out, five random template assignments):

| Mean of 5 splits | Raksham only | + external (weight 0.25) |
|---|---|---|
| ROC AUC | 0.976 | 0.977 |
| Scam templates caught | 96% | 91% |
| Genuine templates left alone | 77% | 86% |
| Hinglish genuine templates left alone | 47% | 62% |

**The result is mixed.** The code default does not use it, but the live website does (it is exported with `raksham-export --external`, and the page starts in strict mode). The ranking quality (AUC) is unchanged. The external data mostly moves the balance toward fewer false alarms and fewer caught scams. On the dataset's own held-out test split it was worse (AUC 0.98 to 0.94, false alarms 7.6% to 31%), and on my 24 hand-written messages it made no net difference. The differences between template splits (up to 0.04 AUC) are larger than the average effect. The variant can be trained with `raksham-train --external` (it writes `models/scam_detector_external.joblib` and `reports/metrics_external.md`).

**Add your own data:** put a file named `data/external/extra_<name>.csv` with columns `text` and `label` (1 = scam, 0 = genuine) next to the others and run `raksham-train --external`. Real Indian messages, especially genuine bank, payment, salary and insurance notices, are what the model needs most. Download them yourself (for example the Hindi and Hinglish sets mentioned above) and check each licence first.

## Limits

- **All data is synthetic and template-written.** These scores describe how well the model separates this dataset's scam and genuine styles. They do not measure accuracy on real messages. Test it on messages you have collected before relying on it.
- **Genuine messages are the weak spot.** The dataset has 56 genuine templates against 82 scam templates, and few cover payment confirmations (salary, premiums, refunds). Hinglish genuine messages are the least reliable. More real genuine messages would help most.
- **Scam type is a weak hint.** Each type has 3 to 6 templates, and type identification on unseen templates is about 27% accurate. Use the verdict, not the type.
- **A verdict is not proof.** Scammers change wording. A short, unusual or very formal scam can score low, and a genuine message that asks you to act can score high.
- The deployed model is trained on all templates, including the test split, so the held-out numbers describe the earlier train+val model.

## Next steps

1. Add real, consented genuine and scam messages, especially payment confirmations and Hinglish (see "More data").
2. Compare against a pretrained multilingual text encoder. It was not possible here because the sandbox could not reach a model hub.
3. Add a sender-header and link-domain check as separate signals, since the text alone cannot see them.

## Real Indian SMS added (24 Oct 2026)

The synthetic Raksham data does not transfer to real messages. On 513 real Indian SMS held out from the India Spam SMS set (never trained on), the Raksham-only model ranked messages **worse than chance (AUC 0.39)**. Adding real data fixed this:

| Model | AUC on the 513 held-out real SMS | Scams caught / false alarms (strict) |
|---|---|---|
| Raksham only | 0.39 | 18/187 / 76/326 |
| + UCI SMS Spam Collection | 0.87 | 63/187 / 14/326 |
| + India SMS + Indian-language scam reports (live) | 0.999 | 167/187 / 0/326 |

Cautions: only 6% of the held-out messages have a close look-alike in the training part, and on the 357 with no look-alike the AUC is still 0.997, but both parts come from the same collection, so real-world accuracy will be lower. On the 56 hand-written messages the live model is slightly worse on genuine bank notices (7/28 false alarms balanced, 2/28 strict), because the genuine Indian messages it learned from are mostly chat, not bank alerts. Leave-templates-out cross-validation on the Raksham data moved from 96% scams caught / 84% genuine left alone to 87% / 88%. Sources and licences are in `data/external/README.md`; the data files are not committed.
