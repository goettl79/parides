import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from parides.prom_conv import from_prom_to_df, from_prom_json_to_df, from_prom_to_csv, from_prom_to_parquet, prepare_time_slices
from tests.constants import (
    API_RESP_RAW_METRIC, 
    API_RESP_DERIVED_METRIC, 
    API_RESP_MULT_METRICS, 
    API_RESPONSE_EMPTY
)

@pytest.fixture
def raw_metric_json():
    return json.loads(API_RESP_RAW_METRIC)

@pytest.fixture
def derived_metric_json():
    return json.loads(API_RESP_DERIVED_METRIC)

@pytest.fixture
def multiple_metrics_json():
    return json.loads(API_RESP_MULT_METRICS)

@pytest.fixture
def empty_metric_json():
    return json.loads(API_RESPONSE_EMPTY)

def test_time_row_is_index(raw_metric_json):
    df = from_prom_json_to_df(raw_metric_json)
    assert df.index.name == 'time'
    assert isinstance(df.index, pd.DatetimeIndex)

def test_parse_works_when_metric_name_was_removed(derived_metric_json):
    df = from_prom_json_to_df(derived_metric_json)
    assert df.shape == (2, 2)
    assert 'value' in df.columns

def test_parse_returns_empty_df_when_no_metrics_found(empty_metric_json):
    df = from_prom_json_to_df(empty_metric_json)
    assert df.empty
    assert df.shape == (0, 0)

def test_result_is_panda_dataframe(raw_metric_json):
    df = from_prom_json_to_df(raw_metric_json)
    assert isinstance(df, pd.DataFrame)

def test_columns_are_timeseries(raw_metric_json):
    df = from_prom_json_to_df(raw_metric_json)
    assert isinstance(df['up:method_GET'], pd.Series)

def test_data_of_type_float64(raw_metric_json):
    df = from_prom_json_to_df(raw_metric_json)
    assert df['up:method_GET'].dtype == 'float64'

def test_metric_values_parsed(raw_metric_json):
    df = from_prom_json_to_df(raw_metric_json)
    assert df['up:method_GET'].iloc[1] == 4

def test_metric_values_parsed_when_metric_name_was_removed(derived_metric_json):
    df = from_prom_json_to_df(derived_metric_json)
    assert df['value'].iloc[0] == 1
    assert df['value'].iloc[1] == 2

def test_series_labels_are_flattened_as_column_names(multiple_metrics_json):
    df = from_prom_json_to_df(multiple_metrics_json)
    # The original test expected (4, 2) because it didn't align by time.
    # With pivot_table, it aligns 2 timestamps and 2 unique 'id' values.
    # Multiple series with same labels but different values? 
    # API_RESP_MULT_METRICS has 2 series with different instances.
    # Instance 10.12.0.1:1012 and 10.1.1.7:102.
    # In my new code, these have different 'id' values.
    # So we get 2 rows per timestamp (one for each id).
    # Total 2 timestamps * 2 ids = 4 rows.
    # Columns: id, up (metric name)
    assert df.shape == (4, 2)

def test_time_is_in_utc(raw_metric_json):
    df = from_prom_json_to_df(raw_metric_json)
    first_time = df.index[0]
    expected = datetime(year=2017, month=7, day=14, hour=4, minute=59, tzinfo=timezone.utc)
    
    # Ensure the timestamp is what we expect and in UTC
    assert first_time.timestamp() == expected.timestamp()
    assert first_time.tzinfo is not None

@pytest.mark.parametrize("start, end, freq, expected_len", [
    (datetime(2017, 7, 14, 4, 0), datetime(2017, 7, 14, 4, 5), "1min", 6),
    (datetime(2017, 7, 14, 4, 0), datetime(2017, 7, 14, 4, 5), "10min", 2),
])
def test_prepare_time_slices(start, end, freq, expected_len):
    slices = prepare_time_slices(start_time=start, end_time=end, freq=freq)
    assert len(slices) == expected_len

