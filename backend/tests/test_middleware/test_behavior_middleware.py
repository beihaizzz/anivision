"""
Tests for app.middleware.behavior_middleware.

Verifies BehaviorLoggingMiddleware correctly logs user actions
and skips excluded paths (health, docs).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database import get_db


# ══════════════════════════════════════════════════════════════════════════
# Helpers
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


def _setup_mock_execute_result(mock_db):
    """Configure mock_db.execute() to return a MagicMock that properly
    handles .scalar(), .scalars().all(), .all(), and .scalar_one_or_none().

    Uses MagicMock (not AsyncMock) so attribute access returns sync values,
    avoiding 'coroutine' object has no attribute 'all' errors.
    """
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_result.scalars.return_value.all.return_value = []
    mock_result.all.return_value = []
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result


# ══════════════════════════════════════════════════════════════════════════
# BehaviorLoggingMiddleware Tests
# ══════════════════════════════════════════════════════════════════════════


class TestBehaviorLogging:
    """Tests for BehaviorLoggingMiddleware behavior logging."""

    # ── Logging Actions ──────────────────────────────────────────────────

    @pytest.mark.unit
    def test_logs_search_action(self, client, app, mock_db):
        """GET /api/search should call _log_behavior with action_type='search'."""
        _override_db(app, mock_db)
        _setup_mock_execute_result(mock_db)

        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/search?q=test")
            assert response.status_code == 200

            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args.kwargs
            assert call_kwargs["action_type"] == "search"
            assert call_kwargs["path"] == "/api/search"

    @pytest.mark.unit
    def test_logs_view_posts_action(self, client, app, mock_db):
        """GET /api/posts should call _log_behavior with action_type='view_posts'."""
        _override_db(app, mock_db)
        _setup_mock_execute_result(mock_db)

        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/posts")
            assert response.status_code == 200

            mock_log.assert_called_once()
            assert mock_log.call_args.kwargs["action_type"] == "view_posts"

    @pytest.mark.unit
    def test_logs_view_characters_action(self, client, app, mock_db):
        """GET /api/characters should call _log_behavior with action_type='view_characters'."""
        _override_db(app, mock_db)
        _setup_mock_execute_result(mock_db)

        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/characters")
            assert response.status_code == 200

            mock_log.assert_called_once()
            assert mock_log.call_args.kwargs["action_type"] == "view_characters"

    @pytest.mark.unit
    def test_logs_unmapped_path_as_other(self, client, app, mock_db):
        """Unmapped paths should be logged as action_type='other'."""
        _override_db(app, mock_db)
        _setup_mock_execute_result(mock_db)

        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/unknown-endpoint")
            # May be 404 or 405 — middleware runs regardless
            assert response.status_code in (200, 404, 405)

            mock_log.assert_called_once()
            assert mock_log.call_args.kwargs["action_type"] == "other"

    # ── Skipping Excluded Paths ──────────────────────────────────────────

    @pytest.mark.unit
    def test_skips_health_check(self, client):
        """GET /api/health should NOT call _log_behavior."""
        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/health")
            assert response.status_code == 200
            mock_log.assert_not_called()

    @pytest.mark.unit
    def test_skips_docs(self, client):
        """GET /api/docs should NOT be logged."""
        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/docs")
            assert response.status_code == 200
            mock_log.assert_not_called()

    @pytest.mark.unit
    def test_skips_redoc(self, client):
        """GET /api/redoc should NOT be logged."""
        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/redoc")
            assert response.status_code == 200
            mock_log.assert_not_called()

    @pytest.mark.unit
    def test_skips_openapi_json(self, client):
        """GET /api/openapi.json should NOT be logged."""
        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/openapi.json")
            assert response.status_code == 200
            mock_log.assert_not_called()

    # ── Anonymous vs Authenticated User ──────────────────────────────────

    @pytest.mark.unit
    def test_logs_anonymous_user_id_none(self, client, app, mock_db):
        """Anonymous requests should log with user_id=None."""
        _override_db(app, mock_db)
        _setup_mock_execute_result(mock_db)

        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/search?q=test")
            assert response.status_code == 200

            mock_log.assert_called_once()
            assert mock_log.call_args.kwargs["user_id"] is None

    # ── IP Address and User-Agent ────────────────────────────────────────

    @pytest.mark.unit
    def test_logs_ip_address(self, client, app, mock_db):
        """Request should log the client IP address."""
        _override_db(app, mock_db)
        _setup_mock_execute_result(mock_db)

        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/search?q=test")
            assert response.status_code == 200

            mock_log.assert_called_once()
            ip = mock_log.call_args.kwargs["ip_address"]
            assert ip == "testclient"  # TestClient uses "testclient" as host

    @pytest.mark.unit
    def test_logs_user_agent(self, client, app, mock_db):
        """Request should log the User-Agent header."""
        _override_db(app, mock_db)
        _setup_mock_execute_result(mock_db)

        custom_ua = "AniVisionTest/1.0"
        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get(
                "/api/search?q=test",
                headers={"User-Agent": custom_ua},
            )
            assert response.status_code == 200

            mock_log.assert_called_once()
            assert mock_log.call_args.kwargs["user_agent"] == custom_ua

    # ── Path Pattern Matching ────────────────────────────────────────────

    @pytest.mark.unit
    def test_logs_recognition_upload_action(self, client, app, mock_db):
        """POST /api/recognition/upload should log action_type='recognition_upload'.

        The endpoint requires authentication — returns 401.
        Middleware runs after call_next and logs regardless of status code.
        """
        _override_db(app, mock_db)
        _setup_mock_execute_result(mock_db)

        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.post("/api/recognition/upload")
            # Auth required — 401, but middleware still logs
            assert response.status_code == 401

            mock_log.assert_called_once()
            assert mock_log.call_args.kwargs["action_type"] == "recognition_upload"

    @pytest.mark.unit
    def test_logs_view_history_action(self, client, app, mock_db):
        """GET /api/recognition/history should log action_type='view_history'.

        The endpoint requires authentication — returns 401.
        Middleware logs regardless.
        """
        _override_db(app, mock_db)
        _setup_mock_execute_result(mock_db)

        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/recognition/history")
            # Auth required — 401, but middleware still logs
            assert response.status_code == 401

            mock_log.assert_called_once()
            assert mock_log.call_args.kwargs["action_type"] == "view_history"

    @pytest.mark.unit
    def test_logs_view_profile_action(self, client, app, mock_db):
        """GET /api/users/1 should log action_type='view_profile'.

        The mock DB returns no user → 404, but middleware still logs.
        """
        _override_db(app, mock_db)
        _setup_mock_execute_result(mock_db)

        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/users/1")
            # User not found → 404, but middleware logs regardless
            assert response.status_code == 404

            mock_log.assert_called_once()
            assert mock_log.call_args.kwargs["action_type"] == "view_profile"

    @pytest.mark.unit
    def test_logs_view_analytics_action(self, client, app, mock_db):
        """GET /api/analytics/overview should log action_type='view_analytics'.

        The analytics endpoints require authentication — returns 401.
        Middleware logs regardless.
        """
        _override_db(app, mock_db)
        _setup_mock_execute_result(mock_db)

        with patch(
            "app.middleware.behavior_middleware._log_behavior",
            new_callable=AsyncMock,
        ) as mock_log:
            response = client.get("/api/analytics/overview")
            # Auth required — 401, but middleware still logs
            assert response.status_code == 401

            mock_log.assert_called_once()
            assert mock_log.call_args.kwargs["action_type"] == "view_analytics"
