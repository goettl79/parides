import errno
import hashlib
import logging
import os
from datetime import datetime as dt, datetime
from datetime import timedelta

import pandas as panda
import pytz
import requests


def from_prom_to_csv(url, metrics_query, dataset_id="id", directory="./prom-ts",
                     start_time=(dt.utcnow() - timedelta(minutes=10)),
                     end_time=dt.utcnow(), resolution="1m"):
    """
    Read data from prometheus and return as a csv file
    """

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
    print("Wrote to " + file  )
    return file


def from_prom_to_df(url, metrics_query,
                    start_time=(dt.utcnow() - timedelta(minutes=10)),
                    end_time=dt.utcnow(),
                    resolution="1m",
                    freq="10min"):
    """Parse data from Prometheus and return it as a panda frame"""
    date_range = prepare_time_slices(end_time=end_time, freq=freq, start_time=start_time)

    results = []
    for idx, date in enumerate(date_range):
        start_slice = date

        if idx < len(date_range) - 1:
            end_slice = date_range[idx + 1]
            json_query_results = __get_prom_api_response(url, metrics_query, start_time=start_slice.isoformat(),
                                                         end_time=end_slice.isoformat(), resolution=resolution)
            results.append(from_prom_json_to_df(json_query_results.json()))

    if len(results) == 0:
        raise ValueError("Prometheus did not return any values for query {}".format(metrics_query))
    return panda.concat(results, axis=0, join='outer', ignore_index=False, keys=None,
                     levels=None, names=None, verify_integrity=False, copy=True)


def from_prom_json_to_df(prom_api_response):
    data_frame = panda.DataFrame()

    if "data" not in prom_api_response:
        return data_frame

    prom_metrics = prom_api_response['data']['result']

    col_pos_index = {}
    anonymous_metric_counter = 0

    for prom_metric in prom_metrics:
        id_keys = {"instance", "job", "name"}
        metric_meta = prom_metric['metric']
        labels = set(metric_meta.keys()) - id_keys
        label_metrics = {label: metric_meta[label] for label in labels if label in metric_meta}
        ids = {label: metric_meta[label] for label in id_keys if label in metric_meta}
        metric_name = ""

        for key, value in sorted(label_metrics.items()):
            if key == '__name__':
                metric_name = metric_name + "{}:".format(value)
            else:
                metric_name = metric_name + "{}_{}_".format(key, value)

        metric_name = metric_name[:-1]

        if metric_name == "":
            anonymous_metric_counter += 1
            metric_name = "value_{}".format(anonymous_metric_counter)

        metric_scrape_id = ""
        for value in sorted(ids.values()):
            metric_scrape_id = metric_scrape_id + "{}_".format(value)
        metric_scrape_id = metric_scrape_id[:-1]

        if metric_name not in col_pos_index:
            col_pos_index[metric_name] = 0

        __convert_timeseries(col_pos_index, data_frame, metric_name, metric_scrape_id, prom_metric)

    if data_frame.size > 0:
        data_frame.set_index('time', inplace=True)
    data_frame.sort_index(inplace=True)
    return data_frame


def __convert_timeseries(column_pos, df, metric_name, metric_scrape_id, prom_metric):
    for value in prom_metric['values']:
        timestamp = panda.to_datetime(int(value[0]), unit='s')
        value = float(value[1])
        df.at[column_pos[metric_name], 'id'] = metric_scrape_id
        df.at[column_pos[metric_name], 'time'] = timestamp
        df.at[column_pos[metric_name], metric_name] = value
        column_pos[metric_name] += 1


def prepare_time_slices(start_time, end_time, freq):
    start_time = start_time.replace(tzinfo=pytz.UTC)
    end_time = end_time.replace(tzinfo=pytz.UTC)
    date_range = panda.to_datetime(panda.date_range(start=start_time, end=end_time, freq=freq, tz=pytz.UTC)).tolist()
    if len(date_range) < 2:
        date_range = [start_time.replace(tzinfo=pytz.UTC), end_time.replace(tzinfo=pytz.UTC)]
    return date_range


def __get_prom_api_response(url,
                            query,
                            end_time=datetime.utcnow(),
                            start_time=(datetime.utcnow() - timedelta(minutes=1)),
                            resolution="60"):
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
        logging.error(msg)
        raise RuntimeError(msg)
