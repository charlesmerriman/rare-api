import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rareapi.models import RareUser
from rareapi.models.post import Post
from rareapi.models.category import Category


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def diana(db):
    return RareUser.objects.create_user(
        username="diana",
        password="pass123",
        email="diana@example.com",
        is_active=True,
    )


@pytest.fixture
def alice(db):
    return RareUser.objects.create_user(
        username="alice",
        password="pass123",
        email="alice@example.com",
        is_active=True,
    )


@pytest.fixture
def category(db):
    return Category.objects.create(label="Tech")


def make_post(author, category, title="A Post", approved=True):
    return Post.objects.create(
        user=author,
        category=category,
        title=title,
        publication_date="2025-01-01",
        content="Content",
        approved=approved,
    )


def authed_client(api_client, user):
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


class TestSearchPosts:
    def test_q_matches_title(self, api_client, diana, category):
        make_post(diana, category, title="Python tips")
        make_post(diana, category, title="Django guide")
        client = authed_client(api_client, diana)
        res = client.get("/posts/search?q=python")
        assert res.status_code == 200
        titles = [p["title"] for p in res.json()]
        assert "Python tips" in titles
        assert "Django guide" not in titles

    def test_author_filter_by_username(self, api_client, diana, alice, category):
        make_post(diana, category, title="Diana post")
        make_post(alice, category, title="Alice post")
        client = authed_client(api_client, diana)
        res = client.get("/posts/search?author=diana")
        assert res.status_code == 200
        titles = [p["title"] for p in res.json()]
        assert "Diana post" in titles
        assert "Alice post" not in titles

    def test_author_filter_case_insensitive(self, api_client, diana, category):
        make_post(diana, category, title="Diana post")
        client = authed_client(api_client, diana)
        res = client.get("/posts/search?author=DIANA")
        titles = [p["title"] for p in res.json()]
        assert "Diana post" in titles

    def test_q_and_author_combined(self, api_client, diana, alice, category):
        make_post(diana, category, title="Python tips")
        make_post(diana, category, title="Django guide")
        make_post(alice, category, title="Python tips")
        client = authed_client(api_client, diana)
        res = client.get("/posts/search?q=python&author=diana")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["title"] == "Python tips"
        assert data[0]["user"]["username"] == "diana"

    def test_no_params_returns_empty(self, api_client, diana, category):
        make_post(diana, category, title="Anything")
        client = authed_client(api_client, diana)
        res = client.get("/posts/search")
        assert res.status_code == 200
        assert res.json() == []

    def test_unapproved_posts_excluded(self, api_client, diana, category):
        make_post(diana, category, title="Draft", approved=False)
        client = authed_client(api_client, diana)
        res = client.get("/posts/search?author=diana")
        assert res.json() == []

    def test_requires_authentication(self, api_client):
        res = api_client.get("/posts/search?q=anything")
        assert res.status_code in (401, 403)