def test_mocked_save_data_to_csv(mocker, raw_metric_json, tmp_path):
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.ok = True
    mock_get.return_value.json.return_value = raw_metric_json
    
    directory = tmp_path / 'metrics'
    dataset_id = "incident_1"

    file_path = from_prom_to_csv(url="http://mock",
                                 metrics_query="up",
                                 dataset_id=dataset_id,
                                 directory=str(directory))

    assert Path(file_path).exists()
    content = Path(file_path).read_text()
    assert 'time,id,up:method_GET' in content

def test_mocked_save_data_to_parquet(mocker, raw_metric_json, tmp_path):
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.ok = True
    mock_get.return_value.json.return_value = raw_metric_json
    
    directory = tmp_path / 'metrics_parquet'
    dataset_id = "incident_parquet"

    file_path = from_prom_to_parquet(url="http://mock",
                                    metrics_query="up",
                                    dataset_id=dataset_id,
                                    directory=str(directory))

    assert Path(file_path).exists()
    assert file_path.endswith(".parquet")
    # Verify we can read it back
    df = pd.read_parquet(file_path)
    assert not df.empty
    assert "up:method_GET" in df.columns

def test_mocked_convert_empty_response(mocker, empty_metric_json):
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.ok = True
    mock_get.return_value.json.return_value = empty_metric_json
    
    # from_prom_to_df raises ValueError if no results are returned across all slices
    with pytest.raises(ValueError, match="Prometheus did not return any values"):
        from_prom_to_df("http://localhost:9090", "non_existent_metric")

@pytest.mark.parametrize("status_code, error_text", [
    (500, "Internal Server Error"),
    (404, "Not Found"),
    (401, "Unauthorized"),
])
def test_mocked_convert_error_response(mocker, status_code, error_text):
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.ok = False
    mock_get.return_value.status_code = status_code
    mock_get.return_value.text = error_text
    
    with pytest.raises(RuntimeError, match=f"Status: {status_code}"):
        from_prom_to_df("http://localhost:9090", "up")


def _matrix(series):
    """series: list of (labels, [(ts, value), ...])"""
    return {"status": "success", "data": {"resultType": "matrix", "result": [
        {"metric": m, "values": [[t, str(v)] for t, v in vals]} for m, vals in series]}}


def _mock_chunks(mocker, responses):
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.ok = True
    mock_get.return_value.json.side_effect = responses


T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
T1 = datetime(2024, 1, 1, 0, 2, tzinfo=timezone.utc)
B = int(T0.timestamp())


def test_chunk_boundary_not_duplicated(mocker):
    _mock_chunks(mocker, [
        _matrix([({"__name__": "up", "instance": "a"}, [(B, 1), (B + 60, 1)])]),
        _matrix([({"__name__": "up", "instance": "a"}, [(B + 60, 1), (B + 120, 1)])]),
    ])
    df = from_prom_to_df("http://mock", "up", start_time=T0, end_time=T1, freq="1min")
    assert len(df) == 3
    assert not df.index.duplicated().any()


def test_long_layout_keeps_labels_as_columns():
    resp = _matrix([({"__name__": "cpu", "instance": "a", "mode": "idle"}, [(B, 1)]),
                    ({"__name__": "cpu", "instance": "b", "mode": "user"}, [(B, 2)])])
    df = from_prom_json_to_df(resp, layout="long")
    assert list(df.columns) == ["metric", "instance", "mode", "value"]
    assert df.index.tz is not None
    assert set(df["mode"]) == {"idle", "user"}


def test_invalid_layout_rejected():
    with pytest.raises(ValueError):
        from_prom_json_to_df({}, layout="tall")


def test_csv_timestamps_iso_utc_roundtrip(mocker, tmp_path):
    _mock_chunks(mocker, [_matrix([({"__name__": "up", "instance": "a"}, [(B, 1)])])])
    path = from_prom_to_csv("http://mock", "up", directory=str(tmp_path),
                            start_time=T0, end_time=T1, chunk_size="6h")
    df = pd.read_csv(path, parse_dates=["time"], index_col="time")
    assert str(df.index.tz) == "UTC"
    assert df.index[0] == pd.Timestamp(T0)


