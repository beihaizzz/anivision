"""
Unit tests for character_service.py

Tests get_character(), list_characters(), get_work(), list_works()
using mocked database sessions from conftest.py.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status

from app.models.character import Character
from app.models.work import Work
from app.schemas.character import CharacterResponse, WorkResponse
from app.schemas.common import PaginatedResponse
from app.services.character_service import (
    get_character,
    get_work,
    list_characters,
    list_works,
)


# ── Helper fixtures ──────────────────────────────────────────────────


@pytest.fixture
def sample_work() -> Work:
    """Return a sample Work ORM object."""
    return Work(
        id=1,
        title="Spy x Family",
        title_jp="スパイファミリー",
        type="anime",
        description="A spy builds a family.",
        cover_url="https://example.com/cover.jpg",
        created_at=datetime(2024, 1, 1),
    )


@pytest.fixture
def sample_character(sample_work: Work) -> Character:
    """Return a sample Character ORM object with work loaded."""
    char = Character(
        id=1,
        name="Anya Forger",
        name_jp="アーニャ・フォージャー",
        aliases=["Anya", "Subject 007"],
        work_id=1,
        description="A telepathic child.",
        image_url="https://example.com/anya.jpg",
        created_at=datetime(2024, 1, 1),
    )
    char.work = sample_work
    return char


@pytest.fixture
def sample_characters(sample_work: Work) -> list[Character]:
    """Return multiple sample Character ORM objects."""
    c1 = Character(
        id=1,
        name="Anya Forger",
        name_jp="アーニャ・フォージャー",
        aliases=["Anya"],
        work_id=1,
        description="A telepathic child.",
        image_url="https://example.com/anya.jpg",
        created_at=datetime(2024, 1, 1),
    )
    c1.work = sample_work

    c2 = Character(
        id=2,
        name="Loid Forger",
        name_jp="ロイド・フォージャー",
        aliases=["Twilight"],
        work_id=1,
        description="A master spy.",
        image_url="https://example.com/loid.jpg",
        created_at=datetime(2024, 1, 2),
    )
    c2.work = sample_work

    return [c1, c2]


@pytest.fixture
def sample_works() -> list[Work]:
    """Return multiple sample Work ORM objects."""
    return [
        Work(
            id=1,
            title="Spy x Family",
            title_jp="スパイファミリー",
            type="anime",
            description="A spy builds a family.",
            cover_url="https://example.com/cover1.jpg",
            created_at=datetime(2024, 1, 1),
        ),
        Work(
            id=2,
            title="Chainsaw Man",
            title_jp="チェンソーマン",
            type="anime",
            description="A boy with a chainsaw devil heart.",
            cover_url="https://example.com/cover2.jpg",
            created_at=datetime(2024, 2, 1),
        ),
    ]


def _setup_scalars_mock(mock_result: AsyncMock, items: list) -> None:
    """Configure mock_result.scalars().all() to return given items.

    SQLAlchemy's Result.scalars() is synchronous — it returns a ScalarResult
    object whose .all() method returns the list. We set scalars as a MagicMock
    (not AsyncMock) so chained calls work without awaiting.
    """
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = items
    mock_result.scalars = MagicMock(return_value=scalars_mock)


# ── Test get_character ───────────────────────────────────────────────


class TestGetCharacter:
    """Tests for get_character()."""

    @pytest.mark.unit
    async def test_returns_character_with_eager_loaded_work(
        self, mock_db: AsyncMock, sample_character: Character
    ):
        """Returns character with eager-loaded Work relationship."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_character)
        mock_db.execute.return_value = mock_result

        result = await get_character(mock_db, character_id=1)

        assert result is sample_character
        assert result.id == 1
        assert result.name == "Anya Forger"
        assert result.work is not None
        assert result.work.title == "Spy x Family"
        mock_db.execute.assert_awaited_once()

    @pytest.mark.unit
    async def test_raises_404_when_character_not_found(
        self, mock_db: AsyncMock
    ):
        """Raises HTTPException 404 when character does not exist."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_character(mock_db, character_id=999)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Character not found"


# ── Test list_characters ─────────────────────────────────────────────


class TestListCharacters:
    """Tests for list_characters()."""

    @pytest.mark.unit
    async def test_returns_paginated_characters(
        self, mock_db: AsyncMock, sample_characters: list[Character]
    ):
        """Returns PaginatedResponse with characters for default page."""
        # Two execute calls: first for count, second for items
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=2)

        items_result = AsyncMock()
        _setup_scalars_mock(items_result, sample_characters)

        mock_db.execute.side_effect = [count_result, items_result]

        result = await list_characters(mock_db)

        assert isinstance(result, PaginatedResponse)
        assert result.total == 2
        assert result.page == 1
        assert result.size == 20
        assert len(result.items) == 2
        assert all(isinstance(item, CharacterResponse) for item in result.items)
        assert result.items[0].name == "Anya Forger"
        assert result.items[1].name == "Loid Forger"
        assert result.items[0].work is not None
        assert result.items[0].work.title == "Spy x Family"
        assert mock_db.execute.call_count == 2

    @pytest.mark.unit
    async def test_returns_empty_list_when_no_characters(
        self, mock_db: AsyncMock
    ):
        """Returns empty PaginatedResponse when there are no characters."""
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=0)

        items_result = AsyncMock()
        _setup_scalars_mock(items_result, [])

        mock_db.execute.side_effect = [count_result, items_result]

        result = await list_characters(mock_db)

        assert result.total == 0
        assert len(result.items) == 0

    @pytest.mark.unit
    async def test_filters_by_name_ilike(
        self, mock_db: AsyncMock, sample_characters: list[Character]
    ):
        """Filters characters by name using ILIKE (case-insensitive)."""
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=1)

        # Only the matching character
        items_result = AsyncMock()
        _setup_scalars_mock(items_result, [sample_characters[0]])

        mock_db.execute.side_effect = [count_result, items_result]

        result = await list_characters(mock_db, name="anya")

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].name == "Anya Forger"

    @pytest.mark.unit
    async def test_filters_by_work_id(
        self, mock_db: AsyncMock, sample_characters: list[Character]
    ):
        """Filters characters by work_id."""
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=2)

        items_result = AsyncMock()
        _setup_scalars_mock(items_result, sample_characters)

        mock_db.execute.side_effect = [count_result, items_result]

        result = await list_characters(mock_db, work_id=1)

        assert result.total == 2
        assert len(result.items) == 2


# ── Test get_work ────────────────────────────────────────────────────


class TestGetWork:
    """Tests for get_work()."""

    @pytest.mark.unit
    async def test_returns_work_with_characters(
        self, mock_db: AsyncMock, sample_work: Work, sample_character: Character
    ):
        """Returns Work with characters relationship eagerly loaded."""
        sample_work.characters = [sample_character]

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_work)
        mock_db.execute.return_value = mock_result

        result = await get_work(mock_db, work_id=1)

        assert result is sample_work
        assert result.id == 1
        assert result.title == "Spy x Family"
        assert len(result.characters) == 1
        assert result.characters[0].name == "Anya Forger"
        mock_db.execute.assert_awaited_once()

    @pytest.mark.unit
    async def test_raises_404_when_work_not_found(
        self, mock_db: AsyncMock
    ):
        """Raises HTTPException 404 when work does not exist."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_work(mock_db, work_id=999)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Work not found"


