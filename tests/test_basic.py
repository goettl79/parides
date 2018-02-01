import datetime
import json
import unittest

import pandas as pd

from parides.converter import data_from_prom_api_response


class TestConversion(unittest.TestCase):

    def test_time_row_is_index(self):
        metrics_data = data_from_prom_api_response(prom_api_response=json.loads(API_RESP_RAW_METRIC))
        self.assertEqual(metrics_data.index.name, 'time')

    def test_parse_works_when_metric_name_was_removed(self):
        metrics_data = data_from_prom_api_response(
            prom_api_response=json.loads(API_RESP_DERIVED_METRIC))
        self.assertTupleEqual(metrics_data.shape, (2, 2))

    def test_parse_returns_empty_df_when_no_metrics_found(self):
        metrics_data = data_from_prom_api_response(
            prom_api_response=json.loads(API_RESPONSE_EMPTY))
        self.assertTupleEqual(metrics_data.shape, (0, 0))

    def test_result_is_panda_dataframe(self):
        metrics_data = data_from_prom_api_response(prom_api_response=json.loads(API_RESP_RAW_METRIC))
        self.assertIsInstance(metrics_data, pd.DataFrame)

    def test_columns_are_timeseries(self):
        metrics_data = data_from_prom_api_response(prom_api_response=json.loads(API_RESP_RAW_METRIC))
        self.assertIsInstance(metrics_data['up:method_GET'], pd.Series)

    def test_data_of_type_float64(self):
        metrics_data = data_from_prom_api_response(prom_api_response=json.loads(API_RESP_RAW_METRIC))
        self.assertEqual(metrics_data['up:method_GET'].dtype, 'float64')

    def test_metric_values_parsed(self):
        metrics_data = data_from_prom_api_response(prom_api_response=json.loads(API_RESP_RAW_METRIC))
        self.assertEqual(metrics_data['up:method_GET'].values[1], 4)

    def test_metric_values_parsed_when_metric_name_was_removed(self):
        metrics_data = data_from_prom_api_response(prom_api_response=json.loads(API_RESP_DERIVED_METRIC))
        self.assertEqual(metrics_data['value_1'].values[0], 1)
        self.assertEqual(metrics_data['value_1'].values[1], 2)

    def test_series_labels_are_flattened_as_column_names(self):
        metrics_data = data_from_prom_api_response(prom_api_response=json.loads(API_RESP_MULT_METRICS))
        self.assertEqual(metrics_data.shape, (4, 2), "Matrix shape doesn't look like two timeseries were exported.")

    def test_time_is_in_utc(self):
        metrics_data = data_from_prom_api_response(prom_api_response=json.loads(API_RESP_RAW_METRIC))
        first_time = metrics_data.index[0]
        pythonDateTime = pd.Timestamp(first_time).to_pydatetime()
        self.assertEqual(pythonDateTime, datetime.datetime(year=2017, month=7, day=14, hour=4, minute=59))


API_RESP_RAW_METRIC = """
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": {
          "method": "GET",
          "instance": "10.1.0.1:102",
          "job": "cadvisor",
         "__name__": "up"

        },
        "values": [
          [
            1500008340,
            "3"
          ],
          [
            1500008400,
            "4"
          ]
        ]
      }
    ]
  }
}
"""
API_RESP_DERIVED_METRIC = """
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": { 
        },
        "values": [
          [
            1500008340,
            "1"
          ],
          [
            1500008400,
            "2"
          ]
        ]
      }
    ]
  }
}
"""
API_RESP_MULT_METRICS = """
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": {
          "__name__": "up",
          "instance": "10.12.0.1:1012",
          "job": "cadvisor"
        },
        "values": [
          [
            1499749200,
            "1"
          ],
          [
            1499749260,
            "1"
          ]
        ]
      },
      {
        "metric": {
          "__name__": "up",
          "instance": "10.1.1.7:102",
          "job": "cadvisor"
        },
        "values": [
          [
            1499749200,
            "1"
          ],
          [
            1499749260,
            "1"
          ]
        ]
      }
    ]
  }
}
"""

API_RESPONSE_ALERTS = """
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": {
          "__name__": "ALERTS",
          "alertname": "HighUsage",
          "alertstate": "firing",
          "code": "200",
          "handler": "graph",
          "instance": "localhost:9090",
          "job": "prometheus",
          "method": "get"
        },
        "values": [
          [
            1502711794.834,
            "1"
          ],
          [
            1502711809.834,
            "1"
          ]
        ]
      }
    ]
  }
}
"""
API_RESPONSE_EMPTY = """
  {"status":"success","data":{"resultType":"matrix","result":[]}}
"""
if __name__ == '__main__':
    unittest.main()
