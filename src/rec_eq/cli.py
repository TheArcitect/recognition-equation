"""CLI entry point for recognition-equation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from . import __version__
from .model import Situation, Comparison, DOMAIN_EXAMPLES
from .journal import Journal


def _render_r_bar(r: float) -> str:
    """Render a visual bar for R value (-10 to 10)."""
    # Map -10..10 to 0..20
    pos = int(r + 10)
    bar = list("." * 20)
    bar[10] = "|"  # zero line
    if pos >= 0 and pos < 20:
        bar[pos] = "#"
    return "".join(bar)


def _calc_cmd(args: argparse.Namespace) -> int:
    """Calculate R = C - A."""
    console = Console()

    s = Situation(
        name=args.name or "",
        domain=args.domain or "",
        contact=args.contact,
        agenda=args.agenda,
        description=args.description or "",
    )

    r = s.recognition
    eff = s.efficiency

    console.print(Panel(
        f"[bold]R = C − A[/bold]\n\n"
        f"  C (Contact):     {s.contact:5.1f}\n"
        f"  A (Agenda):      {s.agenda:5.1f}\n"
        f"  ─────────────────────\n"
        f"  R (Recognition): {r:5.1f}  [{s.signal_label}]\n"
        f"  Efficiency:      {eff:.0%}" if eff is not None else f"  Efficiency:      N/A",
        title=s.name or "Calculation",
    ))

    # Log to journal if requested
    if args.log:
        journal = Journal(args.file)
        journal.append(s)
        console.print("Logged to journal.")

    return 0


def _compare_cmd(args: argparse.Namespace) -> int:
    """Compare two scenarios."""
    console = Console()

    a = Situation(name=args.name_a, contact=args.c_a, agenda=args.a_a)
    b = Situation(name=args.name_b, contact=args.c_b, agenda=args.a_b)
    comp = Comparison(a=a, b=b)

    table = Table(title="Comparison: R = C − A")
    table.add_column("", style="bold")
    table.add_column(a.name or "Scenario A", justify="right")
    table.add_column(b.name or "Scenario B", justify="right")
    table.add_column("Delta", justify="right", style="cyan")

    table.add_row("Contact (C)", f"{a.contact:.1f}", f"{b.contact:.1f}", f"{comp.delta_c:+.1f}")
    table.add_row("Agenda (A)", f"{a.agenda:.1f}", f"{b.agenda:.1f}", f"{comp.delta_a:+.1f}")
    table.add_row("─" * 12, "─" * 6, "─" * 6, "─" * 6)
    table.add_row("Recognition (R)", f"{a.recognition:.1f}", f"{b.recognition:.1f}", f"{comp.delta_r:+.1f}")
    table.add_row("Signal", a.signal_label, b.signal_label, "")

    console.print(table)
    console.print(f"\nPrimary driver of change: [bold]{comp.primary_driver}[/bold]")

    if comp.delta_r > 0:
        console.print(f"Scenario B produces [green]+{comp.delta_r}[/green] more recognition.")
    elif comp.delta_r < 0:
        console.print(f"Scenario A produces [green]+{abs(comp.delta_r)}[/green] more recognition.")
    else:
        console.print("Both scenarios produce equal recognition.")

    return 0


def _domain_cmd(args: argparse.Namespace) -> int:
    """Show domain analysis."""
    console = Console()

    if args.domain_name:
        name = args.domain_name.lower().replace(" ", "_")
        if name not in DOMAIN_EXAMPLES:
            available = ", ".join(sorted(DOMAIN_EXAMPLES.keys()))
            console.print(f"Domain '{name}' not found. Available: {available}")
            return 1

        examples = DOMAIN_EXAMPLES[name]
        high = examples["high_r"]
        low = examples["low_r"]

        comp = Comparison(a=low, b=high)

        console.print(Panel(f"[bold]{name.replace('_', ' ').title()}[/bold] — through R = C − A"))

        table = Table()
        table.add_column("", style="bold")
        table.add_column(f"Low R: {low.name}", justify="right", style="red")
        table.add_column(f"High R: {high.name}", justify="right", style="green")

        table.add_row("Contact (C)", f"{low.contact:.0f}", f"{high.contact:.0f}")
        table.add_row("Agenda (A)", f"{low.agenda:.0f}", f"{high.agenda:.0f}")
        table.add_row("─" * 12, "─" * 6, "─" * 6)
        table.add_row("Recognition (R)", f"{low.recognition:.0f}", f"{high.recognition:.0f}")
        table.add_row("Signal", low.signal_label, high.signal_label)

        console.print(table)

        console.print(f"\n[dim]Low R:[/dim] {low.description}")
        if low.agenda_factors:
            console.print(f"  Agenda factors: {', '.join(low.agenda_factors)}")

        console.print(f"\n[dim]High R:[/dim] {high.description}")
        if high.contact_factors:
            console.print(f"  Contact factors: {', '.join(high.contact_factors)}")

        console.print(f"\nDelta R: [bold]{comp.delta_r:+.0f}[/bold]  |  Primary driver: [bold]{comp.primary_driver}[/bold]")
    else:
        # List all domains
        table = Table(title="Available Domain Analyses")
        table.add_column("Domain", style="cyan")
        table.add_column("High R Example")
        table.add_column("Low R Example")
        table.add_column("R Range")

        for name, examples in sorted(DOMAIN_EXAMPLES.items()):
            high = examples["high_r"]
            low = examples["low_r"]
            table.add_row(
                name.replace("_", " "),
                f"{high.name} (R={high.recognition:.0f})",
                f"{low.name} (R={low.recognition:.0f})",
                f"{low.recognition:.0f} to {high.recognition:.0f}",
            )

        console.print(table)
        console.print("\nUse [bold]rec-eq domain <name>[/bold] for detailed analysis.")

    return 0


def _journal_cmd(args: argparse.Namespace) -> int:
    """Show journal entries and stats."""
    console = Console()
    journal = Journal(args.file)

    if args.stats:
        s = journal.stats()
        if not s:
            console.print("Journal is empty.")
            return 0

        console.print(Panel(
            f"Entries: {s['total']}  |  "
            f"Avg R: {s['avg_r']}  |  "
            f"Range: {s['min_r']} to {s['max_r']}",
            title="Recognition Journal Stats",
        ))

        if s.get("domain_avg_r"):
            table = Table(title="Average R by Domain")
            table.add_column("Domain", style="cyan")
            table.add_column("Avg R", justify="right")
            for domain, avg in sorted(s["domain_avg_r"].items(), key=lambda x: x[1], reverse=True):
                table.add_row(domain, f"{avg:.1f}")
            console.print(table)

        if s.get("signal_distribution"):
            table = Table(title="Signal Distribution")
            table.add_column("Level", style="cyan")
            table.add_column("Count", justify="right")
            for label, count in s["signal_distribution"].items():
                table.add_row(label, str(count))
            console.print(table)

        return 0

    # Show recent entries
    entries = journal.read_last(args.count)
    if not entries:
        console.print("No journal entries found.")
        return 0

    table = Table(title=f"Last {len(entries)} Journal Entries")
    table.add_column("Name")
    table.add_column("Domain", style="dim")
    table.add_column("C", justify="right", style="green")
    table.add_column("A", justify="right", style="red")
    table.add_column("R", justify="right", style="bold")
    table.add_column("Signal")

    for e in entries:
        table.add_row(
            (e.name or "-")[:30],
            e.domain or "-",
            f"{e.contact:.0f}",
            f"{e.agenda:.0f}",
            f"{e.recognition:.0f}",
            e.signal_label,
        )

    console.print(table)
    console.print(f"Total entries: {journal.count}")
    return 0


def _explain_cmd(args: argparse.Namespace) -> int:
    """Print the equation and what it means."""
    console = Console()

    console.print(Panel(
        "[bold]R = C − A[/bold]\n\n"
        "  R  Recognition — the moment insight, resonance, or understanding occurs\n"
        "  C  Contact     — the interaction itself (conversation, encounter, observation)\n"
        "  A  Agenda      — everything the participants bring that isn't the contact\n"
        "                   (expectations, performance, self-consciousness, trying)\n\n"
        "Recognition is what remains when agenda is subtracted from contact.\n"
        "It is not produced by effort. It is revealed by the removal of obstruction.\n\n"
        "Maps to Shannon:  Signal = Channel capacity − Noise\n"
        "                  R      = C                − A",
        title="The Recognition Equation",
    ))

    console.print("\n[bold]Scale[/bold]")
    table = Table()
    table.add_column("R", justify="right")
    table.add_column("Signal Level")
    table.add_column("Example")
    table.add_row("7 to 10", "breakthrough", "Newton in plague isolation, morning walk dictation")
    table.add_row("4 to 6", "high recognition", "Socratic seminar, two people at a whiteboard")
    table.add_row("1 to 3", "moderate recognition", "Good class, useful meeting")
    table.add_row("-1 to 0", "near zero", "Agenda cancels contact")
    table.add_row("-4 to -2", "blocked", "Performing for investors, committee-driven design")
    table.add_row("-10 to -5", "anti-recognition", "Pure performance, no contact")
    console.print(table)

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="rec-eq",
        description="R = C − A — The Recognition Equation.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--file", "-f",
        type=Path,
        default=None,
        help="Path to journal file (default: ~/Documents/Recognition-Journal/journal.jsonl)",
    )

    sub = parser.add_subparsers(dest="command")

    # --- calc ---
    calc_p = sub.add_parser("calc", help="Calculate R = C - A for a situation")
    calc_p.add_argument("contact", type=float, help="Contact score (0-10)")
    calc_p.add_argument("agenda", type=float, help="Agenda score (0-10)")
    calc_p.add_argument("--name", "-n")
    calc_p.add_argument("--domain", "-d")
    calc_p.add_argument("--description")
    calc_p.add_argument("--log", action="store_true", help="Log to journal")

    # --- compare ---
    cmp_p = sub.add_parser("compare", help="Compare two scenarios")
    cmp_p.add_argument("--name-a", default="Scenario A")
    cmp_p.add_argument("--c-a", type=float, required=True, help="Contact for scenario A")
    cmp_p.add_argument("--a-a", type=float, required=True, help="Agenda for scenario A")
    cmp_p.add_argument("--name-b", default="Scenario B")
    cmp_p.add_argument("--c-b", type=float, required=True, help="Contact for scenario B")
    cmp_p.add_argument("--a-b", type=float, required=True, help="Agenda for scenario B")

    # --- domain ---
    dom_p = sub.add_parser("domain", help="Analyze a domain through R = C - A")
    dom_p.add_argument("domain_name", nargs="?", help="Domain to analyze (education, ai_conversation, meetings, creativity, therapy)")

    # --- journal ---
    jour_p = sub.add_parser("journal", help="View journal entries and stats")
    jour_p.add_argument("count", nargs="?", type=int, default=10)
    jour_p.add_argument("--stats", action="store_true", help="Show aggregate statistics")

    # --- explain ---
    sub.add_parser("explain", help="Print the equation and what it means")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    cmd_map = {
        "calc": _calc_cmd,
        "compare": _compare_cmd,
        "domain": _domain_cmd,
        "journal": _journal_cmd,
        "explain": _explain_cmd,
    }
    return cmd_map[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
