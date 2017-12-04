#!/usr/bin/env bash

set -x

function stop_prom {
  sudo systemctl stop prometheus
}

trap stop_prom EXIT

BAZEL="bazel"
${BAZEL} test tests:test_unit
systemctl start prometheus
${BAZEL} run tests:test_integration
${BAZEL} run parides_image
