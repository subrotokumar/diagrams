from typing import Literal

from diagrams.aws.compute import ECR
from diagrams.aws.ml import Bedrock
from diagrams.azure.aimachinelearning import (
    AzureOpenai,
    MachineLearning,
)
from diagrams.custom import Custom
from diagrams.k8s import K8S
from diagrams.k8s.compute import Deploy, Pod
from diagrams.k8s.podconfig import ConfigMap, Secret
from diagrams.onprem.ci import Gitlabci
from diagrams.onprem.client import Client, Users
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.logging import Loki
from diagrams.onprem.monitoring import Grafana, Prometheus
from diagrams.onprem.queue import Kafka
from diagrams.onprem.search import Solr  # BM25 keyword search
from diagrams.onprem.security import Vault  # stand-in: Zanzibar-style permission engine
from diagrams.onprem.tracing import Tempo
from diagrams.programming.flowchart import (
    Database,
    InternalStorage,
    Merge,
    Preparation,
    Sort,
)
from diagrams.programming.framework import Angular, React, Vue
from diagrams.programming.language import Bash, Python
from diagrams.saas.crm import Zendesk  # stand-in: ServiceNow / Jira / HR ticketing

from diagrams import Cluster, Diagram, Edge


def Component(label="", icon: str = "", ext: Literal["png", "jpg", "svg"] = "png"):
    if "." in icon:
        return Custom(label=label, icon_path=f"../icons/{icon.lower()}")
    return Custom(label=label, icon_path=f"../icons/{icon.lower()}.{ext}")


graph_attr = {
    "rankdir": "LR",
    "splines": "ortho",
    "nodesep": "1.0",
    "ranksep": "1.2",
    "pad": "0.5",
    "margin": "15",
    "compound": "true",
}
edge_attr = {
    "fontsize": "10",
}

