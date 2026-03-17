<div align="center">
  <h1>🦋 Parides</h1>
  <p><strong>Bridging the gap between Prometheus and Data Science.</strong></p>
  <p>Convert Prometheus metrics data directly into Pandas DataFrames or CSV files with zero hassle.</p>

  [![Python CI/CD](https://github.com/goettl79/parides/actions/workflows/python-ci.yml/badge.svg)](https://github.com/goettl79/parides/actions/workflows/python-ci.yml)
  [![Docker CI/CD](https://github.com/goettl79/parides/actions/workflows/docker-ci.yml/badge.svg)](https://github.com/goettl79/parides/actions/workflows/docker-ci.yml)
  [![PyPI version](https://badge.fury.io/py/parides.svg)](https://badge.fury.io/py/parides)
  [![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
  [![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
</div>

<br />

**Parides** is a lightweight Python library and CLI tool designed to effortlessly extract time-series data from Prometheus. It automatically handles pagination, time-slicing, and tabular alignment, delivering perfectly formatted data ready for machine learning, anomaly detection, and statistical analysis.

## 💡 Why Parides?

Prometheus is great for monitoring, but its JSON API isn't designed for data science. 
* **Bypass API Limits:** Parides automatically chunks large time-range queries so you never hit Prometheus "too many samples" limits.
* **Data Science Ready:** It pivots long-format JSON into wide-format Pandas DataFrames (features as columns, time as rows) — exactly what `scikit-learn` or `PyTorch` expect.
* **Timezone Safe:** All timestamps are strictly converted to UTC to prevent catastrophic time-shifting bugs in your models.

## 🚀 Installation

### Via Pip (Recommended for DS workflows)
```bash
pip install parides
```

### Via Docker (Recommended for CI/CD / Pipelines)
```bash
docker pull goettl/parides
```

## 🛠️ Usage

### 1. Interactive Wizard (Easiest for Beginners)

If you're not a fan of long commands, just type `parides` and follow the prompts. Our friendly setup wizard will guide you through the conversion:

```bash
parides
```
*Output:*
```text
🦋 Parides Interactive Setup Wizard
-----------------------------------
Prometheus URL [http://localhost:9090]:
PromQL Query (e.g., up): node_cpu_seconds_total
Output Format (csv/parquet) [csv]: parquet
...
```

### 2. Command Line Interface (Power Users)

Extract massive Prometheus datasets directly to CSV or Parquet files without writing code:

```bash
# Basic usage (defaults to last 10 minutes, CSV)
parides http://localhost:9090 'up'

# Export to Parquet format (highly recommended for large datasets)
parides http://localhost:9090 'node_cpu_seconds_total' --format parquet

# Advanced usage: Extract 1 hour of data at 1-minute resolution
parides http://localhost:9090 'node_cpu_seconds_total' \
    --start-date "2024-03-01T00:00:00Z" \
    --end-date "2024-03-01T01:00:00Z" \
    --resolution "1m" \
    --format parquet \
    --output-directory "./training_data"
```

### 3. Docker (Standalone Executable)

If you don't use Python directly (e.g., you're an **R user**, **Data Scientist**, or **DevOps Engineer**), you can run Parides as a standalone tool via Docker. This avoids any local dependency or environment management:

```bash
# Extract metrics to a local 'data' folder
docker run -v $(pwd)/data:/app/timeseries \
    goettl/parides http://prometheus-host:9090 "up" --format parquet
```

### 4. Python API (Jupyter Notebook / Scripts)

Convert metrics directly to a Pandas DataFrame for immediate analysis:

```python
import matplotlib.pyplot as plt
from parides.prom_conv import from_prom_to_df

# Fetch the last 10 minutes of CPU data
df = from_prom_to_df(
    url="http://localhost:9090",
    metrics_query='irate(node_cpu_seconds_total[5m]) * 100',
    resolution="15s"
)

# Your data is perfectly aligned!
print(df.head())

# Instantly visualize or train a model
df.plot()
plt.show()
```

## 🤝 Contributing

We welcome contributions! Whether it's reporting a bug, proposing a feature, or submitting a Pull Request, your input helps make Parides better. Please see our [Contributing Guidelines](CONTRIBUTING.md) to get started.

To set up for local development:
```bash
git clone https://github.com/goettl79/parides.git
cd parides
poetry install
poetry run pytest
```

## 📄 License

This project is licensed under the **Apache License 2.0**.
