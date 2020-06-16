from matplotlib import pyplot
from parides.prom_conv import from_prom_to_df

df = from_prom_to_df(
    resolution="15s",
    url="http://192.168.1.114:9090",
    metrics_query="prometheus_engine_query_duration_seconds{quantile=\"0.99\"}"
)

df.plot()
pyplot.show()
