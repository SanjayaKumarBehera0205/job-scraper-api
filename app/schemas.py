from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    url: HttpUrl
    job_selector: str = Field(min_length=1, max_length=300)
    title_selector: str = Field(min_length=1, max_length=300)
    company_selector: str | None = Field(default=None, max_length=300)
    location_selector: str | None = Field(default=None, max_length=300)
    link_selector: str = Field(default="a", min_length=1, max_length=300)
    description_selector: str | None = Field(default=None, max_length=300)


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    url: str
    job_selector: str
    title_selector: str
    company_selector: str | None
    location_selector: str | None
    link_selector: str
    description_selector: str | None
    is_active: bool
    last_scraped_at: datetime | None
    created_at: datetime


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_id: int
    title: str
    company: str | None
    location: str | None
    url: str
    description: str | None
    is_active: bool
    first_seen_at: datetime
    last_seen_at: datetime


class JobPage(BaseModel):
    items: list[JobRead]
    total: int
    page: int
    page_size: int
    pages: int


class ScrapeResult(BaseModel):
    source_id: int
    discovered: int
    created: int
    updated: int
    deactivated: int


class StatsRead(BaseModel):
    total_jobs: int
    active_jobs: int
    total_sources: int
    active_sources: int
    unique_companies: int
    unique_locations: int
