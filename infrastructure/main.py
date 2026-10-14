from diagrams.aws.network import ALB
from diagrams.aws.network import APIGateway
from diagrams.aws.storage import EFS
from diagrams.aws.compute import ECS
from diagrams.k8s.compute import Cronjob
from architecture import finalize_svg
from diagrams import Cluster, Diagram, Edge
from diagrams.k8s.clusterconfig import Quota
from diagrams.k8s.compute import Deploy, Pod
from diagrams.k8s.network import Service
from diagrams.k8s.podconfig import ConfigMap, Secret
from diagrams.k8s.rbac import RB, SA, Role
from diagrams.onprem.ci import GitlabCI
from diagrams.onprem.client import Users
from diagrams.onprem.logging import Loki
from diagrams.onprem.monitoring import Grafana, Prometheus
from diagrams.onprem.registry import Harbor
from diagrams.onprem.security import Trivy
from diagrams.onprem.tracing import Tempo
from diagrams.programming.language import Bash
from diagrams.saas.security import Sonarqube
from diagrams.aws.storage import S3
from diagrams.aws.database import RDS, Redshift, ElastiCache
from diagrams.aws.compute import ECR, ECR, EKS, EC2
from diagrams.aws.network import CloudFront, Route53
from diagrams.aws.ml import Bedrock




from architecture import Component, edge_attr, get_filename, graph_attr, outformat

