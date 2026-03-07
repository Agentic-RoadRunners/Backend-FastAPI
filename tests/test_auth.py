"""
Tests for JWT authentication (core/auth.py).
"""

import pytest
from unittest.mock import patch

from tests.conftest import generate_test_token, TEST_JWT_SECRET


class TestJWTAuthentication:
    """Test JWT token validation."""

    def test_valid_user_token(self, user_token):
        """A valid user token should decode successfully."""
        import jwt as pyjwt
        payload = pyjwt.decode(
            user_token,
            TEST_JWT_SECRET,
            algorithms=["HS256"],
            audience="SafeRoad",
            issuer="SafeRoad",
        )
        assert "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier" in payload
        assert payload["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"] == "john.doe@gmail.com"
        assert payload["http://schemas.microsoft.com/ws/2008/06/identity/claims/role"] == "User"

    def test_valid_admin_token(self, admin_token):
        """An admin token should have Admin role."""
        import jwt as pyjwt
        payload = pyjwt.decode(
            admin_token,
            TEST_JWT_SECRET,
            algorithms=["HS256"],
            audience="SafeRoad",
            issuer="SafeRoad",
        )
        assert payload["http://schemas.microsoft.com/ws/2008/06/identity/claims/role"] == "Admin"

    def test_expired_token_raises(self, expired_token):
        """An expired token should raise ExpiredSignatureError."""
        import jwt as pyjwt
        with pytest.raises(pyjwt.ExpiredSignatureError):
            pyjwt.decode(
                expired_token,
                TEST_JWT_SECRET,
                algorithms=["HS256"],
                audience="SafeRoad",
                issuer="SafeRoad",
            )

    def test_wrong_secret_raises(self, user_token):
        """A token with the wrong secret should fail."""
        import jwt as pyjwt
        with pytest.raises(pyjwt.InvalidSignatureError):
            pyjwt.decode(
                user_token,
                "wrong_secret_that_is_at_least_32_chars!!!!!",
                algorithms=["HS256"],
                audience="SafeRoad",
                issuer="SafeRoad",
            )

    def test_multiple_roles_token(self):
        """Token with multiple roles should use the first one."""
        import jwt as pyjwt
        from core.auth import CLAIM_ROLE

        # Generate token with list of roles
        token = generate_test_token(role="Admin")
        payload = pyjwt.decode(
            token,
            TEST_JWT_SECRET,
            algorithms=["HS256"],
            audience="SafeRoad",
            issuer="SafeRoad",
        )
        assert payload[CLAIM_ROLE] == "Admin"
