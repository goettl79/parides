# Parides [![Build Status](https://travis-ci.org/goettl79/parides.svg?branch=master)](https://travis-ci.org/goettl79/parides)

Parides is a simple python module to convert Prometheus metrics data to a pandas dataframe or a comma-separated file.
For a jumpstart / converting to csv at the console use the docker command below. The csv file will be created in your /tmp
folder, containing prometheus data from the last 5 minutes.

    mkdir timeseries
    docker run \
        -v $(pwd)/timeseries:/usr/src/app/timeseries \
        -u `id -u $USER` \
        -i goettl/parides \
            http://192.168.42.60:9090 {__name__=~\".+\"} 
