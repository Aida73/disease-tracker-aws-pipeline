"""
Ingest epidemiological data from the WHO( World Heath Organization) API and save it to the bronze layer.
Source : disease.sh — agrège WHO + JHU + gouvernements nationaux (no API key is required)

Stockage : data/bronze/who/ to Parquet partionnes by date
"""

import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
import ingestion.utils
 
logger = ingestion.utils.setup_logging(__name__)
 
WHO_BASE_URL = "https://disease.sh/v3/covid-19"


def fetch_who_country_data():
    """fetch data from WHO API by country
        Returns a list of raw dicts
    """
    url = f"{WHO_BASE_URL}/countries"
    params = {"yesterday": "false", "sort": "cases"}

    logger.info(f"Fetching WHO country data from {url}")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status() # raise an error for bad status codes
    data = response.json()
    logger.info(f"Fetched {len(data)} countries")

    return data


def fetch_who_historical(days: int = 30) -> list[dict]:
    """
    Retrieves the global historical data for the last N days.
    Normalizes it into date/metric/value rows for easier dbt aggregates.
    """
    url = f"{WHO_BASE_URL}/historical/all"
    response = requests.get(url, params={"lastdays": days}, timeout=30)
    response.raise_for_status()
 
    raw = response.json()
    ingestion_ts = datetime.now(timezone.utc).isoformat()
 
    records = []
    for metric in ["cases", "deaths", "recovered"]:
        if metric in raw:
            for date_str, value in raw[metric].items():
                records.append({
                    "date": date_str,
                    "metric": metric,
                    "value": value,
                    "ingested_at": ingestion_ts,
                })
 
    logger.info(f"{len(records)} lignes historiques normalisées")
    return records


def normalize_country_data(raw_data: list[dict]) -> pd.DataFrame:
    """
    Normilize raw country data into a clean DataFrame.
    Keep all useful columns + ingestion timestamp.
    """
    ingestion_ts = datetime.now(timezone.utc).isoformat()
    ingestion_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
 
    rows = []
    for c in raw_data:
        rows.append({
            "country":             c.get("country"),
            "country_code":        c.get("countryInfo", {}).get("iso2"),
            "continent":           c.get("continent"),
            "population":          c.get("population"),
            "cases_total":         c.get("cases"),
            "cases_today":         c.get("todayCases"),
            "deaths_total":        c.get("deaths"),
            "deaths_today":        c.get("todayDeaths"),
            "recovered_total":     c.get("recovered"),
            "active_cases":        c.get("active"),
            "critical_cases":      c.get("critical"),
            "cases_per_million":   c.get("casesPerOneMillion"),
            "deaths_per_million":  c.get("deathsPerOneMillion"),
            "tests_total":         c.get("tests"),
            "tests_per_million":   c.get("testsPerOneMillion"),
            "updated_at":          pd.to_datetime(c.get("updated"), unit="ms", utc=True),
            "ingested_at":         ingestion_ts,
            "ingestion_date":      ingestion_date,
        })
 
    df = pd.DataFrame(rows)
    logger.info(f"DataFrame normalisé : {df.shape[0]} lignes, {df.shape[1]} colonnes")
    return df


def run_who_ingestion() -> dict:
    """
    Entry point — orchestrates the full WHO ingestion.
    Returns a dict of metrics for Airflow monitoring.
    """
    logger.info("=== WHO ingestion starting===")
    metrics = {"status": "success", "rows_country": 0, "rows_historical": 0, "errors": []}
 
    try:
        # Country data
        raw_countries = fetch_who_country_data()
        df_countries = normalize_country_data(raw_countries)
        path_countries = ingestion.utils.save_to_bronze(df_countries, source="who", dataset="countries")
        metrics["rows_country"] = len(df_countries)
        logger.info(f"Country data saved → {path_countries}")
 
        # World historical data
        raw_hist = fetch_who_historical(days=30)
        df_hist = pd.DataFrame(raw_hist)
        path_hist = ingestion.utils.save_to_bronze(df_hist, source="who", dataset="historical")
        metrics["rows_historical"] = len(df_hist)
        logger.info(f"Historique sauvegardé → {path_hist}")
 
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur API WHO : {e}")
        metrics["status"] = "failed"
        metrics["errors"].append(str(e))
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}", exc_info=True)
        metrics["status"] = "failed"
        metrics["errors"].append(str(e))
 
    logger.info(f"=== End WHO ingestion — status : {metrics['status']} ===")
    return metrics

if __name__ == "__main__":
    result = run_who_ingestion()
    print(result)