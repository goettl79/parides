#!/usr/bin/env python
import argparse
import datetime

import dateutil.parser

from parides.prom_conv import from_prom_to_csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("URL",
                        help="Prometheus http API endpoint. "
                             "Local example: http://127.0.0.1:9090")
    parser.add_argument("query", help="Promql query")
    parser.add_argument("-o", "--output-directory", help="Directory to write files to.", default="timeseries")
    parser.add_argument("-r", "--resolution", default="15s")
    parser.add_argument("--dsid", default="prom", help="Id used to identify dataset.")
    parser.add_argument("-s", "--start-date", type=lambda d: dateutil.parser.parse(d),
                        default=datetime.datetime.utcnow() - datetime.timedelta(minutes=2))
    parser.add_argument("-e", "--end-date", type=lambda d: dateutil.parser.parse(d),
                        default=datetime.datetime.utcnow())
    args = parser.parse_args()

    from_prom_to_csv(url=args.URL, metrics_query=args.query, dataset_id=args.dsid, directory=args.output_directory,
                     start_time=args.start_date, end_time=args.end_date, resolution=args.resolution)


if __name__ == "__main__":
    main()
