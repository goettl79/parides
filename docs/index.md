# 🦋 Parides

**Prometheus metrics directly into Pandas and Parquet.**

Parides is a high-performance bridge for **Data Scientists** and **ML Engineers**. It solves the "Too many samples" Prometheus API limit by automatically chunking large queries and aligning multiple time-series into a single, clean tabular format.

---

## 🚀 Quick Start

### 1. Install
```bash
pip install parides
```

### 2. Export Data (CLI for ML/Devs)
Extract months of data directly to **Parquet** for model training. Parides **streams** data to disk to keep memory usage low.

```bash
parides http://localhost:9090 'node_memory_MemFree_bytes' \
    --start-date "2024-01-01T00:00:00Z" \
    --end-date "2024-04-01T00:00:00Z" \
    --chunk-size "1d" \
    --format parquet
```

### 3. Analyze Data (Python for Data Science)
Fetch aligned metrics directly into a **Pandas DataFrame**.

```python
from parides.prom_conv import from_prom_to_df

# Automatically handles pagination and alignment
df = from_prom_to_df(
    url="http://localhost:9090",
    metrics_query='irate(node_cpu_seconds_total{mode="idle"}[5m])'
)

# Ready for Scikit-Learn, PyTorch, or Matplotlib
df.plot()
```

---

## 💎 Key Features for ML & DS

*   **Zero-Config Alignment:** Merges multiple labels into a single wide-format table (features as columns, time as index).
*   **Big Data Streaming:** CLI uses streaming writes (CSV/Parquet) to handle datasets larger than your RAM.
*   **Timezone Aware:** Strictly UTC-based to prevent time-shift bugs in ML models.
*   **Bypass API Limits:** Automatically splits long-range queries into configurable chunks (`--chunk-size`).

---

## 🛠️ CLI Reference

| Flag | Description | Default |
|------|-------------|---------|
| `-r, --resolution` | Query step resolution (e.g., `1m`, `1h`). | `15s` |
| `--chunk-size` | Pagination window (e.g., `6h`, `1d`). | `6h` |
| `-f, --format` | Output format (`csv` or `parquet`). | `csv` |

---

## 🐳 Docker
```bash
docker run -v $(pwd)/data:/app/timeseries \
    ghcr.io/goettl79/parides http://prometheus:9090 "up" --format parquet
```
