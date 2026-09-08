#!/usr/bin/env python3
"""Render secrets-and-flow.png as a sequence diagram with a step legend."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).with_name("secrets-and-flow.png")
W, H = 2400, 1540
BG = (248, 249, 252)
INK = (22, 25, 31)
MUTED = (88, 94, 106)
WHITE = (255, 255, 255)
GUIDE = (203, 213, 225)
LINE_SETUP = (71, 85, 105)
LINE_RUN = (29, 78, 216)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

GROUPS = [
    {
        "title": "Operator",
        "subtitle": "this cookbook / laptop",
        "fill": (243, 232, 250),
        "stroke": (126, 58, 166),
        "nodes": [
            ("ENV", "Laptop .env", (254, 226, 226), (185, 28, 28)),
            ("CB", "Cookbook", (237, 233, 254), (91, 33, 182)),
        ],
    },
    {
        "title": "GitHub",
        "subtitle": "sample application repo",
        "fill": (236, 253, 245),
        "stroke": (4, 120, 87),
        "nodes": [
            ("SEC", "Actions secrets", (254, 226, 226), (185, 28, 28)),
            ("GH", "Repo + Actions", (209, 250, 229), (4, 120, 87)),
        ],
    },
    {
        "title": "Cursor",
        "subtitle": "team Cloud Agents",
        "fill": (226, 239, 252),
        "stroke": (29, 78, 166),
        "nodes": [
            ("CA", "Cloud Agents API", (219, 234, 254), (29, 78, 216)),
        ],
    },
    {
        "title": "AWS",
        "subtitle": "default us-west-2",
        "fill": (255, 247, 237),
        "stroke": (194, 92, 12),
        "nodes": [
            ("SM", "Secrets Manager", (254, 226, 226), (185, 28, 28)),
            ("ECR", "Worker image", (255, 237, 213), (180, 83, 9)),
            ("AC", "AgentCore worker", (224, 231, 255), (67, 56, 202)),
        ],
    },
]

NODES = [node for group in GROUPS for node in group["nodes"]]
NODE_STYLE = {code: (fill, stroke, label) for code, label, fill, stroke in NODES}
NODE_ORDER = [code for code, _label, _fill, _stroke in NODES]

STEPS = [
    (1, "Copy templates", "CB", "GH", "setup"),
    (2, "Grant GitHub App", "CB", "CA", "setup"),
    (3, "Create AWS infra", "CB", "AC", "setup"),
    (4, "Push worker image", "CB", "ECR", "setup"),
    (5, "Put API key secret", "ENV", "SM", "setup"),
    (6, "Store Actions secrets", "ENV", "SEC", "setup"),
    (7, "Inject workflow secrets", "SEC", "GH", "setup"),
    (8, "Start session + pull", "ENV", "AC", "setup", "ECR", "AC"),
    (9, "Fetch API key", "SM", "AC", "boot"),
    (10, "Set git origin (on worker)", "AC", "AC", "boot"),
    (11, "Register outbound", "AC", "CA", "run"),
    (12, "Kick off agent", "GH", "CA", "run"),
    (13, "Assign job", "CA", "AC", "run"),
    (14, "Edit workspace (on worker)", "AC", "AC", "run"),
    (15, "Open PR", "CA", "GH", "run"),
]

LEGEND = [
    "1  Copy the workflow and kick script into the sample app repo. The cookbook is not what the agent patches.",
    "2  In the Cursor dashboard, grant the Team GitHub App on that sample repo. This is how PRs open; it is not a Git credential in the image.",
    "3  terraform apply creates ECR, the secret container, IAM, and runtime env. It does not boot a worker.",
    "4  Build linux/arm64 and push to ECR. A running session does not pick up a new image until you start a new session.",
    "5  Laptop .env → Secrets Manager (CURSOR_API_KEY). Terraform never sees the key value.",
    "6  Store CURSOR_API_KEY and GH_PROJECT_TOKEN as Actions secrets on the sample repo.",
    "7  The workflow injects those secrets. GITHUB_TOKEN is automatic; GH_PROJECT_TOKEN is required to read Projects v2.",
    "8  InvokeAgentRuntime starts the instance; it pulls the ECR image. Record AGENTCORE_SESSION_ID.",
    "9  Adapter GetSecretValue with the runtime execution role (CURSOR_API_KEY_SECRET_ID).",
    "10 Adapter git-inits /mnt/workspace and sets origin to WORKER_REPOSITORY_URL. Fetch is best-effort; no Git credentials in the image.",
    "11 agent worker --pool registers outbound HTTPS to Cursor. Cursor does not connect into the VPC.",
    "12 In Progress / label / workflow_dispatch POSTs /v1/agents with pool=agentcore-platform-agents.",
    "13 Cursor assigns the job over that existing outbound connection.",
    "14 Worker edits, tests, and git on /mnt/workspace. Persistent EBS keeps the tree across stop/start.",
    "15 Cursor GitHub App opens the PR (autoCreatePR). Uses the App grant from step 2, not the worker API key.",
]

PHASES = {
    "setup": ("Setup", (245, 247, 250), (13, 110, 140)),
    "boot": ("Boot", (255, 251, 235), (180, 83, 9)),
    "run": ("Run", (239, 246, 255), (29, 78, 216)),
}

LEFT = 28
GRID_X0 = 300
GRID_X1 = 2368
HEADER_Y0 = 118
HEADER_H = 108
ROW_H = 50
BAND_H = 26


def fnt(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def rr(draw: ImageDraw.ImageDraw, box, fill, outline, width=2, radius=12) -> None:
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


def badge(draw: ImageDraw.ImageDraw, xy, n, fill) -> None:
    x, y = xy
    r = 12
    draw.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=WHITE, width=2)
    label = str(n)
    font = fnt(12, True)
    tw = draw.textlength(label, font=font)
    draw.text((x - tw / 2, y - 7), label, font=font, fill=WHITE)


def arrowhead(draw: ImageDraw.ImageDraw, end, ang, color) -> None:
    ah = 9
    p1 = (end[0] - ah * math.cos(ang - 0.45), end[1] - ah * math.sin(ang - 0.45))
    p2 = (end[0] - ah * math.cos(ang + 0.45), end[1] - ah * math.sin(ang + 0.45))
    draw.polygon([end, p1, p2], fill=color)


def dashed_line(draw: ImageDraw.ImageDraw, x0, y0, x1, y1, color, width=3) -> None:
    dx, dy = x1 - x0, y1 - y0
    dist = max(math.hypot(dx, dy), 1)
    ux, uy = dx / dist, dy / dist
    pos, on = 0.0, True
    while pos < dist:
        length = 7 if on else 5
        nxt = min(pos + length, dist)
        if on:
            draw.line(
                (x0 + ux * pos, y0 + uy * pos, x0 + ux * nxt, y0 + uy * nxt),
                fill=color,
                width=width,
            )
        pos = nxt
        on = not on


def h_arrow(draw: ImageDraw.ImageDraw, x0, x1, y, color, dashed: bool) -> None:
    direction = 1 if x1 >= x0 else -1
    shaft_end = x1 - direction * 10
    if dashed:
        dashed_line(draw, x0, y, shaft_end, y, color)
    else:
        draw.line((x0, y, shaft_end, y), fill=color, width=3)
    arrowhead(draw, (x1, y), 0.0 if direction > 0 else math.pi, color)


def column_centers() -> dict[str, float]:
    n = len(NODE_ORDER)
    width = (GRID_X1 - GRID_X0) / n
    return {code: GRID_X0 + (i + 0.5) * width for i, code in enumerate(NODE_ORDER)}


def group_ranges() -> list[tuple[float, float, dict]]:
    width = (GRID_X1 - GRID_X0) / len(NODE_ORDER)
    ranges = []
    i = 0
    for group in GROUPS:
        count = len(group["nodes"])
        x0 = GRID_X0 + i * width + 4
        x1 = GRID_X0 + (i + count) * width - 4
        ranges.append((x0, x1, group))
        i += count
    return ranges


def pill(draw: ImageDraw.ImageDraw, cx, cy, code: str) -> float:
    fill, stroke, _label = NODE_STYLE[code]
    font = fnt(12, True)
    tw = draw.textlength(code, font=font)
    w, h = tw + 18, 24
    rr(draw, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), fill, stroke, width=2, radius=8)
    draw.text((cx - tw / 2, cy - 8), code, font=font, fill=stroke)
    return w / 2


def draw_flow(
    draw: ImageDraw.ImageDraw,
    src: str,
    dst: str,
    y: float,
    centers: dict[str, float],
    color,
    dashed: bool,
) -> None:
    sx, dx = centers[src], centers[dst]
    if src == dst:
        pill(draw, sx, y, src)
        return
    shalf = pill(draw, sx, y, src)
    dhalf = pill(draw, dx, y, dst)
    if sx < dx:
        h_arrow(draw, sx + shalf + 3, dx - dhalf - 3, y, color, dashed)
    else:
        h_arrow(draw, sx - shalf - 3, dx + dhalf + 3, y, color, dashed)


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    centers = column_centers()
    groups = group_ranges()

    d.text((LEFT, 16), "Self-hosted Cloud Agents — who holds which secret", font=fnt(28, True), fill=INK)
    d.text(
        (LEFT, 52),
        "One row per step, one column per component. Long wording is in the legend. Terraform does not start a worker; the image has no Git credentials; Cursor never connects into the VPC.",
        font=fnt(14),
        fill=MUTED,
    )
    dashed_line(d, LEFT, 92, LEFT + 40, 92, LINE_SETUP)
    d.text((LEFT + 48, 83), "Dashed = setup / boot", font=fnt(13), fill=MUTED)
    d.line((LEFT + 248, 92, LEFT + 288, 92), fill=LINE_RUN, width=3)
    d.text((LEFT + 296, 83), "Solid = kickoff and pool run", font=fnt(13), fill=LINE_RUN)
    d.text((LEFT + 560, 83), "Red chips hold CURSOR_API_KEY.", font=fnt(13), fill=(185, 28, 28))

    # Group headers + column chips
    for x0, x1, group in groups:
        rr(d, (x0, HEADER_Y0, x1, HEADER_Y0 + HEADER_H), group["fill"], group["stroke"], width=2, radius=12)
        d.text((x0 + 12, HEADER_Y0 + 8), group["title"], font=fnt(15, True), fill=group["stroke"])
        d.text((x0 + 12, HEADER_Y0 + 28), group["subtitle"], font=fnt(11), fill=MUTED)

    chip_font = fnt(11, True)
    label_font = fnt(11)
    for code, label, fill, stroke in NODES:
        cx = centers[code]
        tw = d.textlength(code, font=chip_font)
        pw = tw + 16
        cy = HEADER_Y0 + 52
        rr(d, (cx - pw / 2, cy, cx + pw / 2, cy + 22), fill, stroke, width=2, radius=7)
        d.text((cx - tw / 2, cy + 3), code, font=chip_font, fill=stroke)
        lw = d.textlength(label, font=label_font)
        d.text((cx - lw / 2, cy + 26), label, font=label_font, fill=INK)

    life_top = HEADER_Y0 + HEADER_H + 10
    y = life_top + 8
    last_phase = None
    step_bottom = y

    # Measure rows first so lifelines stop above the legend.
    rows: list[tuple] = []
    for step in STEPS:
        n, title, src, dst, phase = step[0], step[1], step[2], step[3], step[4]
        extra = step[5:] if len(step) > 5 else ()
        if phase != last_phase:
            y += BAND_H + 6
            last_phase = phase
        row_h = ROW_H + (36 if extra else 0)
        rows.append((n, title, src, dst, phase, extra, y, row_h))
        y += row_h + 4
        step_bottom = y

    for cx in centers.values():
        dashed_line(d, cx, life_top, cx, step_bottom - 2, GUIDE, width=1)

    last_phase = None
    for n, title, src, dst, phase, extra, y, row_h in rows:
        phase_name, phase_fill, phase_color = PHASES[phase]
        if phase != last_phase:
            band_y = y - BAND_H - 6
            rr(
                d,
                (LEFT, band_y, GRID_X1, band_y + BAND_H),
                phase_fill,
                (max(phase_fill[0] - 8, 0), max(phase_fill[1] - 8, 0), max(phase_fill[2] - 8, 0)),
                width=1,
                radius=8,
            )
            d.text((LEFT + 12, band_y + 5), phase_name, font=fnt(12, True), fill=phase_color)
            last_phase = phase

        # Title column only — keep the grid clean.
        cy = y + (18 if extra else row_h / 2)
        dashed = phase != "run"
        color = LINE_SETUP if dashed else LINE_RUN
        badge_y = y + 18 if extra else cy
        badge(d, (LEFT + 22, badge_y), n, phase_color)
        d.text((LEFT + 42, badge_y - 8), title, font=fnt(14, True), fill=INK)

        if extra:
            draw_flow(d, src, dst, y + 16, centers, color, dashed)
            draw_flow(d, extra[0], extra[1], y + 54, centers, color, dashed)
        else:
            draw_flow(d, src, dst, cy, centers, color, dashed)

    footer_y = step_bottom + 28
    rr(d, (LEFT, footer_y, GRID_X1, H - 18), WHITE, (210, 214, 220), width=1, radius=14)
    d.text((LEFT + 18, footer_y + 12), "Legend", font=fnt(16, True), fill=INK)
    d.text(
        (LEFT + 100, footer_y + 16),
        "Column codes: ENV laptop .env · CB cookbook · SEC Actions secrets · GH sample repo · CA Cloud Agents API · SM Secrets Manager · ECR image · AC worker",
        font=fnt(12),
        fill=MUTED,
    )

    col_w = (GRID_X1 - LEFT - 48) / 2
    nf = fnt(13)
    col_y = [footer_y + 46, footer_y + 46]
    for i, note in enumerate(LEGEND):
        column = 0 if i < 8 else 1
        x = LEFT + 18 + column * (col_w + 12)
        yy = col_y[column]
        for line in wrap(d, note, nf, col_w - 10):
            d.text((x, yy), line, font=nf, fill=INK)
            yy += 17
        col_y[column] = yy + 7

    img.save(OUT, "PNG")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes) legend_end={max(col_y):.0f} canvas={H}")


if __name__ == "__main__":
    main()
