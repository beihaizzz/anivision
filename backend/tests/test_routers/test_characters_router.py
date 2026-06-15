"""
Tests for characters router endpoints using FastAPI TestClient with mocked dependencies.

Tests cover all four character/work endpoints:
- GET /api/characters           — List characters (paginated, filterable)
- GET /api/characters/{id}      — Get character by ID
- GET /api/characters/works     — List works (paginated)
- GET /api/characters/works/{id} — Get work by ID
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.database import get_db
from app.models.character import Character
from app.models.work import Work


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
# Test Fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_work():
    """A sample Work ORM instance for tests."""
    return Work(
        id=1,
        title="One Piece",
        title_jp="ワンピース",
        type="anime",
        description="A pirate adventure",
        cover_url="https://example.com/onepiece.jpg",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_character(sample_work):
    """A sample Character ORM instance with work relationship populated."""
    return Character(
        id=1,
        name="Monkey D. Luffy",
        name_jp="モンキー・D・ルフィ",
        aliases=["Luffy", "Straw Hat"],
        description="Captain of the Straw Hat Pirates",
        image_url="https://example.com/luffy.jpg",
        work_id=1,
        work=sample_work,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_characters(sample_work):
    """A list of sample Character ORM instances."""
    return [
        Character(
            id=1,
            name="Monkey D. Luffy",
            name_jp="モンキー・D・ルフィ",
            aliases=["Luffy"],
            work_id=1,
            work=sample_work,
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        ),
        Character(
            id=2,
            name="Roronoa Zoro",
            name_jp="ロロノア・ゾロ",
            aliases=["Zoro"],
            work_id=1,
            work=sample_work,
            created_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
        ),
    ]


@pytest.fixture
def sample_works():
    """A list of sample Work ORM instances."""
    return [
        Work(
            id=1,
            title="One Piece",
            title_jp="ワンピース",
            type="anime",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        ),
        Work(
            id=2,
            title="Naruto",
            title_jp="ナルト",
            type="anime",
            created_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
        ),
    ]


def _setup_list_mock(mock_result, total=0, items=None):
    """Set up a mock result for paginated list endpoints.
    
    The character service calls:
    1) db.execute(count_query) → .scalar() → total count
    2) db.execute(query)        → .scalars().all() → items list
    
    mock_result.scalars must be a MagicMock (not AsyncMock) because the
    service does synchronous chaining: result.scalars().all()
    """
    if items is None:
        items = []
    mock_result.scalar.return_value = total
    mock_result.scalars = MagicMock()
    mock_result.scalars.return_value.all.return_value = items


# ══════════════════════════════════════════════════════════════════════════
# List Characters Endpoint  GET /api/characters
# ══════════════════════════════════════════════════════════════════════════


class TestListCharacters:
    """Tests for GET /api/characters."""

    @pytest.mark.unit
    def test_returns_paginated_response_with_empty_list(self, client, app, mock_db):
        """200 with paginated response structure and empty items."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        _setup_list_mock(mock_result, total=0, items=[])

        response = client.get("/api/characters?page=1&size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 10

    @pytest.mark.unit
    def test_supports_name_filter(self, client, app, mock_db):
        """200 when filtering by name parameter."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        _setup_list_mock(mock_result, total=0)

        response = client.get("/api/characters?name=luffy")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    @pytest.mark.unit
    def test_supports_work_id_filter(self, client, app, mock_db):
        """200 when filtering by work_id parameter."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        _setup_list_mock(mock_result, total=0)

        response = client.get("/api/characters?work_id=1")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    @pytest.mark.unit
    def test_returns_characters_when_present(
        self, client, app, mock_db, sample_characters
    ):
        """200 with character items populated in response."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        _setup_list_mock(mock_result, total=len(sample_characters), items=sample_characters)

        response = client.get("/api/characters?page=1&size=20")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "Monkey D. Luffy"
        assert data["items"][1]["name"] == "Roronoa Zoro"

    @pytest.mark.unit
    def test_rejects_invalid_page(self, client, app, mock_db):
        """422 when page is less than 1."""
        _override_db(app, mock_db)

        response = client.get("/api/characters?page=0")

        assert response.status_code == 422

    @pytest.mark.unit
    def test_rejects_invalid_size(self, client, app, mock_db):
        """422 when size exceeds maximum."""
        _override_db(app, mock_db)

        response = client.get("/api/characters?size=200")

        assert response.status_code == 422

    @pytest.mark.unit
    def test_default_pagination_values(self, client, app, mock_db):
        """200 with default page=1 and size=20 when not specified."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        _setup_list_mock(mock_result, total=0)

        response = client.get("/api/characters")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 20


# ══════════════════════════════════════════════════════════════════════════
# Get Character Endpoint  GET /api/characters/{id}
# ══════════════════════════════════════════════════════════════════════════


class TestGetCharacter:
    """Tests for GET /api/characters/{character_id}."""

    @pytest.mark.unit
    def test_returns_character_with_work(self, client, app, mock_db, sample_character):
        """200 with full character data including work info."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        mock_result.scalar_one_or_none.return_value = sample_character

        response = client.get("/api/characters/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Monkey D. Luffy"
        assert data["name_jp"] == "モンキー・D・ルフィ"
        assert data["aliases"] == ["Luffy", "Straw Hat"]
        assert data["description"] == "Captain of the Straw Hat Pirates"
        assert "created_at" in data
        # Work relationship should be populated
        assert data["work"] is not None
        assert data["work"]["id"] == 1
        assert data["work"]["title"] == "One Piece"

    @pytest.mark.unit
    def test_404_for_nonexistent_character(self, client, app, mock_db):
        """404 when character ID does not exist."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        mock_result.scalar_one_or_none.return_value = None

        response = client.get("/api/characters/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.unit
    def test_returns_character_with_no_work(self, client, app, mock_db):
        """200 with character where work relationship is None."""
        _override_db(app, mock_db)

        char_no_work = Character(
            id=2,
            name="Unknown Character",
            aliases=[],
            work_id=None,
            work=None,
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        mock_result = mock_db.execute.return_value
        mock_result.scalar_one_or_none.return_value = char_no_work

        response = client.get("/api/characters/2")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 2
        assert data["name"] == "Unknown Character"
        assert data["work"] is None


# ══════════════════════════════════════════════════════════════════════════
# List Works Endpoint  GET /api/characters/works
# ══════════════════════════════════════════════════════════════════════════


class TestListWorks:
    """Tests for GET /api/characters/works."""

    @pytest.mark.unit
    def test_returns_paginated_response_with_empty_list(self, client, app, mock_db):
        """200 with paginated response structure and empty works."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        _setup_list_mock(mock_result, total=0)

        response = client.get("/api/characters/works?page=1&size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 10

    @pytest.mark.unit
    def test_returns_works_when_present(self, client, app, mock_db, sample_works):
        """200 with work items populated in response."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        _setup_list_mock(mock_result, total=len(sample_works), items=sample_works)

        response = client.get("/api/characters/works?page=1&size=20")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["title"] == "One Piece"
        assert data["items"][1]["title"] == "Naruto"

    @pytest.mark.unit
    def test_rejects_invalid_size(self, client, app, mock_db):
        """422 when size exceeds maximum."""
        _override_db(app, mock_db)

        response = client.get("/api/characters/works?size=200")

        assert response.status_code == 422

    @pytest.mark.unit
    def test_default_pagination_values(self, client, app, mock_db):
        """200 with default page=1 and size=20 when not specified."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        _setup_list_mock(mock_result, total=0)

        response = client.get("/api/characters/works")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 20


# ══════════════════════════════════════════════════════════════════════════
# Get Work Endpoint  GET /api/characters/works/{id}
# ══════════════════════════════════════════════════════════════════════════


class TestGetWork:
    """Tests for GET /api/characters/works/{work_id}."""

    @pytest.mark.unit
    def test_returns_work_with_characters(self, client, app, mock_db, sample_work):
        """200 with full work data."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        mock_result.scalar_one_or_none.return_value = sample_work

        response = client.get("/api/characters/works/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "One Piece"
        assert data["title_jp"] == "ワンピース"
        assert data["type"] == "anime"
        assert data["description"] == "A pirate adventure"
        assert data["cover_url"] == "https://example.com/onepiece.jpg"
        assert "created_at" in data

    @pytest.mark.unit
    def test_404_for_nonexistent_work(self, client, app, mock_db):
        """404 when work ID does not exist."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        mock_result.scalar_one_or_none.return_value = None

        response = client.get("/api/characters/works/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ══════════════════════════════════════════════════════════════════════════
# Route Precedence — /works must not be intercepted by /{character_id}
# ══════════════════════════════════════════════════════════════════════════


class TestRoutePrecedence:
    """Verify that /characters/works is not matched as /characters/{id}."""

    @pytest.mark.unit
    def test_works_list_not_intercepted_as_character_id(
        self, client, app, mock_db
    ):
        """/characters/works returns works list, not a character lookup."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        _setup_list_mock(mock_result, total=0)

        response = client.get("/api/characters/works")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        # It should NOT be a character response (no "name" at top level)
        assert "name" not in data

    @pytest.mark.unit
    def test_works_detail_not_intercepted_as_character_id(
        self, client, app, mock_db, sample_work
    ):
        """/characters/works/1 returns a work, not a character."""
        _override_db(app, mock_db)

        mock_result = mock_db.execute.return_value
        mock_result.scalar_one_or_none.return_value = sample_work

        response = client.get("/api/characters/works/1")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "One Piece"
        assert data["type"] == "anime"
