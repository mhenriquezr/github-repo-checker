"""Repository search module."""
from typing import Optional
from github.Repository import Repository

from github_client import GitHubClient
from models import SearchCriteria, RepositoryInfo
from verifier import RepositoryVerifier


class RepositorySearcher:
    """Search for repositories matching criteria."""

    def __init__(self, client: GitHubClient):
        """Initialize searcher with GitHub client."""
        self.client = client
        self.verifier = RepositoryVerifier(client)

    def search_repositories(
        self,
        criteria: SearchCriteria,
        verify: bool = True
    ) -> list[tuple[RepositoryInfo, Optional[float]]]:
        """
        Search for repositories matching criteria.
        
        Args:
            criteria: SearchCriteria object with filters
            verify: Whether to verify each result
            
        Returns:
            List of tuples (RepositoryInfo, score or None)
        """
        # Build search query
        query_parts = []
        
        if criteria.topics:
            for topic in criteria.topics:
                query_parts.append(f"topic:{topic}")
        
        # Add test-related topics if required
        if criteria.has_tests:
            query_parts.append("(topic:testing OR topic:tests OR topic:pytest OR topic:jest)")
        
        query = " ".join(query_parts) if query_parts else "stars:>0"
        
        # Search repositories
        repos = self.client.search_repositories(
            query=query,
            language=criteria.language,
            min_stars=criteria.min_stars,
            max_results=criteria.max_results * 2  # Get more to filter
        )
        
        results = []
        
        for repo in repos:
            # Filter by contributors
            contributors = self.client.get_contributors_count(repo)
            if contributors < criteria.min_contributors:
                continue
            
            repo_info = self.client.get_repo_info(repo)
            
            if verify:
                # Verify the repository
                try:
                    report = self.verifier.verify_repository(repo.html_url)
                    if report.passed:
                        results.append((repo_info, report.score))
                except Exception as e:
                    # Skip repositories that fail verification
                    print(f"Warning: Could not verify {repo.full_name}: {e}")
                    continue
            else:
                results.append((repo_info, None))
            
            if len(results) >= criteria.max_results:
                break
        
        # Sort by score if verified
        if verify:
            results.sort(key=lambda x: x[1] or 0, reverse=True)
        
        return results

    def search_by_library(
        self,
        library_name: str,
        language: Optional[str] = None,
        max_results: int = 10
    ) -> list[tuple[RepositoryInfo, Optional[float]]]:
        """
        Search repositories that use a specific library.
        
        Args:
            library_name: Name of the library to search for
            language: Programming language filter
            max_results: Maximum results to return
            
        Returns:
            List of tuples (RepositoryInfo, score or None)
        """
        criteria = SearchCriteria(
            language=language,
            topics=[library_name.lower()],
            max_results=max_results
        )
        
        return self.search_repositories(criteria, verify=True)

    def search_diverse_codebases(
        self,
        language: str,
        count_per_type: int = 3
    ) -> dict[str, list[tuple[RepositoryInfo, float]]]:
        """
        Search for diverse codebases (libraries, apps, SDKs).
        
        Args:
            language: Programming language to filter
            count_per_type: Number of results per type
            
        Returns:
            Dictionary with codebase types as keys
        """
        results = {
            "libraries": [],
            "applications": [],
            "sdks": [],
            "frameworks": []
        }
        
        # Search for libraries
        lib_criteria = SearchCriteria(
            language=language,
            topics=["library"],
            max_results=count_per_type
        )
        results["libraries"] = self.search_repositories(lib_criteria, verify=True)
        
        # Search for applications
        app_criteria = SearchCriteria(
            language=language,
            topics=["application", "app"],
            max_results=count_per_type
        )
        results["applications"] = self.search_repositories(app_criteria, verify=True)
        
        # Search for SDKs
        sdk_criteria = SearchCriteria(
            language=language,
            topics=["sdk"],
            max_results=count_per_type
        )
        results["sdks"] = self.search_repositories(sdk_criteria, verify=True)
        
        # Search for frameworks
        framework_criteria = SearchCriteria(
            language=language,
            topics=["framework"],
            max_results=count_per_type
        )
        results["frameworks"] = self.search_repositories(framework_criteria, verify=True)
        
        return results

    def get_recommendations(
        self,
        language: str,
        complexity: str = "medium",
        include_type: Optional[str] = None
    ) -> list[tuple[RepositoryInfo, float]]:
        """
        Get repository recommendations based on preferences.
        
        Args:
            language: Programming language
            complexity: "simple", "medium", or "complex"
            include_type: Optional type filter (library, application, etc.)
            
        Returns:
            List of recommended repositories with scores
        """
        topics = []
        
        if include_type:
            topics.append(include_type)
        
        # Adjust stars based on complexity
        if complexity == "simple":
            min_stars = 10
            max_results = 5
        elif complexity == "medium":
            min_stars = 50
            max_results = 5
        else:  # complex
            min_stars = 200
            max_results = 5
        
        criteria = SearchCriteria(
            language=language,
            topics=topics,
            min_stars=min_stars,
            has_tests=True,
            max_results=max_results
        )
        
        return self.search_repositories(criteria, verify=True)
