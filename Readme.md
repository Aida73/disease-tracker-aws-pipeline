# Global Disease Tracker — Pipeline épidémiologique AWS

Pipeline de données end-to-end qui ingère des données épidémiologiques mondiales (WHO / disease.sh), les transforme via dbt, et les expose dans un dashboard interactif Streamlit.

## Architecture

```
WHO API ──► Ingestion Python ──► S3 Bronze (Parquet) ──► dbt + Athena ──► S3 Gold ──► Streamlit Dashboard
                │                                              │
           Airflow DAG                              Great Expectations
          (orchestration)                           (qualité données)
```

**Stack :** Python · Apache Airflow · AWS S3 · AWS Glue · AWS Athena · dbt · Great Expectations · Streamlit · Docker

## Structure du projet

```
disease-tracker-aws-pipeline/
├── ingestion/
│   ├── who_ingest.py       # Ingestion WHO / disease.sh
│   ├── cdc_ingest.py       # Ingestion CDC (à venir)
│   └── utils.py            # Helpers : logging, save_to_bronze, upload S3
├── transformation/
│   ├── models/
│   │   ├── staging/        # Modèles dbt bronze → silver
│   │   └── marts/          # Modèles dbt silver → gold (agrégats)
│   └── dbt_project.yml
├── orchestration/
│   └── dags/
│       └── disease_pipeline_dag.py   # DAG Airflow quotidien
├── tests/
│   └── test_ingestion.py   # Tests unitaires pytest
├── dashboard/
│   └── app.py              # Dashboard Streamlit
├── data/                   # Données locales (gitignored)
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── .env.example
├── Makefile
└── requirements.txt
```

## Démarrage rapide (mode local)

```bash
# 1. Cloner et installer
git clone https://github.com/Aida73/disease-tracker-aws-pipeline
cd disease-tracker-aws-pipeline
pip install -r requirements.txt

# 2. Configurer l'environnement
cp .env.example .env
# Laisser BRONZE_BUCKET vide pour mode local

# 3. Lancer l'ingestion
make ingest

# 4. Lancer les tests
make test

# 5. Lancer le dashboard
streamlit run dashboard/app.py
```

## Déploiement AWS

```bash
# Configurer les credentials AWS
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export BRONZE_BUCKET=mon-bucket-bronze

# L'ingestion uploade automatiquement sur S3
make ingest
```

## Données

- **Source principale :** [disease.sh](https://disease.sh) — agrège WHO, JHU, gouvernements nationaux
- **Fréquence :** mise à jour quotidienne via DAG Airflow
- **Format stockage :** Parquet partitionné par `ingestion_date`
- **Couverture :** 200+ pays, historique 30 jours

## Qualité des données

Chaque run valide :
- Absence de valeurs nulles sur les colonnes clés (`country`, `cases_total`)
- Cohérence : `active_cases = cases_total - deaths_total - recovered_total`
- Fraîcheur : données de moins de 24h

## Auteure

**Aida Sow** — Data Engineer  
[LinkedIn](https://www.linkedin.com/in/aida-sow-804a381b5/) · [GitHub](https://github.com/Aida73)