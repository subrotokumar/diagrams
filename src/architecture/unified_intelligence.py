from typing import Literal

from diagrams.aws.ml import Bedrock
from diagrams.azure.aimachinelearning import (
    AzureOpenai,
    MachineLearning,
)  # stand-in: RAGAS evaluation
from diagrams.custom import Custom
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
    Merge,
    Preparation,
    Sort,
)  # stand-ins: HyDE rewrite, RRF, reranker
from diagrams.programming.language import Python
from diagrams.saas.crm import Zendesk  # stand-in: ServiceNow / Jira / HR ticketing

from diagrams import Cluster, Diagram, Edge


def Component(label="", icon: str = "", ext: Literal["png", "jpg", "svg"] = "png"):
    if "." in icon:
        return Custom(label=label, icon_path=f"../public/{icon.lower()}")
    return Custom(label=label, icon_path=f"../public/{icon.lower()}.{ext}")


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
    user = Users("End User")
    ragas = MachineLearning("RAGAS Eval\n(faithfulness, relevance,\ncontext precision)")

    with Cluster("Agent Interface"):
        supervisor = Python("Multi-Agent\nSupervisor")

        with Cluster("Rag Agent Handoff"):
            agent1 = Python("RAG Agent")
            llm = Python("LLM")
            tools = Python("Tools")

        agent2 = Python("HR Agent")
        agent3 = Python("Jira Agent")

        agent1 >> llm >> Edge(label="action") >> tools
        tools >> Edge(label="feedback") >> llm

        user >> supervisor >> [agent1, agent2, agent3]

    with Cluster("Ingestion Pipeline (scale-to-zero, KEDA)"):
        upload = Client("Presigned URL\nUpload")
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
        vectordb = [aisearch, pgvector, opensearch]
        emb_image >> aisearch
        emb_text >> pgvector
        emb_table >> opensearch

        upload >> storage >> kafka >> workers >> docling
        docling >> [text_data, table_data, image_data]

    otel = Component("OTel", "otel")
    with Cluster("LGTM Stack", direction="RL") as lgtm:
        with Cluster():
            loki = Loki("Loki")
            tempo = Tempo("Tempo")
            prom = Prometheus("Prometheus")

        grafana = Grafana("Grafana")

        grafana >> loki
        grafana >> prom
        grafana >> tempo

    otel >> [loki, prom, tempo]

    with Cluster("Access Control (Zanzibar-style)"):
        sources = Zendesk("ServiceNow / Jira /\nHR Platform")
        permissions = Vault("Relationship-based\nPermission Engine")
        sources >> Edge(label="live relationships") >> permissions

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

    with Cluster("Query-Time Pipeline"):
        cache = Redis("Semantic Cache")
        hyde = Preparation("HyDE Query\nRewrite")
        with Cluster("Hybrid Search"):
            dense = Component("Dense Vector\nSearch", "langchain")
            bm25 = Solr("Sparse BM25\nSearch")
        rrf = Merge("Reciprocal Rank\nFusion\n(RRF)")
        reranker = Sort("Cross-Encoder\nReranker")

        router >> otel
        tools >> Edge(label="query") >> cache
        cache >> Edge(label="hit", style="dashed") >> tools
        cache >> Edge(label="miss") >> hyde
        vectordb >> Edge(style="dashed", label="indexed chunks") >> dense
        vectordb >> Edge(style="dashed") >> bm25
        [dense, bm25] >> rrf >> reranker
        router >> supervisor
        permissions >> Edge(label="post-check") >> supervisor
        (router >> Edge(style="dotted", label="scored") >> ragas)
