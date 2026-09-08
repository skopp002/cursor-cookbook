#!/usr/bin/env python3
"""Render secrets-and-flow.png with the full secret and runtime sequence."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).with_name("secrets-and-flow.png")
W, H = 2180, 1920
BG = (250, 250, 252)
INK = (24, 26, 30)
MUTED = (84, 90, 102)
DASH = (71, 85, 105)
SOLID = (29, 78, 216)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def fnt(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def rr(draw, box, fill, outline, width=2, radius=14) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap(draw, text, font, max_width) -> list[str]:
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


def badge(draw, xy, n, fill=(13, 110, 140)) -> None:
    x, y = xy
    r = 12
    draw.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=(255, 255, 255), width=2)
    label = str(n)
    font = fnt(12, True)
    tw = draw.textlength(label, font=font)
    draw.text((x - tw / 2, y - 7), label, font=font, fill=(255, 255, 255))


def head(draw, end, ang, color) -> None:
    ah = 10
    p1 = (end[0] - ah * math.cos(ang - 0.42), end[1] - ah * math.sin(ang - 0.42))
    p2 = (end[0] - ah * math.cos(ang + 0.42), end[1] - ah * math.sin(ang + 0.42))
    draw.polygon([end, p1, p2], fill=color)


def ortho(draw, points, color, dashed=False, width=3) -> None:
    segs = list(zip(points, points[1:]))
    for i, ((x0, y0), (x1, y1)) in enumerate(segs):
        last = i == len(segs) - 1
        dx, dy = x1 - x0, y1 - y0
        dist = max(math.hypot(dx, dy), 1)
        if dashed:
            ux, uy = dx / dist, dy / dist
            pos, on = 0.0, True
            stop = dist - (12 if last else 0)
            while pos < stop:
                length = 8 if on else 6
                nxt = min(pos + length, stop)
                if on:
                    draw.line(
                        (x0 + ux * pos, y0 + uy * pos, x0 + ux * nxt, y0 + uy * nxt),
                        fill=color,
                        width=width,
                    )
                pos = nxt
                on = not on
        else:
            if last:
                shorten = 8
                x1s = x0 + dx * (dist - shorten) / dist
                y1s = y0 + dy * (dist - shorten) / dist
                draw.line((x0, y0, x1s, y1s), fill=color, width=width)
            else:
                draw.line((x0, y0, x1, y1), fill=color, width=width)
        if last:
            head(draw, (x1, y1), math.atan2(dy, dx), color)


def card(draw, box, fill, outline, code, title, body) -> None:
    rr(draw, box, fill, outline, width=2, radius=12)
    x0, y0, x1, _y1 = box
    draw.text((x0 + 14, y0 + 10), code, font=fnt(13, True), fill=outline)
    draw.text((x0 + 54, y0 + 9), title, font=fnt(15, True), fill=INK)
    y = y0 + 36
    body_font = fnt(12)
    for line in wrap(draw, body, body_font, x1 - x0 - 28):
        draw.text((x0 + 14, y), line, font=body_font, fill=INK)
        y += 17


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    small = fnt(11)

    d.text((40, 18), "Self-hosted Cloud Agents — who holds which secret (built)", font=fnt(28, True), fill=INK)
    d.text(
        (40, 56),
        "Full sequence. Terraform does not start a worker. The image has no Git credentials. Cursor never connects into the VPC.",
        font=fnt(15),
        fill=MUTED,
    )

    lanes = [
        (40, 168, 520, 780, (243, 232, 250), (126, 58, 166), "Operator — this cookbook"),
        (540, 168, 1020, 780, (238, 240, 243), (84, 90, 102), "GitHub — sample application repo"),
        (1040, 168, 1520, 780, (226, 239, 252), (29, 78, 166), "Cursor — team Cloud Agents"),
        (1540, 168, 2080, 780, (255, 243, 224), (194, 92, 12), "AWS account — default us-west-2"),
    ]
    for x0, y0, x1, y1, fill, outline, name in lanes:
        rr(d, (x0, y0, x1, y1), fill, outline, width=2, radius=18)
        d.text((x0 + 16, y0 + 12), name, font=fnt(14, True), fill=outline)

    secret = ((254, 226, 226), (185, 28, 28))
    purple = ((237, 233, 254), (91, 33, 182))
    blue = ((219, 234, 254), (29, 78, 216))
    amber = ((255, 237, 213), (180, 83, 9))
    indigo = ((224, 231, 255), (67, 56, 202))

    env = (58, 214, 502, 340)
    cb = (58, 520, 502, 750)
    sec = (558, 214, 1002, 340)
    gh = (558, 520, 1002, 750)
    ca = (1058, 214, 1502, 750)
    sm = (1558, 214, 2062, 340)
    ecr = (1558, 360, 2062, 490)
    ac = (1558, 520, 2062, 750)

    card(d, env, *secret, "ENV", "Laptop .env",
         "CURSOR_API_KEY. put-secret, contract test, and AWS CLI only. Not the running container.")
    card(d, cb, *purple, "CB", "cursor-cookbook",
         "Lab: adapter, image, Terraform, GitHub templates. Not the app the agent patches.")
    card(d, sec, *secret, "SEC", "Repo Actions secrets",
         "CURSOR_API_KEY + GH_PROJECT_TOKEN stored on the sample repo. GITHUB_TOKEN is automatic.")
    card(d, gh, *purple, "GH", "Sample app + Actions",
         "Copied workflow. GH_PROJECT_TOKEN scans the board. CURSOR_API_KEY kicks POST /v1/agents.")
    card(d, ca, *blue, "CA", "Cursor Cloud Agents API",
         "POST /v1/agents pool=agentcore-platform-agents. Team GitHub App (dashboard) grants the sample repo for PRs. That grant is not a Git credential on the worker. Cursor does not inbound-connect to AWS.")
    card(d, sm, *secret, "SM", "Secrets Manager",
         "Service-account key. Runtime env CURSOR_API_KEY_SECRET_ID. Terraform does not store the value.")
    card(d, ecr, *amber, "ECR", "Elastic Container Registry",
         "Worker image. Terraform creates the repo. Operator builds and pushes. Session start pulls it.")
    card(d, ac, *indigo, "AC", "AgentCore pool worker",
         "adapter PID 1, then agent worker --pool. WORKER_REPOSITORY_URL is origin label only. No Git credentials in the image. Persistent volume at /mnt/workspace.")

    # 15 GitHub App PR above swimlanes
    ortho(d, [(1280, 214), (1280, 108), (780, 108), (780, 214)], SOLID)
    badge(d, (1030, 108), 15)
    d.text((800, 86), "15 GitHub App opens PR (autoCreatePR)", font=small, fill=SOLID)

    # 2 grant GitHub App: operator toward CA (top of CA)
    ortho(d, [(520, 188), (1058, 188)], DASH, dashed=True)
    badge(d, (790, 188), 2)
    d.text((540, 168), "2 grant Team GitHub App on sample repo", font=small, fill=MUTED)

    # 5 put-secret ENV -> SM above top cards
    ortho(d, [(280, 214), (280, 198), (1800, 198), (1800, 214)], DASH, dashed=True)
    badge(d, (1030, 198), 5)
    d.text((1048, 178), "5 put-secret CURSOR_API_KEY", font=small, fill=MUTED)

    # 6 store Actions secrets ENV -> SEC
    ortho(d, [(502, 260), (558, 260)], DASH, dashed=True)
    badge(d, (530, 260), 6)

    # 7 inject SEC -> GH
    ortho(d, [(780, 340), (780, 520)], DASH, dashed=True)
    badge(d, (802, 430), 7)

    # 1 copy templates CB -> GH
    ortho(d, [(502, 560), (558, 560)], DASH, dashed=True)
    badge(d, (530, 560), 1)

    # 12 POST /v1/agents GH -> CA
    ortho(d, [(1002, 600), (1058, 600)], SOLID)
    badge(d, (1030, 600), 12)

    # 9 GetSecretValue: right gutter SM -> AC
    ortho(d, [(2062, 277), (2118, 277), (2118, 600), (2062, 600)], DASH, dashed=True)
    badge(d, (2118, 430), 9)

    # 4 push image: below the lanes, outer right gutter up into ECR
    ortho(d, [(280, 750), (280, 792), (2150, 792), (2150, 425), (2062, 425)], DASH, dashed=True)
    badge(d, (1030, 792), 4)

    # 3 terraform: below the bottom cards, CB -> AC
    ortho(d, [(280, 750), (280, 762), (1800, 762), (1800, 750)], DASH, dashed=True)
    badge(d, (1030, 762), 3)

    # 8 start-session left gutter then into AC; image pull in the ECR-AC gap
    ortho(d, [(58, 277), (16, 277), (16, 818), (1920, 818), (1920, 750)], DASH, dashed=True)
    badge(d, (16, 818), 8)
    ortho(d, [(1810, 490), (1810, 520)], DASH, dashed=True)
    badge(d, (1832, 505), 8)

    # 11 worker registers outbound AC -> CA
    ortho(d, [(1558, 560), (1502, 560)], SOLID)
    badge(d, (1530, 560), 11)

    # 13 assign work over outbound (CA toward AC, labeled as assignment not inbound)
    ortho(d, [(1502, 680), (1558, 680)], SOLID)
    badge(d, (1530, 680), 13)

    d.text((1574, 710), "10 set origin only    14 execute edits on /mnt/workspace", font=small, fill=INK)

    d.text((570, 568), "copy workflow + kick script", font=small, fill=MUTED)
    d.text((1070, 608), "POST /v1/agents", font=small, fill=SOLID)
    d.text((800, 434), "inject secrets", font=small, fill=MUTED)
    d.text((520, 238), "store Actions secrets", font=small, fill=MUTED)
    d.text((300, 744), "3 terraform apply: ECR repo, secret container, runtime env (does not start a session)", font=small, fill=MUTED)
    d.text((300, 776), "4 ecr-build-push", font=small, fill=MUTED)
    d.text((36, 826), "8 start-session (InvokeAgentRuntime); instance pulls ECR image", font=small, fill=MUTED)
    d.text((1310, 538), "registers outbound", font=small, fill=SOLID)
    d.text((1310, 688), "assign job over that connection", font=small, fill=SOLID)
    d.text((1878, 430), "GetSecretValue", font=small, fill=MUTED)
    d.text((1868, 498), "pull image", font=small, fill=MUTED)

    rr(d, (40, 860, 2140, 1890), (255, 255, 255), (210, 214, 220), width=1, radius=14)
    d.text(
        (60, 856),
        "Solid = kickoff and pool run.     Dashed = templates, Terraform, image, or secrets.",
        font=fnt(14, True),
        fill=INK,
    )

    notes = [
        "1  Copy github/ workflow + kick script into the sample application repo. The cookbook is not what the agent patches.",
        "2  In the Cursor dashboard, install the Team GitHub App and grant the sample repo. That is how PRs are opened. It is not a Git credential inside the worker image.",
        "3  terraform apply creates the ECR repo, Secrets Manager container, IAM, capacity provider, and runtime env (WORKER_REPOSITORY_URL, pool, CURSOR_API_KEY_SECRET_ID). It does not boot a worker.",
        "4  make agentcore-ecr-build-push. The laptop builds linux/arm64 and pushes to ECR. A running session does not pick up a new image until you start a new session.",
        "5  make agentcore-put-api-key-secret. Laptop .env -> Secrets Manager. Terraform never sees the key value.",
        "6  Store CURSOR_API_KEY and GH_PROJECT_TOKEN as GitHub Actions secrets on the sample repo (same service-account key as the worker).",
        "7  The workflow injects those secrets. GITHUB_TOKEN is automatic and used for issue comments. GH_PROJECT_TOKEN is required to read Projects v2.",
        "8  make agentcore-start-session (InvokeAgentRuntime). AgentCore provisions the instance, pulls the ECR image, and starts the adapter. Record AGENTCORE_SESSION_ID.",
        "9  Adapter listens on :8080, then GetSecretValue with the runtime execution role (CURSOR_API_KEY_SECRET_ID).",
        "10 Adapter git-inits /mnt/workspace and sets origin to WORKER_REPOSITORY_URL. Fetch is best-effort. The image has no Git credentials; a private HTTPS fetch must not block launch.",
        "11 agent worker --pool registers outbound to Cursor over HTTPS. /ping becomes HealthyBusy. Cursor does not connect into the VPC.",
        "12 In Progress, label, or workflow_dispatch posts to /v1/agents with pool=agentcore-platform-agents. The job waits until a worker is HealthyBusy.",
        "13 Cursor assigns the Cloud Agent over that existing outbound connection.",
        "14 The worker executes edits, tests, and git on /mnt/workspace. Persistent EBS keeps the tree across session stop/start.",
        "15 Cursor GitHub App opens the PR (autoCreatePR) against the sample repo. That uses the App grant from step 2, not the worker API key.",
    ]
    y = 890
    nf = fnt(14)
    for note in notes:
        for line in wrap(d, note, nf, 2040):
            d.text((60, y), line, font=nf, fill=INK)
            y += 19
        y += 6

    img.save(OUT, "PNG")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
