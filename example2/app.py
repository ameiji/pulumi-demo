import pulumi_kubernetes as k8s
import pulumi


class App:
    def __init__(self, app_name: str, app_labels: dict, app_image: str, dependency_list: list, k8s_provider: k8s.Provider):
        self.app_name = app_name
        self.app_labels = app_labels
        self.app_image = app_image
        self.opts = pulumi.ResourceOptions(depends_on=dependency_list, provider=k8s_provider)
        self.deployment = self.create_deployment()
        self.service = self.create_service()

    def create_deployment(self) -> k8s.apps.v1.Deployment:
        """Create the application deployment"""
        deployment = k8s.apps.v1.Deployment(
                    self.app_name,
                    spec=k8s.apps.v1.DeploymentSpecArgs(
                        replicas=1,
                        selector=k8s.meta.v1.LabelSelectorArgs(match_labels=self.app_labels),
                        template=k8s.core.v1.PodTemplateSpecArgs(
                            metadata=k8s.meta.v1.ObjectMetaArgs(labels=self.app_labels),
                            spec=k8s.core.v1.PodSpecArgs(
                                containers=[
                                    k8s.core.v1.ContainerArgs(
                                        name=self.app_name,
                                        image=self.app_image,
                                    )
                                ]
                            ),
                        ),
                    ),
                    opts=self.opts
                )
    
        return deployment

    def create_service(self) -> k8s.core.v1.Service:
        """Allocate an IP to the Deployment."""
        service = k8s.core.v1.Service(
                    self.app_name,
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels=self.app_labels),
                    spec=k8s.core.v1.ServiceSpecArgs(
                        selector=self.app_labels,
                        ports=[
                            k8s.core.v1.ServicePortArgs(
                                port=80,
                                target_port=80,
                                protocol="TCP"
                            )
                        ],
                        type="LoadBalancer",
                    ),
                    opts=self.opts
                )

        return service

    def export(self):
        pulumi.export("frontend_IP", self.service.status.apply(lambda s: s.load_balancer.ingress[0].ip))
