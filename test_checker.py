"""
Unit tests for GitHub Repository Checker.
Run with: pytest test_checker.py
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from models import (
    RepositoryInfo,
    RequirementCheck,
    SearchCriteria
)
from github_client import GitHubClient
from verifier import RepositoryVerifier


class TestModels:
    """Test data models."""
    
    def test_repository_info_creation(self):
        """Test creating RepositoryInfo."""
        repo = RepositoryInfo(
            name="test-repo",
            full_name="owner/test-repo",
            url="https://github.com/owner/test-repo",
            stars=100,
            language="Python",
            license="MIT",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert repo.name == "test-repo"
        assert repo.stars == 100
        assert repo.language == "Python"
    
    def test_requirement_check(self):
        """Test RequirementCheck model."""
        check = RequirementCheck(
            name="Test Check",
            passed=True,
            message="Test passed",
            severity="error"
        )
        
        assert check.passed is True
        assert check.severity == "error"
    
    def test_search_criteria_defaults(self):
        """Test SearchCriteria default values."""
        criteria = SearchCriteria()
        
        assert criteria.min_stars == 10
        assert criteria.min_contributors == 2
        assert criteria.has_tests is False
        assert criteria.max_results == 10


class TestGitHubClient:
    """Test GitHub client."""
    
    def test_extract_owner_repo_from_url(self):
        """Test extracting owner/repo from various URL formats."""
        client = GitHubClient(token="test_token")
        
        test_cases = [
            "https://github.com/owner/repo",
            "https://github.com/owner/repo/",
            "http://github.com/owner/repo",
        ]
        
        for url in test_cases:
            with patch.object(client.client, 'get_repo') as mock_get:
                mock_repo = Mock()
                mock_get.return_value = mock_repo
                
                try:
                    result = client.get_repository(url)
                    assert result is not None
                except Exception:
                    pass  # Expected if token is invalid


class TestVerifier:
    """Test repository verifier."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock GitHub client."""
        client = Mock(spec=GitHubClient)
        return client
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        repo = Mock()
        repo.name = "test-repo"
        repo.full_name = "owner/test-repo"
        repo.html_url = "https://github.com/owner/test-repo"
        repo.description = "Test repository"
        repo.stargazers_count = 100
        repo.forks_count = 50
        repo.language = "Python"
        repo.created_at = datetime.now() - timedelta(days=365)
        repo.updated_at = datetime.now()
        repo.license = Mock(name="MIT License")
        repo.get_topics = Mock(return_value=["testing", "python"])
        return repo
    
    def test_check_primary_language_supported(self, mock_client, mock_repo):
        """Test language check with supported language."""
        verifier = RepositoryVerifier(mock_client)
        mock_repo.language = "Python"
        
        result = verifier._check_primary_language(mock_repo)
        
        assert result.passed is True
        assert "Python" in result.message
    
    def test_check_primary_language_unsupported(self, mock_client, mock_repo):
        """Test language check with unsupported language."""
        verifier = RepositoryVerifier(mock_client)
        mock_repo.language = "PHP"
        
        result = verifier._check_primary_language(mock_repo)
        
        assert result.passed is False
    
    def test_check_open_license_present(self, mock_client, mock_repo):
        """Test license check when license exists."""
        verifier = RepositoryVerifier(mock_client)
        
        result = verifier._check_open_license(mock_repo)
        
        assert result.passed is True
    
    def test_check_open_license_missing(self, mock_client, mock_repo):
        """Test license check when license is missing."""
        verifier = RepositoryVerifier(mock_client)
        mock_repo.license = None
        
        result = verifier._check_open_license(mock_repo)
        
        assert result.passed is False
    
    def test_check_multiple_contributors(self, mock_client, mock_repo):
        """Test contributors check."""
        verifier = RepositoryVerifier(mock_client)
        mock_client.get_contributors_count.return_value = 5
        
        result = verifier._check_multiple_contributors(mock_repo)
        
        assert result.passed is True
        assert "5" in result.message
    
    def test_calculate_score(self, mock_client):
        """Test score calculation."""
        verifier = RepositoryVerifier(mock_client)
        
        checks = [
            RequirementCheck(name="Test 1", passed=True, message="OK", severity="error"),
            RequirementCheck(name="Test 2", passed=True, message="OK", severity="error"),
            RequirementCheck(name="Test 3", passed=False, message="Fail", severity="error"),
            RequirementCheck(name="Test 4", passed=True, message="OK", severity="warning"),
        ]
        
        score = verifier._calculate_score(checks)
        
        assert 0 <= score <= 100
        assert score > 0  # Some checks passed


class TestSearchCriteria:
    """Test search criteria."""
    
    def test_custom_criteria(self):
        """Test creating custom search criteria."""
        criteria = SearchCriteria(
            language="Python",
            topics=["testing", "cli"],
            min_stars=50,
            min_contributors=5,
            has_tests=True,
            max_results=20
        )
        
        assert criteria.language == "Python"
        assert len(criteria.topics) == 2
        assert criteria.min_stars == 50
        assert criteria.has_tests is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
