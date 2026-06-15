"""
Unit tests for Character & Work Schemas

Tests validation, serialization, and edge cases for:
- WorkResponse
- CharacterResponse
- CharacterListResponse
- WorkListResponse
- CharacterFilterParams

NOTE: Tests are self-contained and do not depend on conftest.py fixtures,
because the root conftest triggers app.database module-level engine creation
which is incompatible with SQLite. Run with: pytest --noconftest -m unit
"""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.character import (
    CharacterFilterParams,
    CharacterListResponse,
    CharacterResponse,
    WorkListResponse,
    WorkResponse,
)
from app.schemas.common import PaginatedResponse


def _make_utcnow() -> datetime:
    """Return current UTC datetime (avoiding deprecated utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ══════════════════════════════════════════════════════════════════════════
# WorkResponse
# ══════════════════════════════════════════════════════════════════════════


class TestWorkResponse:
    """Tests for WorkResponse schema."""

    @pytest.mark.unit
    def test_minimal_fields(self):
        """Should accept only required fields."""
        now = _make_utcnow()
        work = WorkResponse(id=1, title="Naruto", type="anime", created_at=now)
        assert work.id == 1
        assert work.title == "Naruto"
        assert work.type == "anime"
        assert work.title_jp is None
        assert work.description is None
        assert work.cover_url is None
        assert work.created_at == now

    @pytest.mark.unit
    def test_all_fields(self):
        """Should accept all fields when provided."""
        now = _make_utcnow()
        work = WorkResponse(
            id=2,
            title="Naruto",
            title_jp="ナルト",
            type="anime",
            description="A ninja story",
            cover_url="https://example.com/cover.jpg",
            created_at=now,
        )
        assert work.title_jp == "ナルト"
        assert work.description == "A ninja story"
        assert work.cover_url == "https://example.com/cover.jpg"

    @pytest.mark.unit
    def test_title_required(self):
        """Should reject missing title."""
        now = _make_utcnow()
        with pytest.raises(ValidationError):
            WorkResponse(id=1, type="anime", created_at=now)

    @pytest.mark.unit
    def test_fields_match_orm_columns(self):
        """Should have fields matching Work ORM column fields."""
        expected = {"id", "title", "title_jp", "type", "description", "cover_url", "created_at"}
        model_fields = set(WorkResponse.model_fields.keys())
        assert model_fields == expected

    @pytest.mark.unit
    def test_from_attributes_config(self):
        """Should support ORM mode via from_attributes=True."""
        assert WorkResponse.model_config.get("from_attributes") is True

    @pytest.mark.unit
    def test_json_serialization(self):
        """Should serialize to JSON correctly."""
        now = _make_utcnow()
        work = WorkResponse(id=1, title="Test", type="anime", created_at=now)
        data = work.model_dump()
        assert data["id"] == 1
        assert data["title"] == "Test"
        assert data["created_at"] == now
        json_str = work.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["id"] == 1
        assert parsed["title"] == "Test"


# ══════════════════════════════════════════════════════════════════════════
# CharacterResponse
# ══════════════════════════════════════════════════════════════════════════


class TestCharacterResponse:
    """Tests for CharacterResponse schema."""

    @pytest.mark.unit
    def test_minimal_fields(self):
        """Should accept only required fields (name, aliases default to [])."""
        now = _make_utcnow()
        char = CharacterResponse(id=1, name="Naruto Uzumaki", aliases=[], created_at=now)
        assert char.id == 1
        assert char.name == "Naruto Uzumaki"
        assert char.aliases == []
        assert char.name_jp is None
        assert char.description == ""
        assert char.image_url is None
        assert char.work is None
        assert char.created_at == now

    @pytest.mark.unit
    def test_all_fields(self):
        """Should accept all fields when provided."""
        now = _make_utcnow()
        work = WorkResponse(id=1, title="Naruto", type="anime", created_at=now)
        char = CharacterResponse(
            id=1,
            name="Naruto Uzumaki",
            name_jp="うずまきナルト",
            aliases=["ナルト", "Naruto"],
            description="The main protagonist",
            image_url="https://example.com/naruto.jpg",
            work=work,
            created_at=now,
        )
        assert char.name_jp == "うずまきナルト"
        assert char.aliases == ["ナルト", "Naruto"]
        assert char.description == "The main protagonist"
        assert char.image_url == "https://example.com/naruto.jpg"
        assert char.work is not None
        assert char.work.title == "Naruto"

    @pytest.mark.unit
    def test_name_required(self):
        """Should reject missing name."""
        now = _make_utcnow()
        with pytest.raises(ValidationError):
            CharacterResponse(id=1, aliases=[], created_at=now)

    @pytest.mark.unit
    def test_aliases_can_be_empty_list(self):
        """Should accept empty list for aliases."""
        now = _make_utcnow()
        char = CharacterResponse(id=1, name="Test", aliases=[], created_at=now)
        assert char.aliases == []

    @pytest.mark.unit
    def test_aliases_defaults_to_empty_list(self):
        """Should default aliases to empty list when not provided."""
        now = _make_utcnow()
        char = CharacterResponse(id=1, name="Test", aliases=[], created_at=now)
        assert char.aliases == []

    @pytest.mark.unit
    def test_aliases_rejects_none(self):
        """Should reject None for aliases (must be a list)."""
        now = _make_utcnow()
        with pytest.raises(ValidationError):
            CharacterResponse(id=1, name="Test", aliases=None, created_at=now)  # type: ignore

    @pytest.mark.unit
    def test_description_default_empty_string(self):
        """Should default description to empty string."""
        now = _make_utcnow()
        char = CharacterResponse(id=1, name="Test", aliases=[], created_at=now)
        assert char.description == ""

    @pytest.mark.unit
    def test_work_optional(self):
        """Should accept missing work (FK can be SET NULL)."""
        now = _make_utcnow()
        char = CharacterResponse(id=1, name="Test", aliases=[], created_at=now)
        assert char.work is None

    @pytest.mark.unit
    def test_from_attributes_config(self):
        """Should support ORM mode via from_attributes=True."""
        assert CharacterResponse.model_config.get("from_attributes") is True

    @pytest.mark.unit
    def test_fields_match_orm_columns_and_relationships(self):
        """Should have fields matching Character ORM."""
        expected = {
            "id", "name", "name_jp", "aliases",
            "description", "image_url", "work", "created_at",
        }
        model_fields = set(CharacterResponse.model_fields.keys())
        assert model_fields == expected

    @pytest.mark.unit
    def test_json_serialization(self):
        """Should serialize to JSON correctly."""
        now = _make_utcnow()
        work = WorkResponse(id=1, title="Naruto", type="anime", created_at=now)
        char = CharacterResponse(
            id=1,
            name="Naruto",
            aliases=["ナルト"],
            work=work,
            created_at=now,
        )
        data = char.model_dump()
        assert data["name"] == "Naruto"
        assert data["work"]["title"] == "Naruto"
        json_str = char.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["name"] == "Naruto"
        assert parsed["work"]["title"] == "Naruto"


# ══════════════════════════════════════════════════════════════════════════
# CharacterListResponse
# ══════════════════════════════════════════════════════════════════════════


class TestCharacterListResponse:
    """Tests for CharacterListResponse (paginated list)."""

    @pytest.mark.unit
    def test_is_paginated_response(self):
        """Should be a subclass of PaginatedResponse."""
        assert issubclass(CharacterListResponse, PaginatedResponse)

    @pytest.mark.unit
    def test_items_type_character_response(self):
        """Should accept list of CharacterResponse as items."""
        now = _make_utcnow()
        chars = [
            CharacterResponse(id=1, name="Naruto", aliases=[], created_at=now),
            CharacterResponse(id=2, name="Sasuke", aliases=[], created_at=now),
        ]
        response = CharacterListResponse(items=chars, total=2, page=1, size=20)
        assert len(response.items) == 2
        assert response.items[0].name == "Naruto"
        assert response.items[1].name == "Sasuke"
        assert response.total == 2
        assert response.page == 1
        assert response.size == 20

    @pytest.mark.unit
    def test_empty_items(self):
        """Should accept empty items list."""
        response = CharacterListResponse(items=[], total=0, page=1, size=20)
        assert response.items == []
        assert response.total == 0

    @pytest.mark.unit
    def test_pages_property(self):
        """Should calculate pages correctly (inherited from PaginatedResponse)."""
        now = _make_utcnow()
        chars = [
            CharacterResponse(id=i, name=f"Char{i}", aliases=[], created_at=now)
            for i in range(25)
        ]
        response = CharacterListResponse(items=chars, total=25, page=1, size=10)
        assert response.pages == 3

    @pytest.mark.unit
    def test_pages_zero_when_size_zero(self):
        """Should return 0 pages when size is 0."""
        response = CharacterListResponse(items=[], total=0, page=1, size=0)
        assert response.pages == 0

    @pytest.mark.unit
    def test_serialize_to_json(self):
        """Should serialize to JSON correctly."""
        now = _make_utcnow()
        char = CharacterResponse(id=1, name="Naruto", aliases=[], created_at=now)
        response = CharacterListResponse(items=[char], total=1, page=1, size=20)
        data = response.model_dump()
        assert data["items"][0]["name"] == "Naruto"
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["size"] == 20


# ══════════════════════════════════════════════════════════════════════════
# WorkListResponse
# ══════════════════════════════════════════════════════════════════════════


class TestWorkListResponse:
    """Tests for WorkListResponse (paginated list)."""

    @pytest.mark.unit
    def test_is_paginated_response(self):
        """Should be a subclass of PaginatedResponse."""
        assert issubclass(WorkListResponse, PaginatedResponse)

    @pytest.mark.unit
    def test_items_type_work_response(self):
        """Should accept list of WorkResponse as items."""
        now = _make_utcnow()
        works = [
            WorkResponse(id=1, title="Naruto", type="anime", created_at=now),
            WorkResponse(id=2, title="Bleach", type="anime", created_at=now),
        ]
        response = WorkListResponse(items=works, total=2, page=1, size=20)
        assert len(response.items) == 2
        assert response.items[0].title == "Naruto"
        assert response.total == 2

    @pytest.mark.unit
    def test_empty_items(self):
        """Should accept empty items list."""
        response = WorkListResponse(items=[], total=0, page=1, size=20)
        assert response.items == []
        assert response.total == 0


# ══════════════════════════════════════════════════════════════════════════
# CharacterFilterParams
# ══════════════════════════════════════════════════════════════════════════


class TestCharacterFilterParams:
    """Tests for CharacterFilterParams schema."""

    @pytest.mark.unit
    def test_all_fields_optional(self):
        """Should accept empty filter params (all fields optional)."""
        params = CharacterFilterParams()
        assert params.name is None
        assert params.work_id is None

    @pytest.mark.unit
    def test_name_filter(self):
        """Should accept name filter."""
        params = CharacterFilterParams(name="Naruto")
        assert params.name == "Naruto"
        assert params.work_id is None

    @pytest.mark.unit
    def test_work_id_filter(self):
        """Should accept work_id filter."""
        params = CharacterFilterParams(work_id=5)
        assert params.name is None
        assert params.work_id == 5

    @pytest.mark.unit
    def test_both_filters(self):
        """Should accept both name and work_id at the same time."""
        params = CharacterFilterParams(name="Naruto", work_id=5)
        assert params.name == "Naruto"
        assert params.work_id == 5

    @pytest.mark.unit
    def test_json_round_trip(self):
        """Should serialize and deserialize correctly."""
        params = CharacterFilterParams(name="Sasuke", work_id=3)
        data = params.model_dump()
        assert data == {"name": "Sasuke", "work_id": 3}
        restored = CharacterFilterParams(**data)
        assert restored.name == "Sasuke"
        assert restored.work_id == 3
