"""
Flow diagram of the pipeline.

Left:  LangGraph + A2A architecture.
Right: seconds spent in each node for the most recent task.
Saved as a PNG; no window is opened.
"""

import re
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")  # draw straight to a file, no GUI needed
import matplotlib.patches as mpatches  # noqa: E402  (must come after matplotlib.use)
import matplotlib.pyplot as plt  # noqa: E402

from travel_planner import config  # noqa: E402
from travel_planner.orchestrator.audit_log import get_task_log  # noqa: E402

BACKGROUND = "#f0f4f8"

NODE_COLORS = {
    "parse_query": "#1A5276",
    "research_destination": "#117A65",
    "check_weather": "#784212",
    "estimate_budget": "#641E16",
    "check_leave_balance": "#6C3483",
    "synthesize_plan": "#1A5276",
}

# Pipeline top to bottom: (node name, how it works, text for its A2A agent box or None)
PIPELINE = [
    ("parse_query", "LangChain LCEL", None),
    ("check_leave_balance", "A2A -> :8004", "LangChain\nagent + SQLite"),
    ("research_destination", "A2A -> :8001", "LangChain\nagent + Wiki"),
    ("check_weather", "A2A -> :8002", "LangChain\nagent + wttr"),
    ("estimate_budget", "A2A -> :8003", "LangChain\nagent + Cost DB"),
    ("synthesize_plan", "LangChain LCEL", None),
]

# Matches node log lines such as "[ab12cd34] check_weather → A2A :8002 (3.1s)"
_TIMING_PATTERN = re.compile(r"(\w+)\s*→.*?\(([\d.]+)s\)")


def _box(ax, x, y, w, h, text, color, font_size=8):
    """Rounded, filled box with centred white text."""
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                                         facecolor=color, edgecolor="#333", linewidth=1.8, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=font_size,
            color="white", fontweight="bold", multialignment="center", zorder=4)


def _arrow(ax, x1, y1, x2, y2, color="#555", width=1.8):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=width))


def _draw_architecture(ax) -> None:
    """Left panel: user → six LangGraph nodes → four A2A agents."""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.set_facecolor(BACKGROUND)
    ax.axis("off")
    ax.set_title("LangGraph + A2A Architecture", fontsize=13, fontweight="bold", pad=12)

    _box(ax, 3.5, 10.6, 3.0, 0.9, "User Query\n+ Employee ID", "#7B68EE", font_size=9)
    ax.add_patch(mpatches.FancyBboxPatch((0.3, 0.4), 9.4, 9.8, boxstyle="round,pad=0.2",
                                         facecolor="#EBF5FB", edgecolor="#2E86C1", linewidth=2, zorder=1))
    ax.text(5.0, 10.0, "LangGraph StateGraph", ha="center", fontsize=9,
            color="#2E86C1", fontweight="bold", zorder=5)

    node_height, spacing = 0.9, 1.5
    for index, (node, how, agent_text) in enumerate(PIPELINE):
        y = 8.6 - index * spacing
        color = NODE_COLORS[node]
        _box(ax, 3.0, y, 4.0, node_height, f"Node {index + 1}: {node}\n({how})", color, 7.5)

        # Arrow into this node: from the user box, or from the node above
        arrow_start = 10.6 if index == 0 else y + spacing
        _arrow(ax, 5.0, arrow_start, 5.0, y + node_height, "#2E86C1")

        # Agent box to the right of every node that calls an agent over A2A
        if agent_text:
            _box(ax, 7.6, y + 0.1, 2.1, 0.7, agent_text, color, 6.5)
            _arrow(ax, 7.0, y + 0.45, 7.6, y + 0.45, color, 1.4)
            ax.text(7.3, y + 0.62, "A2A", fontsize=6, color=color, style="italic", ha="center")


def _draw_timings(ax, task: Optional[dict]) -> None:
    """Right panel: horizontal bar per node showing seconds spent."""
    ax.set_facecolor(BACKGROUND)
    ax.set_title("LangGraph Node Timing (most recent task)", fontsize=13, fontweight="bold", pad=12)

    if task is None:
        ax.text(0.5, 0.5, "No tasks yet.\nPlan a trip first!", ha="center", va="center",
                fontsize=12, color="#aaa", transform=ax.transAxes)
        ax.axis("off")
        return

    nodes, seconds = [], []
    for entry in task["node_log"]:
        match = _TIMING_PATTERN.search(entry)
        if match:
            nodes.append(match.group(1))
            seconds.append(float(match.group(2)))

    labels = [node.replace("_", "\n") for node in nodes]
    colors = [NODE_COLORS.get(node, "#555") for node in nodes]
    bars = ax.barh(labels, seconds, color=colors, edgecolor="white", height=0.5)
    for bar, value in zip(bars, seconds):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                f"{value}s", va="center", fontsize=9, fontweight="bold")
    ax.set_xlabel("Seconds per node", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if seconds:
        ax.set_xlim(0, max(seconds) * 1.3 + 1)

    info = (f"Destination: {task['destination']}\nDuration   : {task['duration']}\n"
            f"Employee   : {task['employee_id']}\nTask ID    : {task['task_id']}")
    ax.text(0.98, 0.04, info, transform=ax.transAxes, fontsize=8, va="bottom", ha="right",
            bbox=dict(boxstyle="round", fc="white", ec="#ccc"))


def save_flow_diagram(path: Optional[Path] = None) -> Path:
    """Draw both panels for the latest task and save them as a PNG. Returns the file path."""
    path = path or config.OUTPUT_DIR / "a2a_langgraph_flow.png"
    path.parent.mkdir(parents=True, exist_ok=True)

    tasks = get_task_log()
    fig, (left, right) = plt.subplots(1, 2, figsize=(17, 8))
    fig.patch.set_facecolor(BACKGROUND)
    _draw_architecture(left)
    _draw_timings(right, tasks[-1] if tasks else None)

    plt.tight_layout(pad=2.0)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BACKGROUND)
    plt.close(fig)
    return path
