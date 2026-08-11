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
    def __init__ (self, vars={}, templar=None):
        """Class constructor.

        @param vars     The vars dict from the current task or module.

        @param templar  The `ansible.template.Templar` instance that should be
                        used to expand vars. Only required (or meaningful)
                        on the Ansible controller (not in a module).
        """

        self._vars = vars
        self._templar = templar

    def has (self, key):
        return key in self._vars

    def expand (self, key):
        if self._templar is not None:
            return self._templar.template("{{ %s }}" % var_name)
        else:
            return self._vars[key]
