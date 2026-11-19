
import random
import time
import socket
import platform
import getpass
import uuid
from datetime import datetime

import psutil
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress_bar import ProgressBar

console = Console()
START_TIME = time.time()
SESSION = uuid.uuid4().hex[:8].upper()

# Demo workflow state: these jobs are simulated.
jobs = [
    ["WF-1042", "API Synchronization", "RUNNING", 68],
    ["WF-1043", "Data Validation", "QUEUED", 0],
    ["WF-1044", "Event Processing", "RUNNING", 34],
    ["WF-1045", "Pipeline Health Check", "SUCCESS", 100],
    ["WF-1046", "Report Generation", "QUEUED", 0],
    ["WF-1047", "Cache Refresh", "SUCCESS", 100],
]

events = [
    ("INFO", "Orchestration engine initialized"),
    ("PASS", "Runtime dependencies verified"),
    ("INFO", "Worker pool connected"),
    ("PASS", "Configuration integrity validated"),
    ("EXEC", "Workflow scheduler started"),
    ("INFO", "Event stream subscription active"),
    ("PASS", "Health-check endpoint responding"),
    ("EXEC", "Processing pending workflow tasks"),
]

def uptime():
    seconds = int(time.time() - START_TIME)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02}:{m:02}:{s:02}"

def header():
    art = Text()
    art.append("  █████╗  ", style="bold bright_cyan")
    art.append("U T O M A T I O N\n", style="bold white")
    art.append("  OPS CONSOLE  /  WORKFLOW ORCHESTRATION",
               style="bright_green")
    art.append("\n  ", style="dim")
    art.append("SYSTEMS", style="cyan")
    art.append("  •  RUNTIME TELEMETRY  •  EVENT STREAM",
               style="dim")
    return Panel(
        Align.left(art),
        border_style="bright_cyan",
        box=box.DOUBLE,
        padding=(1, 1),
    )

def system_panel():
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim")
    table.add_column(style="bold white")
    table.add_column(style="dim")
    table.add_column(style="bold white")

    table.add_row("HOST", socket.gethostname()[:22],
                  "PLATFORM", platform.system())
    table.add_row("USER", getpass.getuser()[:22],
                  "PYTHON", platform.python_version())
    table.add_row("CPU LOAD", f"{cpu:5.1f}%",
                  "MEMORY", f"{mem.percent:5.1f}%")
    table.add_row("DISK USAGE", f"{disk.percent:5.1f}%",
                  "UPTIME", uptime())
    table.add_row("SESSION", SESSION,
                  "CLOCK", datetime.now().strftime("%H:%M:%S"))

    return Panel(
        table,
        title="[bold cyan]01 / SYSTEM TELEMETRY[/]",
        border_style="cyan",
        box=box.ROUNDED,
    )

def pipeline_panel():
    table = Table(
        box=box.SIMPLE_HEAD,
        expand=True,
        header_style="bold bright_cyan",
    )
    table.add_column("JOB ID", style="dim", width=10)
    table.add_column("WORKFLOW", ratio=2)
    table.add_column("PROGRESS", ratio=2)
    table.add_column("STATE", width=10)

    for job in jobs:
        job_id, name, status, pct = job
        color = {
            "RUNNING": "bright_cyan",
            "QUEUED": "yellow",
            "SUCCESS": "bright_green",
        }.get(status, "white")

        bar = ProgressBar(
            total=100,
            completed=pct,
            width=16,
            complete_style=color,
            finished_style="bright_green",
        )

        progress = Group(
            bar,
            Text(f"{pct:3d}%", style=color),
        )

        table.add_row(
            job_id,
            name,
            progress,
            Text(status, style=f"bold {color}"),
        )

    return Panel(
        table,
        title="[bold cyan]02 / WORKFLOW PIPELINE[/]",
        subtitle="[dim]Illustrative jobs · simulated progress[/]",
        border_style="cyan",
        box=box.ROUNDED,
    )

def metrics_panel():
    running = sum(j[2] == "RUNNING" for j in jobs)
    queued = sum(j[2] == "QUEUED" for j in jobs)
    done = sum(j[2] == "SUCCESS" for j in jobs)

    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(justify="center")
    table.add_column(justify="center")
    table.add_column(justify="center")

    table.add_row(
        Text(str(running), style="bold bright_cyan"),
        Text(str(queued), style="bold yellow"),
        Text(str(done), style="bold bright_green"),
    )
    table.add_row(
        Text("RUNNING", style="dim"),
        Text("QUEUED", style="dim"),
        Text("COMPLETED", style="dim"),
    )

    return Panel(
        table,
        title="[bold cyan]03 / JOB METRICS[/]",
        border_style="cyan",
        box=box.ROUNDED,
    )

def event_panel(tick):
    table = Table(
        box=box.SIMPLE,
        expand=True,
        show_header=True,
        header_style="bold bright_cyan",
    )
    table.add_column("TIME", width=10, style="dim")
    table.add_column("LEVEL", width=8)
    table.add_column("EVENT", ratio=1)

    start = tick % len(events)
    batch = [events[(start + i) % len(events)] for i in range(5)]

    for i, (level, message) in enumerate(batch):
        colors = {
            "INFO": "cyan",
            "PASS": "bright_green",
            "EXEC": "bright_magenta",
            "WARN": "yellow",
        }
        clock = datetime.now().strftime("%H:%M:%S")
        table.add_row(
            clock if i == 0 else "   ...",
            Text(level, style=colors.get(level, "white")),
            message,
        )

    return Panel(
        table,
        title="[bold cyan]04 / EVENT STREAM[/]",
        border_style="cyan",
        box=box.ROUNDED,
    )

def footer(tick):
    dots = ["●", "◉", "○", "◉"]
    return Align.center(
        Text.from_markup(
            f"[bright_green]{dots[tick % len(dots)]} CONSOLE ACTIVE[/] "
            f"[dim] | [/]"
            f"[cyan]MONITORING[/] "
            f"[dim] | [/]"
            f"[white]SESSION {SESSION}[/] "
            f"[dim] | CTRL+C TO EXIT[/]"
        )
    )

def build_dashboard(tick):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=6),
        Layout(name="system", size=9),
        Layout(name="pipeline", ratio=2),
        Layout(name="metrics", size=5),
        Layout(name="events", size=10),
        Layout(name="footer", size=2),
    )

    layout["header"].update(header())
    layout["system"].update(system_panel())
    layout["pipeline"].update(pipeline_panel())
    layout["metrics"].update(metrics_panel())
    layout["events"].update(event_panel(tick))
    layout["footer"].update(footer(tick))
    return layout

def simulate_workflows():
    for job in jobs:
        if job[2] == "RUNNING":
            job[3] = min(100, job[3] + random.randint(1, 5))
            if job[3] == 100:
                job[2] = "SUCCESS"

        elif job[2] == "QUEUED" and random.random() < 0.12:
            job[2] = "RUNNING"

def main():
    psutil.cpu_percent(interval=None)

    try:
        with Live(
            build_dashboard(0),
            console=console,
            refresh_per_second=4,
            screen=True,
        ) as live:
            tick = 0
            while True:
                simulate_workflows()
                live.update(build_dashboard(tick))
                tick += 1
                time.sleep(1)

    except KeyboardInterrupt:
        console.print(
            "\n[bold yellow]Console session terminated.[/]"
        )

if __name__ == "__main__":
    main()
