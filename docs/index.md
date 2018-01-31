# Python / Panda

Install package with pip. 

    pip install parides

Use it like this will return you a dataframe from the Prometheus endpoint

    from parides.converter import data_from_prometheus
    
    df = data_from_prometheus(url="192.168.2.111",query="{__name__=~\".+\"}")

# Console  / CSV

Export all metrics there are from the last 20 minutes to a local timeseries folder

    python3 -m parides.cli.main http://127.0.0.1:9090 {__name__=~\".+\"} --id=all --delta=20

It makes most sense to export only a subset of the metrics. Use promql for it.

    python3 -m parides.cli.main http://127.0.0.1:9090 {__name__=~\"http.*\"} --id=http

