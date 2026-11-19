<div align="center">
  <h1>🦋 Parides</h1>
  <p><strong>Prometheus metrics directly into Pandas and Parquet.</strong></p>

  [![Python CI/CD](https://github.com/goettl79/parides/actions/workflows/python-ci.yml/badge.svg)](https://github.com/goettl79/parides/actions/workflows/python-ci.yml)
  [![Docker CI/CD](https://github.com/goettl79/parides/actions/workflows/docker-ci.yml/badge.svg)](https://github.com/goettl79/parides/actions/workflows/docker-ci.yml)
  [![PyPI version](https://badge.fury.io/py/parides.svg)](https://badge.fury.io/py/parides)
  [![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
</div>

<br />

**Parides** is a high-performance bridge between Prometheus and the Data Science stack. It automatically handles pagination, pivoting, and tabular alignment, delivering perfectly formatted data for machine learning and statistical analysis.

## 🚀 Quick Start: Prometheus → Parquet in 2 steps

```bash
pip install "parides[parquet]"
parides http://localhost:9090 'up' --format parquet
```

That's it. The last 10 minutes of `up` are written to `./timeseries/prom_X_<hash>.parquet`. Load it:

```python
import pandas as pd
df = pd.read_parquet("timeseries/prom_X_xxxx.parquet")   # UTC time index, one column per metric
```

Want a different time range? Add `--start-date 2024-01-01T00:00:00Z --end-date 2024-01-08T00:00:00Z`.
Prefer prompts? Run `parides` with no arguments for an interactive wizard.

---

## 📊 Three Ways to Use Parides

### 1. Python Library
Perfect for Jupyter Notebooks or custom scripts. Fetch metrics directly into a **Pandas DataFrame**.

```python
from parides.prom_conv import from_prom_to_df

# Automatically handles pagination and alignment
df = from_prom_to_df(
    url="http://localhost:9090",
    metrics_query='node_cpu_seconds_total{mode="idle"}'
)

df.plot()
```

### 2. Native CLI
High-performance extraction to **Parquet** or **CSV**. Use `--chunk-size` to bypass Prometheus API limits for large exports.

```bash
# Export 3 months of data in 1-day chunks to avoid timeouts
parides http://localhost:9090 'node_cpu_seconds_total' \
    --start-date "2024-01-01T00:00:00Z" \
    --end-date "2024-04-01T00:00:00Z" \
    --chunk-size "1d" \
    --format parquet
```

### 3. Environment Agnostic (Docker)
Run Parides as a standalone tool anywhere without local Python dependencies.

```bash
docker run -v $(pwd)/data:/app/timeseries \
    ghcr.io/goettl79/parides http://prometheus:9090 "up" --format parquet
```

---

## 💡 Why Parides?

*   **Bypass API Limits:** Automatically chunks large time-range queries (`--chunk-size`) so you never hit "too many samples" errors.
*   **Zero-Config Alignment:** Pivots long-format JSON into wide-format tables (features as columns, time as rows) — exactly what `scikit-learn` or `PyTorch` expect.
*   **Timezone Safe:** All timestamps are strictly converted to UTC to prevent catastrophic time-shifting bugs in your models.
*   **Big Data Ready:** CLI uses streaming writes (CSV/Parquet) to handle datasets larger than your system RAM.
*   **Two Layouts:** `--layout wide` (default; one column per metric) or `--layout long` (tidy: `metric`, one column per label, `value`).
*   **Self-describing Parquet:** query, step, window, layout and timezone are stored in the file metadata (`parides.*` keys).

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) to get started.

To set up for local development:
```bash
git clone https://github.com/goettl79/parides.git
cd parides
poetry install
```

## 📄 License

This project is licensed under the **Apache License 2.0**.
