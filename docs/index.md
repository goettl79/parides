# 🦋 Parides

**Prometheus metrics directly into Pandas and Parquet.**

Parides is a high-performance bridge for **Data Scientists** and **ML Engineers**. It solves the "Too many samples" Prometheus API limit by automatically chunking large queries and aligning multiple time-series into a single, clean tabular format.

---

## 🚀 Quick Start

```bash
pip install parides
```

---

## 📊 Three Ways to Use Parides

### 1. Python Library
Perfect for Jupyter Notebooks or custom scripts. Fetch aligned metrics directly into a **Pandas DataFrame**.

```python
from parides.prom_conv import from_prom_to_df

# Automatically handles pagination and alignment
df = from_prom_to_df(
    url="http://localhost:9090",
    metrics_query='node_cpu_seconds_total{mode="idle"}'
)

# Ready for Scikit-Learn, PyTorch, or Matplotlib
df.plot()
```

### 2. Native CLI
High-performance extraction to **Parquet** or **CSV**. Use `--chunk-size` to bypass Prometheus API limits for large historical exports.

```bash
pip install parides

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

---

## 🛠️ CLI Reference

| Flag | Description | Default |
|------|-------------|---------|
| `-r, --resolution` | Query step resolution (e.g., `1m`, `1h`). | `15s` |
| `--chunk-size` | Pagination window (e.g., `6h`, `1d`). | `6h` |
| `-f, --format` | Output format (`csv` or `parquet`). | `csv` |

---

## 📄 License

This project is licensed under the **Apache License 2.0**.
