# 🦋 Parides

**Bridging the gap between Prometheus and Data Science.**

Parides is designed for engineers and data scientists who need to extract large-scale metrics from Prometheus without hitting API limits or dealing with manual data munging. It automatically handles pagination, pivoting, and alignment, delivering clean **Pandas DataFrames** or **Parquet/CSV** files.

---

## 🚀 Installation

Always install within a virtual environment to manage dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install parides
```

---

## 📊 Data Science API (Python)

The core of Parides is the `from_prom_to_df` function, which converts PromQL results into a **wide-format DataFrame** (time as index, metrics as columns).

### Quick Start: Visualize Metrics
```python
import matplotlib.pyplot as plt
from parides.prom_conv import from_prom_to_df

# Fetch CPU usage for the last 1 hour
df = from_prom_to_df(
    url="http://localhost:9090",
    metrics_query='irate(node_cpu_seconds_total{mode="idle"}[5m])',
    resolution="1m"
)

# Parides returns a clean, aligned Pandas DataFrame
print(df.head())
df.plot(title="CPU Idle Time")
plt.show()
```

### Why use the API?
- **Automatic Alignment:** Multiple time-series with different labels are perfectly aligned by timestamp.
- **Timezone Safety:** All timestamps are strictly converted to UTC.
- **Memory Efficient:** Large ranges are automatically queried in chunks (default: 6h) to prevent Prometheus "too many samples" errors.

---

## 🛠️ High-Performance CLI

For large-scale data extraction (ETL pipelines, model training sets), use the CLI. It utilizes **streaming writes** to handle multi-gigabyte exports with minimal RAM usage.

### Standard Export
Export the last 10 minutes of a query to CSV:
```bash
parides http://localhost:9090 'up'
```

### Big Data & Streaming (Parquet)
Export months of data using **1-day chunks**. Parides will stream the results directly to a Parquet file, keeping your memory footprint low:
```bash
parides http://localhost:9090 'node_memory_MemFree_bytes' \
    --start-date "2024-01-01T00:00:00Z" \
    --end-date "2024-04-01T00:00:00Z" \
    --resolution "5m" \
    --chunk-size "1d" \
    --format parquet \
    --output-directory "./ml_dataset"
```

### Advanced Parameters
| Flag | Description | Default |
|------|-------------|---------|
| `-r, --resolution` | Step resolution (e.g., `15s`, `1m`, `1h`). | `15s` |
| `--chunk-size` | Time range per API request (e.g., `6h`, `1d`). | `6h` |
| `-f, --format` | Output format (`csv` or `parquet`). | `csv` |
| `--dsid` | Custom dataset ID used in filename. | `prom` |

---

## 🐳 Running with Docker

Perfect for CI/CD pipelines or environments without a Python runtime:

```bash
docker run -v $(pwd)/data:/app/timeseries \
    ghcr.io/goettl79/parides http://prometheus:9090 "up" --format parquet
```
