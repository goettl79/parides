# Parides

Parides is a simple python module to convert Prometheus metrics data to a
panda frame or a comma-separated file. For a jumpstart use docker
command below:

    docker run \
        -u $(id -u):$(id -g) \
        -v $(pwd)/timeseries:/usr/src/app/timeseries \
        -i goettl/parides \
            http://192.168.2.110:9090 {__name__=~\".+\"} \
            --id=all \
            --delta=20 


Further examples are currently under construction in the [documentation](https://goettl79.github.io/parides/) section.