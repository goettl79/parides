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
                     end_time: Optional[datetime] = None, resolution: str = "1m",
                     chunk_size: str = "6h") -> str:
    """Read Prometheus metrics and save them to a CSV file using streaming.

    This function fetches data in chunks and appends to the CSV file, 
    minimizing memory usage for large exports.

    Args:
        url: The Prometheus API endpoint.
        metrics_query: The PromQL query.
        dataset_id: Identifier used in the resulting filename.
        directory: Target directory for the CSV file.
        start_time: Query start time (UTC).
        end_time: Query end time (UTC).
        resolution: Step resolution.
        chunk_size: Size of each data chunk (e.g., "6h").

    Returns:
        The path to the generated CSV file.
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    if end_time is None:
        end_time = datetime.now(timezone.utc)

    time_id_prefix = "{}-{}".format(start_time.timestamp(), end_time.timestamp())
    prefix = hashlib.sha1(time_id_prefix.encode("UTF-8")).hexdigest()[:4]

    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    file = os.path.join(directory, f"{dataset_id}_X_{prefix}.csv")
    
    # Remove file if it exists to start fresh
    if os.path.exists(file):
        os.remove(file)

    date_range = prepare_time_slices(end_time=end_time, freq=chunk_size, start_time=start_time)
    
    any_data = False
    first_chunk = True
    
    for idx in range(len(date_range) - 1):
        start_slice = date_range[idx]
        end_slice = date_range[idx + 1]
        logger.info(f"Processing chunk {idx+1}/{len(date_range)-1}: {start_slice} to {end_slice}")
        
        try:
            json_query_results = __get_prom_api_response(url, metrics_query, 
                                                         start_time=start_slice.isoformat(),
                                                         end_time=end_slice.isoformat(), 
                                                         resolution=resolution)
            df_slice = from_prom_json_to_df(json_query_results.json())
            
            if not df_slice.empty:
                any_data = True
                # Note: Streaming to CSV with mode='a' assumes stable columns across chunks.
                df_slice.to_csv(file, mode='a', header=first_chunk, date_format="%m/%d/%Y %H:%M:%S")
                first_chunk = False
        except Exception as e:
            logger.error(f"Error processing chunk {start_slice} to {end_slice}: {e}")
            if any_data:
                logger.warning("Continuing with remaining chunks...")
            else:
                raise

    if not any_data:
        raise ValueError("Prometheus did not return any values for query {}".format(metrics_query))

    logger.info("Wrote to " + file)
    return file


def from_prom_to_parquet(url: str, metrics_query: str, dataset_id: str = "id", directory: str = "./prom-ts",
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None, resolution: str = "1m",
                        chunk_size: str = "6h") -> str:
    """Read Prometheus metrics and save them to a Parquet file using streaming.

    Args:
        url: The Prometheus API endpoint.
        metrics_query: The PromQL query.
        dataset_id: Identifier used in filename.
        directory: Target directory.
        start_time: Start time.
        end_time: End time.
        resolution: Step resolution.
        chunk_size: Size of each data chunk.

    Returns:
        The path to the generated Parquet file.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    if end_time is None:
        end_time = datetime.now(timezone.utc)

    time_id_prefix = "{}-{}".format(start_time.timestamp(), end_time.timestamp())
    prefix = hashlib.sha1(time_id_prefix.encode("UTF-8")).hexdigest()[:4]

    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    file = os.path.join(directory, f"{dataset_id}_X_{prefix}.parquet")
    
    if os.path.exists(file):
        os.remove(file)

    date_range = prepare_time_slices(end_time=end_time, freq=chunk_size, start_time=start_time)
    
    any_data = False
    writer = None
    
    for idx in range(len(date_range) - 1):
        start_slice = date_range[idx]
        end_slice = date_range[idx + 1]
        logger.info(f"Processing chunk {idx+1}/{len(date_range)-1}: {start_slice} to {end_slice}")
        
        try:
            json_query_results = __get_prom_api_response(url, metrics_query, 
                                                         start_time=start_slice.isoformat(),
                                                         end_time=end_slice.isoformat(), 
                                                         resolution=resolution)
            df_slice = from_prom_json_to_df(json_query_results.json())
            
            if not df_slice.empty:
                any_data = True
                table = pa.Table.from_pandas(df_slice)
                if writer is None:
                    writer = pq.ParquetWriter(file, table.schema)
                writer.write_table(table)
        except Exception as e:
            logger.error(f"Error processing chunk {start_slice} to {end_slice}: {e}")
            if any_data:
                continue
            else:
                raise

    if writer:
        writer.close()

    if not any_data:
        raise ValueError("Prometheus did not return any values for query {}".format(metrics_query))

    logger.info("Wrote to " + file)
    return file


