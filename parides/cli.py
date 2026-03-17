#!/usr/bin/env python
import argparse
import sys
from datetime import timezone, datetime
import dateutil.parser
import requests

from parides.prom_conv import from_prom_to_csv, from_prom_to_parquet

def get_interactive_input(prompt, default=None):
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()

def run_wizard():
    print("\n🦋 Parides Interactive Setup Wizard")
    print("-----------------------------------")
    url = get_interactive_input("Prometheus URL", "http://localhost:9090")
    query = get_interactive_input("PromQL Query (e.g., up)")
    if not query:
        print("❌ Error: Query is required.")
        sys.exit(1)
        
    fmt = get_interactive_input("Output Format (csv/parquet)", "csv").lower()
    res = get_interactive_input("Resolution (e.g., 1m, 15s)", "1m")
    out = get_interactive_input("Output Directory", "timeseries")
    
    print("\n🚀 Running conversion...")
    try:
        if fmt == "csv":
            from_prom_to_csv(url=url, metrics_query=query, directory=out, resolution=res)
        else:
            from_prom_to_parquet(url=url, metrics_query=query, directory=out, resolution=res)
        print("✅ Done!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="🦋 Parides: Convert Prometheus metrics to CSV or Parquet for Data Science.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # URL and Query are only required if not running the wizard
    parser.add_argument("URL", nargs="?",
                        help="Prometheus API endpoint (e.g., http://localhost:9090)")
    parser.add_argument("query", nargs="?", help="PromQL query (e.g., 'up' or 'node_cpu_seconds_total')")
    
    parser.add_argument("-o", "--output-directory", help="Directory to write files to.", default="timeseries")
    parser.add_argument("-r", "--resolution", help="Step resolution (e.g. 1m, 15s, 1h)", default="15s")
    parser.add_argument("-f", "--format", choices=["csv", "parquet"], default="csv",
                        help="Output file format.")
    parser.add_argument("--dsid", default="prom", help="Dataset ID used in filename.")
    
    parser.add_argument("-s", "--start-date", type=lambda d: dateutil.parser.parse(d),
                        help="Start date (ISO 8601). Defaults to 10m ago.")
    parser.add_argument("-e", "--end-date", type=lambda d: dateutil.parser.parse(d),
                        help="End date (ISO 8601). Defaults to now.")

    # If no arguments at all, run wizard
    if len(sys.argv) == 1:
        run_wizard()
        return

    args = parser.parse_args()

    # If only one positional arg or missing required ones, show help or run wizard
    if not args.URL or not args.query:
        parser.print_help()
        print("\n💡 Pro-tip: Run 'parides' without arguments to start the interactive wizard!")
        sys.exit(1)

    # Date localization
    start_date = args.start_date
    if start_date and start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
        
    end_date = args.end_date
    if end_date and end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    try:
        if args.format == "csv":
            from_prom_to_csv(url=args.URL, metrics_query=args.query, dataset_id=args.dsid, 
                             directory=args.output_directory, start_time=start_date, 
                             end_time=end_date, resolution=args.resolution)
        else:
            from_prom_to_parquet(url=args.URL, metrics_query=args.query, dataset_id=args.dsid, 
                                 directory=args.output_directory, start_time=start_date, 
                                 end_time=args.end_date, resolution=args.resolution)
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to Prometheus at {args.URL}. Is it running?")
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ Prometheus API Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
