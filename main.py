#!/usr/bin/env python3
"""
GitHub Repository Checker CLI
Main entry point for repository verification and search.
"""
import sys
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from github_client import GitHubClient
from verifier import RepositoryVerifier
from searcher import RepositorySearcher
from models import SearchCriteria

console = Console()


def print_verification_report(report):
    """Print verification report in a nice format."""
    repo = report.repository
    
    # Repository info
    console.print(f"\n[bold cyan]{repo.full_name}[/bold cyan]")
    console.print(f"⭐ {repo.stars} | {repo.language or 'Unknown'} | {repo.license or 'No license'}")
    
    # Score and status
    score_color = "green" if report.score >= 70 else "yellow" if report.score >= 50 else "red"
    status = "✅ PASSED" if report.passed else "❌ FAILED"
    console.print(f"\n[{score_color}]{status} - Score: {report.score:.0f}/100[/{score_color}]")
    
    # Show failures and warnings
    failed = report.get_failed_checks()
    warnings = report.get_warnings()
    
    if failed:
        console.print(f"\n[red]Missing ({len(failed)}):[/red]")
        for check in failed:
            console.print(f"  ❌ {check.name}: {check.message}")
    
    if warnings:
        console.print(f"\n[yellow]Warnings ({len(warnings)}):[/yellow]")
        for check in warnings:
            console.print(f"  ⚠️  {check.name}: {check.message}")
    
    if not failed and not warnings:
        console.print("\n[green]✨ All checks passed![/green]")
    
    console.print()


