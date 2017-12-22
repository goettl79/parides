# Python

TODO

# Console 

Export all metrics there are from the last 20 minutes to a local timeseries folder

    python3 -m parides.cli.main http://127.0.0.1:9090 {__name__=~\".+\"} --id=all --delta=20

It makes most sense to export only a subset of the metrics. Use promql for it.

    python3 -m parides.cli.main http://127.0.0.1:9090 {__name__=~\".+\"} --id=http

