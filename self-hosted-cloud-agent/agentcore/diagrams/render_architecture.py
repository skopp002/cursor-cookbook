#!/usr/bin/env python3
"""Render diagrams/architecture.png with official AWS and GitHub icons.

Requires Graphviz and: pip install diagrams

The cookbook does not generate sample-repo files. agentcore/github/ is a static
template the operator copies by hand:

  github/cursor-agent-in-progress.yml  ->  <sample-repo>/.github/workflows/
  github/kick_cursor_agent.py          ->  <sample-repo>/.github/scripts/kick_cursor_agent.py

kaushalavardhanam is the example sample repo used to demonstrate Cloud Agent
capacity, not a required production app.
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
        "pad": "0.55",
        "splines": "spline",
        "nodesep": "0.85",
        "ranksep": "1.05",
        "fontname": "Helvetica",
        "labeljust": "l",
        "compound": "true",
    }
    node_attr = {"fontsize": "11", "fontname": "Helvetica"}
    edge_attr = {"fontsize": "10", "fontname": "Helvetica", "color": "#545B64"}

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

        with Cluster("Configure"):
            github = Github("Sample repo")

        with Cluster("Create and export credentials"):
            secrets = SecretsManager("Secrets Manager")
            ecr = EC2ContainerRegistry("Amazon ECR")

        with Cluster("Run"):
            with Cluster("VPC  (egress only)"):
                runtime = Bedrock("AgentCore Runtime")
                instance = EC2("Managed instance")
                volume = ElasticBlockStoreEBS("EBS /mnt/workspace")
            cursor = InternetAlt1("Cursor Cloud Agents")
            actions = GithubActions("GitHub Actions")

        # Configure
        operator >> Edge(label="1  copy workflow + .github/scripts") >> github
        operator >> Edge(label="2  grant GitHub App") >> github

        # Credentials
        operator >> Edge(label="3  put-secret", style="dashed", color="#7B8794") >> secrets
        operator >> Edge(label="4  push image", style="dashed", color="#7B8794") >> ecr
        operator >> Edge(label="5  gh secret set", style="dashed", color="#7B8794") >> github

        # Run
        operator >> Edge(label="6  InvokeAgentRuntime") >> runtime
        runtime >> Edge(label="7  start session") >> instance
        ecr >> Edge(label="8  pull image") >> instance
        secrets >> Edge(label="9  GetSecretValue") >> instance
        volume >> Edge(label="10  mount workspace") >> instance
        instance >> Edge(label="11  outbound HTTPS") >> cursor
        github >> Edge(label="12  workflow") >> actions
        actions >> Edge(label="13  POST /v1/agents") >> cursor
        cursor >> Edge(label="14  GitHub App PR") >> github


if __name__ == "__main__":
    main()
    png = Path(OUT_STEM + ".png")
    print(f"wrote {png} ({png.stat().st_size} bytes)")
