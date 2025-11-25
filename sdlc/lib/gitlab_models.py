"""Data types for GitLab API responses.

This module contains Pydantic models for GitLab-specific data structures
including issues, merge requests, notes (comments), and related entities.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class GitLabUser(BaseModel):
    """GitLab user model."""

    id: int
    username: str
    name: Optional[str] = None
    state: Optional[str] = None
    web_url: Optional[str] = None


class GitLabLabel(BaseModel):
    """GitLab label model."""

    id: int
    name: str
    color: str
    description: Optional[str] = None


class GitLabMilestone(BaseModel):
    """GitLab milestone model."""

    id: int
    iid: int
    title: str
    description: Optional[str] = None
    state: str
    due_date: Optional[str] = None
    web_url: Optional[str] = None


class GitLabNote(BaseModel):
    """GitLab note (comment) model."""

    id: int
    body: str
    author: GitLabUser
    created_at: datetime
    updated_at: Optional[datetime] = None
    system: bool = False
    noteable_type: Optional[str] = None


class GitLabIssueListItem(BaseModel):
    """GitLab issue model for list responses (simplified)."""

    iid: int  # GitLab uses iid for project-scoped issue number
    title: str
    description: Optional[str] = None
    labels: List[str] = []  # GitLab returns labels as list of strings in list view
    created_at: datetime
    updated_at: datetime


class GitLabIssue(BaseModel):
    """GitLab issue model (full details)."""

    iid: int  # GitLab uses iid for project-scoped issue number
    title: str
    description: Optional[str] = None
    state: str
    author: GitLabUser
    assignees: List[GitLabUser] = []
    labels: List[str] = []  # GitLab returns labels as list of strings
    milestone: Optional[GitLabMilestone] = None
    notes: List[GitLabNote] = []  # GitLab calls comments "notes"
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    web_url: str

    @property
    def number(self) -> int:
        """Alias for iid to maintain compatibility with GitHub models."""
        return self.iid

    @property
    def body(self) -> Optional[str]:
        """Alias for description to maintain compatibility with GitHub models."""
        return self.description

    @property
    def url(self) -> str:
        """Alias for web_url to maintain compatibility with GitHub models."""
        return self.web_url


class GitLabMergeRequest(BaseModel):
    """GitLab merge request model."""

    iid: int  # Project-scoped MR number
    title: str
    description: Optional[str] = None
    state: str
    author: GitLabUser
    assignees: List[GitLabUser] = []
    labels: List[str] = []
    milestone: Optional[GitLabMilestone] = None
    source_branch: str
    target_branch: str
    web_url: str
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
