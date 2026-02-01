#!/usr/bin/env python3
"""Script to verify all approved repositories."""
import os
from dotenv import load_dotenv
from github_client import GitHubClient
from verifier import RepositoryVerifier
from rich.console import Console
from rich.table import Table

load_dotenv()

# Default list of approved repositories
DEFAULT_REPOS = [
    "https://github.com/reliableengineer0308/markitdown",
    "https://github.com/marqbritt/PocketFlow/",
    "https://github.com/strands-agents/sdk-python",
    "https://github.com/i-am-bee/beeai-framework",
    "https://github.com/reliableengineer0308/fastapi_mcp",
    "https://github.com/nlweb-ai/NLWeb",
    "https://github.com/huggingface/smolagents",
    "https://github.com/ScrapeGraphAI/Scrapegraph-ai",
    "https://github.com/deepseek-ai/smallpond/",
    "https://github.com/reliableengineer0308/docling",
    "https://github.com/nicolargo/glances",
    "https://github.com/Grimmys/rpg_tactical_fantasy_game",
    "https://github.com/ymyke/cardio",
    "https://github.com/marqbritt/langroid",
    "https://github.com/marqbritt/zev",
    "https://github.com/jonigl/mcp-client-for-ollama",
    "https://github.com/browser-use/web-ui",
    "https://github.com/gaphor/gaphor",
    "https://github.com/567-labs/instructor",
    "https://github.com/litestar-org/litestar",
    "https://github.com/pydantic/pydantic-ai",
    "https://github.com/marqbritt/fast-agent",
    "https://github.com/pygame/zanthor",
    "https://github.com/gradio-app/fastrtc",
    "https://github.com/lxgr-linux/pokete",
    "https://github.com/falconry/falcon",
    "https://github.com/Dave-YP/cosmic-heat-pygame/",
    "https://github.com/ian-coccimiglio/trafficSimulator",
    "https://github.com/gruns/icecream",
    "https://github.com/pallets/click",
    "https://github.com/pytest-dev/pytest-mock/",
    "https://github.com/scribble-rs/scribble.rs",
    "https://github.com/confident-ai/deepeval",
    "https://github.com/llmhq-hub/promptops",
    "https://github.com/webrtc-rs/webrtc",
    "https://github.com/rustviz/rustviz",
    "https://github.com/model-checking/kani",
    "https://github.com/tekaratzas/RustGPT",
    "https://github.com/gitui-org/gitui",
    "https://github.com/bee-san/RustScan",
    "https://github.com/eza-community/eza",
    "https://github.com/ratatui/ratatui",
    "https://github.com/microsoft/edit",
    "https://github.com/ClementTsang/bottom",
    "https://github.com/o2sh/onefetch",
    "https://github.com/DioCrafts/OxiCloud",
    "https://github.com/Enigmatikk/Torch",
    "https://github.com/TabbyML/tabby",
    "https://github.com/svartalf/rust-battop",
    "https://github.com/timokoesters/nbodysim",
    "https://github.com/alam00000/bentopdf",
    "https://github.com/honojs/hono",
    "https://github.com/marqbritt/puter",
    "https://github.com/flowiseai/flowise",
    "https://github.com/ccxt/ast-transpiler",
    "https://github.com/pocketbase/js-sdk",
]

# Load from environment variable if available
# Set APPROVED_REPOS in .env as comma-separated URLs
env_repos = os.getenv('APPROVED_REPOS', '').strip()
if env_repos:
    APPROVED_REPOS = [repo.strip() for repo in env_repos.split(',') if repo.strip()]
else:
    APPROVED_REPOS = DEFAULT_REPOS


def verify_all():
    """Verify all approved repositories."""
    client = GitHubClient()
    verifier = RepositoryVerifier(client)
    
    print(f"Verifying {len(APPROVED_REPOS)} approved repositories...\n")
    
    passed = []
    failed = []
    
    for i, repo_url in enumerate(APPROVED_REPOS, 1):
        name = repo_url.rstrip('/').split('/')[-1]
        print(f"[{i}/{len(APPROVED_REPOS)}] {name}...", end=" ")
        
        try:
            report = verifier.verify_repository(repo_url)
            if report.passed:
                passed.append((name, report.score))
                print(f"✅ {report.score:.0f}")
            else:
                failed.append((name, report.score, len(report.get_failed_checks())))
                print(f"❌ {report.score:.0f} ({len(report.get_failed_checks())} issues)")
        except Exception as e:
            failed.append((name, 0, str(e)))
            print(f"❌ ERROR: {e}")
    
    print(f"\n✅ Passed: {len(passed)}/{len(APPROVED_REPOS)}")
    if failed:
        print(f"❌ Failed: {len(failed)}")
        print("\nFailed repos:")
        for item in failed:
            print(f"  - {item[0]}: score {item[1]}")


if __name__ == '__main__':
    verify_all()
