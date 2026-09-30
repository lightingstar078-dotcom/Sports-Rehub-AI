from pathlib import Path
from urllib.request import Request, urlopen
import argparse
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'backend' / 'models' / 'pose_landmarker_full.task'
TEMP = OUT.with_suffix('.task.download')
URL = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task'

parser = argparse.ArgumentParser()
parser.add_argument('--force', action='store_true')
args = parser.parse_args()

def valid_model(path: Path) -> bool:
    """A .task file is a model bundle (ZIP), not merely any non-empty file."""
    return path.is_file() and path.stat().st_size > 1_000_000 and zipfile.is_zipfile(path)

if OUT.exists() and valid_model(OUT) and not args.force:
    print(f'Already present: {OUT} ({OUT.stat().st_size / 1024 / 1024:.2f} MB)')
    raise SystemExit(0)

OUT.unlink(missing_ok=True)
TEMP.unlink(missing_ok=True)
print(f'Downloading official MediaPipe Pose Landmarker asset to {OUT}')
OUT.parent.mkdir(parents=True, exist_ok=True)
request = Request(URL, headers={'User-Agent': 'Sports-Rehab-AI/1.0'})
try:
    with urlopen(request, timeout=120) as response, TEMP.open('wb') as target:
        expected = int(response.headers.get('Content-Length', '0'))
        while chunk := response.read(1024 * 1024):
            target.write(chunk)
    received = TEMP.stat().st_size
    if expected and received != expected:
        raise RuntimeError(f'Download incomplete: received {received} of {expected} bytes.')
    if not valid_model(TEMP):
        raise RuntimeError('Downloaded file is not a valid MediaPipe task bundle.')
    TEMP.replace(OUT)
    print(f'Saved {received / 1024 / 1024:.2f} MB')
    print(f'SHA-256 {hashlib.sha256(OUT.read_bytes()).hexdigest()}')
except Exception:
    TEMP.unlink(missing_ok=True)
    OUT.unlink(missing_ok=True)
    raise
