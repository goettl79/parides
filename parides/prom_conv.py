import hashlib
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any, Dict, Union

import pandas as pd
import requests

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 60


def _import_pyarrow():
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as e:
        raise ImportError("Parquet output requires pyarrow: pip install 'parides[parquet]'") from e
    return pa, pq


def _resolve_window(start_time: Optional[datetime], end_time: Optional[datetime]):
    """Apply defaults (last 10 minutes) for a missing query window."""
    if end_time is None:
        end_time = datetime.now(timezone.utc)
    if start_time is None:
        start_time = end_time - timedelta(minutes=10)
    return start_time, end_time


def _prepare_output_file(directory: str, dataset_id: str, extension: str,
                         start_time: datetime, end_time: datetime) -> str:
    """Create the target directory and return a fresh output path."""
    time_id_prefix = "{}-{}".format(start_time.timestamp(), end_time.timestamp())
    prefix = hashlib.sha1(time_id_prefix.encode("UTF-8")).hexdigest()[:4]
    os.makedirs(directory, exist_ok=True)
    file = os.path.join(directory, f"{dataset_id}_X_{prefix}.{extension}")
    if os.path.exists(file):
        os.remove(file)
    return file


VALID_LAYOUTS = ("wide", "long")


def _check_layout(layout: str) -> None:
    if layout not in VALID_LAYOUTS:
        raise ValueError(f"layout must be one of {VALID_LAYOUTS}, got {layout!r}")


def _trim_slice(df: pd.DataFrame, end_slice: datetime, is_last: bool) -> pd.DataFrame:
    """Drop rows at the slice end boundary (except for the last slice).

    Prometheus ``query_range`` includes both ends of the window, so the first
    timestamp of slice N+1 would otherwise duplicate the last timestamp of slice N.
    """
    if is_last or df.empty:
        return df
    return df[df.index < end_slice]


def _align_columns(df: pd.DataFrame, columns: List[str], first_slice: bool) -> pd.DataFrame:
    """Force every chunk onto the schema of the first chunk.

    Missing columns are filled with NaN. Columns that did not exist in the first
    chunk cannot be appended to a streaming file; they are dropped with a warning.
    """
    if first_slice:
        return df
    extra = [c for c in df.columns if c not in columns]
    if extra:
        logger.warning("Dropping %d column(s) that first appeared after the first chunk "
                       "(streaming output has a fixed schema): %s", len(extra), extra)
    return df.reindex(columns=columns)


def _metadata(metrics_query: str, resolution: str, start_time: datetime, end_time: datetime,
              layout: str) -> Dict[str, str]:
    return {
        "parides.query": metrics_query,
        "parides.step": str(resolution),
        "parides.start": start_time.isoformat(),
        "parides.end": end_time.isoformat(),
        "parides.layout": layout,
        "parides.timezone": "UTC",
    }


def _iter_slices(url: str, metrics_query: str, start_time: datetime, end_time: datetime,
                 resolution: str, chunk_size: str, layout: str):
    """Yield de-duplicated per-chunk DataFrames (possibly empty)."""
    date_range = prepare_time_slices(end_time=end_time, freq=chunk_size, start_time=start_time)
    n = len(date_range) - 1
    for idx in range(n):
        start_slice = date_range[idx]
        end_slice = date_range[idx + 1]
        logger.info(f"Processing chunk {idx+1}/{n}: {start_slice} to {end_slice}")
        resp = __get_prom_api_response(url, metrics_query,
                                       start_time=start_slice.isoformat(),
                                       end_time=end_slice.isoformat(),
                                       resolution=resolution)
        df_slice = from_prom_json_to_df(resp.json(), layout=layout)
        yield _trim_slice(df_slice, end_slice, is_last=(idx == n - 1))


def from_prom_to_csv(url: str, metrics_query: str, dataset_id: str = "id", directory: str = "./prom-ts",
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None, resolution: str = "1m",
                     chunk_size: str = "6h", layout: str = "wide") -> str:
    """Read Prometheus metrics and save them to a CSV file using streaming.

    Timestamps are written as unambiguous ISO 8601 with a UTC offset
    (``2024-01-01 00:00:00+00:00``), so ``pd.read_csv(..., parse_dates=['time'])``
    yields tz-aware UTC values.

    Args:
        url: The Prometheus API endpoint.
        metrics_query: The PromQL query.
        dataset_id: Identifier used in the resulting filename.
        directory: Target directory for the CSV file.
        start_time: Query start time (UTC).
        end_time: Query end time (UTC).
        resolution: Step resolution.
        chunk_size: Size of each data chunk (e.g., "6h").
        layout: "wide" (one column per metric) or "long" (tidy: metric, labels, value).

    Returns:
        The path to the generated CSV file.
    """
    _check_layout(layout)
    start_time, end_time = _resolve_window(start_time, end_time)
    file = _prepare_output_file(directory, dataset_id, "csv", start_time, end_time)

    columns: Optional[List[str]] = None

    try:
        for df_slice in _iter_slices(url, metrics_query, start_time, end_time,
                                     resolution, chunk_size, layout):
            if df_slice.empty:
                continue
            first = columns is None
            if first:
                columns = list(df_slice.columns)
            df_slice = _align_columns(df_slice, columns, first)
            df_slice.to_csv(file, mode='a', header=first)
    except Exception as e:
        logger.error(f"Export aborted: {e}")
        if columns is None:
            raise
        raise RuntimeError(f"Export failed after partial write to {file}: {e}") from e

    if columns is None:
        raise ValueError("Prometheus did not return any values for query {}".format(metrics_query))

    logger.info("Wrote to " + file)
    return file


