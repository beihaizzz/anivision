"""
Tests for search router endpoint using FastAPI TestClient with mocked dependencies.

Tests cover the global search endpoint:
- GET /api/search?q=<query>           — search all types
- GET /api/search?q=<query>&type=X    — filter by type
- GET /api/search?q=<query>&page=N&size=M — pagination
"""

import pytest
from unittest.mock import MagicMock

from app.database import get_db


# ══════════════════════════════════════════════════════════════════════════
# Override Helpers
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _clear_overrides(app):
    """Ensure no dependency overrides leak between tests."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _override_db(app, mock_db):
    """Override get_db with the given mock session."""
    async def _gen():
        yield mock_db

    app.dependency_overrides[get_db] = _gen


# ══════════════════════════════════════════════════════════════════════════
# Search Endpoint  GET /api/search
# ══════════════════════════════════════════════════════════════════════════


class TestSearch:
    """Tests for GET /api/search."""

    # ── Success Cases ───────────────────────────────────────────────────

    @pytest.mark.unit
    def test_search_characters_by_name(self, client, app, mock_db):
        """200: search returns matching character with all section keys."""
        _override_db(app, mock_db)

        from app.models.character import Character
        from app.models.work import Work

        mock_result = MagicMock()
        # scalar called for: char_count, post_count, user_count → [1, 0, 0]
        mock_result.scalar.side_effect = [1, 0, 0]

        char = Character(
            id=1,
            name="蒙奇·D·路飞",
            description="草帽海贼团船长",
            image_url="https://example.com/luffy.jpg",
            work=Work(id=1, title="One Piece"),
        )
        mock_result.scalars.return_value.all.return_value = [char]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=路飞")

        assert response.status_code == 200
        data = response.json()
        assert "characters" in data
        assert "posts" in data
        assert "users" in data
        assert data["total"] == 1
        assert len(data["characters"]) == 1
        assert data["characters"][0]["name"] == "蒙奇·D·路飞"
        assert data["characters"][0]["id"] == 1
        assert len(data["posts"]) == 0
        assert len(data["users"]) == 0

    @pytest.mark.unit
    def test_search_all_types(self, client, app, mock_db):
        """200: search across all types returns empty results for no matches."""
        _override_db(app, mock_db)

        mock_result = MagicMock()
        mock_result.scalar.side_effect = [0, 0, 0]  # all empty
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=test")

        assert response.status_code == 200
        data = response.json()
        assert len(data["characters"]) == 0
        assert len(data["posts"]) == 0
        assert len(data["users"]) == 0
        assert data["total"] == 0

    @pytest.mark.unit
    def test_search_posts_by_content(self, client, app, mock_db):
        """200: search matches posts by content ILIKE."""
        _override_db(app, mock_db)

        from app.models.post import Post
        from datetime import datetime, timezone

        mock_result = MagicMock()
        # char_count=0, post_count=1, user_count=0
        mock_result.scalar.side_effect = [0, 1, 0]

        post = Post(
            id=10,
            content="路飞真是太帅了！我最喜欢的角色。",
            created_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
        )
        mock_result.scalars.return_value.all.return_value = [post]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=路飞")

        assert response.status_code == 200
        data = response.json()
        assert len(data["posts"]) == 1
        assert data["posts"][0]["id"] == 10
        assert "路飞" in data["posts"][0]["content"]
        assert data["posts"][0]["created_at"] is not None
        assert data["total"] == 1

    @pytest.mark.unit
    def test_search_users_by_username(self, client, app, mock_db):
        """200: search matches users by username ILIKE."""
        _override_db(app, mock_db)

        from app.models.user import User

        mock_result = MagicMock()
        # char_count=0, post_count=0, user_count=1
        mock_result.scalar.side_effect = [0, 0, 1]

        user = User(
            id=5,
            username="luffy_fan_2024",
            avatar_url="https://example.com/avatar5.jpg",
        )
        mock_result.scalars.return_value.all.return_value = [user]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=luffy")

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 1
        assert data["users"][0]["id"] == 5
        assert data["users"][0]["username"] == "luffy_fan_2024"
        assert "password_hash" not in data["users"][0]
        assert "email" not in data["users"][0]
        assert data["total"] == 1

    @pytest.mark.unit
    def test_search_mixed_results(self, client, app, mock_db):
        """200: search returns results from multiple types simultaneously."""
        _override_db(app, mock_db)

        from app.models.character import Character
        from app.models.post import Post
        from app.models.user import User
        from datetime import datetime, timezone

        mock_result = MagicMock()
        # char_count=2, post_count=1, user_count=0
        mock_result.scalar.side_effect = [2, 1, 0]

        char1 = Character(id=1, name="蒙奇·D·路飞", description="", image_url=None)
        char2 = Character(id=2, name="路飞太郎", description="", image_url=None)
        post = Post(id=10, content="关于路飞的讨论", created_at=datetime(2025, 1, 1, tzinfo=timezone.utc))

        # scalars() is called for characters query, then posts query
        # Use side_effect to return different lists per call
        mock_scalars = MagicMock()
        mock_scalars.all.side_effect = [[char1, char2], [post]]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=路飞&size=50")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3  # 2 + 1 + 0
        assert len(data["characters"]) == 2
        assert len(data["posts"]) == 1
        assert len(data["users"]) == 0

    # ── Type Filtering ──────────────────────────────────────────────────

    @pytest.mark.unit
    def test_filter_by_type_characters(self, client, app, mock_db):
        """200: type=character only searches characters."""
        _override_db(app, mock_db)

        mock_result = MagicMock()
        mock_result.scalar.side_effect = [0, 0, 0]
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=luffy&type=character")

        assert response.status_code == 200
        data = response.json()
        assert "characters" in data
        assert data["total"] == 0

    @pytest.mark.unit
    def test_filter_by_type_posts(self, client, app, mock_db):
        """200: type=post only searches posts."""
        _override_db(app, mock_db)

        from app.models.post import Post
        from datetime import datetime, timezone

        mock_result = MagicMock()
        # Only post_count is queried → 1
        mock_result.scalar.side_effect = [1]
        post = Post(id=7, content="test post content", created_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
        mock_result.scalars.return_value.all.return_value = [post]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=test&type=post")

        assert response.status_code == 200
        data = response.json()
        assert len(data["posts"]) == 1
        assert len(data["characters"]) == 0
        assert len(data["users"]) == 0
        assert data["total"] == 1

    @pytest.mark.unit
    def test_filter_by_type_users(self, client, app, mock_db):
        """200: type=user only searches users."""
        _override_db(app, mock_db)

        mock_result = MagicMock()
        mock_result.scalar.side_effect = [0, 0, 0]
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=admin&type=user")

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert data["total"] == 0

    # ── Pagination ─────────────────────────────────────────────────────

    @pytest.mark.unit
    def test_pagination_first_page(self, client, app, mock_db):
        """200: pagination with page=1 returns first page results."""
        _override_db(app, mock_db)

        from app.models.character import Character

        mock_result = MagicMock()
        mock_result.scalar.side_effect = [5, 0, 0]  # 5 total chars

        chars = [Character(id=i, name=f"Character {i}", description="", image_url=None) for i in range(1, 4)]
        mock_result.scalars.return_value.all.return_value = chars
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=char&page=1&size=3")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5  # total count, not paginated
        assert len(data["characters"]) == 3  # page size

    @pytest.mark.unit
    def test_pagination_second_page(self, client, app, mock_db):
        """200: page=2 with offset applied correctly."""
        _override_db(app, mock_db)

        from app.models.character import Character

        mock_result = MagicMock()
        mock_result.scalar.side_effect = [10, 0, 0]  # 10 total

        chars = [Character(id=i, name=f"Char {i}", description="", image_url=None) for i in range(11, 14)]
        mock_result.scalars.return_value.all.return_value = chars
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=char&page=2&size=3")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["characters"]) == 3

    # ── Validation ──────────────────────────────────────────────────────

    @pytest.mark.unit
    def test_empty_query_rejected(self, client, app, mock_db):
        """422 when query is empty."""
        _override_db(app, mock_db)

        response = client.get("/api/search?q=")

        assert response.status_code == 422

    @pytest.mark.unit
    def test_missing_query_rejected(self, client, app, mock_db):
        """422 when query parameter is missing."""
        _override_db(app, mock_db)

        response = client.get("/api/search")

        assert response.status_code == 422

    @pytest.mark.unit
    def test_invalid_type_rejected(self, client, app, mock_db):
        """422 when type is not all/character/post/user."""
        _override_db(app, mock_db)

        response = client.get("/api/search?q=test&type=invalid")

        assert response.status_code == 422

    @pytest.mark.unit
    def test_page_less_than_one_rejected(self, client, app, mock_db):
        """422 when page < 1."""
        _override_db(app, mock_db)

        response = client.get("/api/search?q=test&page=0")

        assert response.status_code == 422

    @pytest.mark.unit
    def test_size_exceeds_maximum_rejected(self, client, app, mock_db):
        """422 when size > 100."""
        _override_db(app, mock_db)

        response = client.get("/api/search?q=test&size=101")

        assert response.status_code == 422

    # ── Edge Cases ──────────────────────────────────────────────────────

    @pytest.mark.unit
    def test_search_with_special_characters(self, client, app, mock_db):
        """200: special characters in query handled correctly."""
        _override_db(app, mock_db)

        mock_result = MagicMock()
        mock_result.scalar.side_effect = [0, 0, 0]
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=%E3%83%AB%E3%83%95%E3%82%A3")  # URL-encoded "ルフィ"

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    @pytest.mark.unit
    def test_search_post_content_truncation(self, client, app, mock_db):
        """200: post content longer than 200 chars is truncated in results."""
        _override_db(app, mock_db)

        from app.models.post import Post
        from datetime import datetime, timezone

        long_content = "A" * 500
        mock_result = MagicMock()
        mock_result.scalar.side_effect = [0, 1, 0]

        post = Post(id=1, content=long_content, created_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
        mock_result.scalars.return_value.all.return_value = [post]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=A")

        assert response.status_code == 200
        data = response.json()
        assert len(data["posts"]) == 1
        assert len(data["posts"][0]["content"]) <= 200

    @pytest.mark.unit
    def test_search_no_auth_required(self, client, app, mock_db):
        """200: search endpoint is public — no authentication required."""
        _override_db(app, mock_db)

        mock_result = MagicMock()
        mock_result.scalar.side_effect = [0, 0, 0]
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # No auth header
        response = client.get("/api/search?q=public")

        assert response.status_code == 200

    @pytest.mark.unit
    def test_user_results_exclude_sensitive_fields(self, client, app, mock_db):
        """200: user results never expose password_hash or email."""
        _override_db(app, mock_db)

        from app.models.user import User

        mock_result = MagicMock()
        mock_result.scalar.side_effect = [0, 0, 1]

        user = User(
            id=7,
            username="sensitive_user",
            email="secret@example.com",
            password_hash="should_not_leak",
            avatar_url="https://example.com/av.jpg",
        )
        mock_result.scalars.return_value.all.return_value = [user]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=sensitive")

        assert response.status_code == 200
        data = response.json()
        user_result = data["users"][0]
        assert "password_hash" not in user_result
        assert "email" not in user_result
        assert user_result["id"] == 7
        assert user_result["username"] == "sensitive_user"

    @pytest.mark.unit
    def test_search_with_unicode_japanese(self, client, app, mock_db):
        """200: Japanese unicode characters work correctly."""
        _override_db(app, mock_db)

        from app.models.character import Character
        from app.models.work import Work

        mock_result = MagicMock()
        mock_result.scalar.side_effect = [1, 0, 0]

        char = Character(
            id=42,
            name="モンキー・D・ルフィ",
            description="麦わらのルフィ",
            image_url=None,
            work=Work(id=1, title="ワンピース"),
        )
        mock_result.scalars.return_value.all.return_value = [char]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=ルフィ")

        assert response.status_code == 200
        data = response.json()
        assert len(data["characters"]) == 1
        assert "ルフィ" in data["characters"][0]["name"]
