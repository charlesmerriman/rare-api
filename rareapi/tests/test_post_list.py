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


@pytest.fixture
def other_category(db):
    return Category.objects.create(label="Sports")


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
        titles = [p["title"] for p in res.json()["results"]]
        assert "Other's approved post" in titles

    def test_own_unapproved_post_visible_to_author(self, api_client, regular_user, category):
        make_post(regular_user, category, title="My draft", approved=False)
        client = authed_client(api_client, regular_user)
        res = client.get("/posts")
        assert res.status_code == 200
        titles = [p["title"] for p in res.json()["results"]]
        assert "My draft" in titles

    def test_own_unapproved_post_has_approved_false(self, api_client, regular_user, category):
        make_post(regular_user, category, title="My draft", approved=False)
        client = authed_client(api_client, regular_user)
        res = client.get("/posts")
        draft = next(p for p in res.json()["results"] if p["title"] == "My draft")
        assert draft["approved"] is False

    def test_other_users_unapproved_posts_hidden(self, api_client, regular_user, other_user, category):
        make_post(other_user, category, title="Carol's draft", approved=False)
        client = authed_client(api_client, regular_user)
        res = client.get("/posts")
        assert res.status_code == 200
        titles = [p["title"] for p in res.json()["results"]]
        assert "Carol's draft" not in titles

    def test_requires_authentication(self, api_client):
        res = api_client.get("/posts")
        assert res.status_code in (401, 403)


class TestPostListPagination:
    def test_response_has_envelope_fields(self, api_client, regular_user, category):
        make_post(regular_user, category)
        client = authed_client(api_client, regular_user)
        res = client.get("/posts")
        assert res.status_code == 200
        data = res.json()
        assert "count" in data
        assert "total_pages" in data
        assert "page" in data
        assert "results" in data

    def test_page_1_returns_at_most_10_posts(self, api_client, regular_user, category):
        # Create 15 posts so page 1 must be capped at 10
        for i in range(15):
            make_post(regular_user, category, title=f"Post {i}")
        client = authed_client(api_client, regular_user)
        res = client.get("/posts?page=1")
        assert res.status_code == 200
        assert len(res.json()["results"]) == 10

    def test_second_page_returns_remaining_posts(self, api_client, regular_user, category):
        for i in range(15):
            make_post(regular_user, category, title=f"Post {i}")
        client = authed_client(api_client, regular_user)
        res = client.get("/posts?page=2")
        assert res.status_code == 200
        assert len(res.json()["results"]) == 5

    def test_count_and_total_pages_are_correct(self, api_client, regular_user, category):
        for i in range(23):
            make_post(regular_user, category, title=f"Post {i}")
        client = authed_client(api_client, regular_user)
        res = client.get("/posts")
        data = res.json()
        assert data["count"] == 23
        assert data["total_pages"] == 3  # ceil(23/10)

    def test_out_of_range_page_clamps_to_last_page(self, api_client, regular_user, category):
        for i in range(5):
            make_post(regular_user, category, title=f"Post {i}")
        client = authed_client(api_client, regular_user)
        res = client.get("/posts?page=999")
        assert res.status_code == 200
        data = res.json()
        # Should return the last (and only) page
        assert data["page"] == 1
        assert len(data["results"]) == 5

    def test_invalid_page_param_defaults_to_page_1(self, api_client, regular_user, category):
        make_post(regular_user, category)
        client = authed_client(api_client, regular_user)
        res = client.get("/posts?page=abc")
        assert res.status_code == 200
        assert res.json()["page"] == 1

    def test_category_filter_returns_only_matching_posts(self, api_client, regular_user, category, other_category):
        make_post(regular_user, category, title="Tech Post")
        make_post(regular_user, other_category, title="Sports Post")
        client = authed_client(api_client, regular_user)
        res = client.get(f"/posts?category_id={category.id}")
        assert res.status_code == 200
        titles = [p["title"] for p in res.json()["results"]]
        assert "Tech Post" in titles
        assert "Sports Post" not in titles

    def test_category_filter_count_reflects_filtered_set(self, api_client, regular_user, category, other_category):
        for i in range(3):
            make_post(regular_user, category, title=f"Tech {i}")
        for i in range(7):
            make_post(regular_user, other_category, title=f"Sports {i}")
        client = authed_client(api_client, regular_user)
        res = client.get(f"/posts?category_id={category.id}")
        assert res.json()["count"] == 3
