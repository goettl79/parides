import errno
import hashlib
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any, Dict, Union

import pandas as pd
import pytz
import requests

logger = logging.getLogger(__name__)


def from_prom_to_csv(url: str, metrics_query: str, dataset_id: str = "id", directory: str = "./prom-ts",
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None, resolution: str = "1m") -> str:
    """Read Prometheus metrics and save them to a CSV file.

    This function handles time-slicing and pagination automatically to avoid
    Prometheus sample limits.

    Args:
        url: The Prometheus API endpoint (e.g., http://localhost:9090).
        metrics_query: The PromQL query to execute.
        dataset_id: Identifier used in the resulting filename.
        directory: Target directory for the CSV file.
        start_time: Query start time (UTC). Defaults to 10 minutes ago.
        end_time: Query end time (UTC). Defaults to now.
        resolution: Step resolution (e.g., "1m", "15s").

    Returns:
        The path to the generated CSV file.
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    if end_time is None:
        end_time = datetime.now(timezone.utc)

    time_id_prefix = "{}-{}".format(start_time.timestamp(), end_time.timestamp())
    prefix = hashlib.sha1(time_id_prefix.encode("UTF-8")).hexdigest()[:4]

    try:
        os.makedirs(directory)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(directory):
            pass
        else:
            raise

    x_buckets = from_prom_to_df(url, metrics_query, start_time, end_time, resolution)
    file = directory + "/" + dataset_id + "_X_{}.csv".format(prefix)
    x_buckets.to_csv(file, date_format="%m/%d/%Y %H:%M:%S")
    logger.info("Wrote to " + file)
    return file


def from_prom_to_parquet(url: str, metrics_query: str, dataset_id: str = "id", directory: str = "./prom-ts",
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None, resolution: str = "1m") -> str:
    """Read Prometheus metrics and save them to a compressed Parquet file.

    Parquet is the recommended format for data science due to its efficient 
    compression and type preservation.

    Args:
        url: The Prometheus API endpoint (e.g., http://localhost:9090).
        metrics_query: The PromQL query to execute.
        dataset_id: Identifier used in the resulting filename.
        directory: Target directory for the Parquet file.
        start_time: Query start time (UTC). Defaults to 10 minutes ago.
        end_time: Query end time (UTC). Defaults to now.
        resolution: Step resolution (e.g., "1m", "15s").

    Returns:
        The path to the generated Parquet file.
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    if end_time is None:
        end_time = datetime.now(timezone.utc)

    time_id_prefix = "{}-{}".format(start_time.timestamp(), end_time.timestamp())
    prefix = hashlib.sha1(time_id_prefix.encode("UTF-8")).hexdigest()[:4]

    try:
        os.makedirs(directory)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(directory):
            pass
        else:
            raise

    x_buckets = from_prom_to_df(url, metrics_query, start_time, end_time, resolution)
    file = directory + "/" + dataset_id + "_X_{}.parquet".format(prefix)
    x_buckets.to_parquet(file)
    logger.info("Wrote to " + file)
    return file


def from_prom_to_df(url: str, metrics_query: str,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None,
                    resolution: str = "1m",
                    freq: str = "10min") -> pd.DataFrame:
    """Fetch Prometheus metrics and convert them to a wide-format Pandas DataFrame.

    Automatically handles time-slicing and aligns multiple time-series into a 
    single tabular structure where metrics are columns and time is the index.

    Args:
        url: The Prometheus API endpoint.
        metrics_query: The PromQL query.
        start_time: Start time (UTC). Defaults to 10 minutes ago.
        end_time: End time (UTC). Defaults to now.
        resolution: Step resolution (e.g., "1m").
        freq: Slicing frequency (e.g., "10min").

    Returns:
        A timezone-aware Pandas DataFrame.
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    if end_time is None:
        end_time = datetime.now(timezone.utc)

    date_range = prepare_time_slices(end_time=end_time, freq=freq, start_time=start_time)

    results = []
    # If date_range has [start, end], we want to query that interval.
    # The original loop: for idx, date in enumerate(date_range): if idx < len(date_range) - 1: ...
    # This works for [start, end] (idx 0 < 1)
    for idx in range(len(date_range) - 1):
        start_slice = date_range[idx]
        end_slice = date_range[idx + 1]
        json_query_results = __get_prom_api_response(url, metrics_query, start_time=start_slice.isoformat(),
                                                     end_time=end_slice.isoformat(), resolution=resolution)
        df_slice = from_prom_json_to_df(json_query_results.json())
        if not df_slice.empty:
            results.append(df_slice)

    if not results:
        raise ValueError("Prometheus did not return any values for query {}".format(metrics_query))

    return pd.concat(results, axis=0, join='outer', ignore_index=False)


def from_prom_json_to_df(prom_api_response: Dict[str, Any]) -> pd.DataFrame:
    """Convert raw Prometheus JSON response to a wide-format Pandas DataFrame.

    This is the core conversion engine. It extracts labels, creates unique 
    identities for series, and pivots the data so that each unique series 
    becomes a column.

    Args:
        prom_api_response: The JSON dictionary returned by the Prometheus API.

    Returns:
        A pivoted Pandas DataFrame with 'time' as index and 'id' as a column.
    """
    if "data" not in prom_api_response:
        return pd.DataFrame()

    prom_metrics = prom_api_response['data']['result']
    all_records = []

    id_keys = {"instance", "job", "name"}

    for prom_metric in prom_metrics:
        metric_meta = prom_metric['metric']

        # Extract labels and ID
        labels = {k: v for k, v in metric_meta.items() if k not in id_keys}
        ids = {k: v for k, v in metric_meta.items() if k in id_keys}

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
        metric_scrape_id = "_".join(v for k, v in sorted(ids.items()))

        for timestamp, value in prom_metric['values']:
            record = {
                'time': pd.to_datetime(int(timestamp), unit='s'),
                'id': metric_scrape_id,
                metric_name: float(value)
            }
            all_records.append(record)

    if not all_records:
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    # We want 'time' and 'id' as index/columns and metrics as columns.
    # pivot_table will handle different metric names becoming their own columns
    # while aligning them by time and id.
    df = df.pivot_table(index=['time', 'id']).reset_index()

    df['time'] = df['time'].dt.tz_localize('UTC')
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    return df

def __convert_timeseries(column_pos: Dict[str, int], df: pd.DataFrame, metric_name: str, 
                         metric_scrape_id: str, prom_metric: Dict[str, Any]):
    # This function is now deprecated by the refactoring above but kept if needed for API compatibility
    # though it was internal-ish (prefixed with __).
    pass


def prepare_time_slices(start_time: datetime, end_time: datetime, freq: str) -> List[datetime]:
    start_time = start_time.replace(tzinfo=pytz.UTC)
    end_time = end_time.replace(tzinfo=pytz.UTC)
    date_range = pd.to_datetime(pd.date_range(start=start_time, end=end_time, freq=freq, tz=pytz.UTC)).tolist()
    if len(date_range) < 2:
        date_range = [start_time.replace(tzinfo=pytz.UTC), end_time.replace(tzinfo=pytz.UTC)]
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
                                    'step': resolution})
    if response.ok:
        return response
    else:
        msg = "Status: {0} Text: {1}".format(response.status_code, response.text)
        logger.error(msg)
        raise RuntimeError(msg)

