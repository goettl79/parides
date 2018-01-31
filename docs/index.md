# Python / Panda Dataframe

Install package with pip. 

    pip install parides

Method ```data_from_prometheus``` returns a panda dataframe with Prometheus metrics. 

    from parides.converter import data_from_prometheus
    
    df = data_from_prometheus(url="192.168.2.111",query="{__name__=~\".+\"}")

# Console  / CSV

Export all metrics there are from the last 20 minutes to a local timeseries folder

    python3 -m parides.cli.main \
        http://127.0.0.1:9090 \
        {__name__=~\".+\"} \
        --id=all \
        --delta=20

Export a subset of the metrics with promql, otherwise use defaults.

    python3 -m parides.cli.main \
        http://127.0.0.1:9090 \
        {__name__=~\"http.*\"} \
        --id=http

