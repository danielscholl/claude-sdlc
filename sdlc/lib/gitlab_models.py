"""Data types for GitLab API responses.

This module contains Pydantic models for GitLab-specific data structures
including issues, merge requests, notes (comments), and related entities.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


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
    created_at: datetime = Field(alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")
    system: bool = False
    noteable_type: Optional[str] = None

    class Config:
        populate_by_name = True


class GitLabIssueListItem(BaseModel):
    """GitLab issue model for list responses (simplified)."""

    iid: int  # GitLab uses iid for project-scoped issue number
    title: str
    description: Optional[str] = None
    labels: List[str] = []  # GitLab returns labels as list of strings in list view
    created_at: datetime = Field(alias="created_at")
    updated_at: datetime = Field(alias="updated_at")

    class Config:
        populate_by_name = True


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
    created_at: datetime = Field(alias="created_at")
    updated_at: datetime = Field(alias="updated_at")
    closed_at: Optional[datetime] = Field(None, alias="closed_at")
    web_url: str

    class Config:
        populate_by_name = True

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
    created_at: datetime = Field(alias="created_at")
    updated_at: datetime = Field(alias="updated_at")
    merged_at: Optional[datetime] = Field(None, alias="merged_at")
    closed_at: Optional[datetime] = Field(None, alias="closed_at")

    class Config:
        populate_by_name = True
