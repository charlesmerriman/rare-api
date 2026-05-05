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
def author(db):
    return RareUser.objects.create_user(
        username="author",
        password="pass123",
        first_name="Author",
        last_name="User",
        email="author@example.com",
        is_active=True,
    )


@pytest.fixture
def viewer(db):
    return RareUser.objects.create_user(
        username="viewer",
        password="pass123",
        email="viewer@example.com",
        is_active=True,
    )


@pytest.fixture
def category(db):
    return Category.objects.create(label="General")


def make_post(author, category, approved, title="A Post"):
    return Post.objects.create(
        user=author,
        category=category,
        title=title,
        publication_date="2025-01-01",
        content="Some content",
        approved=approved,
    )


def get_profile(api_client, viewer, author_id):
    token = Token.objects.create(user=viewer)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client.get(f"/profiles/{author_id}")


class TestPostCountField:
    def test_post_count_present_in_response(self, api_client, author, viewer):
        response = get_profile(api_client, viewer, author.id)
        assert response.status_code == 200
        assert "post_count" in response.json()

    def test_zero_posts(self, api_client, author, viewer):
        response = get_profile(api_client, viewer, author.id)
        assert response.json()["post_count"] == 0

    def test_counts_approved_posts(self, api_client, author, viewer, category):
        make_post(author, category, approved=True, title="Approved 1")
        make_post(author, category, approved=True, title="Approved 2")
        response = get_profile(api_client, viewer, author.id)
        assert response.json()["post_count"] == 2

    def test_excludes_unapproved_posts(self, api_client, author, viewer, category):
        make_post(author, category, approved=False, title="Draft")
        response = get_profile(api_client, viewer, author.id)
        assert response.json()["post_count"] == 0

    def test_mixed_approved_and_unapproved(self, api_client, author, viewer, category):
        make_post(author, category, approved=True, title="Published")
        make_post(author, category, approved=False, title="Draft 1")
        make_post(author, category, approved=False, title="Draft 2")
        response = get_profile(api_client, viewer, author.id)
        assert response.json()["post_count"] == 1

    def test_only_counts_posts_belonging_to_that_user(self, api_client, author, viewer, category, db):
        other = RareUser.objects.create_user(
            username="other", password="pass", email="other@example.com"
        )
        make_post(other, category, approved=True, title="Other's Post")
        make_post(author, category, approved=True, title="Author's Post")
        response = get_profile(api_client, viewer, author.id)
        assert response.json()["post_count"] == 1

    def test_visible_to_other_users(self, api_client, author, viewer, category):
        make_post(author, category, approved=True, title="Public Post")
        response = get_profile(api_client, viewer, author.id)
        # viewer is not the author — count should still be present and correct
        assert response.json()["post_count"] == 1

    def test_visible_on_own_profile(self, api_client, author, category):
        make_post(author, category, approved=True, title="Own Post")
        token = Token.objects.create(user=author)
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = api_client.get(f"/profiles/{author.id}")
        assert response.json()["post_count"] == 1

    def test_requires_authentication(self, api_client, author, db):
        response = api_client.get(f"/profiles/{author.id}")
        assert response.status_code in (401, 403)
