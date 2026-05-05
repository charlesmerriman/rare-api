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
def regular_user(db):
    return RareUser.objects.create_user(
        username="bob",
        password="pass123",
        email="bob@example.com",
        is_active=True,
    )


@pytest.fixture
def other_user(db):
    return RareUser.objects.create_user(
        username="carol",
        password="pass123",
        email="carol@example.com",
        is_active=True,
    )


@pytest.fixture
def category(db):
    return Category.objects.create(label="Tech")


def make_post(author, category, title="A Post", approved=True, publication_date="2025-01-01"):
    return Post.objects.create(
        user=author,
        category=category,
        title=title,
        publication_date=publication_date,
        content="Content",
        approved=approved,
    )


def authed_client(api_client, user):
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


class TestPostList:
    def test_approved_posts_visible_to_everyone(self, api_client, regular_user, other_user, category):
        make_post(other_user, category, title="Other's approved post")
        client = authed_client(api_client, regular_user)
        res = client.get("/posts")
        assert res.status_code == 200
        titles = [p["title"] for p in res.json()]
        assert "Other's approved post" in titles

    def test_own_unapproved_post_visible_to_author(self, api_client, regular_user, category):
        make_post(regular_user, category, title="My draft", approved=False)
        client = authed_client(api_client, regular_user)
        res = client.get("/posts")
        assert res.status_code == 200
        titles = [p["title"] for p in res.json()]
        assert "My draft" in titles

    def test_own_unapproved_post_has_approved_false(self, api_client, regular_user, category):
        make_post(regular_user, category, title="My draft", approved=False)
        client = authed_client(api_client, regular_user)
        res = client.get("/posts")
        draft = next(p for p in res.json() if p["title"] == "My draft")
        assert draft["approved"] is False

    def test_other_users_unapproved_posts_hidden(self, api_client, regular_user, other_user, category):
        make_post(other_user, category, title="Carol's draft", approved=False)
        client = authed_client(api_client, regular_user)
        res = client.get("/posts")
        assert res.status_code == 200
        titles = [p["title"] for p in res.json()]
        assert "Carol's draft" not in titles

    def test_requires_authentication(self, api_client):
        res = api_client.get("/posts")
        assert res.status_code in (401, 403)
