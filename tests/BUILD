load(
    "@io_bazel_rules_python//python:python.bzl",
    "py_test",
)

py_test(
    name = "test_unit",
    size = "small",
    srcs = [
        "__init__.py",
        "context.py",
        "test_basic.py",
    ],
    default_python_version = "PY3",
    main = "test_basic.py",
    srcs_version = "PY3",
    deps = [
        "//:lib",
    ],
)

py_test(
    name = "test_integration",
    size = "small",
    srcs = [
        "__init__.py",
        "context.py",
        "test_integration.py",
    ],
    default_python_version = "PY3",
    main = "test_integration.py",
    srcs_version = "PY3",
    deps = [
        "//:lib",
    ],
)
