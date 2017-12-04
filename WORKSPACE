git_repository(
    name = "io_bazel_rules_docker",
    remote = "https://github.com/bazelbuild/rules_docker.git",
    tag = "v0.3.0",
)

load(
    "@io_bazel_rules_docker//container:container.bzl",
    "container_pull",
    container_repositories = "repositories",
)

container_repositories()

######################### container end

load(
    "@io_bazel_rules_docker//python:image.bzl",
    _py_image_repos = "repositories",
)

git_repository(
    name = "io_bazel_rules_python",
    commit = "346b898e15e75f832b89e5da6a78ee79593237f0",
    remote = "https://github.com/bazelbuild/rules_python.git",
)

load("@io_bazel_rules_python//python:pip.bzl", "pip_repositories")
load("@io_bazel_rules_python//python:pip.bzl", "pip_import")

pip_repositories()

pip_import(
    name = "my_deps",
    requirements = "//:requirements.txt",
)

load("@my_deps//:requirements.bzl", "pip_install")

pip_install()

###### python image
load(
    "@io_bazel_rules_docker//python:image.bzl",
    _py_image_repos = "repositories",
)

_py_image_repos()
