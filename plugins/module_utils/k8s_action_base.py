from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.k8s.plugins.module_utils.kubeconfig import Kubeconfig

class K8sActionBase (ActionBase):
    def run(self, task_vars=None):
        kubeconfig = Kubeconfig(vars=task_vars, args=self._task.args,
                                expand_vars_fn=self._templar.template)

        return self._execute_module(
                module_name=self.WRAPPED_MODULE_NAME,
                module_args=kubeconfig.as_augmented_args(),
                task_vars=task_vars)
