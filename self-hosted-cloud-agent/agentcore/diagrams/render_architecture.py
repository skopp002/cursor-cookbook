#!/usr/bin/env python3
"""Render diagrams/architecture.png with official AWS and GitHub icons.

Requires Graphviz and: pip install diagrams
"""

from __future__ import annotations

from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import EC2, EC2ContainerRegistry
from diagrams.aws.general import InternetAlt1
from diagrams.aws.ml import Bedrock
from diagrams.aws.security import SecretsManager
from diagrams.aws.storage import ElasticBlockStoreEBS
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.client import User
from diagrams.onprem.vcs import Github

OUT_DIR = Path(__file__).resolve().parent
OUT_STEM = str(OUT_DIR / "architecture")


def main() -> None:
    graph_attr = {
        "fontsize": "14",
        "bgcolor": "white",
        "pad": "0.6",
        "splines": "spline",
        "nodesep": "0.9",
        "ranksep": "1.1",
        "fontname": "Helvetica",
        "labeljust": "l",
    }
    node_attr = {"fontsize": "11", "fontname": "Helvetica"}
    edge_attr = {"fontsize": "11", "fontname": "Helvetica", "color": "#545B64"}

    with Diagram(
        "Self-hosted Cloud Agents on AgentCore",
        filename=OUT_STEM,
        show=False,
        direction="LR",
        graph_attr=graph_attr,
        node_attr=node_attr,
        edge_attr=edge_attr,
    ):
        operator = User("Operator")
        github = Github("Sample app repo")
        actions = GithubActions("GitHub Actions")
        cursor = InternetAlt1("Cursor Cloud Agents")

        with Cluster("AWS account   us-west-2"):
            secrets = SecretsManager("Secrets Manager")
            ecr = EC2ContainerRegistry("Amazon ECR")
            with Cluster("VPC  (egress only)"):
                runtime = Bedrock("AgentCore Runtime")
                instance = EC2("Managed instance")
                volume = ElasticBlockStoreEBS("EBS /mnt/workspace")

        operator >> Edge(label="1  put-secret", style="dashed", color="#7B8794") >> secrets
        operator >> Edge(label="2  push image", style="dashed", color="#7B8794") >> ecr
        operator >> Edge(label="3  InvokeAgentRuntime") >> runtime

        runtime >> Edge(label="4  start session") >> instance
        ecr >> Edge(label="5  pull image") >> instance
        secrets >> Edge(label="6  GetSecretValue") >> instance
        volume >> Edge(label="7  mount workspace") >> instance

        instance >> Edge(label="8  outbound HTTPS") >> cursor
        github >> Edge(label="9  workflow") >> actions
        actions >> Edge(label="10  POST /v1/agents") >> cursor
        cursor >> Edge(label="11  GitHub App PR") >> github


if __name__ == "__main__":
    main()
    png = Path(OUT_STEM + ".png")
    print(f"wrote {png} ({png.stat().st_size} bytes)")
