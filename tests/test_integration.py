import datetime
import unittest
from datetime import timedelta

from parides.converter import data_to_csv, data_from_prometheus, data_from_csv

PROMETHEUS_URL = "http://127.0.0.1:9090"
TEST_TIME = datetime.datetime.utcnow()

class ApiIntegration(unittest.TestCase):

    def test_save_data_to_csv(self):
        directory = 'container_metrics'
        dataset_id = "incident_1"

        f = data_to_csv(url=PROMETHEUS_URL, metrics_query="up", dataset_id=dataset_id, directory=directory,
                        start_time=TEST_TIME - timedelta(minutes=5), end_time=TEST_TIME, resolution="15s")

        with open(f, 'r') as X_data:
            self.assertTrue('time,id,up' in X_data.read())

    def test_load_data_from_csv(self):
        X = data_from_csv(
            directory="data",
            dataset_id="incident_1",
        )
        print(X)

    def test_query_resolution_can_be_changed(self):
        metrics_data_high_res = \
            data_from_prometheus(url=PROMETHEUS_URL,
                                 query="up",
                                 start_time=TEST_TIME - timedelta(minutes=5),
                                 end_time=TEST_TIME,
                                 resolution="15s")

        metrics_data_low_res = \
            data_from_prometheus(url=PROMETHEUS_URL,
                                 query="up",
                                 start_time=TEST_TIME - timedelta(minutes=5),
                                 end_time=TEST_TIME,
                                 resolution="30s")

        self.assertLess(metrics_data_low_res['up'].sum(), metrics_data_high_res['up'].sum())


if __name__ == '__main__':
    unittest.main()
