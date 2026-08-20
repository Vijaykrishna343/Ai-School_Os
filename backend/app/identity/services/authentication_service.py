from uuid import UUID

from sqlalchemy.orm import Session

from app.common.enums.identity.token_type import TokenType
from app.common.exceptions import (
    BadRequestException,
    UnauthorizedException,
)
from app.common.logger.logger import get_logger
from app.core.config import settings
from app.identity.repositories import identity_user_repository
from app.identity.schemas.user import (
    RefreshToken,
    UserLogin,
    UserLoginResponse,
)
from app.identity.security import (
    jwt_manager,
    verify_password,
)
from app.identity.services.base_identity_service import (
    BaseIdentityService,
)
from app.repositories.school.school_repository import school_repository

logger = get_logger(__name__)


class AuthenticationService(BaseIdentityService):
    """
    Handles authentication operations.
    """

    def login(
        self,
        db: Session,
        credentials: UserLogin,
        client_ip: str | None = None,
    ) -> UserLoginResponse:
        """
        Authenticate a user with school_code, email, and password.
        """
        logger.info(
            "Login attempt for email '%s' under school code '%s'",
            credentials.email,
            credentials.school_code,
        )

        # ---------------------------------------
        # Find School
        # ---------------------------------------

        school = school_repository.get_by_code(
            db,
            credentials.school_code,
        )

        if school is None:
            logger.warning(
                "Authentication failure: Invalid school code '%s'",
                credentials.school_code,
            )
            if client_ip:
                from app.common.security.rate_limiter import rate_limiter
                rate_limiter.record_failure(client_ip)
            raise BadRequestException(
                "Invalid school code."
            )

        # ---------------------------------------
        # Find User
        # ---------------------------------------

        user = identity_user_repository.get_by_email(
            db,
            school.id,
            credentials.email,
        )

        if user is None:
            logger.warning(
                "Authentication failure: User email '%s' not found for school '%s'",
                credentials.email,
                credentials.school_code,
            )
            if client_ip:
                from app.common.security.rate_limiter import rate_limiter
                rate_limiter.record_failure(client_ip)
            raise UnauthorizedException(
                "Invalid email or password."
            )

        # ---------------------------------------
        # Active Check
        # ---------------------------------------

        if not user.is_active:
            logger.warning(
                "Authentication failure: User account ID '%s' is inactive",
                user.id,
            )
            if client_ip:
                from app.common.security.rate_limiter import rate_limiter
                rate_limiter.record_failure(client_ip)
            raise UnauthorizedException(
                "User account is inactive."
            )

        # ---------------------------------------
        # Password Check
        # ---------------------------------------

        if not verify_password(
            credentials.password,
            user.password_hash,
        ):
            logger.warning(
                "Authentication failure: Invalid credentials for user ID '%s'",
                user.id,
            )
            if client_ip:
                from app.common.security.rate_limiter import rate_limiter
                rate_limiter.record_failure(client_ip)
            raise UnauthorizedException(
                "Invalid email or password."
            )

        # Successful authentication: reset rate limiter for this IP
        if client_ip:
            from app.common.security.rate_limiter import rate_limiter
            rate_limiter.reset_attempts(client_ip)

        # ---------------------------------------
        # Tokens
        # ---------------------------------------

        access_token = jwt_manager.create_access_token(
            user.id,
            school.id,
        )

        refresh_token = jwt_manager.create_refresh_token(
            user.id,
            school.id,
        )

        # ---------------------------------------
        # Update Last Login
        # ---------------------------------------

        identity_user_repository.update_last_login(
            db,
            user,
        )

        logger.info(
            "User %s logged in successfully (school=%s)",
            user.id,
            school.id,
        )

        return UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=(
                settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            ),
        )

    def refresh_token(
        self,
        db: Session,
        data: RefreshToken,
    ) -> UserLoginResponse:
        """
        Issue a new access + refresh token pair using a valid refresh token.
        """
        logger.info("Token refresh request received")
        payload = jwt_manager.verify_token(
            data.refresh_token,
        )

        if payload is None:
            logger.warning("Token refresh failure: Invalid or expired refresh token")
            raise UnauthorizedException(
                "Invalid or expired refresh token."
            )

        # -------------------------------------------
        # Validate token type
        # -------------------------------------------

        token_type = payload.get("type")

        if token_type != TokenType.REFRESH:
            logger.warning("Token refresh failure: Invalid token type '%s'", token_type)
            raise UnauthorizedException(
                "Invalid token type. Refresh token required."
            )

        # -------------------------------------------
        # Retrieve user
        # -------------------------------------------

        user_id = UUID(payload["sub"])
        school_id = UUID(payload["school_id"])

        user = identity_user_repository.get_by_id(
            db,
            user_id,
        )

        if user is None:
            logger.warning("Token refresh failure: User ID '%s' not found", user_id)
            raise UnauthorizedException(
                "User not found."
            )

        if not user.is_active:
            logger.warning("Token refresh failure: User ID '%s' is inactive", user_id)
            raise UnauthorizedException(
                "User account is inactive."
            )

        # -------------------------------------------
        # Issue new tokens
        # -------------------------------------------

        new_access_token = (
            jwt_manager.create_access_token(
                user_id,
                school_id,
            )
        )

        new_refresh_token = (
            jwt_manager.create_refresh_token(
                user_id,
                school_id,
            )
        )

        logger.info(
            "Token refreshed successfully for user %s",
            user_id,
        )

        return UserLoginResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=(
                settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            ),
        )


authentication_service = AuthenticationService()