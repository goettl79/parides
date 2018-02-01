
# Python / Panda Dataframe

Install package with pip. 

    pip install parides

Method ```data_from_prometheus``` returns a panda dataframe with Prometheus metrics. 

    from parides.converter import data_from_prometheus
    
    df = data_from_prometheus(url="192.168.2.111",query="{__name__=~\".+\"}")

# CLI

Export all metrics there are from the last 20 minutes to a local folder

    python3 -m parides.cli.main \
        http://127.0.0.1:9090 \
        {__name__=~\".+\"} 
        
Export a subset of the metrics with promql, otherwise use defaults.

    python3 -m parides.cli.main \
        http://127.0.0.1:9090 \
        {__name__=~\"http.*\"} 

Decrease data by increasing the sample rate of the query function with parameter "r"
  
    python3 -m parides.cli http://192.168.1.100:9090 {__name__=~\".+\"} \
        -s 2017-04-28T11:50:00+00:00 \
        -e 2017-04-30T12:55:00+00:00 \
        -r 15m