with Diagram(
    "Unified Intelligence Platform",
    filename="diagrams/unified_intelligence_platform",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    edge_attr=edge_attr,
    outformat="png",
):
    files = Component("Files", "files")
    dev_sre = Users("DEV/SRE")
    eval = MachineLearning("Eval\n(faithfulness, relevance,\ncontext precision)")
    react = React("Client")

    with Cluster("Agent Service"):
        supervisor = Component("Multi-Agent\nSupervisor", "langgraph")

        with Cluster("Rag Agent Handoff"):
            agent1 = Component("RAG Agent", "langgraph")
            llm = Python("LLM")
            tools = Python("Tools")

        agent2 = Component(
            "HR Agent\nJira Agent\nSolution Architect Agent\nSupport Agent\nBA Agent",
            "langgraph",
        )
        MCPs = Component("Mcp", "mcp")

        agent1 >> llm >> Edge(label="action") >> tools
        tools >> Edge(label="feedback") >> llm

        supervisor >> [MCPs, agent1, agent2]  # , agent3, agent4, agent5]

    with Cluster("Ingestion Pipeline (scale-to-zero, KEDA)"):
        with Cluster("Document Ingestion"):
            presigned_url = Client("Presigned URL\nUpload")
            storage = Component("Object Storage", "s3")
        kafka = Kafka("Message Broker\n(upload events)")
        workers = Component("KEDA-scaled\nIngestion Workers", "keda")

        with Cluster("Multi-Model Embeddings Pipeline"):
            docling = Component("Layout-aware\nParsing", "docling")

            with Cluster("Text Embedding Ingestion"):
                text_data = Component("Text Content", "text")
                emb_text = Component("Text\nEmbedding\n[f1,f2,...fn]\n", "numpy")
                splitter = Component("Chuck Splitter\nwith Metadata", "langchain")

                text_data >> splitter >> emb_text

            with Cluster("Table Embedding Ingestion"):
                table_data = Component("Table Data", "table")
                emb_table = Component("Table\nEmbedding\n[f1,f2,...fn]", "numpy")

                table_data >> emb_table

            with Cluster("Image Embedding Ingestion"):
                with Cluster():
                    image_data = Component("Image Data\n(Base64)", "image_data")
                    image_summary = Component("Image\nContext", "text")
                emb_image = Component("Image\nEmbedding\n[f1,f2,...fn]", "numpy")
                image_data >> image_summary >> emb_image

    with Cluster("VectorDB"):
        aisearch = Database("Image\nCollection")
        pgvector = Database("Text\nCollection")
        opensearch = Database("Table Collection")

    otel = Component("OTel", "otel")

    with Cluster("Observability", direction="RL") as lgtm:
        grafana = Grafana("Grafana")
        with Cluster(""):
            loki = Loki("Loki")
            tempo = Tempo("Tempo")
            prom = Prometheus("Prometheus")
        grafana << loki
        grafana << prom
        grafana << tempo

    otel >> [loki, prom, tempo]

    with Cluster("LLM Gateway"):
        openai = AzureOpenai("OpenAI")
        ollama = Component("Ollama", "ollama")
        bedrock = Bedrock("Bedrock")
        huggingface = Component("HuggingFace", "huggingface")
        router = Component("Routing\n(cost / latency /\ncontext window)", "go")
        (
            [openai, ollama, bedrock, huggingface]
            >> Edge(label="parallel tool calls\n+ retry/fallback")
            >> router
        )

    with Cluster("Retrieval Pipeline"):
        cache = Redis("Semantic Cache")
        hyde = Preparation("HyDE Query\nRewrite")
        with Cluster("Hybrid Search"):
            dense = InternalStorage("Dense Vector\nSearch")
            bm25 = Solr("Sparse BM25\nSearch")
        rrf = Merge("Reciprocal Rank\nFusion\n(RRF)")
        reranker = Sort("Cross-Encoder\nReranker")

    with Cluster("Access Control (Zanzibar-style)"):
        sources = Zendesk("ServiceNow / Jira /\nHR Platform")
        permissions = Vault("Relationship-based\nPermission Engine")
        sources >> Edge(label="live relationships") >> permissions

    user = Users("Users")
    user >> files
    user >> react
    react >> supervisor
    vectordb = [aisearch, pgvector, opensearch]
    emb_image >> aisearch
    emb_text >> pgvector
    emb_table >> opensearch
    supervisor >> eval
    storage >> Edge(label="Upload Event") >> kafka >> workers >> docling
    docling >> [text_data, table_data, image_data]
    # router >> otel
    tools >> Edge(label="query") >> cache
    cache >> Edge(label="hit", style="dashed") >> tools
    cache >> Edge(label="miss") >> hyde
    vectordb >> Edge(style="dashed", label="indexed chunks") >> dense
    vectordb >> Edge(style="dashed") >> bm25
    [dense, bm25] >> rrf >> reranker
    router >> supervisor
    permissions >> Edge(label="post-check") >> supervisor
    (files >> presigned_url << Edge(label="Signed URL") << storage)
    presigned_url >> Edge(label="Uploading file") >> storage
    llm << router

    with Cluster("DevOps"):
        cloud = Component("Cloud Infrastructure", "clouds")

        infra_repo = Component("Infra Repository", "gitlab")
        codebase = Component("Codebase\nRepository", "gitlab")
        helm = Component("Helm Chart\nRepository", "helm")
        argocd = Component("ArgoCD", "argocd")
        vault = Vault("Secret Vault")
        registry = ECR("Image Registry")

        with Cluster("Kubernetes Cluster"):
            istio = Component("Gateway API", "istio")
            k8s = K8S("Kubernetes")
            reloader = Pod("Reloader")
            eso = Component("ESO", "eso")
            with Cluster("Application"):
                deploy = Deploy("Deployment")
                cm = ConfigMap("Configmap")
                sk = Secret("Secrets")

        with Cluster("Multi Environment CI/CD Pipeline"):
            gitlab_ci = Gitlabci("Gitlab")
            with Cluster("Application\nDeployment Pipeline"):
                cicd = Bash(
                    "lint\ntest\npackage\nsecurity\nImage Push\nUpdate Helm Chart"
                )
            with Cluster("IaC Pipeline"):
                iac = Bash("Plan\nApply")
        (
            infra_repo
            >> gitlab_ci
            >> Edge(label="Merging the PR")
            >> iac
            >> Component("Infrastructure\nAs Code", "terraform")
            >> cloud
        )
        (codebase >> gitlab_ci >> cicd >> helm >> argocd >> k8s)
        cicd >> registry >> k8s >> deploy
        (vault >> eso >> Edge(label="Sync") >> sk >> reloader >> deploy)
        cm >> reloader
        dev_sre << grafana
