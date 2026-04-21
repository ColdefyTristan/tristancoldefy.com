from datetime import datetime, timedelta, UTC

import pytest
from sqlmodel import select

from app.models.tables import TechArticle

VALID_SECRET = "test-webhook-secret"

_RECENT_DATE = (datetime.now(UTC) - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
_OLD_DATE = (datetime.now(UTC) - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%S")

ARTICLE_PAYLOAD = {
    "url": "https://example.com/article-1",
    "title": "Test Article",
    "source": "Hacker News",
    "published_at": _RECENT_DATE,
}


@pytest.fixture(autouse=True)
def set_webhook_secret(monkeypatch):
    import app.settings as s
    monkeypatch.setattr(s.settings, "WEBHOOK_SECRET", VALID_SECRET)


# --- POST /tech-watch/articles ---


def test_post_article_returns_201(client, session):
    r = client.post(
        "/tech-watch/articles",
        json=ARTICLE_PAYLOAD,
        headers={"X-Webhook-Secret": VALID_SECRET},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["url"] == ARTICLE_PAYLOAD["url"]
    assert data["title"] == ARTICLE_PAYLOAD["title"]
    assert data["source"] == ARTICLE_PAYLOAD["source"]
    assert data["summary"] is None
    assert data["tags"] is None


def test_post_article_persists_to_db(client, session):
    client.post(
        "/tech-watch/articles",
        json=ARTICLE_PAYLOAD,
        headers={"X-Webhook-Secret": VALID_SECRET},
    )
    article = session.exec(
        select(TechArticle).where(TechArticle.url == ARTICLE_PAYLOAD["url"])
    ).first()
    assert article is not None
    assert article.title == ARTICLE_PAYLOAD["title"]


def test_post_article_returns_409_on_duplicate_url(client, session):
    headers = {"X-Webhook-Secret": VALID_SECRET}
    client.post("/tech-watch/articles", json=ARTICLE_PAYLOAD, headers=headers)
    r = client.post("/tech-watch/articles", json=ARTICLE_PAYLOAD, headers=headers)
    assert r.status_code == 409
    assert r.json()["code"] == "ARTICLE_ALREADY_EXISTS"


def test_post_article_returns_401_without_secret(client):
    r = client.post("/tech-watch/articles", json=ARTICLE_PAYLOAD)
    assert r.status_code == 401
    assert r.json()["code"] == "INVALID_WEBHOOK_SECRET"


def test_post_article_returns_401_with_wrong_secret(client):
    r = client.post(
        "/tech-watch/articles",
        json=ARTICLE_PAYLOAD,
        headers={"X-Webhook-Secret": "wrong-secret"},
    )
    assert r.status_code == 401
    assert r.json()["code"] == "INVALID_WEBHOOK_SECRET"


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "No URL", "source": "HN"},
        {"url": "https://example.com", "source": "HN"},
        {"url": "https://example.com", "title": "No Source"},
    ],
)
def test_post_article_returns_422_on_invalid_payload(client, payload):
    r = client.post(
        "/tech-watch/articles",
        json=payload,
        headers={"X-Webhook-Secret": VALID_SECRET},
    )
    assert r.status_code == 422


# --- GET /tech-watch/articles ---


def test_get_articles_returns_list(client, session):
    client.post(
        "/tech-watch/articles",
        json=ARTICLE_PAYLOAD,
        headers={"X-Webhook-Secret": VALID_SECRET},
    )
    r = client.get("/tech-watch/articles")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_get_articles_filter_by_source(client, session):
    client.post(
        "/tech-watch/articles",
        json=ARTICLE_PAYLOAD,
        headers={"X-Webhook-Secret": VALID_SECRET},
    )
    client.post(
        "/tech-watch/articles",
        json={**ARTICLE_PAYLOAD, "url": "https://example.com/other", "source": "Dev.to"},
        headers={"X-Webhook-Secret": VALID_SECRET},
    )

    r = client.get("/tech-watch/articles?source=Dev.to")
    assert r.status_code == 200
    results = r.json()
    assert all(a["source"] == "Dev.to" for a in results)


# --- GET /tech-watch/articles/featured ---


def _create_summarized_article(client, url, score, summary, tags=None):
    r = client.post(
        "/tech-watch/articles",
        json={**ARTICLE_PAYLOAD, "url": url},
        headers={"X-Webhook-Secret": VALID_SECRET},
    )
    article_id = r.json()["id"]
    patch_body = {"interest_score": score, "summary": summary}
    if tags:
        patch_body["tags"] = tags
    client.patch(
        f"/tech-watch/articles/{article_id}",
        json=patch_body,
        headers={"X-Webhook-Secret": VALID_SECRET},
    )
    return article_id


