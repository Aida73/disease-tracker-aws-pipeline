"""
Tests unitaires pour le module d'ingestion WHO.
Lance avec : pytest tests/ -v
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from ingestion.who_ingest import normalize_country_data, fetch_who_country_data


MOCK_COUNTRY = {
    "country": "France",
    "countryInfo": {"iso2": "FR"},
    "continent": "Europe",
    "population": 67000000,
    "cases": 3800000,
    "todayCases": 150,
    "deaths": 115000,
    "todayDeaths": 5,
    "recovered": 3600000,
    "active": 85000,
    "critical": 1200,
    "casesPerOneMillion": 56716,
    "deathsPerOneMillion": 1716,
    "tests": 250000000,
    "testsPerOneMillion": 3731343,
    "updated": 1700000000000,
}


class TestNormalizeCountryData:

    def test_retourne_dataframe(self):
        df = normalize_country_data([MOCK_COUNTRY])
        assert isinstance(df, pd.DataFrame)

    def test_colonnes_presentes(self):
        df = normalize_country_data([MOCK_COUNTRY])
        colonnes_requises = [
            "country", "country_code", "continent", "population",
            "cases_total", "deaths_total", "ingested_at", "ingestion_date"
        ]
        for col in colonnes_requises:
            assert col in df.columns, f"Colonne manquante : {col}"

    def test_country_code_extrait(self):
        df = normalize_country_data([MOCK_COUNTRY])
        assert df.iloc[0]["country_code"] == "FR"

    def test_valeurs_nulles_si_donnee_manquante(self):
        country_incomplet = {"country": "TestPays", "countryInfo": {}}
        df = normalize_country_data([country_incomplet])
        assert df.iloc[0]["cases_total"] is None or pd.isna(df.iloc[0]["cases_total"])

    def test_plusieurs_pays(self):
        df = normalize_country_data([MOCK_COUNTRY, MOCK_COUNTRY])
        assert len(df) == 2


class TestFetchWhoCountryData:

    @patch("ingestion.who_ingest.requests.get")
    def test_appel_api_reussi(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [MOCK_COUNTRY]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_who_country_data()
        assert len(result) == 1
        assert result[0]["country"] == "France"

    @patch("ingestion.who_ingest.requests.get")
    def test_erreur_api_leve_exception(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("timeout")
        with pytest.raises(requests.exceptions.ConnectionError):
            fetch_who_country_data()