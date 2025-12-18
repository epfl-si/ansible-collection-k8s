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

class Kubeconfig:
    """Access (credentials to) the Kubernetes cluster in the `epfl_si.k8s` way."""
    def __init__ (self, *, args, vars=None, expand_vars_fn=None):
        """Class constructor.


        @param args           The arguments dict, as if from the YAML (after
                              Jinja expansion).

        @param vars           The vars dict from the current task. Only required
                              (or meaningful) on the Ansible controller (not in
                              a module). If set, `expand_vars_fn` must be set as well.

        @param expand_vars_fn The function that should be used to expand
                              vars, e.g. the `templar.template` bound
                              method from an Ansible `Templar` instance.
        """

        self.args = args

        if vars is not None:
            if expand_vars_fn is None:
                raise ValueError("`expand_vars_fn` is required if `vars` is passed.")
            self._vars = vars
            self._expand_vars_fn = expand_vars_fn
        else:
            self._vars = {}

    def has_var (self, key):
        return key in self._vars

    def expand_var (self, key):
        if self.has_var(key):
            return self._expand_vars_fn(self._vars[key])
        else:
            return None

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
        if "kubeconfig" not in ret and self.has_var("ansible_k8s_kubeconfig"):
            ret["kubeconfig"] = self.expand_var("ansible_k8s_kubeconfig")

        return ret
