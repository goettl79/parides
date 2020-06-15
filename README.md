# Parides [![Build Status](https://github.com/goettl79/parides/workflows/Python-Package/badge.svg)](https://github.com/goettl79/parides/workflows/Python-Package/badge.svg)

Parides is a simple python module to convert Prometheus metrics data to a pandas dataframe or a comma-separated file.
For a jumpstart / converting to csv at the console use the docker command below. The csv file will be created in your /tmp
folder, containing prometheus data from the last 5 minutes.

    docker run \
        -v $(pwd)/timeseries:/usr/src/app/timeseries \
        -i goettl/parides \
            http://192.168.1.114:9090 "{__name__=~\".+\"}>0"
