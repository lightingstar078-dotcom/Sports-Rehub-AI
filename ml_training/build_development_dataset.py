from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dataset' / 'processed' / 'development_features.csv'
RNG = np.random.default_rng(42)
FEATURES = [
    'movement_quality', 'symmetry', 'rom', 'stability',
    'landing_control', 'movement_consistency', 'pain',
    'psychological_readiness', 'recovery_trend'
]

def clipped(n, mean, sd):
    return np.clip(RNG.normal(mean, sd, n), 0, 100)

def main():
    # Synthetic development data ONLY for end-to-end software verification.
    # It must never be presented as athlete evidence or clinical validation.
    n_each = 300
    rows = []
    specs = {
        'GREEN': dict(mq=86, sym=91, rom=84, stab=88, land=88, cons=89, pain=1.8, psych=86, trend=86),
        'YELLOW': dict(mq=69, sym=73, rom=67, stab=68, land=64, cons=69, pain=5.0, psych=63, trend=60),
        'RED': dict(mq=45, sym=52, rom=46, stab=43, land=40, cons=48, pain=7.8, psych=42, trend=38),
    }
    for label, s in specs.items():
        n = n_each
        for i in range(n):
            rows.append({
                'video_id': f'dev_{label.lower()}_{i:04d}',
                'exercise': RNG.choice(['squat', 'single_leg_hop', 'single_leg_balance']),
                'movement_quality': float(clipped(1, s['mq'], 7)[0]),
                'symmetry': float(clipped(1, s['sym'], 6)[0]),
                'rom': float(clipped(1, s['rom'], 8)[0]),
                'stability': float(clipped(1, s['stab'], 8)[0]),
                'landing_control': float(clipped(1, s['land'], 8)[0]),
                'movement_consistency': float(clipped(1, s['cons'], 7)[0]),
                'pain': float(np.clip(RNG.normal(s['pain'], 1.1), 0, 10)),
                'psychological_readiness': float(clipped(1, s['psych'], 9)[0]),
                'recovery_trend': float(clipped(1, s['trend'], 10)[0]),
                'label': label,
            })
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f'Wrote {len(df)} synthetic development rows to {OUT}')
    print(df['label'].value_counts().sort_index().to_string())

if __name__ == '__main__':
    main()
