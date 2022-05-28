from app import App
import iam
import vpc
import utils
import pulumi
from pulumi_aws import eks
import pulumi_kubernetes as k8s

config = pulumi.Config('app')
app_name = config.require('name')
app_image = config.require('image')
app_labels = {"app": app_name}
# EKS Cluster

eks_cluster = eks.Cluster(
    'eks-cluster',
    role_arn=iam.eks_role.arn,
    tags={
        'Name': 'pulumi-eks-cluster',
    },
    vpc_config=eks.ClusterVpcConfigArgs(
        public_access_cidrs=['0.0.0.0/0'],
        security_group_ids=[vpc.eks_security_group.id],
        subnet_ids=vpc.subnet_ids,
    ),
)

eks_node_group = eks.NodeGroup(
    'eks-node-group',
    cluster_name=eks_cluster.name,
    node_group_name='pulumi-eks-nodegroup',
    node_role_arn=iam.ec2_role.arn,
    subnet_ids=vpc.subnet_ids,
    tags={
        'Name': 'pulumi-cluster-nodeGroup',
    },
    scaling_config=eks.NodeGroupScalingConfigArgs(
        desired_size=2,
        max_size=2,
        min_size=1,
    ),
)

dependency_list = [
    eks_cluster,
    eks_node_group,
]

kubeconfig = utils.generate_kube_config(eks_cluster)

k8s_provider = k8s.Provider('k8s_provider', kubeconfig=kubeconfig)
app = App(app_name, app_labels, app_image, dependency_list, k8s_provider)

pulumi.export('cluster-name', eks_cluster.name)
pulumi.export('kubeconfig', kubeconfig)
pulumi.export("frontend_IP", app.service.status.apply(lambda s: s.load_balancer.ingress[0].ip))
