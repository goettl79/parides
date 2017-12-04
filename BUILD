package(default_visibility = ["//visibility:public"])

load("@io_bazel_rules_docker//python:image.bzl", "py_image")
load("@io_bazel_rules_python//python:python.bzl", "py_binary", "py_library")
load("@my_deps//:requirements.bzl", "requirement")

py_library(
    name = "lib",
    srcs = glob(
        ["parides/*.py"],
    ),
    srcs_version = "PY3",
    deps = [
        requirement("pandas"),
        requirement("requests"),
        requirement("numpy"),
    ],
)

py_binary(
    name = "parides_fly",
    srcs = glob(
        ["parides/cli/*.py"],
    ),
    default_python_version = "PY3",
    main = "parides/cli/main.py",
    srcs_version = "PY3",
    deps = [":lib"],
)

py_image(
    name = "parides_image",
    srcs = [":parides_fly"],
    main = "parides/cli/main.py",
)
