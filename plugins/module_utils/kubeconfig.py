# -*- coding: utf-8; -*-

"""Tools for consuming the Kubernetes configuration (“kubeconfig”) in the `epfl_si.k8s` way.

This is “isometric” code, meaning that it supports being imported
indifferently from local code (e.g. actions), or AnsiballZ mobile code
(e.g., modules). In the latter case, Ansible provides some
tree-shaking support that parses your module's imports, and ensure
that any `a.b.c.module_utils.d.e` dependencies are bundled in the
AnsiballZ.
"""

from copy import deepcopy

from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import requires
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import get_api_client
from ansible_collections.epfl_si.k8s.plugins.module_utils.ansible_internals import AnsibleVars

class Kubeconfig:
    """Access (credentials to) the Kubernetes cluster in the `epfl_si.k8s` way."""
    def __init__ (self, *, args, **vars_kwargs):
        """Class constructor.


        @param args           The arguments dict, as if from the YAML (after
                              Jinja expansion).

        @param vars_kwargs    Passed to `ansible_collections.epfl_si.k8s.plugins.module_utils.ansible_internals.AnsibleVars` as-is
        """

        self.args = args
        self.vars = AnsibleVars(**vars_kwargs)

    def as_augmented_args (self):
        """Returns a copy of construction-time `args`, with `kubeconfig` set from `vars` (unless already set.)

        This is for calling from the Ansible controller only (i.e. an
        action plugin; not a module). It is typically used for
        smuggling Kubernetes credentials to a module (i.e. remote
        AnsiballZ code), as if the `kubeconfig` task argument had been
        stipulated in full as a dict (like modern `kubernetes.k8s`
        permits).

        @return A dict that looks like the `args` constructor argument.

        """
        ret = deepcopy(self.args)
        if "kubeconfig" not in ret and self.vars.has("ansible_k8s_kubeconfig"):
            ret["kubeconfig"] = self.vars.expand("ansible_k8s_kubeconfig")

        return ret

    def get_api_client (self, server_side_dry_run=False):
        """
        @return An instance of `kubernetes.client.APIClient`
        """

        class MockModule:
            def __init__ (self, params):
                self.params = params
                self.server_side_dry_run = server_side_dry_run

            def requires (self, *args, **kwargs):
                return requires(*args, **kwargs)

        return get_api_client(module=MockModule(self.as_augmented_args())).client
