"""
Tests for app.utils.security — password hashing and JWT token management.

Covers verify_password, get_password_hash, create_access_token, and
roundtrip encode/decode scenarios.
"""

from datetime import datetime, timedelta

import pytest
from jose import jwt
from passlib.hash import bcrypt

from app.config import settings
from app.utils.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)


# ══════════════════════════════════════════════════════════════════════════
# verify_password
# ══════════════════════════════════════════════════════════════════════════


class TestVerifyPassword:
    """Test password verification against bcrypt hashes."""

    @pytest.mark.unit
    def test_correct_password_returns_true(self):
        """verify_password returns True when the plaintext matches the hash."""
        plain = "my_secure_p@ssw0rd"
        hashed = get_password_hash(plain)
        assert verify_password(plain, hashed) is True

    @pytest.mark.unit
    def test_wrong_password_returns_false(self):
        """verify_password returns False when the plaintext does not match."""
        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False

    @pytest.mark.unit
    def test_empty_password_against_hash(self):
        """Empty password should verify against its own hash."""
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True

    @pytest.mark.unit
    def test_empty_password_against_nonempty_hash(self):
        """Empty password should not match a non-empty password's hash."""
        hashed = get_password_hash("nonempty")
        assert verify_password("", hashed) is False

    @pytest.mark.unit
    def test_empty_hash_raises_error(self):
        """An empty or invalid hash string should raise a ValueError."""
        with pytest.raises(ValueError):
            verify_password("anything", "")

    @pytest.mark.unit
    def test_unicode_password(self):
        """Passwords with Unicode characters verify correctly."""
        plain = "パスワード🔒"
        hashed = get_password_hash(plain)
        assert verify_password(plain, hashed) is True

    @pytest.mark.unit
    def test_long_password(self):
        """Very long passwords should hash and verify correctly."""
        plain = "a" * 1024
        hashed = get_password_hash(plain)
        assert verify_password(plain, hashed) is True

    @pytest.mark.unit
    def test_similar_passwords_dont_match(self):
        """Passwords that differ by one character should not match."""
        hashed = get_password_hash("Password123!")
        assert verify_password("password123!", hashed) is False


# ══════════════════════════════════════════════════════════════════════════
# get_password_hash
# ══════════════════════════════════════════════════════════════════════════


class TestGetPasswordHash:
    """Test bcrypt hash generation."""

    @pytest.mark.unit
    def test_produces_valid_bcrypt_hash(self):
        """The returned string is a valid bcrypt hash prefixed with $2b$."""
        hashed = get_password_hash("test_password")
        assert isinstance(hashed, str)
        assert hashed.startswith("$2")
        # bcrypt.verify confirms it's a real hash
        assert bcrypt.verify("test_password", hashed) is True

    @pytest.mark.unit
    def test_same_password_produces_different_hash(self):
        """Each call generates a unique salt, so hashes differ."""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2

    @pytest.mark.unit
    def test_hash_can_be_verified(self):
        """A generated hash should verify against the original password."""
        password = "verifiable_p@ss"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    @pytest.mark.unit
    def test_empty_string(self):
        """Hashing an empty string produces a valid bcrypt hash."""
        hashed = get_password_hash("")
        assert hashed.startswith("$2")
        assert verify_password("", hashed) is True

    @pytest.mark.unit
    def test_special_characters(self):
        """Passwords with special characters hash correctly."""
        special = r"!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        hashed = get_password_hash(special)
        assert verify_password(special, hashed) is True


# ══════════════════════════════════════════════════════════════════════════
# create_access_token
# ══════════════════════════════════════════════════════════════════════════