def print_search_results(results, title="Search Results"):
    """Print search results in a nice format."""
    if not results:
        console.print("[yellow]No repositories found matching criteria[/yellow]")
        return
    
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Repository", style="cyan", no_wrap=True)
    table.add_column("Language", style="magenta")
    table.add_column("Stars", justify="right", style="yellow")
    table.add_column("Score", justify="center", style="green")
    table.add_column("License", style="blue")
    
    for repo_info, score in results:
        score_str = f"{score:.1f}" if score is not None else "N/A"
        table.add_row(
            repo_info.full_name,
            repo_info.language or "Unknown",
            str(repo_info.stars),
            score_str,
            repo_info.license or "None"
        )
    
    console.print(table)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    GitHub Repository Checker
    
    Verify and search for high-quality GitHub repositories.
    """
    pass


@cli.command()
@click.argument('repo_url')
@click.option('--token', '-t', help='GitHub API token (or use GITHUB_TOKEN env var)')
def verify(repo_url, token):
    """
    Verify a repository against quality requirements.
    
    REPO_URL: GitHub repository URL or owner/repo format
    
    Example: python main.py verify https://github.com/pallets/flask
    """
    try:
        console.print(f"[cyan]Verifying repository: {repo_url}[/cyan]\n")
        
        client = GitHubClient(token)
        verifier = RepositoryVerifier(client)
        
        with console.status("[bold green]Checking requirements..."):
            report = verifier.verify_repository(repo_url)
        
        print_verification_report(report)
        
        # Exit with appropriate code
        sys.exit(0 if report.passed else 1)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option('--language', '-l', help='Programming language (Python, JavaScript, TypeScript, Rust)')
@click.option('--topics', '-t', help='Comma-separated topics to search for')
@click.option('--min-stars', default=10, help='Minimum number of stars')
@click.option('--min-contributors', default=2, help='Minimum number of contributors')
@click.option('--has-tests', is_flag=True, help='Require testing practices')
@click.option('--max-results', '-n', default=10, help='Maximum number of results')
@click.option('--no-verify', is_flag=True, help='Skip verification of results')
@click.option('--token', help='GitHub API token')
def search(language, topics, min_stars, min_contributors, has_tests, max_results, no_verify, token):
    """
    Search for repositories matching criteria.
    
    Examples:
    
      python main.py search --language Python --min-stars 100
      
      python main.py search --topics testing,cli --language TypeScript
      
      python main.py search --language Rust --has-tests --min-contributors 5
    """
    try:
        client = GitHubClient(token)
        searcher = RepositorySearcher(client)
        
        # Parse topics
        topic_list = [t.strip() for t in topics.split(',')] if topics else []
        
        criteria = SearchCriteria(
            language=language,
            topics=topic_list,
            min_stars=min_stars,
            min_contributors=min_contributors,
            has_tests=has_tests,
            max_results=max_results
        )
        
        console.print("[cyan]Searching repositories...[/cyan]\n")
        
        with console.status("[bold green]Fetching and verifying repositories..."):
            results = searcher.search_repositories(criteria, verify=not no_verify)
        
        print_search_results(results)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option('--language', '-l', required=True, help='Programming language')
@click.option('--count', '-n', default=3, help='Results per category')
@click.option('--no-verify', is_flag=True, help='Skip verification (faster)')
@click.option('--token', help='GitHub API token')
def diverse(language, count, no_verify, token):
    """
    Find diverse codebases (libraries, apps, SDKs, frameworks).
    
    Example: python main.py diverse --language Python --count 3
    """
    try:
        client = GitHubClient(token)
        searcher = RepositorySearcher(client)
        
        console.print(f"[cyan]Finding diverse {language} codebases...[/cyan]\n")
        
        categories = {
            "Libraries": ["library"],
            "Applications": ["application", "app"],
            "SDKs": ["sdk"],
            "Frameworks": ["framework"]
        }
        
        for category, topics in categories.items():
            with console.status(f"[bold green]Searching {category.lower()}..."):
                criteria = SearchCriteria(
                    language=language,
                    topics=topics,
                    max_results=count
                )
                results = searcher.search_repositories(criteria, verify=not no_verify)
            
            if results:
                print_search_results(results, title=category)
                console.print()
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option('--language', '-l', required=True, help='Programming language')
@click.option('--complexity', '-c', 
              type=click.Choice(['simple', 'medium', 'complex']),
              default='medium',
              help='Codebase complexity level')
@click.option('--type', '-t',
              type=click.Choice(['library', 'application', 'sdk', 'framework']),
              help='Type of codebase')
@click.option('--no-verify', is_flag=True, help='Skip verification (faster)')
@click.option('--token', help='GitHub API token')
def recommend(language, complexity, type, no_verify, token):
    """
    Get repository recommendations based on preferences.
    
    Example: python main.py recommend --language Python --complexity medium --type library
    """
    try:
        client = GitHubClient(token)
        searcher = RepositorySearcher(client)
        
        console.print(f"[cyan]Finding {complexity} {language} codebases...[/cyan]\n")
        
        with console.status("[bold green]Getting recommendations..."):
            topics = [type] if type else []
            
            if complexity == "simple":
                min_stars = 10
                max_results = 10
            elif complexity == "medium":
                min_stars = 50
                max_results = 10
            else:
                min_stars = 200
                max_results = 10
            
            criteria = SearchCriteria(
                language=language,
                topics=topics,
                min_stars=min_stars,
                has_tests=False,
                max_results=max_results
            )
            
            results = searcher.search_repositories(criteria, verify=not no_verify)
        
        print_search_results(results, title="Recommended Repositories")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument('library_name')
@click.option('--language', '-l', help='Programming language filter')
@click.option('--max-results', '-n', default=10, help='Maximum number of results')
@click.option('--no-verify', is_flag=True, help='Skip verification (faster)')
@click.option('--token', help='GitHub API token')
def by_library(library_name, language, max_results, no_verify, token):
    """
    Search repositories that use a specific library.
    
    LIBRARY_NAME: Name of the library to search for
    
    Example: python main.py by-library pytest --language Python
    """
    try:
        client = GitHubClient(token)
        searcher = RepositorySearcher(client)
        
        console.print(f"[cyan]Searching repositories using {library_name}...[/cyan]\n")
        
        with console.status("[bold green]Searching..."):
            criteria = SearchCriteria(
                language=language,
                topics=[library_name.lower()],
                max_results=max_results
            )
            results = searcher.search_repositories(criteria, verify=not no_verify)
        
        print_search_results(results, title=f"Repositories using {library_name}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()
