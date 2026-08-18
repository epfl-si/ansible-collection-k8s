# -*- coding: utf-8; -*-

"""Abstractions to defend against shenanigans in Ansible.

This is “isometric” code, meaning that it supports being imported
indifferently from local code (e.g. actions), or AnsiballZ mobile code
(e.g., modules). In the latter case, Ansible provides some
tree-shaking support that parses your module's imports, and ensure
that any `a.b.c.module_utils.d.e` dependencies are bundled in the
AnsiballZ.
"""

class AnsibleVars:
    """A bunch of Ansible variables, with optional support for template expansion."""
    def __init__ (self, vars={}, templar=None, jinja=None):
        """Class constructor.

        @param vars     The vars dict from the current task or module.

        @param templar  The `ansible.template.Templar` instance that should be
                        used to expand vars. Only required (or meaningful)
                        on the Ansible controller (not in a module).

        @param jinja    An instance of the `AnsibleJinja` class from the
                        `epfl_si.actions` collection. Requires `epfl_si.actions`
                        version 2.5.0 or above. Mutually
                        exclusive with both `vars` and `templar` (as
                        instances of that class encapsulate both).
        """

        self._vars = vars
        self._templar = templar
        self._jinja = jinja
        if self._jinja is not None and not hasattr(self._jinja, "resolve_variable"):
            raise RuntimeError("epfl_si.actions version 2.5.0 or above is required for the `jinja` constructor parameter")

    def has (self, key):
        if self._jinja is not None:
            return key in self._jinja.vars
        else:
            return key in self._vars

    def expand (self, var_name):
        if self._jinja is not None:
            return self._jinja.resolve_variable(var_name)
        elif self._templar is None:
            return self._vars[var_name]
        elif hasattr(self._templar, "resolve_variable_expression"):
            return self._templar.resolve_variable_expression(var_name)
        else:  # Older Ansibles before https://github.com/ansible/ansible/pull/84621
            return self._templar.template("{{ %s }}" % var_name)
