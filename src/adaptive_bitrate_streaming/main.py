from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import EKS
from diagrams.aws.database import ElastiCache, RDSPostgresqlInstance
from diagrams.aws.integration import SQS
from diagrams.aws.network import CloudFront
from diagrams.aws.security import Cognito
from diagrams.aws.storage import S3
from diagrams.k8s.compute import Job
from diagrams.onprem.client import Users
from diagrams.onprem.container import Docker

from architecture import (
    Component,
    edge_attr,
    finalize_svg,
    get_filename,
    graph_attr,
    outformat,
)

with Diagram(
    "End-to-End Adaptive Bitrate Video Streaming Platform with Automated Multi-Quality Transcoding",
    filename=get_filename(__file__),
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    edge_attr=edge_attr,
    outformat=outformat,
):
    users = Users("User")

    # Backend services running on Kubernetes (EKS)
    with Cluster("Kubernetes (EKS)"):
        backend = EKS("Backend\nServices on K8s")
        upload = Component("Upload Service", "go")

        with Cluster("KEDA ScaledJob"):
            jobs = [Job("job"), Job("job"), Job("job")]

        ffmpeg = Docker("FFMPEG")

    cognito = Cognito("Cognito\nUser Pool")
    redis = ElastiCache("Redis or\nElastiCache")
    postgres = RDSPostgresqlInstance("Postgres\n(Aurora DB)")

    raw_bucket = S3("Raw Media\nBucket")
    sqs = SQS("SQS Queue")
    processed_bucket = S3("Processed\nMedia Bucket")
    cdn = CloudFront("CloudFront")

    # User -> backend (auth, cache, metadata)
    users >> Edge(color="olive") >> backend
    backend - Edge(color="olive") >> cognito
    backend >> Edge(color="olive") >> redis
    backend >> Edge(color="olive") >> postgres

    # Upload path: user -> raw bucket -> SQS -> KEDA jobs
    users >> Edge(color="olive") >> raw_bucket
    raw_bucket >> Edge(color="olive") >> sqs
    sqs >> Edge(color="olive") >> jobs

    # Jobs run FFMPEG in Docker, update DB, write processed output
    for job in jobs:
        job >> Edge(color="olive") >> ffmpeg
    jobs[1] >> Edge(color="olive") >> postgres
    jobs[1] >> Edge(color="olive") >> processed_bucket

    # Delivery path: processed bucket -> CDN -> user
    processed_bucket >> Edge(color="olive") >> cdn
    cdn >> Edge(color="olive") >> users


finalize_svg(__file__)
