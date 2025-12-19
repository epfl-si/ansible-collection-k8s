# -*- coding: utf-8; -*-

"""
Re-useable `kubectl exec` implementation.
"""

from collections import namedtuple
import shlex
import uuid
import yaml

from kubernetes.client.api import core_v1_api
from kubernetes.stream import stream


KubeExecResult = namedtuple('KubeExecResult', ('stdout', 'stderr', 'rc'))


class KubeExecError (Exception):
    """Raised when `kube_exec` returns a failed status at the Kubernetes level."""


def kube_exec (client, namespace, pod_name, container_name,
               cmd_and_args, *,
               stdin=None,
               close_stdin=True,
               **stream_opts):
    """
    Run `cmd_and_args` (a list of strings) in container
    `container_name` of pod `pod_name` in namespace `namespace`.

    If set, pass `stdin` (of type `string` or `bytes`) to the remote
    process' standard input. If `close_stdin` is true, attempt to
    close stdin (using some shell-based trickery, because stdin
    needing closing for POSIX pipelines to terminate, is apparently
    something the Kubernetes crew doesn't know or care about).

    Collect stdout, stderr and return code.
    """
    stream_opts.setdefault("stdout", True)
    stream_opts.setdefault("stderr", True)
    stream_opts.setdefault("tty", False)

    if  (stdin is not None) and close_stdin:
        # SIGHH. https://github.com/kubernetes-client/python/issues/2371
        # 💡 If your container doesn't have `dd` in the PATH (or
        # `/bin/sh`), too bad — Try passing `close_stdin=False` and
        # munging the command line on your own.
        cmd_and_args = ['/bin/sh', '-c',
                        'dd count=1 bs=%d status=none | %s' % (
                            bytes_length(stdin),
                            " ".join(shlex.quote(c)
                                     for c in cmd_and_args))]
        # ... At least the return code is preserved (POSIX says it's
        # the one of the last command in the pipeline).

    resp = stream(
        core_v1_api.CoreV1Api(client.client).connect_get_namespaced_pod_exec,
        pod_name,
        namespace,
        command=cmd_and_args,
        container=container_name,
        stdin=stdin is not None,
        **stream_opts,
        _preload_content=False)

    stdout, stderr = "", ""
    if stdin is not None:
        resp.write_stdin(stdin)
    while resp.is_open():
        resp.update(timeout=1)
        if resp.peek_stdout():
            stdout += resp.read_stdout()
        if resp.peek_stderr():
            stderr += resp.read_stderr()

    # Don't ask me, I just hoovered this from wherever 🤷‍♂️
    status = yaml.safe_load(resp.read_channel(3))

    if status["status"] == "Failure":
        raise KubeExecError(status["message"])
    if status["status"] == "Success":
        rc = 0
    else:
        rc = int(status["details"]["causes"][0]["message"])

    return KubeExecResult(rc=rc, stdout=stdout, stderr=stderr)


def bytes_length(bytes_or_string):
    if type(bytes_or_string) == bytes:
        return len(bytes_or_string)
    else:
        return len(bytes(bytes_or_string, 'utf-8'))
