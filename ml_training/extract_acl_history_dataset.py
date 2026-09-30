"""Convert the public Figshare ACL jump-landing data to a separate ML table.

This dataset labels previous ACL injury history vs healthy control. It is NOT
the app's GREEN/YELLOW/RED return-to-play target.
"""
from __future__ import annotations

import csv
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "dataset" / "external" / "acl_jump_landing"
ARCHIVE = SOURCE / "Kinematic_data.zip"
SPREADSHEETS = SOURCE / "source"
OUT = SOURCE / "derived" / "acl_jump_trials.csv"

TASK_LABELS = {
    ("CMJ", None): "labeling_CMJ.xlsx",
    ("DJ", None): "labeling_DJ.xlsx",
    ("COH", "l"): "labeling_COH_left.xlsx",
    ("COH", "r"): "labeling_COH_right.xlsx",
    ("MRH", "l"): "labeling_MRH_left.xlsx",
    ("MRH", "r"): "labeling_MRH_right.xlsx",
    ("SLH", "l"): "labeling_SLH_left.xlsx",
    ("SLH", "r"): "labeling_SLH_right.xlsx",
    # The source calls this task uCMJ in the MAT filename but CMJ in its labels.
    ("uCMJ", "l"): "labeling_CMJ_left.xlsx",
    ("uCMJ", "r"): "labeling_CMJ_right.xlsx",
}
MAT_TASKS = ("CMJ", "COH", "DJ", "MRH", "SLH", "uCMJ")
# The source paper explicitly excludes this recorded trial from joint-angle data.
EXCLUDED_TRIALS = {("sub29", "uCMJ", "r", "CMJ_r_t2")}
XML_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _xlsx_rows(path: Path) -> list[list[str]]:
    """Read the simple, single-sheet source XLSX files with stdlib XML."""
    with zipfile.ZipFile(path) as book:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in book.namelist():
            root = ET.fromstring(book.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in item.findall(".//x:t", XML_NS))
                      for item in root.findall("x:si", XML_NS)]
        sheet_path = "xl/worksheets/sheet1.xml"
        sheet = ET.fromstring(book.read(sheet_path))
        rows = []
        for row in sheet.findall(".//x:sheetData/x:row", XML_NS):
            values = []
            for cell in row.findall("x:c", XML_NS):
                value = cell.find("x:v", XML_NS)
                text = value.text if value is not None and value.text else ""
                if cell.get("t") == "s" and text:
                    text = shared[int(text)]
                elif cell.get("t") == "inlineStr":
                    text = "".join(t.text or "" for t in cell.findall(".//x:t", XML_NS))
                values.append(text.strip())
            rows.append(values)
        return rows


def _number(value: str, name: str, path: Path) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {name} value {value!r} in {path.name}") from exc


def _load_labels() -> dict[tuple[str, str, int], str]:
    labels: dict[tuple[str, int, int], str] = {}
    for filename in sorted({name for name in TASK_LABELS.values()}):
        path = SPREADSHEETS / filename
        if not path.exists():
            raise SystemExit(f"Missing public label spreadsheet: {path}")
        rows = _xlsx_rows(path)
        if len(rows) < 2:
            continue
        headers = [h.casefold() for h in rows[0]]
        try:
            sub_col = next(i for i, h in enumerate(headers) if h.strip() == "sub")
            group_col = next(i for i, h in enumerate(headers) if h.startswith("group"))
            fatigue_col = next(
                i for i, h in enumerate(headers)
                if h.startswith("trial") or "nonfatigued" in h or "fatigued" in h
            )
            missing_col = next(i for i, h in enumerate(headers) if "missing data" in h)
        except StopIteration as exc:
            raise ValueError(f"Unexpected label-sheet columns in {filename}: {rows[0]}") from exc
        for row in rows[1:]:
            if len(row) <= max(sub_col, group_col, fatigue_col, missing_col) or not row[sub_col]:
                continue
            if _number(row[missing_col], "missing-data flag", path) != 0:
                continue
            subject = f"sub{_number(row[sub_col], 'subject', path):02d}"
            group_code = _number(row[group_col], "group", path)
            fatigue = _number(row[fatigue_col], "fatigue", path)
            # Trial-label sheets specify 1=control and 2=ACL group.
            if group_code not in (1, 2) or fatigue not in (0, 1):
                continue
            label = "CONTROL" if group_code == 1 else "ACL_HISTORY"
            key = (filename, subject, fatigue)
            previous = labels.setdefault(key, label)
            if previous != label:
                raise ValueError(f"Conflicting participant labels for {key}: {previous} vs {label}")
    return labels


