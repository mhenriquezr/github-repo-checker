"""Data models for repository verification."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class RepositoryInfo(BaseModel):
    """Repository basic information."""
    name: str
    full_name: str
    url: str
    description: Optional[str] = None
    stars: int = 0
    forks: int = 0
    language: Optional[str] = None
    license: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    topics: list[str] = Field(default_factory=list)


class RequirementCheck(BaseModel):
    """Single requirement check result."""
    name: str
    passed: bool
    message: str
    severity: str = "error"  # error, warning, info


class VerificationReport(BaseModel):
    """Complete verification report for a repository."""
    repository: RepositoryInfo
    checks: list[RequirementCheck]
    score: float  # 0-100
    passed: bool
    summary: str
    timestamp: datetime = Field(default_factory=datetime.now)

    def get_failed_checks(self) -> list[RequirementCheck]:
        """Get all failed requirement checks."""
        return [check for check in self.checks if not check.passed and check.severity == "error"]

    def get_warnings(self) -> list[RequirementCheck]:
        """Get all warning checks."""
        return [check for check in self.checks if not check.passed and check.severity == "warning"]


class SearchCriteria(BaseModel):
    """Search criteria for finding repositories."""
    language: Optional[str] = None
    topics: list[str] = Field(default_factory=list)
    min_stars: int = 10
    min_contributors: int = 2
    has_tests: bool = False
    has_license: bool = True
    max_results: int = 10
