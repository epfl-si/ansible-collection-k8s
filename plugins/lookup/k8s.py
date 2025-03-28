
DOCUMENTATION = """
    name: k8s

    short_description: Like C(kubernetes.core.k8s) lookup plugin, except it honors C(ansible_k8s_kubeconfig)
"""

EXAMPLES = """
- name: Fetch a list of namespaces
  set_fact:
    projects: "{{ query('epfl_si.k8s.k8s', api_version='v1', kind='Namespace') }}"

- name: Fetch all deployments
  set_fact:
    deployments: "{{ query('epfl_si.k8s.k8s', kind='Deployment') }}"

- name: Fetch all deployments in a namespace
  set_fact:
    deployments: "{{ query('epfl_si.k8s.k8s', kind='Deployment', namespace='testing') }}"

- name: Fetch a specific deployment by name
  set_fact:
    deployments: "{{ query('epfl_si.k8s.k8s', kind='Deployment', namespace='testing', resource_name='elastic') }}"

- name: Fetch with label selector
  set_fact:
    service: "{{ query('epfl_si.k8s.k8s', kind='Service', label_selector='app=galaxy') }}"

# Use parameters from a YAML config

- name: Load config from the Ansible controller filesystem
  set_fact:
    config: "{{ lookup('file', 'service.yml') | from_yaml }}"

- name: Using the config (loaded from a file in prior task), fetch the latest version of the object
  set_fact:
    service: "{{ query('epfl_si.k8s.k8s', resource_definition=config) }}"

- name: Use a config from the local filesystem
  set_fact:
    service: "{{ query('epfl_si.k8s.k8s', src='service.yml') }}"
"""

RETURN = """
  _list:
    description:
      - One ore more object definitions returned from the API.
    type: list
    elements: dict
    sample:
        - kind: ConfigMap
          apiVersion: v1
          metadata:
            creationTimestamp: "2022-03-04T13:59:49Z"
            name: my-config-map
            namespace: default
            resourceVersion: "418"
            uid: 5714b011-d090-4eac-8272-a0ea82ec0abd
          data:
            key1: val1
"""


from ansible_collections.kubernetes.core.plugins.lookup.k8s import KubernetesLookup, LookupBase


class LookupModule(LookupBase):
    """Lifted verbatim from kubernetes.core.k8s"""
    def _run(self, terms, variables=None, **kwargs):
        if "ansible_k8s_kubeconfig" in variables and "kubeconfig" not in kwargs:
            kwargs["kubeconfig"] = self._templar.template(variables["ansible_k8s_kubeconfig"])
        return KubernetesLookup().run(terms, variables=variables, **kwargs)

    run = _run if not hasattr(LookupBase, "run_on_daemon") else LookupBase.run_on_daemon
