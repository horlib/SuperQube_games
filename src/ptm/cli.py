# -*- coding: utf-8 -*-
"""CLI entrypoint for Pricing Truth Machine."""

import sys
from pathlib import Path

import click
from rich.console import Console

from ptm.aggregation import aggregate_competitor_pricing
from ptm.json_output import generate_json_report
from ptm.llm_reasoning import enhance_verdict_with_llm
from ptm.query_strategy import QueryStrategy
from ptm.reporting import generate_markdown_report
from ptm.schemas import EvidenceBundle, ProductInput
from ptm.tavily_client import TavilyClient
from ptm.verdict import compute_verdict

console = Console()


@click.group()
def cli() -> None:
    """Pricing Truth Machine - Evidence-based pricing analysis."""
    pass


@cli.command()
@click.option(
    "--product-name",
    required=True,
    help="Product name",
)
@click.option(
    "--product-url",
    required=True,
    help="Product URL",
)
@click.option(
    "--current-price",
    required=True,
    help="Current price (e.g., '$99/month')",
)
@click.option(
    "--competitor-url",
    multiple=True,
    help="Competitor URL (can be repeated)",
)
@click.option(
    "--no-llm",
    is_flag=True,
    default=False,
    help="Disable LLM reasoning mode",
)
@click.option(
    "--outdir",
    type=click.Path(path_type=Path),
    default=Path("output"),
    help="Output directory for reports",
)
def run(
    product_name: str,
    product_url: str,
    current_price: str,
    competitor_url: tuple[str, ...],
    no_llm: bool,
    outdir: Path,
) -> None:
    """Run pricing analysis for a product.

    Example:
        ptm run --product-name "My Product" --product-url "https://example.com" --current-price "$99/month"
    """
    try:
        console.print("[bold blue]Pricing Truth Machine[/bold blue]")
        console.print("=" * 50)

        # Create product input
        product_input = ProductInput(
            name=product_name,
            url=product_url,
            current_price=current_price,
            competitor_urls=list(competitor_url) if competitor_url else [],
        )

        console.print(f"\n[bold]Product:[/bold] {product_name}")
        console.print(f"[bold]URL:[/bold] {product_url}")
        console.print(f"[bold]Current Price:[/bold] {current_price}")

        # Initialize Tavily client
        console.print("\n[yellow]Searching for pricing data...[/yellow]")
        tavily_client = TavilyClient()

        # Discover pricing sources
        query_strategy = QueryStrategy(tavily_client)

        # Log query intent
        console.print("[dim]Query: Product pricing context[/dim]")
        console.print("[dim]Query: Competitor/alternative pricing[/dim]")
        if competitor_url:
            console.print(
                f"[dim]Query: Direct competitor URLs ({len(competitor_url)} provided)[/dim]"
            )

        sources = query_strategy.discover_pricing_sources(product_input)

        console.print(f"[green][OK] Found {len(sources)} sources[/green]")

        # Log source domains
        if sources:
            domains = set()
            for source in sources[:10]:  # Show first 10
                try:
                    from urllib.parse import urlparse

                    domain = urlparse(str(source.url)).netloc
                    if domain:
                        domains.add(domain)
                except Exception:
                    pass
            if domains:
                console.print(
                    f"[dim]  Domains: {', '.join(list(domains)[:5])}{'...' if len(domains) > 5 else ''}[/dim]"
                )

        # Aggregate competitor pricing
        console.print("\n[yellow]Extracting competitor pricing...[/yellow]")
        competitor_pricing = aggregate_competitor_pricing(sources)

        console.print(f"[green][OK] Analyzed {len(competitor_pricing)} competitors[/green]")

        # Log competitor details
        comparable_count = sum(
            1 for cp in competitor_pricing if cp.normalized_monthly_usd is not None
        )
        console.print(f"[dim]  Comparable: {comparable_count} (with normalized pricing)[/dim]")
        if comparable_count < len(competitor_pricing):
            console.print(
                f"[dim]  Non-comparable: {len(competitor_pricing) - comparable_count} (missing data)[/dim]"
            )

        # Build evidence bundle
        evidence_bundle = EvidenceBundle(
            product_input=product_input,
            tavily_sources=sources,
            competitor_pricing=competitor_pricing,
        )

        # Compute verdict
        console.print("\n[yellow]Computing verdict...[/yellow]")
        verdict = compute_verdict(product_input, evidence_bundle)

        # Optionally enhance with LLM
        if not no_llm:
            try:
                console.print("[yellow]Enhancing with LLM reasoning...[/yellow]")
                verdict = enhance_verdict_with_llm(verdict, evidence_bundle)
                console.print("[green]LLM enhancement completed[/green]")
            except Exception as e:
                console.print(f"[yellow]LLM enhancement skipped: {e}[/yellow]")

        # Display verdict with provenance
        console.print("\n[bold]Verdict:[/bold]")
        status_colors = {
            "UNDERPRICED": "green",
            "FAIR": "blue",
            "OVERPRICED": "red",
            "UNDETERMINABLE": "yellow",
        }
        color = status_colors.get(verdict.status.value, "white")
        console.print(f"  Status: [{color}]{verdict.status.value}[/{color}]")
        console.print(f"  Confidence: {verdict.confidence:.1%}")
        console.print(f"  Comparable Competitors: {verdict.competitor_count}")

        # Log verdict provenance
        console.print("\n[dim]Verdict Provenance:[/dim]")
        console.print(
            f"[dim]  - Based on {len(verdict.evidence_bundle.tavily_sources)} evidence sources[/dim]"
        )
        console.print(f"[dim]  - {len(verdict.citations)} citations[/dim]")
        if verdict.gaps:
            console.print(f"[dim]  - {len(verdict.gaps)} data gaps identified[/dim]")

        if verdict.key_reasons:
            console.print("\n[bold]Key Reasons:[/bold]")
            for reason in verdict.key_reasons:
                console.print(f"  - {reason}")

        if verdict.gaps:
            console.print("\n[yellow]Gaps & Limitations:[/yellow]")
            for gap in verdict.gaps[:5]:  # Show first 5
                console.print(f"  - {gap}")

        # Generate reports
        console.print(f"\n[yellow]Generating reports in {outdir}...[/yellow]")
        outdir.mkdir(parents=True, exist_ok=True)

        generate_markdown_report(verdict, outdir / "report.md")
        generate_json_report(verdict, outdir / "report.json")

        console.print(f"[green][OK] Markdown report: {outdir / 'report.md'}[/green]")
        console.print(f"[green][OK] JSON report: {outdir / 'report.json'}[/green]")

        console.print("\n[bold green]Analysis complete![/bold green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def main() -> None:
    """Main CLI entrypoint."""
    cli()


if __name__ == "__main__":
    main()
