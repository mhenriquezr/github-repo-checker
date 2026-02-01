"""GitHub API client wrapper."""
from typing import Optional
from datetime import datetime, timedelta, timezone
from github import Github, GithubException
from github.Repository import Repository

from config import GITHUB_TOKEN
from models import RepositoryInfo


class GitHubClient:
    """Wrapper for GitHub API operations."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client with token."""
        self.token = token or GITHUB_TOKEN
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN in .env file")
        self.client = Github(self.token)

    def get_repository(self, repo_url: str) -> Repository:
        """
        Get repository object from URL or full name.
        
        Args:
            repo_url: GitHub URL or owner/repo format
            
        Returns:
            Repository object
        """
        # Extract owner/repo from URL
        if "github.com" in repo_url:
            parts = repo_url.rstrip("/").split("/")
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1]
                full_name = f"{owner}/{repo}"
            else:
                raise ValueError(f"Invalid GitHub URL: {repo_url}")
        else:
            full_name = repo_url

        try:
            return self.client.get_repo(full_name)
        except GithubException as e:
            raise ValueError(f"Could not fetch repository: {e}")

    def get_repo_info(self, repo: Repository) -> RepositoryInfo:
        """Extract basic information from repository."""
        stars = repo.stargazers_count
        
        # If it's a fork, always use parent's stars for evaluation
        if repo.fork:
            try:
                parent = repo.parent
                if parent:
                    stars = parent.stargazers_count
            except (GithubException, AttributeError):
                pass
        
        return RepositoryInfo(
            name=repo.name,
            full_name=repo.full_name,
            url=repo.html_url,
            description=repo.description,
            stars=stars,
            forks=repo.forks_count,
            language=repo.language,
            license=repo.license.name if repo.license else None,
            created_at=repo.created_at,
            updated_at=repo.updated_at,
            topics=repo.get_topics()
        )

    def get_contributors_count(self, repo: Repository) -> int:
        """Get number of contributors to repository."""
        try:
            return repo.get_contributors().totalCount
        except GithubException:
            return 0

    def has_recent_activity(self, repo: Repository, days: int = 180) -> bool:
        """Check if repository has activity in the last N days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        return repo.updated_at > cutoff_date

    def check_file_exists(self, repo: Repository, path: str) -> bool:
        """Check if a file or directory exists in repository."""
        try:
            result = repo.get_contents(path)
            return result is not None
        except (GithubException, TypeError, AttributeError):
            return False

    def check_any_file_exists(self, repo: Repository, patterns: list[str]) -> bool:
        """Check if any file matching patterns exists."""
        for pattern in patterns:
            if self.check_file_exists(repo, pattern):
                return True
        return False

    def get_repo_files(self, repo: Repository, path: str = "") -> list[str]:
        """Get list of files in repository path."""
        try:
            contents = repo.get_contents(path)
            files = []
            if isinstance(contents, list):
                for content in contents:
                    files.append(content.path)
            else:
                files.append(contents.path)
            return files
        except GithubException:
            return []

    def search_repositories(
        self,
        query: str,
        language: Optional[str] = None,
        min_stars: int = 10,
        max_results: int = 10
    ) -> list[Repository]:
        """
        Search for repositories matching criteria.
        
        Args:
            query: Search query string
            language: Programming language filter
            min_stars: Minimum number of stars
            max_results: Maximum number of results to return
            
        Returns:
            List of Repository objects
        """
        search_query = f"{query} stars:>={min_stars}"
        
        if language:
            search_query += f" language:{language}"

        try:
            results = self.client.search_repositories(query=search_query, sort="stars")
            return list(results[:max_results])
        except GithubException as e:
            raise ValueError(f"Search failed: {e}")
