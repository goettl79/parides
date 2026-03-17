import pytest
import os
import requests
from pathlib import Path
from parides.prom_conv import from_prom_to_df, from_prom_to_csv

# Integration tests are designed to run against a real Prometheus instance.
# They are skipped unless PROM_URL is provided in the environment.
PROM_URL = os.getenv("PROM_URL", "http://localhost:9090")

def is_prometheus_available():
    try:
        response = requests.get(f"{PROM_URL}/-/healthy", timeout=1)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not is_prometheus_available(),
        reason=f"Prometheus not available at {PROM_URL}. Set PROM_URL to enable."
    )
]

def test_integration_from_prom_to_df():
    # A simple query that should always work if Prometheus is up
    query = 'prometheus_http_requests_total'
    df = from_prom_to_df(url=PROM_URL, metrics_query=query, resolution="1m")
    
    assert not df.empty
    assert "time" == df.index.name
    # Metric column name might vary depending on labels, but at least one column besides 'id' should exist
    assert len(df.columns) >= 2
    assert "id" in df.columns

def test_integration_from_prom_to_csv(tmp_path):
    query = 'prometheus_http_requests_total'
    directory = tmp_path / "integration_csv"
    
    file_path = from_prom_to_csv(
        url=PROM_URL,
        metrics_query=query,
        dataset_id="integration_test",
        directory=str(directory)
    )
    
    assert Path(file_path).exists()
    assert Path(file_path).stat().st_size > 0
