import errno
import glob
import hashlib
import logging
import os
from datetime import timedelta
from datetime import datetime as dt

import pandas as panda
import pytz
import requests


def data_to_csv(url,
                directory,
                dataset_id,
                metrics_query,
                start_time=(dt.utcnow() - timedelta(hours=1)),
                end_time=dt.utcnow(),
                resolution="1m"):
  
    time_id_prefix = "{}-{}".format(start_time.timestamp(), end_time.timestamp())
    prefix = hashlib.sha1(time_id_prefix.encode("UTF-8")).hexdigest()[:4]

    X = data_from_prometheus(url, metrics_query, start_time, end_time, resolution)

    if X.empty:
        print("Prometheus did not return any values for query {}".format(metrics_query))
        return

    try:
        os.makedirs(directory)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(directory):
            pass
        else:
            raise

    file = directory + "/" + dataset_id + "_X_{}.csv".format(prefix)
    X.to_csv(file, date_format="%m/%d/%Y %H:%M:%S")
    return file

def data_from_csv(directory, dataset_id):
    training_data_files = glob.glob(directory + "/" + dataset_id + "_X_*.csv")

    X = panda.DataFrame()

    for training_data_file in training_data_files:
        Xtmp = panda.DataFrame.from_csv(training_data_file, index_col=0, header=0, infer_datetime_format=True)
        X = X.append(Xtmp)

    return X


def data_from_prometheus(url, query, start_time=(dt.now() - timedelta(hours=1)),
                         end_time=dt.now(), resolution="1m"):
    start_time_ts = start_time.replace(tzinfo=pytz.UTC).isoformat()
    end_time_ts = end_time.replace(tzinfo=pytz.UTC).isoformat()
    json_query_results = __fetch_data(url, query, end_time_ts, start_time_ts, resolution=resolution)
    # TODO Raise error here if query error / validate response
    X = data_from_prom_api_response(json_query_results)
    return X


def data_from_prom_api_response(prom_api_response):
    data_frame = panda.DataFrame()

    if "data" not in prom_api_response:
        return data_frame

    ts_raw_data = prom_api_response['data']['result']

    col_pos_index = {}
    anonymous_metric_counter = 0

    for prom_metric in ts_raw_data:
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

        if metric_name is "":
            anonymous_metric_counter += 1
            metric_name = "value_{}".format(anonymous_metric_counter)

        metric_scrape_id = ""
        for value in sorted(ids.values()):
            metric_scrape_id = metric_scrape_id + "{}_".format(value)
        metric_scrape_id = metric_scrape_id[:-1]

        if metric_name not in col_pos_index:
            col_pos_index[metric_name] = 0

        __convert_timeseries(col_pos_index, data_frame, metric_name, metric_scrape_id, prom_metric)

    data_frame.fillna(0, inplace=True)
    data_frame.set_index('time',inplace=True)
    data_frame.sort_index(inplace=True)
    return data_frame


def __fetch_data(url, query, end_time, start_time, resolution="1m"):
    url_new = '{0}/api/v1/query_range'.format(url)
    prom_response = requests.get(url_new,
                                 params={'query': query,
                                         'start': start_time,
                                         'end': end_time,
                                         'step': resolution})

    if prom_response.status_code != 200:
        logging.error("could not receive values " + prom_response.text)
    return prom_response.json()


def __convert_timeseries(column_pos, df, metric_name, metric_scrape_id, prom_metric):
    for value in prom_metric['values']:
        timestamp = dt.utcfromtimestamp(int(value[0]))
        value = float(value[1])
        df.at[column_pos[metric_name], 'id'] = metric_scrape_id
        df.at[column_pos[metric_name], 'time'] = timestamp
        df.at[column_pos[metric_name], metric_name] = value
        column_pos[metric_name] += 1
