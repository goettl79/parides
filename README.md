# Parides

Parides is a simple python module to convert Prometheus metrics data to a panda frame or a comma-separated file. 
The following python example will export all metrics there are from the last 20 minutes to a default local timeseries 
folder called "timeseries". 

    python3 -m parides.cli.main \
        --id=all \
        --delta=20 \
        http://127.0.0.1:9090 {__name__=~\".+\"}


Alternatively, if you prefer docker do:        


    docker run \
        -u $(id -u):$(id -g) \
        -v $(pwd)/timeseries:/usr/src/app/timeseries \
        -i goettl/parides \
            http://192.168.2.110:9090 {__name__=~\".+\"} \
            --id=all \
            --delta=20 

Some examples of how to use it are in the [documentation](docs/index.md) section.