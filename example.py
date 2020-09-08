from matplotlib import pyplot
from parides.prom_conv import from_prom_to_df

df = from_prom_to_df(
    resolution="15s",
    url="http://192.168.1.114:9090",
    metrics_query="irate(node_cpu_seconds_total{instance=\"192.168.1.114:9100\"}[5m]) * 100"
)
plot = df.plot()
plot.get_legend().remove()
pyplot.show()
