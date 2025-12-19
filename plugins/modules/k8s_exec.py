from kubernetes.client.apis import core_v1_api
from kubernetes.client.exceptions import ApiException

from ansible.module_utils._text import to_native

from ansible_collections.kubernetes.core.plugins.module_utils.ansiblemodule import (
    AnsibleModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    AUTH_ARG_SPEC,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import (
    AnsibleK8SModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.exceptions import (
    CoreException,
)

from ansible_collections.epfl_si.k8s.plugins.module_utils.kubeconfig import Kubeconfig
from ansible_collections.epfl_si.k8s.plugins.module_utils.exec import kube_exec

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
"""

def argspec():
    spec = dict(**AUTH_ARG_SPEC)
    spec["namespace"] = dict(type="str", required=True)
    spec["pod"] = dict(type="str", required=True)
    spec["container"] = dict(type="str")
    spec["command"] = dict(type="list", elements="str", required=True)
    spec["stdin"] = dict(type="str")
    spec["close_stdin"] = dict(type="bool", default=True)
    return spec


def execute_module(module, client):
    """Copied and modified from kubernetes.core.k8s's k8s_exec module."""
    optional_kwargs = {}
    container_name = None
    if module.params.get("container"):    # Tolerate `container: ~` in YAML
        container_name = module.params["container"]
    else:
        # default to the first container available on pod
        resp = None
        try:
            api = core_v1_api.CoreV1Api(client.client)
            resp = api.read_namespaced_pod(
                name=module.params["pod"], namespace=module.params["namespace"]
            )
        except ApiException:
            pass

        if resp and len(resp.spec.containers) >= 1:
            container_name = resp.spec.containers[0].name

    if container_name is None:
        raise ValueError("Must specify `container_name`")

    k = kube_exec(
        client,
        module.params["namespace"],
        module.params["pod"],
        container_name,
        module.params["command"],
        stdin=module.params.get("stdin"),
        close_stdin=module.params.get("close_stdin"))

    module.exit_json(
        changed=True,  # Must assume that way, since we don't know what the command does
        stdout=k.stdout,
        stderr=k.stderr,
        rc=k.rc,
        return_code=k.rc)


def main():
    module = AnsibleK8SModule(
        module_class=AnsibleModule,
        check_pyyaml=False,
        argument_spec=argspec(),
        supports_check_mode=True)

    try:
        execute_module(module, Kubeconfig(args=module.params).get_api_client())
    except CoreException as e:
        module.fail_from_exception(e)


if __name__ == "__main__":
    main()
