import argparse
import datetime
from parides.converter import data_to_csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("URL",
                        help="Prometheus http API endpoint. "
                             "Local example: http://127.0.0.1:9090")
    parser.add_argument("query", help="query to issue")
    parser.add_argument("-o", "--output-directory", help="Directory to write files to.", default="./timeseries/")
    parser.add_argument("-r", "--resolution", default="15s")
    parser.add_argument("--id", default="default")
    parser.add_argument("--delta", default=1, type=int, help="Time delta from now up to delta minutes back")
    args = parser.parse_args()


    END_TIME = datetime.datetime.utcnow()
    START_TIME_CALC = END_TIME - datetime.timedelta(minutes=args.delta)

    data_to_csv(url=args.URL,
                directory=args.output_directory,
                metrics_query=args.query,
                start_time=START_TIME_CALC,
                end_time=END_TIME,
                resolution=args.resolution,
                dataset_id=args.id)

if __name__ == "__main__":
    main()