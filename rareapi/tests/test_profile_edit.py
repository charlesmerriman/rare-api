import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rareapi.models import RareUser


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return RareUser.objects.create_user(
        username="edituser",
        password="pass123",
        first_name="Original",
        last_name="Name",
        email="edit@example.com",
        bio="Original bio",
        is_active=True,
    )


@pytest.fixture
def other_user(db):
    return RareUser.objects.create_user(
        username="otheruser",
        password="pass123",
        first_name="Other",
        last_name="Person",
        email="other@example.com",
        is_active=True,
    )


@pytest.fixture
def auth_client(api_client, user):
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


class TestProfileEdit:
    def test_owner_can_update_all_fields(self, auth_client, user):
        response = auth_client.patch(f"/profiles/{user.id}", {
            "first_name": "Updated",
            "last_name": "Person",
            "bio": "New bio here",
        }, format="json")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.last_name == "Person"
        assert user.bio == "New bio here"

    def test_partial_update_only_bio(self, auth_client, user):
        response = auth_client.patch(f"/profiles/{user.id}", {
            "bio": "Just the bio changed",
        }, format="json")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.bio == "Just the bio changed"
        assert user.first_name == "Original"
        assert user.last_name == "Name"

    def test_response_contains_profile_detail(self, auth_client, user):
        response = auth_client.patch(f"/profiles/{user.id}", {
            "first_name": "New",
        }, format="json")
        assert response.status_code == 200
        data = response.json()
        assert "full_name" in data
        assert "username" in data

    def test_non_owner_gets_403(self, api_client, user, other_user):
        token = Token.objects.create(user=other_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = api_client.patch(f"/profiles/{user.id}", {
            "bio": "Hacked",
        }, format="json")
        assert response.status_code == 403
        user.refresh_from_db()
        assert user.bio == "Original bio"

    def test_unauthenticated_gets_401(self, api_client, user):
        response = api_client.patch(f"/profiles/{user.id}", {
            "bio": "No auth",
        }, format="json")
        assert response.status_code == 401
