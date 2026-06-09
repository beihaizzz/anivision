"""
Unit tests for Common Schemas

Tests validation, pagination logic, and edge cases for:
- PaginationParams
- PaginatedResponse
- MessageResponse

NOTE: Tests are self-contained and do not depend on conftest.py fixtures,
because the root conftest triggers app.database module-level engine creation
which is incompatible with SQLite. Run with: pytest --noconftest -m unit
"""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.auth import UserResponse
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationParams


def _make_utcnow() -> datetime:
    """Return current UTC datetime (avoiding deprecated utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ══════════════════════════════════════════════════════════════════════════
# PaginationParams
# ══════════════════════════════════════════════════════════════════════════


class TestPaginationParams:
    """Tests for PaginationParams schema."""

    @pytest.mark.unit
    def test_default_values(self):
        """Should use default page=1 and size=20 when no args given."""
        params = PaginationParams()
        assert params.page == 1
        assert params.size == 20

    @pytest.mark.unit
    def test_custom_page_and_size(self):
        """Should accept custom page and size values."""
        params = PaginationParams(page=3, size=50)
        assert params.page == 3
        assert params.size == 50

    @pytest.mark.unit
    def test_boundary_page_min(self):
        """Should accept page=1 (minimum)."""
        params = PaginationParams(page=1)
        assert params.page == 1

    @pytest.mark.unit
    def test_boundary_size_min(self):
        """Should accept size=1 (minimum)."""
        params = PaginationParams(size=1)
        assert params.size == 1

    @pytest.mark.unit
    def test_boundary_size_max(self):
        """Should accept size=100 (maximum)."""
        params = PaginationParams(size=100)
        assert params.size == 100

    @pytest.mark.unit
    def test_page_zero(self):
        """Should reject page=0 (less than ge=1)."""
        with pytest.raises(ValidationError) as exc:
            PaginationParams(page=0)
        errors = exc.value.errors()
        assert any(e["loc"] == ("page",) for e in errors)

    @pytest.mark.unit
    def test_negative_page(self):
        """Should reject negative page number."""
        with pytest.raises(ValidationError) as exc:
            PaginationParams(page=-1)
        errors = exc.value.errors()
        assert any(e["loc"] == ("page",) for e in errors)

    @pytest.mark.unit
    def test_size_exceeds_max(self):
        """Should reject size > 100."""
        with pytest.raises(ValidationError) as exc:
            PaginationParams(size=101)
        errors = exc.value.errors()
        assert any(e["loc"] == ("size",) for e in errors)

    @pytest.mark.unit
    def test_size_zero(self):
        """Should reject size=0 (less than ge=1)."""
        with pytest.raises(ValidationError) as exc:
            PaginationParams(size=0)
        errors = exc.value.errors()
        assert any(e["loc"] == ("size",) for e in errors)

    @pytest.mark.unit
    def test_negative_size(self):
        """Should reject negative size."""
        with pytest.raises(ValidationError) as exc:
            PaginationParams(size=-5)
        errors = exc.value.errors()
        assert any(e["loc"] == ("size",) for e in errors)

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict and JSON with defaults."""
        params = PaginationParams()
        d = params.model_dump()
        assert d == {"page": 1, "size": 20}
        json_str = params.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed == {"page": 1, "size": 20}

    @pytest.mark.unit
    def test_serialization_custom_values(self):
        """Should serialize custom values correctly."""
        params = PaginationParams(page=5, size=25)
        d = params.model_dump()
        assert d == {"page": 5, "size": 25}


# ══════════════════════════════════════════════════════════════════════════
# PaginatedResponse
# ══════════════════════════════════════════════════════════════════════════


