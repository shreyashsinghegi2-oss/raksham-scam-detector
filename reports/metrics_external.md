# Results

Detector: `logreg` (TF-IDF word and character n-grams with logistic regression), fitted on the Raksham messages plus 8198 external messages at a quarter weight (never scored). Verdict threshold 0.6 (balanced); strict threshold 0.9 (at most 1% false alarms on development data).

Every message in the dataset comes from one of 138 templates, about 50 near-copies each. All results below are therefore also given per template: a template counts as caught or missed as a whole. Messages from one template never appear on both sides of any split.

## 1. Cross-validation over all templates (leave-templates-out, 6 folds)

This is the most stable estimate: every template is scored by a model that never saw it.

| | Scam templates caught | Genuine templates left alone | Message accuracy | Message F1 | ROC AUC |
|---|---|---|---|---|---|
| All (82 scam, 56 genuine templates) | 0.8659 | 0.875 | 0.9134 | 0.92 | 0.976 |
| en (53 scam, 41 genuine) | 0.8868 | 0.9024 | 0.9475 | 0.9486 | 0.986 |
| hindi (12 scam, 6 genuine) | 0.9167 | 0.8333 | 0.8619 | 0.8944 | 0.9963 |
| hinglish (17 scam, 9 genuine) | 0.7647 | 0.7778 | 0.7846 | 0.8248 | 0.9163 |

Scam-type identification across unseen templates: accuracy 0.2669, macro F1 0.2182 over 17 types.

## 2. The dataset's own held-out test split

A model fitted on train+val only (6558 messages) and scored once on the test split (1464 messages, 25 templates, none seen in training). The split has one test template per scam type and only 8 genuine templates, so treat each figure as coarse.

| Threshold | Scam templates caught | Genuine templates left alone | Message recall | False positive rate | Message F1 | ROC AUC |
|---|---|---|---|---|---|---|
| balanced (0.6) | 0.8235 | 0.75 | 0.7726 | 0.2461 | 0.7856 | 0.9382 |
| strict (0.9) | 0.5882 | 1.0 | 0.6345 | 0.0 | 0.7764 | 0.9382 |

Held-out test by language (balanced threshold):

| Language | Scam templates caught | Genuine templates left alone |
|---|---|---|
| en | 0.9091 | 1.0 |
| hindi | 1.0 | 0.5 |
| hinglish | 0.6 | 0.0 |

Held-out test by scam type (one template each; balanced threshold):

| Scam type | Messages flagged | Type identified |
|---|---|---|
| digital_arrest_parcel | 1.0 | 1.0 |
| digital_arrest_relative | 0.9608 | 0.0 |
| electricity_kyc_apk | 0.0 | 0.0 |
| fake_customer_care | 1.0 | 1.0 |
| fake_job_fee | 1.0 | 0.0 |
| fake_trading_app | 1.0 | 1.0 |
| impersonation_money_request | 0.0 | 0.0 |
| kyc_account_block | 1.0 | 0.1778 |
| otp_pin_cvv_request | 1.0 | 0.0123 |
| part_time_task_job | 1.0 | 0.6667 |
| prize_lottery_offer | 1.0 | 0.0 |
| remote_access_app | 1.0 | 0.0 |
| senior_citizen_offers | 1.0 | 0.0 |
| sextortion | 0.0 | 0.0 |
| stock_tips_pump_dump | 1.0 | 1.0 |
| trai_dot_disconnection | 1.0 | 0.0 |
| upi_collect_request | 1.0 | 1.0 |

## Limits

- Every message is synthetic and written from templates. These scores show how well the model separates this dataset's scam and genuine styles on unseen templates. They do not measure accuracy on real messages.
- Each scam type has 3 to 6 training templates, so the type label is a weak hint and is returned with its own confidence. The scam or genuine verdict is the reliable part.
- Genuine messages that look like scams (money sent between family members, one-time-password notices) are the main false alarms. The deployed model is trained on all templates, including the test split, so the numbers in section 2 describe the earlier train+val model.
- Only the message text is used. Sender, link and phone metadata are not available to the model.