def _iter_trials(value):
    """Recursively yield MATLAB structs containing one trial's angle matrix."""
    if hasattr(value, "_fieldnames"):
        fields = value._fieldnames or []
        if "Joint_Angles" in fields and "File" in fields:
            yield value
            return
        for field in fields:
            yield from _iter_trials(getattr(value, field))
    elif isinstance(value, np.ndarray) and value.dtype == object:
        for item in value.flat:
            yield from _iter_trials(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_trials(item)


def _trial_features(trial) -> dict[str, float]:
    angles = np.asarray(trial.Joint_Angles, dtype=float)
    if angles.ndim != 2 or angles.shape[1] < 1:
        return {}
    # Center a 0.4 s landing window on knee initial contact when available.
    try:
        contact = int(np.asarray(getattr(trial, "IC_K", 0)).squeeze()) - 1  # MATLAB is 1-based
    except (TypeError, ValueError):
        contact = 0
    if contact < 0 or contact >= angles.shape[0]:
        contact = 0
    segment = angles[contact:min(angles.shape[0], contact + 101), :]
    if segment.size == 0:
        segment = angles
    result: dict[str, float] = {}
    for channel in range(segment.shape[1]):
        values = segment[:, channel]
        values = values[np.isfinite(values)]
        if values.size == 0:
            continue
        prefix = f"joint_{channel + 1:02d}"
        result[f"{prefix}_mean"] = float(np.mean(values))
        result[f"{prefix}_std"] = float(np.std(values))
        result[f"{prefix}_range"] = float(np.max(values) - np.min(values))
    return result


def extract() -> int:
    if not ARCHIVE.exists():
        raise SystemExit(f"Download the public data archive first: {ARCHIVE}")
    label_map = _load_labels()
    rows: list[dict[str, object]] = []
    with zipfile.ZipFile(ARCHIVE) as archive:
        for task in MAT_TASKS:
            member = f"Kinematic_data/Joint_angles/{task}.mat"
            print(f"Reading {task}.mat...", flush=True)
            with archive.open(member) as stream:
                data = loadmat(stream, squeeze_me=True, struct_as_record=False)
            if task not in data:
                raise ValueError(f"Expected MATLAB variable {task!r} in {member}")
            matrix = np.asarray(data[task], dtype=object)
            for index in np.ndindex(matrix.shape):
                subject_index = index[0] if len(index) > 1 else index[0]
                subject = f"sub{subject_index + 1:02d}"
                for trial in _iter_trials(matrix[index]):
                    name = str(trial.File).strip()
                    fatigue = int(bool(re.match(r"^f_", name)))
                    side_match = re.search(r"(?:^|_)([lr])_t\d+$", name, re.IGNORECASE)
                    side = side_match.group(1).lower() if side_match else None
                    if (subject, task, side, name) in EXCLUDED_TRIALS:
                        continue
                    label_file = TASK_LABELS.get((task, side))
                    if label_file is None:
                        continue
                    label = label_map.get((label_file, subject, fatigue))
                    if label is None:
                        continue
                    features = _trial_features(trial)
                    if not features:
                        continue
                    rows.append({
                        "participant_id": subject,
                        "task": task,
                        "side": side or "bilateral",
                        "fatigued": fatigue,
                        "trial_file": name,
                        "label": label,
                        **features,
                    })
            del data, matrix
    if not rows:
        raise SystemExit("No labeled joint-angle trials matched the spreadsheets; refusing to write an empty dataset.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    counts: dict[str, int] = {}
    subjects: dict[str, set[str]] = {}
    for row in rows:
        label = str(row["label"])
        counts[label] = counts.get(label, 0) + 1
        subjects.setdefault(label, set()).add(str(row["participant_id"]))
    print(f"Wrote {len(rows)} public ACL-history research trials to {OUT}")
    print("Trial counts:", counts)
    print("Participant counts:", {k: len(v) for k, v in subjects.items()})
    return len(rows)


if __name__ == "__main__":
    extract()
