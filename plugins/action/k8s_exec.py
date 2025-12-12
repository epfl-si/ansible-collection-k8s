from ansible_collections.epfl_si.k8s.module_utils.k8s_action_base import K8sActionBase

class ActionModule (K8sActionBase):
    WRAPPED_MODULE_NAME = "kubernetes.core.k8s_exec"
