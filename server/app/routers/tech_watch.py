from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pydantic import BaseModel, field_validator
from typing import Optional

from app.db import get_session
from app.deps import verify_webhook_secret
from app.models.tables import TechArticle, TechTag
from app.utils.time import utcnow_naive

router = APIRouter(prefix="/tech-watch", tags=["tech-watch"])


class ArticleIn(BaseModel):
    url: str
    title: str
    source: str
    published_at: Optional[datetime] = None
    priority: int = 0

    @field_validator("published_at", mode="before")
    @classmethod
    def normalize_date(cls, v: object) -> object:
        if not v:
            return None
        if isinstance(v, datetime):
            return v
        s = str(v)
        try:
            return parsedate_to_datetime(s).replace(tzinfo=None)
        except Exception:
            pass
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None


class ArticleOut(BaseModel):
    id: int
    url: str
    title: str
    source: str
    priority: int
    interest_score: Optional[int]
    published_at: Optional[datetime]
    summary: Optional[str]
    summarized: bool
    tags: Optional[list[str]]
    tried_at: Optional[datetime]
    error: Optional[str]
    created_at: datetime


@router.post("/articles", response_model=ArticleOut, status_code=201, dependencies=[Depends(verify_webhook_secret)])
def receive_article(payload: ArticleIn, session: Session = Depends(get_session)):
    article = TechArticle(
        url=payload.url,
        title=payload.title,
        source=payload.source,
        published_at=payload.published_at,
        priority=payload.priority,
    )
    session.add(article)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "ARTICLE_ALREADY_EXISTS", "message": "Article with this URL already exists.", "fields": {"url": "duplicate"}},
        )
    session.refresh(article)
    return article


class BatchResult(BaseModel):
    inserted: int
    skipped: int


@router.post("/articles/batch", response_model=BatchResult, dependencies=[Depends(verify_webhook_secret)])
def receive_articles_batch(payload: list[ArticleIn], session: Session = Depends(get_session)):
    inserted = 0
    skipped = 0
    for article_in in payload:
        try:
            with session.begin_nested():
                session.add(TechArticle(
                    url=article_in.url,
                    title=article_in.title,
                    source=article_in.source,
                    published_at=article_in.published_at,
                    priority=article_in.priority,
                ))
            inserted += 1
        except IntegrityError:
            skipped += 1
    session.commit()
    return BatchResult(inserted=inserted, skipped=skipped)


@router.get("/articles", response_model=list[ArticleOut])
def list_articles(
    source: Optional[str] = None,
    has_summary: Optional[bool] = None,
    limit: Optional[int] = None,
    session: Session = Depends(get_session),
):
    stmt = select(TechArticle).order_by(TechArticle.published_at.desc())
    if source:
        stmt = stmt.where(TechArticle.source == source)
    if has_summary is False:
        stmt = stmt.where(TechArticle.summary.is_(None))
    elif has_summary is True:
        stmt = stmt.where(TechArticle.summary.isnot(None))
    if limit:
        stmt = stmt.limit(limit)
    return session.exec(stmt).all()


class TagOut(BaseModel):
    id: int
    name: str


@router.get("/tags", response_model=list[TagOut])
def list_tags(session: Session = Depends(get_session)):
    return session.exec(select(TechTag).order_by(TechTag.name)).all()


class TagStat(BaseModel):
    name: str
    count: int


@router.get("/tags/stats", response_model=list[TagStat])
def tags_stats(session: Session = Depends(get_session)):
    stmt = select(TechArticle).where(
        TechArticle.summarized == True,  # noqa: E712
        TechArticle.tags.isnot(None),
    )
    articles = session.exec(stmt).all()
    counts: dict[str, int] = {}
    for article in articles:
        if article.tags:
            for tag in article.tags:
                counts[tag] = counts.get(tag, 0) + 1
    return sorted(
        [TagStat(name=k, count=v) for k, v in counts.items()],
        key=lambda x: -x.count,
    )


@router.get("/articles/featured", response_model=list[ArticleOut])
def featured_articles(
    limit: int = 20,
    session: Session = Depends(get_session),
):
    since = utcnow_naive() - timedelta(days=7)
    stmt = (
        select(TechArticle)
        .where(TechArticle.summarized == True)  # noqa: E712
        .where(TechArticle.summary.isnot(None))
        .where(TechArticle.created_at >= since)
        .order_by(TechArticle.interest_score.desc(), TechArticle.published_at.desc())
        .limit(limit)
    )
    return session.exec(stmt).all()


class ArticleSummaryIn(BaseModel):
    interest_score: Optional[int] = None
    summary: Optional[str] = None
    tags: Optional[list[str]] = None
    error: Optional[str] = None


@router.patch("/articles/{article_id}", response_model=ArticleOut, dependencies=[Depends(verify_webhook_secret)])
def update_article_summary(
    article_id: int,
    payload: ArticleSummaryIn,
    session: Session = Depends(get_session),
):
    article = session.get(TechArticle, article_id)
    if not article:
        raise HTTPException(
            status_code=404,
            detail={"code": "ARTICLE_NOT_FOUND", "message": "Article not found.", "fields": {}},
        )

    article.tried_at = utcnow_naive()

    if payload.error is not None:
        article.error = payload.error
    else:
        if payload.interest_score is not None:
            article.interest_score = payload.interest_score
        if payload.summary is not None:
            article.summary = payload.summary
            article.summarized = True
        if payload.tags is not None:
            for tag_name in payload.tags:
                existing = session.exec(select(TechTag).where(TechTag.name == tag_name)).first()
                if not existing:
                    session.add(TechTag(name=tag_name))
            article.tags = payload.tags

    session.commit()
    session.refresh(article)
    return article


@router.get("/articles/next-to-summarize", response_model=ArticleOut)
def next_article_to_summarize(session: Session = Depends(get_session)):
    stmt = (
        select(TechArticle)
        .where(TechArticle.tried_at.is_(None))
        .order_by(TechArticle.priority.desc(), TechArticle.published_at.desc())
        .limit(1)
    )
    article = session.exec(stmt).first()
    if not article:
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_ARTICLE_TO_SUMMARIZE", "message": "No unsummarized article found.", "fields": {}},
        )
    return article
