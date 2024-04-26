import pulumi

from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs

from pulumi_kubernetes.core.v1 import Namespace, Service, ServiceSpecArgs, ServicePortArgs
from pulumi_kubernetes.core.v1 import ContainerArgs, ContainerPortArgs, EnvVarArgs
from pulumi_kubernetes.core.v1 import PodTemplateSpecArgs, PodSpecArgs, VolumeMountArgs, ResourceRequirementsArgs
from pulumi_kubernetes.core.v1 import PersistentVolumeClaimVolumeSourceArgs, VolumeArgs, PersistentVolumeClaim, PersistentVolumeClaimSpecArgs

from pulumi_kubernetes.meta.v1 import ObjectMetaArgs, LabelSelectorArgs

# https://github.com/open-webui/open-webui/blob/main/kubernetes/manifest/base/

# Define Kubernetes Namespace where the resources will be deployed
app_namespace = Namespace("ollama",
    metadata=ObjectMetaArgs(
        name="ollama-service",
    )
)

# Define the image for the custom ML service
container_image = "ollama/ollama:latest"

# Define a PersistentVolumeClaim for Ollama
labels_oollama = {"app": "ollama"}
claim_name_oollama = "ollama-pvc"
pvc_ollama = PersistentVolumeClaim(
    claim_name_oollama,
    metadata=ObjectMetaArgs(
        name="ollama-pvc",
        namespace=app_namespace.metadata.apply(lambda m: m["name"]),
        labels=labels_oollama,
    ),
    spec=PersistentVolumeClaimSpecArgs(
        access_modes=["ReadWriteMany"],
        resources=ResourceRequirementsArgs(
            requests={"storage": "5Gi"}
        ),
    ),
)

# Define the Kubernetes Deployment for OLLama
ml_deployment = Deployment(
    "ollama-deployment",
    metadata=ObjectMetaArgs(
        namespace=app_namespace.metadata.apply(lambda m: m["name"])
    ),
    spec=DeploymentSpecArgs(
        replicas=1,
        selector=LabelSelectorArgs(
            match_labels=labels_oollama
        ),
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(
                labels=labels_oollama,
            ),
            spec=PodSpecArgs(
                containers=[
                    ContainerArgs(
                        name="ollama",
                        image=container_image,
                        ports=[
                            ContainerPortArgs(container_port=11434)
                        ],
                        resources=ResourceRequirementsArgs(
                            requests={
                                "cpu": "8000m",
                                "memory": "8Gi",
                            },
                            limits={
                                "cpu": "10000m",
                                "memory": "10Gi",
                                "nvidia.com/gpu": "0",
                            },
                        ),
                        volume_mounts=[
                            VolumeMountArgs(
                                name="oollama-volume",
                                mount_path="/root/.ollama", #where models gets saved
                            ),
                        ],
                    ),
                ],
                volumes=[
                    VolumeArgs(
                        name="oollama-volume",
                        persistent_volume_claim=PersistentVolumeClaimVolumeSourceArgs(
                            claim_name=claim_name_oollama,
                        ),
                    ),
                ],
            ),
        ),
    )
)

# Define the Service to expose the custom ML service
ml_service = Service(
    "ollama-service",
    metadata=ObjectMetaArgs(
        namespace=app_namespace.metadata.apply(lambda m: m["name"])
    ),
    spec=ServiceSpecArgs(
        type="ClusterIP",
        selector=labels_oollama,
        ports=[
            ServicePortArgs(
                port=11434,
                target_port=11434,
            ),
        ],
    )
)


# Ensure that the labels defined in the Deployment match those in the Service
labels = {"app": "open-webui"}


# Define a PersistentVolumeClaim for UI
claim_name = "open-webui-pvc"
pvc = PersistentVolumeClaim(
    claim_name,
    metadata=ObjectMetaArgs(
        name="open-webui-pvc",
        namespace=app_namespace.metadata.apply(lambda m: m["name"]),
        labels=labels,
    ),
    spec=PersistentVolumeClaimSpecArgs(
        access_modes=["ReadWriteOnce"],
        resources=ResourceRequirementsArgs(
            requests={"storage": "2Gi"}
        ),
    ),
)


# Define the Deployment for open-webui
combined_name = pulumi.Output.all(
    ml_service.spec.apply(lambda spec: spec.cluster_ip)
).apply(
    lambda names: f"http://{names[0]}:11434"
)

open_webui_deployment = Deployment(
    "open-webui-deployment",
    metadata=ObjectMetaArgs(
        namespace=app_namespace.metadata.apply(lambda m: m["name"]),
    ),
    spec=DeploymentSpecArgs(
        replicas=1,
        selector=LabelSelectorArgs(
            match_labels=labels,
        ),
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(
                labels=labels,
            ),
            spec=PodSpecArgs(
                host_network=True,  # https://docs.openwebui.com/getting-started/troubleshooting/#open-webui-server-connection-error
                containers=[
                    ContainerArgs(
                        name="open-webui",
                        image="ghcr.io/open-webui/open-webui:main",
                        ports=[ContainerPortArgs(container_port=8080)],
                        env=[
                            EnvVarArgs(
                                name="OLLAMA_BASE_URL",
                                value=combined_name,
                            ),
                        ],
                        tty=True,
                        volume_mounts=[
                            VolumeMountArgs(
                                name="webui-volume",
                                mount_path="/app/backend/data",
                            ),
                        ],
                    ),
                ],
                volumes=[
                    VolumeArgs(
                        name="webui-volume",
                        persistent_volume_claim=PersistentVolumeClaimVolumeSourceArgs(
                            claim_name=claim_name,
                        ),
                    ),
                ],
            ),
        ),
    )
)

# Define the Service for the open-webui Deployment
webui_service = Service(
    "open-webui-service",
    metadata=ObjectMetaArgs(
        namespace=app_namespace.metadata.apply(lambda m: m["name"])
    ),
    spec=ServiceSpecArgs(
        selector=labels,
        ports=[
            ServicePortArgs(
                port=8080,
                target_port=8080,
            ),
        ],
        type="ClusterIP",
    )
)



# Export the internal cluster IP of the ML service for reference
pulumi.export('persistent_volume_claim_name', pvc.metadata["name"])
pulumi.export('ollama_cluster_ip', ml_service.spec.apply(lambda spec: spec.cluster_ip))
pulumi.export('webui_service_endpoint', webui_service.spec.apply(lambda spec: spec.cluster_ip))
pulumi.export('OLLAMA_BASE_URL', combined_name)