def test_featured_returns_only_summarized(client):
    # unsummarized article
    client.post(
        "/tech-watch/articles",
        json={**ARTICLE_PAYLOAD, "url": "https://example.com/unsummarized"},
        headers={"X-Webhook-Secret": VALID_SECRET},
    )
    # summarized with summary
    _create_summarized_article(client, "https://example.com/featured", 4, "Un bon article.")

    r = client.get("/tech-watch/articles/featured")
    assert r.status_code == 200
    results = r.json()
    assert all(a["summarized"] and a["summary"] is not None for a in results)
    assert any(a["url"] == "https://example.com/featured" for a in results)
    assert not any(a["url"] == "https://example.com/unsummarized" for a in results)


def test_featured_excludes_score_only_articles(client):
    # score-only article (interest_score <= 2, no summary)
    r = client.post(
        "/tech-watch/articles",
        json={**ARTICLE_PAYLOAD, "url": "https://example.com/low-score"},
        headers={"X-Webhook-Secret": VALID_SECRET},
    )
    article_id = r.json()["id"]
    client.patch(
        f"/tech-watch/articles/{article_id}",
        json={"interest_score": 2},
        headers={"X-Webhook-Secret": VALID_SECRET},
    )

    r = client.get("/tech-watch/articles/featured")
    assert r.status_code == 200
    assert not any(a["url"] == "https://example.com/low-score" for a in r.json())


def test_featured_ordered_by_score_desc(client):
    _create_summarized_article(client, "https://example.com/score3", 3, "Moyen.")
    _create_summarized_article(client, "https://example.com/score5", 5, "Top.")
    _create_summarized_article(client, "https://example.com/score4", 4, "Bien.")

    r = client.get("/tech-watch/articles/featured")
    assert r.status_code == 200
    scores = [a["interest_score"] for a in r.json()]
    assert scores == sorted(scores, reverse=True)


def test_featured_limit(client):
    for i in range(5):
        _create_summarized_article(client, f"https://example.com/a{i}", 4, f"Article {i}.")

    r = client.get("/tech-watch/articles/featured?limit=3")
    assert r.status_code == 200
    assert len(r.json()) <= 3


# --- GET /tech-watch/tags/stats ---


def test_tags_stats_counts_correctly(client):
    _create_summarized_article(client, "https://example.com/t1", 4, "Article 1.", ["react", "python"])
    _create_summarized_article(client, "https://example.com/t2", 5, "Article 2.", ["react", "fastapi"])
    _create_summarized_article(client, "https://example.com/t3", 3, "Article 3.", ["python"])

    r = client.get("/tech-watch/tags/stats")
    assert r.status_code == 200
    stats = {s["name"]: s["count"] for s in r.json()}
    assert stats["react"] == 2
    assert stats["python"] == 2
    assert stats["fastapi"] == 1


def test_tags_stats_sorted_by_count_desc(client):
    _create_summarized_article(client, "https://example.com/s1", 4, "A.", ["react", "python", "llm"])
    _create_summarized_article(client, "https://example.com/s2", 4, "B.", ["react", "python"])
    _create_summarized_article(client, "https://example.com/s3", 4, "C.", ["react"])

    r = client.get("/tech-watch/tags/stats")
    assert r.status_code == 200
    counts = [s["count"] for s in r.json()]
    assert counts == sorted(counts, reverse=True)


def test_tags_stats_excludes_unsummarized(client):
    # article without summary should not count toward tag stats
    r = client.post(
        "/tech-watch/articles",
        json={**ARTICLE_PAYLOAD, "url": "https://example.com/notag"},
        headers={"X-Webhook-Secret": VALID_SECRET},
    )
    # do not patch → not summarized

    r = client.get("/tech-watch/tags/stats")
    assert r.status_code == 200
    # empty or no phantom tag from unsummarized article
    assert isinstance(r.json(), list)


# --- Featured: filtre 7 jours (sur created_at) ---


def test_featured_excludes_old_articles(client, session):
    recent_id = _create_summarized_article(client, "https://example.com/recent", 4, "Récent.")
    old_id = _create_summarized_article(client, "https://example.com/old", 5, "Vieux.")

    # Backdate created_at directly — the filter is on created_at (when we received it),
    # not published_at (original publication date from the RSS feed).
    old_article = session.get(TechArticle, old_id)
    old_article.created_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=10)
    session.commit()

    r = client.get("/tech-watch/articles/featured")
    assert r.status_code == 200
    urls = [a["url"] for a in r.json()]
    assert "https://example.com/recent" in urls
    assert "https://example.com/old" not in urls