def test_schema_drift_across_chunks_is_aligned(mocker, tmp_path):
    _mock_chunks(mocker, [
        _matrix([({"__name__": "m", "k": "x"}, [(B, 1)]), ({"__name__": "m", "k": "y"}, [(B, 2)])]),
        _matrix([({"__name__": "m", "k": "x"}, [(B + 60, 3)])]),
    ])
    path = from_prom_to_parquet("http://mock", "m", directory=str(tmp_path),
                                start_time=T0, end_time=T1, chunk_size="1min")
    df = pd.read_parquet(path)
    assert len(df) == 2  # series share one (empty) id, so they align on time
    assert df["m:k_y"].isna().sum() == 1
    import pyarrow.parquet as pq
    assert pq.read_schema(path).metadata[b"parides.layout"] == b"wide"


def _three_chunk_responses():
    s = {"__name__": "up", "instance": "a", "job": "j"}
    return [
        _matrix([(s, [(B, 1), (B + 60, 2)])]),
        _matrix([(s, [(B + 60, 2), (B + 120, 3)])]),
        _matrix([(s, [(B + 120, 3), (B + 180, 4)])]),
    ]


T3 = datetime(2024, 1, 1, 0, 3, tzinfo=timezone.utc)


def test_parquet_metadata_values(mocker, tmp_path):
    import pyarrow.parquet as pq
    _mock_chunks(mocker, _three_chunk_responses())
    path = from_prom_to_parquet("http://mock", "up", directory=str(tmp_path), start_time=T0,
                                end_time=T3, resolution="1m", chunk_size="1min", layout="long")
    meta = pq.read_schema(path).metadata
    assert meta[b"parides.query"] == b"up"
    assert meta[b"parides.step"] == b"1m"
    assert meta[b"parides.layout"] == b"long"
    assert meta[b"parides.timezone"] == b"UTC"
    assert meta[b"parides.start"] == T0.isoformat().encode()
    assert meta[b"parides.end"] == T3.isoformat().encode()
    assert b"pandas" in meta  # pandas round-trip metadata preserved


def test_multi_chunk_parquet_no_dupes_and_ordered(mocker, tmp_path):
    _mock_chunks(mocker, _three_chunk_responses())
    path = from_prom_to_parquet("http://mock", "up", directory=str(tmp_path), start_time=T0,
                                end_time=T3, chunk_size="1min")
    df = pd.read_parquet(path)
    assert df["up"].tolist() == [1, 2, 3, 4]
    assert df.index.is_monotonic_increasing
    assert str(df.index.tz) == "UTC"


def test_multi_chunk_csv_single_header_no_dupes(mocker, tmp_path):
    _mock_chunks(mocker, _three_chunk_responses())
    path = from_prom_to_csv("http://mock", "up", directory=str(tmp_path), start_time=T0,
                            end_time=T3, chunk_size="1min")
    lines = Path(path).read_text().splitlines()
    assert sum(l.startswith("time,") for l in lines) == 1
    assert len(lines) == 5


def test_multi_chunk_long_layout_df(mocker):
    _mock_chunks(mocker, _three_chunk_responses())
    df = from_prom_to_df("http://mock", "up", start_time=T0, end_time=T3, freq="1min", layout="long")
    assert df["value"].tolist() == [1, 2, 3, 4]
    assert list(df.columns) == ["metric", "instance", "job", "value"]


def test_multi_chunk_error_after_partial_write_raises(mocker, tmp_path):
    good = _three_chunk_responses()[0]
    _mock_chunks(mocker, [good, RuntimeError("boom")])
    with pytest.raises(RuntimeError, match="partial write"):
        from_prom_to_csv("http://mock", "up", directory=str(tmp_path), start_time=T0,
                         end_time=T3, chunk_size="1min")
