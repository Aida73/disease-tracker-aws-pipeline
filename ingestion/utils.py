"""
Utilitaires partagés : logging, sauvegarde bronze, upload S3.
"""
 
import logging
import os
import boto3
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
 
 
def setup_logging(name: str) -> logging.Logger:
    """Configure un logger avec format timestamp + niveau."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(name)

def save_to_bronze(df: pd.DataFrame, source: str, dataset: str) -> Path:
    """
    Sauvegarde un DataFrame en Parquet dans data/bronze/{source}/{dataset}/
    partitionné par date d'ingestion.
 
    En local  → écrit dans data/bronze/
    Sur AWS   → upload sur S3 si BRONZE_BUCKET est défini dans les variables d'env
 
    Retourne le chemin local du fichier créé.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    local_dir = Path(f"data/bronze/{source}/{dataset}/ingestion-date={today}")
    local_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{dataset}_{today}.parquet"
    local_path = local_dir / filename
    df.to_parquet(local_path, index=False, engine="pyarrow")

    # Upload S3 if defined
    bucket = os.getenv("BRONZE_BUCKET")
    if bucket:
        s3_key = f"bronze/{source}/{dataset}/ingestion-date={today}/{filename}"
        upload_to_s3(local_path, bucket, s3_key)
    
    return local_path


def upload_to_s3(local_path: Path, bucket: str, s3_key: str) -> None:
    """Upload a file to s3"""
    logger = setup_logging(__name__)
    s3 = boto3.client("s3")
    s3.upload_file(str(local_path), bucket, s3_key)
    logger.info(f"Uploaded {local_path} to s3://{bucket}/{s3_key}")


def read_bronze(source: str, dataset: str, date: str| None=None) -> pd.DataFrame:
    """read bronze parquet file from local or s3
    if date is None, read the latest file
    """

    base = Path(f"data/bronze/{source}/{dataset}")
    if not base.exists():
        raise FileNotFoundError(f"No data found for {source}/{dataset}")
    
    if date:
        partition = base / f"ingestion-date={date}"
    else:
        partions = sorted(base.glob("ingestion-date=*"))
        if not partions:
            raise FileNotFoundError(f"No data found for {source}/{dataset}")
        partition = partions[-1]  # latest partition

    files = list(partition.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"Aucun fichier Parquet dans {partition}")
 
    return pd.read_parquet(files[0])