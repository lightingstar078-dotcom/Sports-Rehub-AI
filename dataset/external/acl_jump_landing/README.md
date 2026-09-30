# Public ACL jump-landing research data

This folder is for a separate research experiment and must not be used as a
replacement for the app's return-to-play (GREEN/YELLOW/RED) readiness dataset.

## Source and scope

Calisti et al. (2025), “Motion capture data of six jump-landings, fatigued and
non-fatigued, after ACL injury.” The dataset contains motion-capture trials
from participants with a history of ACL injury and healthy controls. The source
target is participant group (ACL history vs control), not clinical readiness,
re-injury probability, or clearance to return to sport.

- Article: https://www.nature.com/articles/s41597-025-05934-5
- Dataset DOI: https://doi.org/10.6084/m9.figshare.28890545.v1
- License: CC BY 4.0 (attribute the authors and source in any redistribution)
- Downloaded archive: `Kinematic_data.zip` (kept local; not committed to Git)

Any derived table/model must preserve participant IDs for group-aware train/test
splitting and must document its feature extraction and limitations. Trial rows
from one participant must never be split across train and test. This is a
research demonstration only, not validated for diagnosis, rehabilitation
decisions, or clinical use.

## Reproduce locally (PowerShell)

The 6.27 GiB source ZIP and original XLSX files are kept under `source/` and are
ignored by Git. After placing/downloading the Figshare archive and the participant
and labeling spreadsheets there, run:

```powershell
py -3.13 -m pip install -r ml_training/requirements-acl-research.txt
py -3.13 ml_training/extract_acl_history_dataset.py
py -3.13 ml_training/train_acl_history_model.py
```

The converter writes `derived/acl_jump_trials.csv`; training writes a research
model artifact (ignored by Git) and the group-held-out metrics in
`derived/acl_history_cv_results.json`. Validation uses 5-fold stratified group
cross-validation by participant. These outputs are not connected to the app's
readiness predictor.

The current conversion produces 2,199 unique trials from 43 participants (22
controls, 21 ACL-history). The initial 5-fold participant-held-out baseline
achieves 55.8% participant-level accuracy and 55.7% balanced accuracy. This is
close to chance and should be treated as a weak research baseline, not evidence
of clinical performance. The reported scope and limitations are also recorded
in the JSON evaluation file.