def from_prom_to_df(url: str, metrics_query: str,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None,
                    resolution: str = "1m",
                    freq: str = "6h") -> pd.DataFrame:
    """Fetch Prometheus metrics and convert them to a wide-format Pandas DataFrame.

    Automatically handles time-slicing and aligns multiple time-series into a 
    single tabular structure where metrics are columns and time is the index.

    Args:
        url: The Prometheus API endpoint.
        metrics_query: The PromQL query.
        start_time: Start time (UTC). Defaults to 10 minutes ago.
        end_time: End time (UTC). Defaults to now.
        resolution: Step resolution (e.g., "1m").
        freq: Slicing frequency (e.g., "6h").

    Returns:
        A timezone-aware Pandas DataFrame.
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    if end_time is None:
        end_time = datetime.now(timezone.utc)

    date_range = prepare_time_slices(end_time=end_time, freq=freq, start_time=start_time)

    results = []
    for idx in range(len(date_range) - 1):
        start_slice = date_range[idx]
        end_slice = date_range[idx + 1]
        logger.info(f"Fetching chunk {idx+1}/{len(date_range)-1}: {start_slice} to {end_slice}")
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

    Optimized for memory and speed by using vectorized operations.

    Args:
        prom_api_response: The JSON dictionary returned by the Prometheus API.

    Returns:
        A pivoted Pandas DataFrame with 'time' as index and 'id' as a column.
    """
    if "data" not in prom_api_response:
        return pd.DataFrame()

    prom_metrics = prom_api_response['data']['result']
    if not prom_metrics:
        return pd.DataFrame()

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
            times.append(int(timestamp))
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

    # Pivot to wide format
    # Optimization: if only one metric name, avoid full pivot_table
    unique_metrics = df['metric_name'].unique()
    if len(unique_metrics) == 1:
        metric_name = unique_metrics[0]
        df.rename(columns={'value': metric_name}, inplace=True)
        df.drop(columns=['metric_name'], inplace=True)
        df = df.set_index(['time', 'id'])
    else:
        df = df.pivot_table(index=['time', 'id'], columns='metric_name', values='value')

    df = df.reset_index()
    df['time'] = df['time'].dt.tz_localize('UTC')
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    return df

def __convert_timeseries(column_pos: Dict[str, int], df: pd.DataFrame, metric_name: str, 
                         metric_scrape_id: str, prom_metric: Dict[str, Any]):
    # This function is now deprecated
    pass


def prepare_time_slices(start_time: datetime, end_time: datetime, freq: str) -> List[datetime]:
    start_time = start_time.replace(tzinfo=pytz.UTC)
    end_time = end_time.replace(tzinfo=pytz.UTC)
    
    date_range = pd.to_datetime(pd.date_range(start=start_time, end=end_time, freq=freq, tz=pytz.UTC)).tolist()
    
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
                                    'step': resolution})
    if response.ok:
        return response
    else:
        msg = "Status: {0} Text: {1}".format(response.status_code, response.text)
        logger.error(msg)
        raise RuntimeError(msg)