class TestPaginatedResponse:
    """Tests for PaginatedResponse schema and its pages property."""

    @pytest.mark.unit
    def test_construct_with_empty_items(self):
        """Should construct with empty items list."""
        resp = PaginatedResponse[str](items=[], total=0, page=1, size=20)
        assert resp.items == []
        assert resp.total == 0
        assert resp.page == 1
        assert resp.size == 20

    @pytest.mark.unit
    def test_pages_empty(self):
        """Pages should be 0 when total=0 (no items)."""
        resp = PaginatedResponse[str](items=[], total=0, page=1, size=20)
        assert resp.pages == 0

    @pytest.mark.unit
    def test_pages_partial(self):
        """Pages should floor-divide correctly for partial final page."""
        # 15 items, size=10 -> ceil(15/10) = 2 pages
        resp = PaginatedResponse[str](items=["a"] * 5, total=15, page=2, size=10)
        assert resp.pages == 2

    @pytest.mark.unit
    def test_pages_full(self):
        """Pages should divide evenly for full pages."""
        # 20 items, size=5 -> 4 pages
        resp = PaginatedResponse[str](items=["a"] * 5, total=20, page=1, size=5)
        assert resp.pages == 4

    @pytest.mark.unit
    def test_pages_single_item(self):
        """Pages should return 1 for a single item."""
        resp = PaginatedResponse[str](items=["only"], total=1, page=1, size=20)
        assert resp.pages == 1

    @pytest.mark.unit
    def test_pages_exact_boundary(self):
        """Pages should be correct when total equals size."""
        resp = PaginatedResponse[str](items=["a"] * 20, total=20, page=1, size=20)
        assert resp.pages == 1

    @pytest.mark.unit
    def test_pages_one_over_boundary(self):
        """Pages should increment when total exceeds size by one."""
        resp = PaginatedResponse[str](items=["a"] * 1, total=21, page=2, size=20)
        assert resp.pages == 2

    @pytest.mark.unit
    def test_pages_many(self):
        """Pages should handle large totals correctly."""
        resp = PaginatedResponse[str](items=[], total=1000, page=1, size=20)
        assert resp.pages == 50

    @pytest.mark.unit
    def test_generic_with_user_response(self):
        """Should accept UserResponse items for generic typing."""
        now = _make_utcnow()
        user1 = UserResponse(
            id=1, username="user1", email="u1@test.com", role="user", created_at=now,
        )
        user2 = UserResponse(
            id=2, username="user2", email="u2@test.com", role="user", created_at=now,
        )
        resp = PaginatedResponse[UserResponse](
            items=[user1, user2], total=2, page=1, size=20,
        )
        assert len(resp.items) == 2
        assert isinstance(resp.items[0], UserResponse)
        assert resp.items[0].username == "user1"
        assert resp.items[1].username == "user2"
        assert resp.pages == 1

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict and JSON. pages is a property, not in dump."""
        resp = PaginatedResponse[str](items=["a", "b", "c"], total=10, page=1, size=3)
        d = resp.model_dump()
        assert d["items"] == ["a", "b", "c"]
        assert d["total"] == 10
        assert d["page"] == 1
        assert d["size"] == 3
        # pages is a computed property, not a serialized field
        assert "pages" not in d
        json_str = resp.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["items"] == ["a", "b", "c"]

    @pytest.mark.unit
    def test_serialization_with_user_response(self):
        """Should serialize nested UserResponse items correctly."""
        now = _make_utcnow()
        user = UserResponse(
            id=1, username="nested", email="n@test.com", role="user", created_at=now,
        )
        resp = PaginatedResponse[UserResponse](
            items=[user], total=1, page=1, size=20,
        )
        d = resp.model_dump()
        assert isinstance(d["items"][0], dict)
        assert d["items"][0]["username"] == "nested"


# ══════════════════════════════════════════════════════════════════════════
# MessageResponse
# ══════════════════════════════════════════════════════════════════════════


class TestMessageResponse:
    """Tests for MessageResponse schema."""

    @pytest.mark.unit
    def test_basic_construction(self):
        """Should construct with a message string."""
        resp = MessageResponse(message="Operation successful")
        assert resp.message == "Operation successful"
        assert resp.detail is None

    @pytest.mark.unit
    def test_with_detail(self):
        """Should accept an optional detail field."""
        resp = MessageResponse(
            message="Error occurred",
            detail="Something went wrong internally",
        )
        assert resp.message == "Error occurred"
        assert resp.detail == "Something went wrong internally"

    @pytest.mark.unit
    def test_detail_none(self):
        """Should have detail default to None."""
        resp = MessageResponse(message="OK")
        assert resp.detail is None

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict and JSON."""
        resp = MessageResponse(message="Hello", detail="World")
        d = resp.model_dump()
        assert d == {"message": "Hello", "detail": "World"}
        json_str = resp.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["message"] == "Hello"
        assert parsed["detail"] == "World"

    @pytest.mark.unit
    def test_serialization_without_detail(self):
        """Should serialize with detail as null when not provided."""
        resp = MessageResponse(message="Status OK")
        d = resp.model_dump()
        assert d == {"message": "Status OK", "detail": None}
        json_str = resp.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["detail"] is None
