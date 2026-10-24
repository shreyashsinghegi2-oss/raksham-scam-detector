import csv
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "raksham_scam_dataset.csv"
EXTERNAL_PATH = ROOT / "data" / "external" / "uci_sms_spam.tsv"
MODEL_PATH = ROOT / "models" / "scam_detector.joblib"
REPORTS = ROOT / "reports"


def load(path: Path = DATA_PATH) -> pd.DataFrame:
    """The dataset with clean text. Only `text` is used as a model input: the other columns
    (has_link, mentions_otp_pin, sender_header, ...) are labels or metadata a real message does not carry."""
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["text"] = df["text"].astype(str).str.strip()
    return df


def dev_and_test(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Development data (train + val) and the held-out test split, which is never used for any choice."""
    dev = df[df["split"].isin(["train", "val"])].reset_index(drop=True)
    test = df[df["split"] == "test"].reset_index(drop=True)
    return dev, test


def load_external(exclude_texts=frozenset()) -> pd.DataFrame:
    """The UCI SMS Spam Collection, plus any data/external/extra_*.csv, as optional extra training data (label 1 = spam, 0 = ham), deduplicated and with any
    text already in the Raksham data removed. It is English SMS from the UK and Singapore, not Indian fraud:
    it only widens the range of genuine and promotional messages the model has seen. See data/external/README.md."""
    df = pd.read_csv(EXTERNAL_PATH, sep="\t", header=None, names=["name", "text"], quoting=csv.QUOTE_NONE, encoding="utf-8")
    df["text"] = df["text"].astype(str).str.strip()
    df = df.drop_duplicates("text")
    df = df[~df["text"].isin(exclude_texts)]
    df["label"] = (df["name"] == "spam").astype(int)
    frames = [df[["text", "label"]]]
    for path in sorted(EXTERNAL_PATH.parent.glob("extra_*.csv")):  # your own data: columns text,label (1 = scam, 0 = genuine)
        extra = pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)  # a message that is literally "NA" or "null" is text, not a missing value
        if not {"text", "label"} <= set(extra.columns) or not set(extra["label"].unique()) <= {0, 1}:
            raise ValueError(f"{path.name} needs columns text and label, with label 1 for scam and 0 for genuine")
        extra["text"] = extra["text"].astype(str).str.strip()
        extra = extra[extra["text"] != ""]
        frames.append(extra[["text", "label"]])
    out = pd.concat(frames).drop_duplicates("text")
    out = out[~out["text"].isin(exclude_texts)]
    return out.reset_index(drop=True)
