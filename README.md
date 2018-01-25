# Parides

Parides is a simple python module to convert Prometheus metrics data to a panda frame or a comma-separated file.
The following example will export all metrics there are from the last 20 minutes to a local timeseries folder


    python3 -m parides.cli.main http://127.0.0.1:9090 {__name__=~\".+\"} --id=all --delta=20

Some examples of how to use it are in the [documentation](docs/index.md) section.