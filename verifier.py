"""Repository verification module."""
import re
from typing import Optional
from github.Repository import Repository

from github_client import GitHubClient
from models import RequirementCheck, VerificationReport, RepositoryInfo
from config import (
    SUPPORTED_LANGUAGES,
    MIN_STARS,
    MIN_CONTRIBUTORS,
    ACTIVITY_DAYS,
    TESTING_FILES,
    BUILD_FILES,
    LINTER_FILES,
    NETWORK_INDICATORS,
    MIN_FILES,
    MIN_DIRECTORIES,
    MAX_SIZE_MB
)


class RepositoryVerifier:
    """Verify repository against quality requirements."""

    def __init__(self, client: GitHubClient):
        """Initialize verifier with GitHub client."""
        self.client = client

    def verify_repository(self, repo_url: str) -> VerificationReport:
        """
        Verify a repository against all requirements.
        
        Args:
            repo_url: GitHub repository URL or owner/repo format
            
        Returns:
            VerificationReport with all checks and score
        """
        repo = self.client.get_repository(repo_url)
        repo_info = self.client.get_repo_info(repo)
        
        checks = [
            self._check_is_git_repo(repo),
            self._check_primary_language(repo),
            self._check_open_license(repo),
            self._check_multiple_contributors(repo),
            self._check_recent_activity(repo),
            self._check_has_testing(repo),
            self._check_build_instructions(repo),
            self._check_code_quality_indicators(repo),
            self._check_network_usage(repo),
            self._check_complexity(repo),
            self._check_not_vibe_coded(repo),
            self._check_size(repo),
        ]

        # Calculate score
        score = self._calculate_score(checks)
        
        # Import PASS_THRESHOLD from config
        from config import PASS_THRESHOLD
        passed = score >= PASS_THRESHOLD
        
        summary = self._generate_summary(checks, score)

        return VerificationReport(
            repository=repo_info,
            checks=checks,
            score=score,
            passed=passed,
            summary=summary
        )

    def _check_is_git_repo(self, repo: Repository) -> RequirementCheck:
        """Check if it's a valid git repository."""
        # If we can fetch it, it's a git repo
        return RequirementCheck(
            name="Git Repository",
            passed=True,
            message="Valid git repository",
            severity="error"
        )

    def _check_primary_language(self, repo: Repository) -> RequirementCheck:
        """Check if primary language is detected."""
        language = repo.language
        
        if not language:
            return RequirementCheck(
                name="Primary Language",
                passed=False,
                message="No primary language detected",
                severity="error"
            )
        
        return RequirementCheck(
            name="Primary Language",
            passed=True,
            message=f"Primary language is {language}",
            severity="error"
        )

    def _check_open_license(self, repo: Repository) -> RequirementCheck:
        """Check if repository has an open source license."""
        license_obj = repo.license
        
        if not license_obj:
            return RequirementCheck(
                name="Open License",
                passed=False,
                message="No license detected",
                severity="error"
            )
        
        return RequirementCheck(
            name="Open License",
            passed=True,
            message=f"Licensed under {license_obj.name}",
            severity="error"
        )

    def _check_multiple_contributors(self, repo: Repository) -> RequirementCheck:
        """Check if repository has multiple contributors."""
        contributors_count = self.client.get_contributors_count(repo)
        
        if contributors_count >= MIN_CONTRIBUTORS:
            return RequirementCheck(
                name="Multiple Contributors",
                passed=True,
                message=f"Has {contributors_count} contributors",
                severity="error"
            )
        else:
            return RequirementCheck(
                name="Multiple Contributors",
                passed=False,
                message=f"Only {contributors_count} contributor(s), minimum is {MIN_CONTRIBUTORS}",
                severity="error"
            )

    def _check_recent_activity(self, repo: Repository) -> RequirementCheck:
        """Check for recent activity in repository."""
        has_activity = self.client.has_recent_activity(repo, ACTIVITY_DAYS)
        
        if has_activity:
            return RequirementCheck(
                name="Recent Activity",
                passed=True,
                message=f"Active in last {ACTIVITY_DAYS} days",
                severity="warning"
            )
        else:
            return RequirementCheck(
                name="Recent Activity",
                passed=False,
                message=f"No activity in last {ACTIVITY_DAYS} days",
                severity="warning"
            )

    def _check_has_testing(self, repo: Repository) -> RequirementCheck:
        """Check if repository has testing practices."""
        has_tests = self.client.check_any_file_exists(repo, TESTING_FILES)
        
        if has_tests:
            return RequirementCheck(
                name="Testing Practices",
                passed=True,
                message="Testing files/directories found",
                severity="warning"
            )
        else:
            return RequirementCheck(
                name="Testing Practices",
                passed=False,
                message="No testing files/directories detected",
                severity="warning"
            )

    def _check_build_instructions(self, repo: Repository) -> RequirementCheck:
        """Check if repository has build/setup instructions."""
        has_build_files = self.client.check_any_file_exists(repo, BUILD_FILES)
        
        if has_build_files:
            return RequirementCheck(
                name="Build Instructions",
                passed=True,
                message="Build/setup files found",
                severity="error"
            )
        else:
            return RequirementCheck(
                name="Build Instructions",
                passed=False,
                message="No clear build/setup instructions found",
                severity="error"
            )

    def _check_code_quality_indicators(self, repo: Repository) -> RequirementCheck:
        """Check for code quality tools (linters, formatters)."""
        has_quality_tools = self.client.check_any_file_exists(repo, LINTER_FILES)
        
        stars = repo.stargazers_count
        
        # If it's a fork, always use parent's stars for evaluation
        if repo.fork:
            try:
                parent = repo.parent
                if parent:
                    stars = parent.stargazers_count
            except:
                pass
        
        if has_quality_tools:
            return RequirementCheck(
                name="Code Quality",
                passed=True,
                message=f"Quality tools found (linters/formatters)",
                severity="warning"
            )
        elif stars >= 50:
            return RequirementCheck(
                name="Code Quality",
                passed=True,
                message=f"High community validation ({stars} stars)",
                severity="warning"
            )
        else:
            return RequirementCheck(
                name="Code Quality",
                passed=False,
                message=f"No quality tools and limited stars ({stars})",
                severity="warning"
            )

    def _check_network_usage(self, repo: Repository) -> RequirementCheck:
        """Check if repository makes extensive network/port usage."""
        # This is a heuristic check - look for common server patterns
        try:
            readme = repo.get_readme()
            readme_content = readme.decoded_content.decode('utf-8').lower() if readme.decoded_content else ""
            
            network_keywords = ['server', 'port', 'host', 'api endpoint', 'microservice']
            found_keywords = [kw for kw in network_keywords if readme_content and kw in readme_content]
            
            if len(found_keywords) >= 3:
                return RequirementCheck(
                    name="Network Usage",
                    passed=False,
                    message=f"May require extensive network access (keywords: {', '.join(found_keywords)})",
                    severity="warning"
                )
        except Exception:
            pass  # If README can't be fetched, skip this check
        
        return RequirementCheck(
            name="Network Usage",
            passed=True,
            message="No obvious extensive network usage detected",
            severity="warning"
        )

    def _check_complexity(self, repo: Repository) -> RequirementCheck:
        """Check if repository has sufficient complexity."""
        try:
            # Get repository contents to count files and directories
            contents = repo.get_contents("")
            files_count = 0
            dirs_count = 0
            
            items_to_check = list(contents) if isinstance(contents, list) else [contents]
            checked_items = set()
            
            while items_to_check and files_count < 150:  # Limit to avoid too many API calls
                item = items_to_check.pop(0)
                
                # Avoid checking same path twice
                if item.path in checked_items:
                    continue
                checked_items.add(item.path)
                
                # Skip common non-code directories
                skip_dirs = ['.git', '.github', 'node_modules', '__pycache__', '.pytest_cache', 
                            'dist', 'build', '.venv', 'venv', 'htmlcov']
                if any(skip in item.path for skip in skip_dirs):
                    continue
                
                if item.type == "dir":
                    dirs_count += 1
                    try:
                        sub_contents = repo.get_contents(item.path)
                        sub_items = list(sub_contents) if isinstance(sub_contents, list) else [sub_contents]
                        items_to_check.extend(sub_items)
                    except:
                        pass
                else:
                    files_count += 1
            
            # Check if meets minimum complexity
            if files_count >= MIN_FILES and dirs_count >= MIN_DIRECTORIES:
                return RequirementCheck(
                    name="Project Complexity",
                    passed=True,
                    message=f"Sufficient complexity ({files_count} files, {dirs_count} directories)",
                    severity="error"
                )
            else:
                return RequirementCheck(
                    name="Project Complexity",
                    passed=False,
                    message=f"Too simple: {files_count} files, {dirs_count} dirs (need {MIN_FILES}+ files, {MIN_DIRECTORIES}+ dirs)",
                    severity="error"
                )
        except Exception as e:
            # If we can't check complexity, fail to be safe
            return RequirementCheck(
                name="Project Complexity",
                passed=False,
                message=f"Could not verify complexity: {str(e)}",
                severity="error"
            )

    def _check_not_vibe_coded(self, repo: Repository) -> RequirementCheck:
        """Check if repository is not a quickly vibe-coded project."""
        red_flags = []
        
        try:
            # Get stars (use parent's if fork)
            stars = repo.stargazers_count
            if repo.fork:
                try:
                    parent = repo.parent
                    if parent:
                        stars = parent.stargazers_count
                except:
                    pass
            
            # Check 1: Very recent creation with all commits in short timespan
            age_days = (datetime.now(timezone.utc) - repo.created_at).days
            if age_days < 30:
                # Check commit distribution
                try:
                    commits = list(repo.get_commits()[:20])
                    if len(commits) >= 10:
                        first_commit_date = commits[-1].commit.author.date
                        last_commit_date = commits[0].commit.author.date
                        commit_span_days = (last_commit_date - first_commit_date).days
                        
                        if commit_span_days < 7:
                            red_flags.append("All commits in < 7 days")
                except:
                    pass
            
            # Check 2: No description
            if not repo.description or len(repo.description.strip()) < 20:
                red_flags.append("No proper description")
            
            # Check 3: No releases/tags
            try:
                releases = repo.get_releases().totalCount
                if releases == 0 and stars < 100:
                    red_flags.append("No releases")
            except:
                pass
            
            # Check 4: README too short
            try:
                readme = repo.get_readme()
                if readme.size < 500:  # Less than 500 bytes
                    red_flags.append("Minimal README")
            except:
                red_flags.append("No README")
            
            # Check 5: Very few stars for project age
            if age_days > 90 and stars < 5:
                red_flags.append("Old project with <5 stars")
            
            # Decision
            if len(red_flags) >= 3:
                return RequirementCheck(
                    name="Quality Project",
                    passed=False,
                    message=f"Appears vibe-coded: {', '.join(red_flags)}",
                    severity="error"
                )
            elif len(red_flags) >= 1:
                return RequirementCheck(
                    name="Quality Project",
                    passed=True,
                    message=f"Some concerns: {', '.join(red_flags)}",
                    severity="warning"
                )
            else:
                return RequirementCheck(
                    name="Quality Project",
                    passed=True,
                    message="Appears well-maintained",
                    severity="warning"
                )
        except Exception as e:
            return RequirementCheck(
                name="Quality Project",
                passed=True,
                message="Could not fully verify",
                severity="warning"
            )

    def _check_size(self, repo: Repository) -> RequirementCheck:
        """Check if repository size is reasonable."""
        try:
            size_kb = repo.size  # GitHub API returns size in KB
            size_mb = size_kb / 1024
            
            if size_mb <= MAX_SIZE_MB:
                return RequirementCheck(
                    name="Repository Size",
                    passed=True,
                    message=f"Reasonable size ({size_mb:.1f} MB)",
                    severity="error"
                )
            else:
                return RequirementCheck(
                    name="Repository Size",
                    passed=False,
                    message=f"Too large: {size_mb:.1f} MB (max {MAX_SIZE_MB} MB)",
                    severity="error"
                )
        except Exception as e:
            return RequirementCheck(
                name="Repository Size",
                passed=True,
                message="Could not verify size",
                severity="warning"
            )

    def _calculate_score(self, checks: list[RequirementCheck]) -> float:
        """Calculate overall score from checks."""
        if not checks:
            return 0.0
        
        # Weight errors more than warnings
        total_weight = 0
        earned_weight = 0
        
        for check in checks:
            weight = 10 if check.severity == "error" else 5
            total_weight += weight
            if check.passed:
                earned_weight += weight
        
        return (earned_weight / total_weight) * 100 if total_weight > 0 else 0

    def _generate_summary(self, checks: list[RequirementCheck], score: float) -> str:
        """Generate a text summary of the verification."""
        failed_errors = [c for c in checks if not c.passed and c.severity == "error"]
        failed_warnings = [c for c in checks if not c.passed and c.severity == "warning"]
        
        if score >= 90:
            quality = "Excellent"
        elif score >= 70:
            quality = "Good"
        elif score >= 50:
            quality = "Fair"
        else:
            quality = "Poor"
        
        summary = f"{quality} quality (Score: {score:.1f}/100). "
        
        if failed_errors:
            summary += f"Failed {len(failed_errors)} critical requirement(s). "
        if failed_warnings:
            summary += f"{len(failed_warnings)} warning(s). "
        
        if score >= 75:
            summary += "Repository meets minimum requirements."
        else:
            summary += "Repository does not meet minimum requirements."
        
        return summary
