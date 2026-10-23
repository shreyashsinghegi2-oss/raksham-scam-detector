# External data

`uci_sms_spam.tsv` is the **SMS Spam Collection** (5,574 English text messages, labelled `ham` or `spam`), collected by T. A. Almeida, J. M. Gómez Hidalgo and A. Yamakami and published by the UCI Machine Learning Repository: https://archive.ics.uci.edu/dataset/228/sms+spam+collection

Citation: Almeida, T. A., Gómez Hidalgo, J. M., Yamakami, A. (2011). Contributions to the study of SMS spam filtering: new collection and results. Proceedings of the 2011 ACM Symposium on Document Engineering (DocEng '11).

This copy was downloaded from a public GitHub mirror (justmarkham/pycon-2016-tutorial, `data/sms.tsv`) because the UCI site was not reachable from the build sandbox. Check the licence on the UCI page before redistributing it.

How it is used: only as extra training data, at a quarter of the weight of a Raksham message, and never scored. It is UK and Singapore SMS from the 2000s, so it adds variety in genuine and promotional messages but no Indian fraud patterns. `experiments/external_data.py` compares training with and without it.

Datasets considered and not used: a 5,240-message Nigerian SMS set (no licence, personal messages with metadata); Hindi, Hinglish, Bangla and smishing sets on Hugging Face, Mendeley and IEEE DataPort (not reachable from the sandbox, and some need a licence check).
