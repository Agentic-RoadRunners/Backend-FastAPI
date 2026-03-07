"""
JWT authentication utilities.
Validates tokens issued by the .NET backend using the same shared secret.

CRITICAL: .NET uses ClaimTypes with full XML namespace URIs as claim keys.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import settings

security = HTTPBearer()

# .NET ClaimTypes constants — these are the actual keys in the JWT payload
CLAIM_NAME_IDENTIFIER = (
    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
)
CLAIM_EMAIL = (
    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
)
CLAIM_NAME = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
CLAIM_ROLE = (
    "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Decode and validate Bearer JWT token.
    Returns dict with user_id, email, name, role.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )

    user_id = payload.get(CLAIM_NAME_IDENTIFIER)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identifier claim",
        )

    # Role can be a string or a list (if user has multiple roles)
    role_claim = payload.get(CLAIM_ROLE, "User")
    if isinstance(role_claim, list):
        role = role_claim[0] if role_claim else "User"
    else:
        role = role_claim

    return {
        "user_id": user_id,
        "email": payload.get(CLAIM_EMAIL, ""),
        "name": payload.get(CLAIM_NAME, ""),
        "role": role,
    }


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency that requires the Admin role."""
    if user["role"] != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user