# ── Test list_works ──────────────────────────────────────────────────


class TestListWorks:
    """Tests for list_works()."""

    @pytest.mark.unit
    async def test_returns_paginated_works(
        self, mock_db: AsyncMock, sample_works: list[Work]
    ):
        """Returns PaginatedResponse with works for default page."""
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=2)

        items_result = AsyncMock()
        _setup_scalars_mock(items_result, sample_works)

        mock_db.execute.side_effect = [count_result, items_result]

        result = await list_works(mock_db)

        assert isinstance(result, PaginatedResponse)
        assert result.total == 2
        assert result.page == 1
        assert result.size == 20
        assert len(result.items) == 2
        assert all(isinstance(item, WorkResponse) for item in result.items)
        assert result.items[0].title == "Spy x Family"
        assert result.items[1].title == "Chainsaw Man"
        assert mock_db.execute.call_count == 2

    @pytest.mark.unit
    async def test_returns_empty_list_when_no_works(
        self, mock_db: AsyncMock
    ):
        """Returns empty PaginatedResponse when there are no works."""
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=0)

        items_result = AsyncMock()
        _setup_scalars_mock(items_result, [])

        mock_db.execute.side_effect = [count_result, items_result]

        result = await list_works(mock_db)

        assert result.total == 0
        assert len(result.items) == 0
