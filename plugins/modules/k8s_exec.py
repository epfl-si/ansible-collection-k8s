import yaml

from kubernetes.client.apis import core_v1_api
from kubernetes.client.exceptions import ApiException
from kubernetes.stream import stream

from ansible.module_utils._text import to_native

from ansible_collections.kubernetes.core.plugins.module_utils.ansiblemodule import (
    AnsibleModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    AUTH_ARG_SPEC,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import (
    get_api_client,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import (
    AnsibleK8SModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.exceptions import (
    CoreException,
)

DOCUMENTATION = r"""

module: k8s_exec

short_description: Execute a command in a Pod

version_added: 0.10.0

author: "EPFL ISAS-FSD <isas-fsd@groupes.epfl.ch>"

description:
  - Like C(kubernetes.core.k8s_exec), with additional features.

extends_documentation_fragment:
  - kubernetes.core.k8s_exec

options:
  command:
    required: yes
    type: list
    elements: str
    description:
    - The command to execute remotely, as an *array* rather than a shell-compatible string
  stdin:
    required: yes
    type: str
    description:
    - The UTF-8 encoded standard input text to pass to the remote command.
    - ⚠ stdin will *not* be closed in the remote process after sending this text,
      because this is not something that Kubernetes supports (kubernetes-client/python
      issue #2371). Consider (shudder!) using a variation of
      `['bash', '-c', 'sed -e "/#### CUT HERE ####/" | ...']` for your `command` if you
      require a properly closed stdin.
"""

def argspec():
    spec = dict(**AUTH_ARG_SPEC)
    spec["namespace"] = dict(type="str", required=True)
    spec["pod"] = dict(type="str", required=True)
    spec["container"] = dict(type="str")
    spec["command"] = dict(type="list", elements="str", required=True)
    spec["stdin"] = dict(type="str")
    return spec


def execute_module(module, client):
    """Copied and modified from kubernetes.core.k8s's k8s_exec module."""
    api = core_v1_api.CoreV1Api(client.client)

    optional_kwargs = {}
    if module.params.get("container"):    # Tolerate `container: ~` in YAML
        optional_kwargs["container"] = module.params["container"]
    else:
        # default to the first container available on pod
        resp = None
        try:
            resp = api.read_namespaced_pod(
                name=module.params["pod"], namespace=module.params["namespace"]
            )
        except ApiException:
            pass

        if resp and len(resp.spec.containers) >= 1:
            optional_kwargs["container"] = resp.spec.containers[0].name

    try:
        resp = stream(
            api.connect_get_namespaced_pod_exec,
            module.params["pod"],
            module.params["namespace"],
            command=module.params["command"],
            stdin="stdin" in module.params,
            stdout=True,
            stderr=True,
            tty=False,
            _preload_content=False,
            **optional_kwargs
        )
    except Exception as e:
        module.fail_json(
            msg="Failed to execute on pod %s"
            " due to : %s" % (module.params.get("pod"), to_native(e))
        )

    if "stdin" in module.params:
        resp.write_stdin(module.params["stdin"])

    stdout, stderr, rc = [], [], 0
    while resp.is_open():
        resp.update(timeout=1)
        if resp.peek_stdout():
            stdout.append(resp.read_stdout())
        if resp.peek_stderr():
            stderr.append(resp.read_stderr())
    err = resp.read_channel(3)
    err = yaml.safe_load(err)
    if err["status"] == "Success":
        rc = 0
    else:
        rc = int(err["details"]["causes"][0]["message"])

    module.exit_json(
        changed=True,
        stdout="".join(stdout),
        stderr="".join(stderr),
        rc=rc,
        return_code=rc)


def main():
    module = AnsibleK8SModule(
        module_class=AnsibleModule,
        check_pyyaml=False,
        argument_spec=argspec(),
        supports_check_mode=True)

    try:
        client = get_api_client(module)
        execute_module(module, client.client)
    except CoreException as e:
        module.fail_from_exception(e)


if __name__ == "__main__":
    main()
