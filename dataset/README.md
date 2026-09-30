# Dataset

## Real model path
Put controlled, labeled exercise videos under:

- `raw/squat/`
- `raw/single_leg_hop/`
- `raw/single_leg_balance/`

Create `labels.csv` using the columns in `labels.example.csv`:

```csv
video_id,exercise,pain_score,psychological_readiness,label
squat_001,squat,2,82,GREEN
...
```

Then run:

```powershell
py -3.13 ml_training\extract_dataset.py
py -3.13 ml_training\train_model.py --real-only
python ml_training\evaluate_model.py
```

The real-data commands fail rather than silently using development data when
there are no extracted labelled videos. A balanced dataset with enough examples
per class is required for the train/test split.

## Development model
`python ml_training\build_development_dataset.py` creates synthetic data so the full software pipeline can be tested immediately. The resulting model is explicitly marked `demo=true` and must not be described as clinical or real-world model performance.
