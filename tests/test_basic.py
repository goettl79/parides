import json
import unittest
from datetime import datetime as datetime

from unittest.mock import patch

import pandas as pd

from parides.prom_conv import from_prom_to_df, from_prom_json_to_df
from tests.constants import API_RESP_RAW_METRIC, API_RESP_DERIVED_METRIC, API_RESP_MULT_METRICS, API_RESPONSE_EMPTY


class TestConversion(unittest.TestCase):

    def test_time_row_is_index(self):
        metrics_data = from_prom_json_to_df(prom_api_response=json.loads(API_RESP_RAW_METRIC))
        self.assertEqual(metrics_data.index.name, 'time')

    def test_parse_works_when_metric_name_was_removed(self):
        metrics_data = from_prom_json_to_df(
            prom_api_response=json.loads(API_RESP_DERIVED_METRIC))
        self.assertTupleEqual(metrics_data.shape, (2, 2))

    def test_parse_returns_empty_df_when_no_metrics_found(self):
        metrics_data = from_prom_json_to_df(
            prom_api_response=json.loads(API_RESPONSE_EMPTY))
        self.assertTupleEqual(metrics_data.shape, (0, 0))

    def test_result_is_panda_dataframe(self):
        metrics_data = from_prom_json_to_df(prom_api_response=json.loads(API_RESP_RAW_METRIC))
        self.assertIsInstance(metrics_data, pd.DataFrame)

    def test_columns_are_timeseries(self):
        metrics_data = from_prom_json_to_df(prom_api_response=json.loads(API_RESP_RAW_METRIC))
        self.assertIsInstance(metrics_data['up:method_GET'], pd.Series)

    def test_data_of_type_float64(self):
        metrics_data = from_prom_json_to_df(prom_api_response=json.loads(API_RESP_RAW_METRIC))
        self.assertEqual(metrics_data['up:method_GET'].dtype, 'float64')

    def test_metric_values_parsed(self):
        metrics_data = from_prom_json_to_df(prom_api_response=json.loads(API_RESP_RAW_METRIC))
        self.assertEqual(metrics_data['up:method_GET'].values[1], 4)

    def test_metric_values_parsed_when_metric_name_was_removed(self):
        metrics_data = from_prom_json_to_df(prom_api_response=json.loads(API_RESP_DERIVED_METRIC))
        self.assertEqual(metrics_data['value_1'].values[0], 1)
        self.assertEqual(metrics_data['value_1'].values[1], 2)

    def test_series_labels_are_flattened_as_column_names(self):
        metrics_data = from_prom_json_to_df(prom_api_response=json.loads(API_RESP_MULT_METRICS))
        self.assertEqual(metrics_data.shape, (4, 2), "Matrix shape doesn't look like two timeseries were exported.")

    def test_time_is_in_utc(self):
        metrics_data = from_prom_json_to_df(prom_api_response=json.loads(API_RESP_RAW_METRIC))
        first_time = metrics_data.index[0]
        python_date_time = pd.Timestamp(first_time).to_pydatetime()
        self.assertEqual(python_date_time, datetime(year=2017, month=7, day=14, hour=4, minute=59))


class TestIterateOverBigResults(unittest.TestCase):

    @patch('parides.prom_conv.requests.get')
    def test_query_is_splitted_with_freq(self, mock):
        dfs = from_prom_to_df(url="http://localhost", query="tralala",
                              start_time=datetime(year=2017, month=7, day=14, hour=4, minute=0),
                              end_time=datetime(year=2017, month=7, day=14, hour=4, minute=5),
                              freq="1min")
        self.assertEqual(5, len(dfs))

    @patch('parides.prom_conv.requests.get')
    def test_query_is_not_splitted_for_default(self, mock):
        dfs = from_prom_to_df(url="http://localhost", query="tralala")
        self.assertEqual(1, len(dfs))

    @patch('parides.prom_conv.requests.get')
    def test_queries_are_not_splitted_for_open_intervals(self, mock):
        dfs = from_prom_to_df(url="http://localhost", query="tralala",
                              start_time=datetime(year=2017, month=7, day=14, hour=4, minute=0),
                              end_time=datetime(year=2017, month=7, day=14, hour=4, minute=5),
                              freq="10min")
        self.assertEqual(1, len(dfs))


class TestPromApiV1Integration(unittest.TestCase):

    @patch('parides.prom_conv.requests.get')
    def test_convert_empty_response(self, mock_get):
        mock_get.return_value.ok = True
        # Call the service, which will send a request to the server.
        response = from_prom_to_df("http://localhost:9090", "{__name__=\".+\"}")

        # If the request is sent successfully, then I expect a response to be returned.
        self.assertIsNotNone(response)

    @patch('parides.prom_conv.requests.get')
    def test_convert_error_response(self, mock_get):
        mock_get.return_value.ok = False
        # Call the service, which will send a request to the server.
        try:
            from_prom_to_df("http://localhost:9090", "{__name__=\".+\"}")
            self.fail("This should have caused an exception to be thrown!")
        except RuntimeError:
            pass


if __name__ == '__main__':
    unittest.main()
