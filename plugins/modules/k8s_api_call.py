from functools import cached_property
import json

from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import AnsibleK8SModule


import kubernetes   # Because Ansible code has this bizarre `except ImportError` clause on it, which we really don't want to investigate (again)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import get_api_client

DOCUMENTATION = r'''
---
module: k8s_api_call
short_description: Perform custom Kubernetes API calls
description:

- This is an I(Ansible module), i.e. some mobile Python code that
  Ansible executes on the remote host.

- This module lets your configuration-as-code send custom API calls to
  your Kubernetes API server, so as to perform operations not provided
  by the `kubernetes.core.k8s` module. For instance, Rancher uses
  custom API calls to install Helm packages.

- B(⚠ This module always returns a “changed“) (i.e. yellow) B(Ansible
  result.) It is up to you to short-circuit it (using a C(when:)
  clause) if its post-condition is already met.

options:
  method:
    description:
      - The HTTP method to use.
    type: str
    required: true

  uri:
    description:
      - The relative URI below the target cluster's entry point;
        typically starts with C(/v1/)
    type: str
    required: true

  body:
    description:
      - The HTTP request body, as a data structure I(before)
        serialization to JSON (done by the module)
    type: complex

  kubeconfig:
    type: complex
    required: false
    description:
      - The deserialized `kubeconfig` YAML file to authenticate with.
      - If not set, the (remote) file pointed to by the
        C(K8S_AUTH_KUBECONFIG) environment variable or the
        C(ansible_k8s_kubeconfig) Ansible var will be used.

version_added: 0.2.0
'''

EXAMPLES = r'''

- name: Install `some-helm-chart` on a Rancher cluster
  epfl_si.k8s.k8s_api_call:
    method: POST
    uri: /v1/catalog.cattle.io.clusterrepos/some-helm-repo?action=install
    body:
      namespace: some-namespace
      charts:
        - annotations:
            catalog.cattle.io/ui-source-repo-type: cluster
            catalog.cattle.io/ui-source-repo: some-helm-repo
          chartName: some-helm-chart
          releaseName: some-helm-chart
          version: 1.2.3
          resetValues: false
          values:
            foo: bar
            baz: quux
      wait: true
      timeout: 600s

'''

class APIError (Exception):
    pass

class APICall:
    """Implementation for `k8s_api_call` Ansible tasks."""
    module_args = dict(
        method=dict(type='str'),
        uri=dict(type='str'),
        body=dict(type='dict'),
        kubeconfig=dict(type='dict'))

    @cached_property
    def client (self):
        if self.module.params.get("kubeconfig") is not None:
            return APIClient(kubeconfig=self.module.params["kubeconfig"])
        else:
            return APIClient(module=self.module)

    @cached_property
    def module (self):
        return AnsibleK8SModule(
            argument_spec=self.module_args)

    def run (self):
        # https://stackoverflow.com/a/63747147
        data = self.client.call(
            self.module.params['method'],
            self.module.params['uri'],
            body=self.module.params['body'])

        self.module.exit_json(
            changed=True,
            api_response=data)


class APIClient:
    def __init__ (self, module=None, kubeconfig=None):
        if module is not None:
            # Ansible-style API: pass in an AnsibleModule instance
            client = get_api_client(module=module)
        elif kubeconfig is not None:
            client = get_api_client(kubeconfig=kubeconfig)
        else:
            raise ValueError("Unable to create API client from constructor arguments")

        self.client = client

    def call (self, method, uri, body=None):
        client = self.client.client.client  # Ansible was there 🤷
        (data, status, headers) = client.call_api(
            uri, method,   # Google was there 🤷
            auth_settings=['BearerToken'],
            response_type="object",
            body=body)

        if status not in (200, 201):
            raise APIError(data)

        return data


if __name__ == '__main__':
    APICall().run()
