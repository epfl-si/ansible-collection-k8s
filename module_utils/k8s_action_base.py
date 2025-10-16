from copy import deepcopy

from ansible.plugins.action import ActionBase

class K8sActionBase (ActionBase):
    def run(self, task_vars=None):
        module_args = self._task.args

        if (
                "ansible_k8s_kubeconfig" in task_vars
                and "kubeconfig" not in module_args
        ):
            module_args = deepcopy(module_args)
            module_args["kubeconfig"] = self._templar.template(
                task_vars["ansible_k8s_kubeconfig"])

        return self._execute_module(
                module_name=self.WRAPPED_MODULE_NAME,
                module_args=module_args,
                task_vars=task_vars)