def from_prom_to_parquet(url: str, metrics_query: str, dataset_id: str = "id", directory: str = "./prom-ts",
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None, resolution: str = "1m",
                         chunk_size: str = "6h", layout: str = "wide") -> str:
    """Read Prometheus metrics and save them to a Parquet file using streaming.

    The file carries key/value metadata (query, step, window, layout, timezone)
    in its schema metadata under the ``parides.*`` keys.

    Args:
        url: The Prometheus API endpoint.
        metrics_query: The PromQL query.
        dataset_id: Identifier used in filename.
        directory: Target directory.
        start_time: Start time.
        end_time: End time.
        resolution: Step resolution.
        chunk_size: Size of each data chunk.
        layout: "wide" (one column per metric) or "long" (tidy: metric, labels, value).

    Returns:
        The path to the generated Parquet file.
    """
    pa, pq = _import_pyarrow()
    _check_layout(layout)

    start_time, end_time = _resolve_window(start_time, end_time)
    file = _prepare_output_file(directory, dataset_id, "parquet", start_time, end_time)

    columns: Optional[List[str]] = None
    writer = None

    try:
        for df_slice in _iter_slices(url, metrics_query, start_time, end_time,
                                     resolution, chunk_size, layout):
            if df_slice.empty:
                continue
            first = columns is None
            if first:
                columns = list(df_slice.columns)
            df_slice = _align_columns(df_slice, columns, first)
            table = pa.Table.from_pandas(df_slice)
            if writer is None:
                meta = dict(table.schema.metadata or {})
                meta.update({k.encode(): v.encode() for k, v in
                             _metadata(metrics_query, resolution, start_time, end_time, layout).items()})
                schema = table.schema.with_metadata(meta)
                writer = pq.ParquetWriter(file, schema)
            else:
                # An all-NaN column may be inferred as another type; cast to the file schema.
                table = table.cast(writer.schema)
            writer.write_table(table)
    except Exception as e:
        logger.error(f"Export aborted: {e}")
        if columns is None:
            raise
        raise RuntimeError(f"Export failed after partial write to {file}: {e}") from e
    finally:
        if writer:
            writer.close()

    if columns is None:
        raise ValueError("Prometheus did not return any values for query {}".format(metrics_query))

    logger.info("Wrote to " + file)
    return file


def from_prom_to_df(url: str, metrics_query: str,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None,
                    resolution: str = "1m",
                    freq: str = "6h", layout: str = "wide") -> pd.DataFrame:
    """Fetch Prometheus metrics into a Pandas DataFrame indexed by UTC time.

    Args:
        url: The Prometheus API endpoint.
        metrics_query: The PromQL query.
        start_time: Start time (UTC). Defaults to 10 minutes ago.
        end_time: End time (UTC). Defaults to now.
        resolution: Step resolution (e.g., "1m").
        freq: Slicing frequency (e.g., "6h").
        layout: "wide" (``id`` column + one column per metric) or "long"
            (tidy: ``metric``, one column per label, ``value``).

    Returns:
        A timezone-aware Pandas DataFrame.
    """
    _check_layout(layout)
    start_time, end_time = _resolve_window(start_time, end_time)

    results = [df for df in _iter_slices(url, metrics_query, start_time, end_time,
                                         resolution, freq, layout) if not df.empty]

    if not results:
        raise ValueError("Prometheus did not return any values for query {}".format(metrics_query))

    return pd.concat(results, axis=0, join='outer', ignore_index=False)


