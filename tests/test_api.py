from app.models import JobSource
from app.scraper import parse_jobs


def test_authentication(client):
    assert client.get("/api/v1/jobs").status_code == 401
    assert client.post("/api/v1/auth/register", json={"name": "User", "email": "user@example.com", "password": "password123"}).status_code == 201


def test_create_and_list_source(client, auth):
    payload = {
        "name": "Example Careers",
        "url": "https://example.com/careers",
        "job_selector": ".job",
        "title_selector": ".title",
        "company_selector": ".company",
        "location_selector": ".location",
        "link_selector": "a",
    }
    created = client.post("/api/v1/sources", headers=auth, json=payload)
    assert created.status_code == 201
    assert client.get("/api/v1/sources", headers=auth).json()[0]["name"] == "Example Careers"


def test_html_parser_extracts_jobs():
    source = JobSource(
        name="Demo", url="https://example.com/jobs/", job_selector=".job", title_selector=".title",
        company_selector=".company", location_selector=".location", link_selector="a", description_selector=".description"
    )
    html = """
    <article class="job"><a href="python-engineer"><h2 class="title">Python Engineer</h2></a>
    <span class="company">Acme</span><span class="location">Remote</span>
    <p class="description">Build APIs</p></article>
    """
    jobs = parse_jobs(html, source)
    assert len(jobs) == 1
    assert jobs[0].title == "Python Engineer"
    assert jobs[0].url == "https://example.com/jobs/python-engineer"
    assert jobs[0].location == "Remote"


def test_duplicate_source_is_rejected(client, auth):
    payload = {"name": "Duplicate", "url": "https://example.com/jobs", "job_selector": ".job", "title_selector": ".title", "link_selector": "a"}
    assert client.post("/api/v1/sources", headers=auth, json=payload).status_code == 201
    assert client.post("/api/v1/sources", headers=auth, json=payload).status_code == 409


def test_stats(client, auth):
    response = client.get("/api/v1/stats", headers=auth)
    assert response.status_code == 200
    assert response.json()["total_jobs"] == 0
