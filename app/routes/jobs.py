import math
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import distinct, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Job, JobSource, User
from app.schemas import JobPage, JobRead, ScrapeResult, SourceCreate, SourceRead, StatsRead
from app.scraper import fetch_source, parse_jobs

router = APIRouter(tags=["Jobs"])


@router.post("/sources", response_model=SourceRead, status_code=201)
def create_source(payload: SourceCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    source = JobSource(**payload.model_dump(mode="json"))
    db.add(source)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Source name already exists")
    db.refresh(source)
    return source


@router.get("/sources", response_model=list[SourceRead])
def list_sources(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list(db.scalars(select(JobSource).order_by(JobSource.name)))


@router.delete("/sources/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    source = db.get(JobSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return Response(status_code=204)


@router.post("/sources/{source_id}/scrape", response_model=ScrapeResult)
async def scrape_source(source_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    source = db.get(JobSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if not source.is_active:
        raise HTTPException(status_code=400, detail="Source is inactive")
    try:
        html = await fetch_source(source)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Scraping failed: {exc}")
    scraped = parse_jobs(html, source)
    now = datetime.now(timezone.utc)
    seen: set[str] = set()
    created = updated = 0
    for item in scraped:
        seen.add(item.external_key)
        job = db.scalar(select(Job).where(Job.source_id == source.id, Job.external_key == item.external_key))
        if job is None:
            db.add(Job(source_id=source.id, **item.__dict__, last_seen_at=now))
            created += 1
        else:
            for key, value in item.__dict__.items():
                setattr(job, key, value)
            job.is_active = True
            job.last_seen_at = now
            updated += 1
    deactivated = 0
    active_keys = list(seen)
    if active_keys:
        result = db.execute(
            update(Job)
            .where(Job.source_id == source.id, Job.is_active.is_(True), Job.external_key.not_in(active_keys))
            .values(is_active=False)
        )
        deactivated = result.rowcount or 0
    source.last_scraped_at = now
    db.commit()
    return ScrapeResult(source_id=source.id, discovered=len(scraped), created=created, updated=updated, deactivated=deactivated)


@router.get("/jobs", response_model=JobPage)
def list_jobs(
    search: str | None = Query(default=None, max_length=200),
    company: str | None = Query(default=None, max_length=200),
    location: str | None = Query(default=None, max_length=200),
    source_id: int | None = None,
    active_only: bool = True,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    filters = []
    if active_only:
        filters.append(Job.is_active.is_(True))
    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(Job.title.ilike(term), Job.description.ilike(term), Job.company.ilike(term)))
    if company:
        filters.append(Job.company.ilike(f"%{company.strip()}%"))
    if location:
        filters.append(Job.location.ilike(f"%{location.strip()}%"))
    if source_id is not None:
        filters.append(Job.source_id == source_id)
    total = db.scalar(select(func.count()).select_from(Job).where(*filters)) or 0
    items = list(db.scalars(
        select(Job).where(*filters).order_by(Job.last_seen_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ))
    return JobPage(items=items, total=total, page=page, page_size=page_size, pages=math.ceil(total / page_size) if total else 0)


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/stats", response_model=StatsRead)
def stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return StatsRead(
        total_jobs=db.scalar(select(func.count()).select_from(Job)) or 0,
        active_jobs=db.scalar(select(func.count()).select_from(Job).where(Job.is_active.is_(True))) or 0,
        total_sources=db.scalar(select(func.count()).select_from(JobSource)) or 0,
        active_sources=db.scalar(select(func.count()).select_from(JobSource).where(JobSource.is_active.is_(True))) or 0,
        unique_companies=db.scalar(select(func.count(distinct(Job.company))).where(Job.company.is_not(None))) or 0,
        unique_locations=db.scalar(select(func.count(distinct(Job.location))).where(Job.location.is_not(None))) or 0,
    )