class TestCreateAccessToken:
    """Test JWT access token creation."""

    @pytest.mark.unit
    def test_returns_string_with_three_parts(self):
        """A JWT is a base64-encoded string with three dot-separated parts."""
        token = create_access_token(data={"sub": "42"})
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

    @pytest.mark.unit
    def test_decoded_token_contains_sub_claim(self):
        """The token payload includes the 'sub' claim from input data."""
        token = create_access_token(data={"sub": "42"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "42"

    @pytest.mark.unit
    def test_token_includes_expiration(self):
        """The token payload includes an 'exp' (expiration) claim."""
        token = create_access_token(data={"sub": "user"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload
        assert isinstance(payload["exp"], int)

    @pytest.mark.unit
    def test_custom_expiry_is_respected(self):
        """A custom expires_delta produces a token with that lifetime."""
        custom_delta = timedelta(minutes=5)
        before = datetime.utcnow()
        token = create_access_token(data={"sub": "custom"}, expires_delta=custom_delta)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        after = datetime.utcnow()

        exp_time = datetime.utcfromtimestamp(payload["exp"])
        # Token expiry should be roughly 'before' + 5 minutes
        expected_lower = before + timedelta(minutes=4, seconds=30)
        expected_upper = after + timedelta(minutes=5)
        assert expected_lower <= exp_time <= expected_upper

    @pytest.mark.unit
    def test_default_expiry_uses_settings(self):
        """Without a custom delta, the default ACCESS_TOKEN_EXPIRE_MINUTES is used."""
        token = create_access_token(data={"sub": "default"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        before = datetime.utcnow()
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        # Default is 1440 minutes (1 day)
        expected_lower = before + timedelta(minutes=1439)
        assert exp_time > expected_lower

    @pytest.mark.unit
    def test_token_with_additional_claims(self):
        """Extra data claims are preserved in the token payload."""
        data = {"sub": "user1", "role": "admin", "scope": "write"}
        token = create_access_token(data=data)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "user1"
        assert payload["role"] == "admin"
        assert payload["scope"] == "write"

    @pytest.mark.unit
    def test_empty_data_dict(self):
        """An empty data dict produces a token containing only the 'exp' claim."""
        token = create_access_token(data={})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload
        assert "sub" not in payload

    @pytest.mark.unit
    def test_data_original_dict_not_mutated(self):
        """The input data dict is copied, so the original is not modified."""
        original = {"sub": "safe"}
        original_copy = original.copy()
        create_access_token(data=original)
        assert original == original_copy
        assert "exp" not in original

    @pytest.mark.unit
    def test_token_with_negative_expiry_raises_on_decode(self):
        """A token with a negative expiry delta raises ExpiredSignatureError."""
        token = create_access_token(
            data={"sub": "past"}, expires_delta=timedelta(minutes=-10)
        )
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": True},
            )


# ══════════════════════════════════════════════════════════════════════════
# JWT Roundtrip (encode → decode)
# ══════════════════════════════════════════════════════════════════════════


class TestJwtRoundtrip:
    """End-to-end encode-then-decode scenarios (no conftest fixtures)."""

    @pytest.mark.unit
    def test_valid_token_roundtrip(self):
        """Encode a payload, then decode it — all claims should survive."""
        data = {"sub": "roundtrip_user", "email": "rt@example.com"}
        token = create_access_token(data=data)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == data["sub"]
        assert decoded["email"] == data["email"]
        assert "exp" in decoded

    @pytest.mark.unit
    def test_expired_token_raises_on_decode(self):
        """An expired token (negative delta) raises ExpiredSignatureError on decode."""
        token = create_access_token(
            data={"sub": "expired_user"}, expires_delta=timedelta(minutes=-60)
        )
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": True},
            )

    @pytest.mark.unit
    def test_tampered_token_rejected(self):
        """A token with a modified payload fails signature verification."""
        token = create_access_token(data={"sub": "genuine"})
        parts = token.split(".")
        # Replace the payload section with a forged payload
        forged_payload = jwt.encode({"sub": "hacker"}, "wrong-key", algorithm="HS256").split(".")[1]
        tampered = f"{parts[0]}.{forged_payload}.{parts[2]}"
        with pytest.raises(jwt.JWTError):
            jwt.decode(tampered, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    @pytest.mark.unit
    def test_wrong_secret_key_rejected(self):
        """Decoding with an incorrect secret key fails."""
        token = create_access_token(data={"sub": "user"})
        with pytest.raises(jwt.JWTError):
            jwt.decode(token, "wrong-secret-key", algorithms=[settings.ALGORITHM])

    @pytest.mark.unit
    def test_wrong_algorithm_rejected(self):
        """Decoding with a mismatched algorithm fails."""
        token = create_access_token(data={"sub": "user"})
        with pytest.raises(jwt.JWTError):
            jwt.decode(token, settings.SECRET_KEY, algorithms=["HS512"])
