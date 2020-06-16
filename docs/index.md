# PYTHON
    from matplotlib import pyplot
    from parides.prom_conv import from_prom_to_df
    
    df = from_prom_to_df(
        resolution="15s",
        url="http://192.168.1.114:9090",
        metrics_query="prometheus_engine_query_duration_seconds{quantile=\"0.99\"}"
    )
    
    df.plot()
    pyplot.show()

# CLI

Export all metrics there are from the last 20 minutes to a local folder (useless, but doable :-)

    parides http://127.0.0.1:9090 {__name__=~\".+\"} 
        
Export a subset of the metrics with promql, otherwise use defaults.

    parides http://127.0.0.1:9090 {__name__=~\"http.*\"} 

Decrease data by increasing the sample rate of the query function with parameter "r"
  
    parides http://192.168.1.100:9090 {__name__=~\".+\"} \
        -s 2017-04-28T11:50:00+00:00 \
        -e 2017-04-30T12:55:00+00:00 \
        -r 15m

Query all alerts in a timeframe: 

    parides http://192.168.1.100:9090 \
            "sum(ALERTS{alertname=\"APIHighRequestLatencyOnGet\"}) by (host, alertname)"\
             -s 2017-04-28T11:50:00+00:00\
             -e 2017-04-30T12:55:00+00:00\
              -r 500