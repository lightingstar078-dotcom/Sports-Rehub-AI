import os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FALLBACK_DIR = Path(os.getenv("STORAGE_DIR", BASE / "storage")) / "videos"
FALLBACK_DIR.mkdir(parents=True, exist_ok=True)

def configured() -> bool:
    return all(os.getenv(k) for k in ["S3_BUCKET", "S3_ENDPOINT", "S3_ACCESS_KEY", "S3_SECRET_KEY"])

def upload(path: str) -> str | None:
    source=Path(path)
    if not configured():
        target=FALLBACK_DIR / source.name
        if source.resolve() != target.resolve():
            target.write_bytes(source.read_bytes())
        return str(target)
    import boto3
    bucket=os.environ["S3_BUCKET"]
    endpoint=os.environ["S3_ENDPOINT"]
    key=f"sports-rehab/{source.name}"
    client=boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=os.environ["S3_ACCESS_KEY"], aws_secret_access_key=os.environ["S3_SECRET_KEY"], region_name=os.getenv("S3_REGION","auto"))
    client.upload_file(str(source), bucket, key, ExtraArgs={"ContentType":"video/mp4"})
    return key
