from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Cookie, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import DecodeError, InvalidSignatureError
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from models import UserModel

security = HTTPBearer(auto_error=False)  # Don't auto error to allow cookie fallback

# If you are in production set secure_bool to true but in dev set it to false
secure_bool = False


def set_secure_cookies(response: Response, access_token: str, refresh_token: str):
    """Set secure HTTP-only cookies for tokens"""
    # Set access token cookie (5 minutes)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=60 * 5,  # 5 minutes
        httponly=True,  # Prevent XSS attacks
        secure=secure_bool,  # Only send over HTTPS in production
        samesite="lax",  # CSRF protection
    )

    # Set refresh token cookie (24 hours)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=60 * 60 * 24,  # 24 hours
        httponly=True,  # Prevent XSS attacks
        secure=secure_bool,  # Only send over HTTPS in production
        samesite="lax",  # CSRF protection
    )


def clear_auth_cookies(response: Response):
    """Clear authentication cookies"""
    response.delete_cookie(
        key="access_token", httponly=True, secure=True, samesite="lax"
    )
    response.delete_cookie(
        key="refresh_token", httponly=True, secure=True, samesite="lax"
    )


def get_authenticated_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None, alias="access_token"),
):
    """
    Get authenticated user from either Authorization header or HTTP-only cookie
    Priority: Authorization header -> Cookie
    """
    token = None

    # First try to get token from Authorization header
    if credentials:
        token = credentials.credentials
    # If no Authorization header, try to get from cookie
    elif access_token:
        token = access_token
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: No token provided",
        )

    try:
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = decoded.get("user_id", None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, user_id not in the payload",
            )

        if decoded.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, token type not valid",
            )

        # Check token expiration
        exp_timestamp = decoded.get("exp")
        if not exp_timestamp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, no expiration time",
            )

        if datetime.now() > datetime.fromtimestamp(exp_timestamp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, token expired",
            )

        user_obj = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, user not found",
            )

        return user_obj

    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed, invalid signature",
        )
    except DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed, decode failed",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed, {e}",
        )


def generate_access_token(user_id: int, expires_in: int = 60 * 5) -> str:
    now = datetime.now()
    payload = {
        "type": "access",
        "user_id": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def generate_refresh_token(user_id: int, expires_in: int = 3600 * 24) -> str:
    now = datetime.now()
    payload = {
        "type": "refresh",
        "user_id": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def validate_refresh_token(refresh_token: str, db: Session):
    """Validate refresh token and return user_id"""
    try:
        decoded = jwt.decode(
            refresh_token, settings.JWT_SECRET_KEY, algorithms=["HS256"]
        )
        user_id = decoded.get("user_id", None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token: user_id not in payload",
            )

        if decoded.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token: token type not valid",
            )

        exp_timestamp = decoded.get("exp")
        if not exp_timestamp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token: no expiration time",
            )

        if datetime.now() > datetime.fromtimestamp(exp_timestamp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
            )

        # Check if user still exists
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        return user_id

    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token: invalid signature",
        )
    except DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token: decode failed",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {e}",
        )


def validate_refresh_token_from_cookie(
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(None, alias="refresh_token"),
):
    """Validate refresh token from HTTP-only cookie and return user_id"""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required"
        )

    return validate_refresh_token(refresh_token, db)
