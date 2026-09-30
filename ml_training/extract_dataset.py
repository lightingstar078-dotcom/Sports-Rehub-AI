from pathlib import Path
import sys, csv
sys.path.insert(0, str(Path(__file__).resolve().parents[0] / ".." / "backend"))
from vision.feature_extractor import extract_features

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "dataset" / "labels.csv"
OUT = ROOT / "dataset" / "processed" / "movement_features.csv"

def main():
    if not LABELS.exists():
        print("Missing dataset/labels.csv. Add controlled videos and labels first.")
        return
    rows=[]
    required = {"video_id", "exercise", "pain_score", "psychological_readiness", "label"}
    with LABELS.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        missing_columns = required - set(reader.fieldnames or [])
        if missing_columns:
            raise SystemExit(f"dataset/labels.csv is missing columns: {', '.join(sorted(missing_columns))}")
        for line_number, r in enumerate(reader, start=2):
            if not any((value or '').strip() for value in r.values()):
                continue
            if r["exercise"] not in {"squat", "single_leg_hop", "single_leg_balance"}:
                print(f"Skipping line {line_number}: unsupported exercise '{r['exercise']}'")
                continue
            if r["label"] not in {"GREEN", "YELLOW", "RED"}:
                print(f"Skipping line {line_number}: label must be GREEN, YELLOW, or RED")
                continue
            p = ROOT / "dataset" / "raw" / r["exercise"] / r["video_id"]
            ext = p.suffix or ".mp4"
            if not p.exists():
                for e in [".mp4",".mov",".m4v",".webm",".avi",".mkv"]:
                    candidate = p.with_suffix(e)
                    if candidate.exists(): p=candidate; break
            if not p.exists():
                print(f"Skipping missing video: {r['video_id']}"); continue
            fts=extract_features(str(p), r["exercise"])
            rows.append({"video_id":r["video_id"],"exercise":r["exercise"],**{k:r[k] for k in ["pain_score","psychological_readiness","label"]},**fts})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        OUT.unlink(missing_ok=True)
        raise SystemExit("No real labelled videos were extracted. Add valid videos and labels before real-model training.")
    with OUT.open("w",newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows)} real labelled rows to {OUT}")

if __name__ == "__main__": main()
