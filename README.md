# Parides [![Build Status](https://travis-ci.org/goettl79/parides.svg?branch=master)](https://travis-ci.org/goettl79/parides)

Parides is a simple python module to convert Prometheus metrics data to a pandas dataframe or a comma-separated file.
For a jumpstart / converting to csv at the console use the docker command below. The csv file will be created in your /tmp
folder, containing prometheus data from the last 5 minutes.

    docker run \
        -v /tmp:/usr/src/app/timeseries \
        -i goettl/parides \
            192.168.42.60:9090 {__name__=~\".+\"} 


Further examples are currently under construction in the [documentation](https://goettl79.github.io/parides/) section.