import logging
from datetime import datetime
from datetime import timedelta

import requests


def get_prom_api_response(url,
                          query,
                          end_time=datetime.utcnow(),
                          start_time=(datetime.utcnow() - timedelta(minutes=1)),
                          resolution="60"):

    url_new = '{0}/api/v1/query_range'.format(url)
    response = requests.get(url_new,
                            params={'query': query,
                                    'start': start_time,
                                    'end': end_time,
                                    'step': resolution})
    if response.ok:
        return response
    else:
        msg = "Status: {0} Text: {1}".format(response.status_code, response.text)
        logging.error(msg)
        raise RuntimeError(msg)
