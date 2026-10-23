import pytest

from raksham import data

needs_data = pytest.mark.skipif(not data.DATA_PATH.exists(), reason="the dataset is not in this repository: put raksham_scam_dataset.csv in data/")
needs_external = pytest.mark.skipif(not data.EXTERNAL_PATH.exists(), reason="data/external/uci_sms_spam.tsv is not in this repository")


@needs_data
def test_dataset_columns_and_labels():
    df = data.load()
    assert {"text", "label", "template_id", "split", "scam_type", "language"} <= set(df.columns)
    assert set(df["label"].unique()) == {0, 1}
    assert df["text"].str.len().min() > 0


@needs_data
def test_test_split_templates_and_texts_are_unseen():
    dev, test = data.dev_and_test(data.load())
    assert not set(dev["template_id"]) & set(test["template_id"])
    assert not set(dev["text"]) & set(test["text"])


@needs_data
@needs_external
def test_external_data_is_clean_and_does_not_overlap():
    df = data.load()
    ext = data.load_external(set(df["text"]))
    assert len(ext) > 1000 and ext["text"].is_unique
    assert set(ext["label"].unique()) == {0, 1}
    assert not set(ext["text"]) & set(df["text"])


@needs_external
def test_extra_csv_files_are_picked_up_and_validated(tmp_path, monkeypatch):
    import shutil

    import pytest

    shutil.copy(data.EXTERNAL_PATH, tmp_path / "uci_sms_spam.tsv")
    monkeypatch.setattr(data, "EXTERNAL_PATH", tmp_path / "uci_sms_spam.tsv")
    base = len(data.load_external())
    (tmp_path / "extra_mine.csv").write_text('text,label\n"Your parcel is held, pay Rs 50 now",1\nSee you at 6,0\n', encoding="utf-8")
    assert len(data.load_external()) == base + 2
    (tmp_path / "extra_bad.csv").write_text("message,verdict\nhello,spam\n", encoding="utf-8")
    with pytest.raises(ValueError):
        data.load_external()