def from_prom_json_to_df(prom_api_response: Dict[str, Any], layout: str = "wide") -> pd.DataFrame:  # noqa: C901
    """Convert a raw Prometheus ``query_range`` JSON response to a DataFrame.

    Args:
        prom_api_response: The JSON dictionary returned by the Prometheus API.
        layout: ``"wide"`` - index ``time``, column ``id`` (instance/job/name
            joined by ``_``) and one float column per metric/label combination.
            ``"long"`` - tidy format: index ``time``, column ``metric``, one
            column per label (real values, no flattening) and ``value``.

    Returns:
        A DataFrame with a tz-aware (UTC) ``time`` index, or an empty DataFrame.
    """
    _check_layout(layout)
    if "data" not in prom_api_response:
        return pd.DataFrame()

    prom_metrics = prom_api_response['data']['result']
    if not prom_metrics:
        return pd.DataFrame()

    if layout == "long":
        return _to_long(prom_metrics)

    id_keys = {"instance", "job", "name"}

    times = []
    ids = []
    metric_names = []
    values = []

    for prom_metric in prom_metrics:
        metric_meta = prom_metric['metric']

        # Extract labels and ID
        labels = {k: v for k, v in metric_meta.items() if k not in id_keys}
        ids_dict = {k: v for k, v in metric_meta.items() if k in id_keys}

        # Build metric name
        metric_name_base = labels.get('__name__', '')
        if metric_name_base:
            other_labels = [f"{k}_{v}" for k, v in sorted(labels.items()) if k != '__name__']
            metric_name = ":".join([metric_name_base] + other_labels)
        else:
            other_labels = [f"{k}_{v}" for k, v in sorted(labels.items())]
            metric_name = "_".join(other_labels)

        if not metric_name:
            metric_name = "value"

        # Build scrape ID
        metric_scrape_id = "_".join(v for k, v in sorted(ids_dict.items()))

        for timestamp, value in prom_metric['values']:
            times.append(float(timestamp))
            ids.append(metric_scrape_id)
            metric_names.append(metric_name)
            values.append(float(value))

    if not times:
        return pd.DataFrame()

    df = pd.DataFrame({
        'time': pd.to_datetime(times, unit='s'),
        'id': ids,
        'metric_name': metric_names,
        'value': values
    })

    # Colliding (time, id, metric) entries cannot be represented in wide format.
    dup = df.duplicated(subset=['time', 'id', 'metric_name'], keep='last')
    if dup.any():
        logger.warning("%d duplicate (time, id, metric) samples; keeping the last. "
                       "Use layout='long' to retain all label information.", int(dup.sum()))
        df = df[~dup]

    # Pivot to wide format
    unique_metrics = df['metric_name'].unique()
    if len(unique_metrics) == 1:
        metric_name = unique_metrics[0]
        df.rename(columns={'value': metric_name}, inplace=True)
        df.drop(columns=['metric_name'], inplace=True)
        df = df.set_index(['time', 'id'])
    else:
        df = df.pivot(index=['time', 'id'], columns='metric_name', values='value')
        df.columns.name = None

    df = df.reset_index()
    df['time'] = df['time'].dt.tz_localize('UTC')
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    return df


def _to_long(prom_metrics: List[Dict[str, Any]]) -> pd.DataFrame:
    """Tidy layout: one row per sample, labels kept as real columns."""
    frames = []
    for prom_metric in prom_metrics:
        meta = dict(prom_metric['metric'])
        name = meta.pop('__name__', '')
        samples = prom_metric['values']
        if not samples:
            continue
        ts, vals = zip(*samples)
        frame = pd.DataFrame({
            'time': pd.to_datetime([float(t) for t in ts], unit='s', utc=True),
            'metric': name or 'value',
            'value': [float(v) for v in vals],
        })
        for k, v in meta.items():
            frame[k] = v
        frames.append(frame)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    label_cols = sorted(c for c in df.columns if c not in ('time', 'metric', 'value'))
    df = df[['time', 'metric'] + label_cols + ['value']]
    df = df.set_index('time').sort_index(kind='stable')
    return df


def prepare_time_slices(start_time: datetime, end_time: datetime, freq: str) -> List[datetime]:
    # Naive datetimes are assumed UTC; aware ones are converted (not relabelled).
    start_time = start_time.replace(tzinfo=timezone.utc) if start_time.tzinfo is None else start_time.astimezone(timezone.utc)
    end_time = end_time.replace(tzinfo=timezone.utc) if end_time.tzinfo is None else end_time.astimezone(timezone.utc)

    date_range = pd.to_datetime(pd.date_range(start=start_time, end=end_time, freq=freq, tz=timezone.utc)).tolist()

    # Ensure start and end are included and range is covered
    if not date_range or date_range[0] > start_time:
        date_range.insert(0, start_time)
    if date_range[-1] < end_time:
        date_range.append(end_time)

    return date_range


def __get_prom_api_response(url: str,
                            query: str,
                            end_time: Optional[Union[datetime, str]] = None,
                            start_time: Optional[Union[datetime, str]] = None,
                            resolution: str = "60") -> requests.Response:
    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(minutes=1)
    if end_time is None:
        end_time = datetime.now(timezone.utc)

    url_new = '{0}/api/v1/query_range'.format(url)
    response = requests.get(url_new,
                            params={'query': query,
                                    'start': start_time,
                                    'end': end_time,
                                    'step': resolution},
                            timeout=REQUEST_TIMEOUT_SECONDS)
    if response.ok:
        return response
    else:
        msg = "Status: {0} Text: {1}".format(response.status_code, response.text)
        logger.error(msg)
        raise RuntimeError(msg)