with Diagram(
    "DevOps",
    filename=get_filename(__file__),
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    edge_attr=edge_attr,
    outformat=outformat,
):
    code_repo = Component("Git Repository", "gitlab")
    ci_repo = Component("Centralized CI Repository", "gitlab")
    infra_repo = Component("Infra Repository", "gitlab")
    gitops_repo = Component("GitOps Repository", "gitlab")

    dev_branch = Component("Dev Branch", "git")
    stage_branch = Component("Stage Branch", "git")
    main_branch = Component("Main Branch", "git")

    ci_repo >> code_repo
    dev_branch >> Edge(label="PR") >> stage_branch
    stage_branch >> Edge(label="PR") >> main_branch

    with Cluster("Precommit"):
        lint = Bash("Lint")
        format = Bash("Format Check")
        secret_scan = Bash("Secret Scan")

    (
        Users("Developer")
        >> Component("precommit", "git")
        >> [lint, format, secret_scan]
        >> Component("git push", "git")
        >> code_repo
        >> Component("Feature Branch", "git")
        >> Edge(label="PR")
        >> dev_branch
    )

    with Cluster("Infrastructure CI/CD"):
        with Cluster("Dev Infrastructure"):
            dev_infra_cicd = GitlabCI("Dev Infra CI/CD")
            dev_plan = Bash("TF Plan")
            dev_apply = Bash("TF Apply")

            dev_infra_cicd >> dev_plan >> dev_apply

        with Cluster("Stage Infrastructure"):
            stage_infra_cicd = GitlabCI("Stage Infra CI/CD")
            stage_plan = Bash("TF Plan")
            stage_apply = Bash("TF Apply")

            stage_infra_cicd >> stage_plan >> stage_apply

        with Cluster("Prod Infrastructure"):
            prod_infra_cicd = GitlabCI("Prod Infra CI/CD")
            prod_plan = Bash("TF Plan")
            prod_apply = Bash("TF Apply")

            prod_infra_cicd >> prod_plan >> prod_apply

    infra_repo >> Edge(label="Dev Branch") >> dev_infra_cicd
    infra_repo >> Edge(label="Stage Branch") >> stage_infra_cicd
    infra_repo >> Edge(label="Prod Branch") >>   prod_infra_cicd,


    with Cluster("Cloud Services"):
        azure = Component("Azure")
        aws = Component("AWS")
        gcp = Component("GCP")

        terraform = Component("Terraform")

        (
            [
                dev_apply,
                stage_apply,
                prod_apply,
            ]
            - terraform
            >> [
                azure,
                aws,
                gcp,
            ]
        )
    
    with Cluster("AWS"):
        with Cluster("Compute"):
            ec2 = EC2()
            ec2 - ECR() - ECS() - EKS()
        with Cluster("Database"):
            rds = RDS()
            rds - Redshift() -   ElastiCache()
        with Cluster("ML"):
            bedrock = Bedrock()
        with Cluster("Storage"):
            s3 = S3()
            s3 - EFS()
        with Cluster("Network"):
            cloudfront = CloudFront()
            cloudfront - APIGateway() -  ALB() - Route53()

    aws - [ec2, rds, bedrock, s3, cloudfront]

    otel = Component("OpenTelemetry", "otel")

    with Cluster("Observability"):
        grafana = Grafana("Grafana")

        with Cluster("LGTM"):
            loki = Loki("Loki")
            tempo = Tempo("Tempo")
            prometheus = Prometheus("Prometheus")

        otel >> [
            loki,
            tempo,
            prometheus,
        ]

        [
            loki,
            tempo,
            prometheus,
        ] >> grafana

    with Cluster("Dev Environment CI/CD"):
        dev_cicd = GitlabCI("Dev CI/CD")

        dev_lint = Bash("Lint")

        dev_test = Bash("Unit Test")

        dev_sast = Component(
            "SAST",
            "sonar",
        )

        dev_sca = Trivy("Dependency / SCA")

        dev_quality = Sonarqube("Quality Gate")

        dev_build = Bash("Build")

        dev_package = Bash("Build Container Image")

        dev_image_scan = Trivy("Container Image Scan")

        dev_push = Harbor("Push Image")

        dev_gitops = Bash("Update GitOps")

        dev_cicd >> [
            dev_lint,
            dev_test,
            dev_sast,
            dev_sca,
        ]

        [
            dev_lint,
            dev_test,
            dev_sast,
            dev_sca,
        ] >> dev_quality

        (
            dev_quality
            >> dev_build
            >> dev_package
            >> dev_image_scan
            >> dev_push
            >> dev_gitops
        )

    dev_branch >> dev_cicd

    dev_gitops >> Edge(label="Git Commit") >> gitops_repo

    with Cluster("Stage Promotion"):
        stage_cicd = GitlabCI("Stage CI/CD")

        stage_validate = Bash("Validate")

        stage_promote = Bash("Promote Image")

        stage_gitops = Bash("Update GitOps")

        (stage_cicd >> stage_validate >> stage_promote >> stage_gitops)

    stage_branch >> stage_cicd

    stage_gitops >> Edge(label="Git Commit") >> gitops_repo

    with Cluster("Prod Promotion"):
        prod_cicd = GitlabCI("Prod CI/CD")

        prod_validate = Bash("Validate")

        prod_approval = Bash("Manual Approval")

        prod_tag_generation = Bash("Manual Approval")

        prod_promote = Bash("Promote Image")

        prod_gitops = Bash("Update GitOps")

        (prod_cicd >> prod_validate >> prod_approval >> prod_tag_generation >> prod_promote >> prod_gitops)
        code_repo << prod_tag_generation

    main_branch >> prod_cicd

    prod_gitops >> Edge(label="Git Commit") >> gitops_repo

    with Cluster("DEV Kubernetes Cluster"):
        with Cluster("KEDA"):
            Component("","keda")
        
        with Cluster("Serverless"):
            Component("Knative","knative")
        
        with Cluster("Virtualization "):
            Component("KubeVirt","kubevirt")

        with Cluster("ArgoCD Namespace"):
            dev_argocd = Component(
                "Argo CD",
                "argocd",
            )

        with Cluster("Application Namespace"):
            dev_deployment = Deploy("Deployment")
            dev_cj = Cronjob("CronJob")

            with Cluster("Pod Config"):
                dev_cm = ConfigMap("ConfigMap")

                dev_secret = Secret("Secret")

            with Cluster("RBAC"):
                dev_sa = SA("Service Account")

                dev_role = Role("Role")

                dev_rb = RB("Role Binding")

            dev_quota = Quota("Resource Quota")

            dev_service = Service("Service")

            dev_deployment << [
                dev_cm,
                dev_secret,
            ] >> dev_cj

            dev_service << dev_deployment

        with Cluster("Gateway API & Service Mesh"):
            dev_gateway = Component(
                "Istio Service Mesh",
                "istio",
            )

        dev_gateway << dev_service

        dev_reloader = Pod("Reloader")

    with Cluster("STAGE Kubernetes Cluster"):
        with Cluster("KEDA"):
            Component("","keda")

        with Cluster("Serverless"):
            Component("Knative","knative")

        with Cluster("Virtualization "):
            Component("KubeVirt","kubevirt")

        with Cluster("ArgoCD Namespace"):
            stage_argocd = Component(
                "Argo CD",
                "argocd",
            )

        with Cluster("Application Namespace"):
            stage_deployment = Deploy("Deployment")
            stage_cj = Cronjob("CronJob")

            with Cluster("Pod Config"):
                stage_cm = ConfigMap("ConfigMap")

                stage_secret = Secret("Secret")

            with Cluster("RBAC"):
                stage_sa = SA("Service Account")

                stage_role = Role("Role")

                stage_rb = RB("Role Binding")

            stage_quota = Quota("Resource Quota")

            stage_service = Service("Service")

            stage_deployment << [
                stage_cm,
                stage_secret,
            ] >> stage_cj

            stage_service << stage_deployment

        with Cluster("Gateway API & Service Mesh"):
            stage_gateway = Component("Istio", "istio")

        stage_gateway << stage_service

        stage_reloader = Pod("Reloader")

    with Cluster("PROD Kubernetes Cluster"):
        with Cluster("KEDA"):
            Component("","keda")

        with Cluster("Serverless"):
            Component("Knative","knative")
        
        with Cluster("Virtualization "):
            Component("KubeVirt","kubevirt")
            
        with Cluster("ArgoCD Namespace"):
            prod_argocd = Component(
                "Argo CD",
                "argocd",
            )

        with Cluster("Application Namespace"):
            prod_deployment = Deploy("Deployment")
            prod_cj = Cronjob("CronJob")

            with Cluster("Pod Config"):
                prod_cm = ConfigMap("ConfigMap")

                prod_secret = Secret("Secret")

            with Cluster("RBAC"):
                prod_sa = SA("Service Account")

                prod_role = Role("Role")

                prod_rb = RB("Role Binding")

            prod_quota = Quota("Resource Quota")

            prod_service = Service("Service")

            prod_deployment << [
                prod_cm,
                prod_secret,
            ] >> prod_cj

            prod_service << prod_deployment

        
        with Cluster("Gateway API & Service Mesh"):
            prod_gateway = Component("Istio", "istio")


        prod_gateway << prod_service

        prod_reloader = Pod("Reloader")

    (
        gitops_repo
        >> Edge(label="Watch / Sync")
        >> [
            dev_argocd,
            stage_argocd,
            prod_argocd,
        ]
    )

    [
        dev_deployment,
        stage_deployment,
        prod_deployment,
    ] >> otel


finalize_svg(__file__)
