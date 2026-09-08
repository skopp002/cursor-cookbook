#!/usr/bin/env python3
"""Render secrets-and-flow.png: env-var commands plus the 15-step path."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).with_name("secrets-and-flow.png")
W, H = 2200, 2040
BG = (246, 247, 250)
INK = (15, 23, 42)
MUTED = (71, 85, 105)
WHITE = (255, 255, 255)
CODE_BG = (15, 23, 42)
CODE_FG = (226, 232, 240)
CODE_DIM = (148, 163, 184)
CODE_ACCENT = (125, 211, 252)
TEAL = (14, 116, 144)
RED = (185, 28, 28)
AMBER = (180, 83, 9)
INDIGO = (67, 56, 202)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
M = 36


def fnt(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def mono(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(MONO_B if bold else MONO, size)


def rr(draw: ImageDraw.ImageDraw, box, fill, outline=None, width=1, radius=12) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: float) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else f"{cur} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def badge(draw: ImageDraw.ImageDraw, xy, n, fill=TEAL) -> None:
    x, y = xy
    r = 13
    draw.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=WHITE, width=2)
    label = str(n)
    font = fnt(12, True)
    tw = draw.textlength(label, font=font)
    draw.text((x - tw / 2, y - 7), label, font=font, fill=WHITE)


def code_block(draw: ImageDraw.ImageDraw, x, y, w, lines: list[tuple[str, str]], pad=14) -> int:
    line_h = 20
    h = pad * 2 + line_h * max(len(lines), 1)
    rr(draw, (x, y, x + w, y + h), CODE_BG, radius=10)
    cy = y + pad
    fonts = {"cmd": mono(13, True), "cmt": mono(12), "dim": mono(13)}
    colors = {"cmd": CODE_ACCENT, "cmt": CODE_DIM, "dim": CODE_FG}
    for kind, text in lines:
        if kind != "blank":
            draw.text((x + pad, cy), text, font=fonts.get(kind, fonts["dim"]), fill=colors.get(kind, CODE_FG))
        cy += line_h
    return h


def heading(draw: ImageDraw.ImageDraw, x, y, title: str) -> None:
    draw.text((x, y), title, font=fnt(18, True), fill=TEAL)


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((M, 20), "Self-hosted Cloud Agents — secrets, env vars, and the 15-step path", font=fnt(26, True), fill=INK)
    d.text(
        (M, 56),
        "Make reads agentcore/.env and exports it. Terraform never stores CURSOR_API_KEY. The worker image has no Git credentials. Cursor never connects into the VPC.",
        font=fnt(14),
        fill=MUTED,
    )

    y = 92
    heading(d, M, y, "1. Set environment variables on the laptop")
    y += 30
    d.text(
        (M, y),
        "Working directory: self-hosted-cloud-agent/agentcore. Makefile: `-include .env` then `export`. Putting a value in .env is the same as export for every make target.",
        font=fnt(13),
        fill=MUTED,
    )
    y += 26

    left_w, right_w, gap = 1060, 1040, 24
    h1 = code_block(
        d,
        M,
        y,
        left_w,
        [
            ("cmt", "# once"),
            ("cmd", "cd self-hosted-cloud-agent/agentcore"),
            ("cmd", "cp .env.example .env"),
            ("blank", ""),
            ("cmt", "# required — Cursor service-account key, not a user/team key"),
            ("cmd", "export CURSOR_API_KEY='key_...'"),
            ("cmt", "# required — app the agent patches, NOT this cookbook"),
            ("cmd", "export WORKER_REPOSITORY_URL='https://github.com/kaushalavardhanam/kaushalavardhanam.git'"),
            ("cmd", "export CURSOR_WORKER_POOL_NAME=agentcore-platform-agents"),
            ("cmd", "export CURSOR_API_KEY_SECRET_NAME=cursor-agentcore-worker-api-key"),
        ],
    )
    h2 = code_block(
        d,
        M + left_w + gap,
        y,
        right_w,
        [
            ("cmt", "# AWS for terraform / put-secret / ecr-build-push / start-session"),
            ("cmd", "export AWS_PROFILE=default"),
            ("cmd", "export AWS_REGION=us-west-2"),
            ("cmd", "export AWS_ACCOUNT_ID='123456789012'"),
            ("blank", ""),
            ("cmt", "# GitHub PAT with Projects:Read. Not in agentcore/.env"),
            ("cmd", "export GH_PROJECT_TOKEN='github_pat_...'"),
            ("blank", ""),
            ("cmt", "# after make agentcore-start-session prints the id:"),
            ("cmd", "export AGENTCORE_SESSION_ID='cursor-worker-<uuid>'"),
        ],
    )
    y += max(h1, h2) + 28

    heading(d, M, y, "2. How each destination receives those variables  (no crossing arrows)")
    y += 30

    cards = [
        (
            (254, 242, 242),
            RED,
            "Laptop  — you type it",
            [
                "CURSOR_API_KEY",
                "WORKER_REPOSITORY_URL",
                "AWS_PROFILE / REGION / ACCOUNT_ID",
                "CURSOR_WORKER_POOL_NAME",
                "CURSOR_API_KEY_SECRET_NAME",
                "AGENTCORE_SESSION_ID  (after start)",
            ],
            "Used by Make and AWS CLI only. Not a file inside the container.",
        ),
        (
            (254, 242, 242),
            RED,
            "GitHub Actions  — sample app repo",
            [
                "gh secret set CURSOR_API_KEY --body \"$CURSOR_API_KEY\"",
                "gh secret set GH_PROJECT_TOKEN --body \"$GH_PROJECT_TOKEN\"",
                "",
                "workflow then sets:",
                "CURSOR_API_KEY: ${{ secrets.CURSOR_API_KEY }}",
                "GH_PROJECT_TOKEN: ${{ secrets.GH_PROJECT_TOKEN }}",
                "CURSOR_POOL_NAME: agentcore-platform-agents",
            ],
            "Secrets live on the sample app, not the cookbook. GITHUB_TOKEN is automatic.",
        ),
        (
            (255, 247, 237),
            AMBER,
            "AgentCore runtime  — Terraform",
            [
                "CURSOR_API_KEY_SECRET_ID=<secret ARN>",
                "WORKER_REPOSITORY_URL=<app git URL>",
                "CURSOR_WORKER_POOL_NAME=agentcore-platform-agents",
                "CURSOR_WORKER_DIR=/mnt/workspace",
                "CURSOR_WORKER_IDLE_RELEASE_TIMEOUT=600",
                "CURSOR_WORKER_LABELS_JSON=...",
            ],
            "Terraform writes the secret ARN, never the raw API key.",
        ),
        (
            (238, 242, 255),
            INDIGO,
            "Worker process  — adapter",
            [
                "aws secretsmanager get-secret-value \\",
                "  --secret-id \"$CURSOR_API_KEY_SECRET_ID\"",
                "",
                "# adapter then starts the child with:",
                "export CURSOR_API_KEY='<fetched value>'",
                "agent worker --pool start",
            ],
            "No Git credentials in the image. origin is WORKER_REPOSITORY_URL only.",
        ),
    ]
    cg = 16
    card_w = (W - 2 * M - 3 * cg) / 4
    card_h = 300
    for i, (fill, stroke, title, lines, foot) in enumerate(cards):
        x = M + i * (card_w + cg)
        rr(d, (x, y, x + card_w, y + card_h), fill, stroke, width=2, radius=12)
        d.text((x + 14, y + 12), title, font=fnt(14, True), fill=stroke)
        cy = y + 44
        for line in lines:
            d.text((x + 14, cy), line or " ", font=mono(11), fill=INK)
            cy += 18
        fy = y + card_h - 52
        for wline in wrap(d, foot, fnt(12), card_w - 28):
            d.text((x + 14, fy), wline, font=fnt(12), fill=MUTED)
            fy += 16
    y += card_h + 28

    heading(d, M, y, "3. CURSOR_API_KEY path  (the only secret that is copied)")
    y += 30
    key_lines = [
        ("cmt", "# laptop  →  Secrets Manager   (Terraform does not see the value)"),
        ("cmd", "make agentcore-put-api-key-secret     # reads $CURSOR_API_KEY from .env"),
        ("blank", ""),
        ("cmt", "# laptop  →  GitHub Actions secrets on the SAMPLE APP repo"),
        ("cmd", "gh secret set CURSOR_API_KEY --repo kaushalavardhanam/kaushalavardhanam --body \"$CURSOR_API_KEY\""),
        ("cmd", "gh secret set GH_PROJECT_TOKEN --repo kaushalavardhanam/kaushalavardhanam --body \"$GH_PROJECT_TOKEN\""),
        ("blank", ""),
        ("cmt", "# runtime: Terraform set CURSOR_API_KEY_SECRET_ID; adapter fetches, then:"),
        ("cmd", "export CURSOR_API_KEY='<SecretString>'   # injected into `agent worker` only"),
    ]
    y += code_block(d, M, y, W - 2 * M, key_lines) + 28

    heading(d, M, y, "4. Fifteen steps  — command on the right, no overlapping connectors")
    y += 32

    steps = [
        (TEAL, "Copy templates", "cp github/cursor-agent-in-progress.yml  github/kick_cursor_agent.py  →  <sample-app>/.github/"),
        (TEAL, "Grant GitHub App", "Cursor dashboard: Team GitHub App on the sample app repo (PR grant, not a Git credential)"),
        (TEAL, "Write .env / export", "cp .env.example .env   &&   export CURSOR_API_KEY=... WORKER_REPOSITORY_URL=... AWS_REGION=..."),
        (TEAL, "Create AWS infra", "make agentcore-terraform-apply     # ECR, secret container, IAM, runtime env. Does not boot a worker"),
        (TEAL, "Push worker image", "make agentcore-ecr-build-push     # linux/arm64 → ECR"),
        (TEAL, "Put API key secret", "make agentcore-put-api-key-secret     # $CURSOR_API_KEY → Secrets Manager"),
        (TEAL, "Store Actions secrets", "gh secret set CURSOR_API_KEY --body \"$CURSOR_API_KEY\"   &&   gh secret set GH_PROJECT_TOKEN ..."),
        (TEAL, "Inject workflow env", "CURSOR_API_KEY: ${{ secrets.CURSOR_API_KEY }}     GH_PROJECT_TOKEN: ${{ secrets.GH_PROJECT_TOKEN }}"),
        (AMBER, "Start session + pull", "make agentcore-start-session     &&     export AGENTCORE_SESSION_ID=cursor-worker-<uuid>"),
        (AMBER, "Fetch API key", "aws secretsmanager get-secret-value --secret-id \"$CURSOR_API_KEY_SECRET_ID\""),
        (AMBER, "Set git origin", "git remote add origin \"$WORKER_REPOSITORY_URL\"     # fetch best-effort; no Git creds in the image"),
        (INDIGO, "Register outbound", "agent worker --pool start     # HTTPS out to Cursor. No inbound into the VPC"),
        (INDIGO, "Kick off agent", "Actions POST /v1/agents  pool=agentcore-platform-agents  (Authorization: $CURSOR_API_KEY)"),
        (INDIGO, "Assign + edit", "Cursor assigns the job on that outbound connection. Edits land on /mnt/workspace"),
        (INDIGO, "Open PR", "GitHub App opens the PR (autoCreatePR). Uses step 2 grant, not the worker API key"),
    ]

    row_h = 56
    inner = W - 2 * M
    for i, (color, title, command) in enumerate(steps, start=1):
        rr(d, (M, y, M + inner, y + row_h - 6), WHITE, (226, 232, 240), width=1, radius=10)
        badge(d, (M + 22, y + 24), i, color)
        d.text((M + 44, y + 6), title, font=fnt(14, True), fill=INK)
        d.text((M + 44, y + 28), command, font=mono(12), fill=MUTED)
        y += row_h

    y += 8
    d.text(
        (M, y),
        "You export on the laptop. GitHub gets secrets via gh secret set. The worker gets CURSOR_API_KEY only after GetSecretValue. Terraform never sees the key.",
        font=fnt(13),
        fill=MUTED,
    )

    img.save(OUT, "PNG")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes) last_y={y} canvas={H}")


if __name__ == "__main__":
    main()
