API_RESP_RAW_METRIC = """
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": {
          "method": "GET",
          "instance": "10.1.0.1:102",
          "job": "cadvisor",
         "__name__": "up"

        },
        "values": [
          [
            1500008340,
            "3"
          ],
          [
            1500008400,
            "4"
          ]
        ]
      }
    ]
  }
}
"""
API_RESP_DERIVED_METRIC = """
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": { 
        },
        "values": [
          [
            1500008340,
            "1"
          ],
          [
            1500008400,
            "2"
          ]
        ]
      }
    ]
  }
}
"""
API_RESP_MULT_METRICS = """
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": {
          "__name__": "up",
          "instance": "10.12.0.1:1012",
          "job": "cadvisor"
        },
        "values": [
          [
            1499749200,
            "1"
          ],
          [
            1499749260,
            "1"
          ]
        ]
      },
      {
        "metric": {
          "__name__": "up",
          "instance": "10.1.1.7:102",
          "job": "cadvisor"
        },
        "values": [
          [
            1499749200,
            "1"
          ],
          [
            1499749260,
            "1"
          ]
        ]
      }
    ]
  }
}
"""
API_RESPONSE_ALERTS = """
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": {
          "__name__": "ALERTS",
          "alertname": "HighUsage",
          "alertstate": "firing",
          "code": "200",
          "handler": "graph",
          "instance": "localhost:9090",
          "job": "prometheus",
          "method": "get"
        },
        "values": [
          [
            1502711794.834,
            "1"
          ],
          [
            1502711809.834,
            "1"
          ]
        ]
      }
    ]
  }
}
"""
API_RESPONSE_EMPTY = """
  {"status":"success","data":{"resultType":"matrix","result":[]}}
"""