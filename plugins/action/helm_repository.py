from ansible_collections.epfl_si.k8s.plugins.module_utils.k8s_action_base import K8sActionBase

class ActionModule (K8sActionBase):
    """Like `kubernetes.core.helm_repository`, except the task implicitly
    does `helm repo update` in case the repository was already
    `helm repo add`ed."""

    WRAPPED_MODULE_NAME = "kubernetes.core.helm_repository"

    def run (self, task_vars=None):
        result = super(ActionModule, self).run(task_vars=task_vars)

        if not result.get("changed"):
            result = self._merge_failure_result(
                result,
                self._low_level_execute_command("helm repo update"))

        return result

    def _merge_failure_result (self, r1, r2):
        if "failed" in r2:
            for k in ("failed", "stdin", "stdout", "message", "msg"):
                if k in r2:
                    r1[k] = r2[k]

        return r1
