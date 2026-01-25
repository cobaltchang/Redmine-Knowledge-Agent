"""Data models for Redmine entities.

This module defines Pydantic models for all Redmine API entities,
including issues, projects, users, and attachments.
"""

from datetime import datetime
from typing import Any, Iterator, Optional, Self

from pydantic import BaseModel, Field, field_validator


class Project(BaseModel):
    """Represents a Redmine project.
    
    Attributes:
        id: The unique project identifier.
        name: The project name.
    """
    
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    
    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate that name is not empty or whitespace only."""
        if not v.strip():
            raise ValueError("Project name cannot be empty")
        return v


class Tracker(BaseModel):
    """Represents a Redmine tracker (e.g., Bug, Feature, Task).
    
    Attributes:
        id: The unique tracker identifier.
        name: The tracker name.
    """
    
    id: int = Field(gt=0)
    name: str = Field(min_length=1)


class Status(BaseModel):
    """Represents an issue status (e.g., New, In Progress, Closed).
    
    Attributes:
        id: The unique status identifier.
        name: The status name.
    """
    
    id: int = Field(gt=0)
    name: str = Field(min_length=1)


class Priority(BaseModel):
    """Represents an issue priority (e.g., Low, Normal, High).
    
    Attributes:
        id: The unique priority identifier.
        name: The priority name.
    """
    
    id: int = Field(gt=0)
    name: str = Field(min_length=1)


class User(BaseModel):
    """Represents a Redmine user.
    
    Attributes:
        id: The unique user identifier.
        name: The user's display name.
    """
    
    id: int = Field(gt=0)
    name: str = Field(min_length=1)


class Attachment(BaseModel):
    """Represents a file attachment on an issue.
    
    Attributes:
        id: The unique attachment identifier.
        filename: The original filename.
        filesize: The file size in bytes.
        content_type: The MIME type of the file.
        content_url: The URL to download the attachment.
        created_on: When the attachment was uploaded.
        author: The user who uploaded the attachment.
    """
    
    id: int = Field(gt=0)
    filename: str = Field(min_length=1)
    filesize: int = Field(ge=0)
    content_type: str
    content_url: str
    created_on: datetime
    author: User
    
    @property
    def is_image(self) -> bool:
        """Check if the attachment is an image file.
        
        Returns:
            True if the content type indicates an image.
        """
        return self.content_type.startswith("image/")
    
    @property
    def is_pdf(self) -> bool:
        """Check if the attachment is a PDF file.
        
        Returns:
            True if the content type indicates a PDF.
        """
        return self.content_type == "application/pdf"


class Issue(BaseModel):
    """Represents a Redmine issue.
    
    Attributes:
        id: The unique issue identifier.
        subject: The issue subject/title.
        description: The issue description (may be None).
        project: The project this issue belongs to.
        tracker: The issue tracker type.
        status: The current status.
        priority: The issue priority.
        author: The user who created the issue.
        assigned_to: The user assigned to the issue (may be None).
        created_on: When the issue was created.
        updated_on: When the issue was last updated.
        attachments: List of file attachments.
    """
    
    id: int = Field(gt=0)
    subject: str = Field(min_length=1)
    description: Optional[str] = None
    project: Project
    tracker: Tracker
    status: Status
    priority: Priority
    author: User
    assigned_to: Optional[User] = None
    created_on: datetime
    updated_on: datetime
    attachments: list[Attachment] = Field(default_factory=list)
    
    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v: str) -> str:
        """Validate that subject is not empty or whitespace only."""
        if not v.strip():
            raise ValueError("Issue subject cannot be empty")
        return v
    
    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> Self:
        """Create an Issue from a Redmine API response.
        
        Args:
            data: The issue data from the API response.
            
        Returns:
            An Issue instance.
        """
        attachments = []
        for att_data in data.get("attachments", []):
            attachments.append(Attachment(
                id=att_data["id"],
                filename=att_data["filename"],
                filesize=att_data["filesize"],
                content_type=att_data["content_type"],
                content_url=att_data["content_url"],
                created_on=att_data["created_on"],
                author=User(
                    id=att_data["author"]["id"],
                    name=att_data["author"]["name"],
                ),
            ))
        
        return cls(
            id=data["id"],
            subject=data["subject"],
            description=data.get("description"),
            project=Project(
                id=data["project"]["id"],
                name=data["project"]["name"],
            ),
            tracker=Tracker(
                id=data["tracker"]["id"],
                name=data["tracker"]["name"],
            ),
            status=Status(
                id=data["status"]["id"],
                name=data["status"]["name"],
            ),
            priority=Priority(
                id=data["priority"]["id"],
                name=data["priority"]["name"],
            ),
            author=User(
                id=data["author"]["id"],
                name=data["author"]["name"],
            ),
            assigned_to=(
                User(
                    id=data["assigned_to"]["id"],
                    name=data["assigned_to"]["name"],
                )
                if data.get("assigned_to")
                else None
            ),
            created_on=data["created_on"],
            updated_on=data["updated_on"],
            attachments=attachments,
        )


class IssueList(BaseModel):
    """Represents a paginated list of issues from the API.
    
    Attributes:
        issues: The list of issues in this page.
        total_count: Total number of issues matching the query.
        offset: The offset of this page (0-based).
        limit: The maximum number of issues per page.
    """
    
    issues: list[Issue]
    total_count: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(gt=0)
    
    @property
    def has_more(self) -> bool:
        """Check if there are more pages available.
        
        Returns:
            True if there are more issues beyond this page.
        """
        return self.offset + len(self.issues) < self.total_count
    
    @property
    def next_offset(self) -> int:
        """Get the offset for the next page.
        
        Returns:
            The offset value to use for fetching the next page.
        """
        return self.offset + self.limit
    
    def __iter__(self) -> Iterator[Issue]:
        """Allow iteration over issues in the list."""
        return iter(self.issues)
    
    def __len__(self) -> int:
        """Return the number of issues in this page."""
        return len(self.issues)
    
    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> Self:
        """Create an IssueList from a Redmine API response.
        
        Args:
            data: The response data from the API.
            
        Returns:
            An IssueList instance.
        """
        issues = [Issue.from_api_response(issue_data) for issue_data in data["issues"]]
        
        return cls(
            issues=issues,
            total_count=data["total_count"],
            offset=data["offset"],
            limit=data["limit"],
        )
