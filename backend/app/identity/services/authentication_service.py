import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.enums.identity.token_type import TokenType
from app.common.exceptions import (
    BadRequestException,
    ForbiddenException,
    UnauthorizedException,
)
from app.common.logger.logger import get_logger
from app.core.config import settings
from app.identity.models.user import IdentityUser
from app.identity.repositories import (
    identity_password_reset_token_repository,
    identity_refresh_token_repository,
    identity_user_repository,
)
from app.identity.schemas.user import (
    ForgotPassword,
    ForgotPasswordResponse,
    RefreshToken,
    ResetPassword,
    ResetPasswordResponse,
    UserLogin,
    UserLoginResponse,
    UserLogout,
    UserLogoutResponse,
)
from app.identity.security import (
    hash_password,
    jwt_manager,
    verify_password,
)
from app.identity.services.base_identity_service import (
    BaseIdentityService,
)
from app.identity.services.password_reset_delivery_service import (
    password_reset_delivery_service,
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
        Records an active refresh token session for explicit revocation tracking.
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
            raise UnauthorizedException(
                "Invalid email or password."
            )

        # ---------------------------------------
        # Active Check
        # ---------------------------------------

        if not user.is_active or getattr(user, "status", "ACTIVE") in ("SUSPENDED", "INACTIVE", "DELETED", "BLOCKED"):
            logger.warning(
                "Authentication failure: User account ID '%s' is inactive",
                user.id,
            )
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
        # Record Refresh Session
        # ---------------------------------------
        refresh_payload = jwt_manager.decode_token(refresh_token)
        jti = refresh_payload["jti"]
        exp_ts = refresh_payload["exp"]
        expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        token_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()

        identity_refresh_token_repository.create_session(
            db=db,
            school_id=school.id,
            user_id=user.id,
            jti=jti,
            expires_at=expires_at,
            token_hash=token_hash,
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
        Issue a new access + refresh token pair using a valid, unrevoked refresh token.
        Rotates the refresh token and revokes the previous session.
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

        jti = payload.get("jti")
        if not jti:
            logger.warning("Token refresh failure: Missing token identifier (jti)")
            raise UnauthorizedException(
                "Invalid refresh token identifier."
            )

        # -------------------------------------------
        # Retrieve and validate persisted refresh session with row lock
        # -------------------------------------------
        session = identity_refresh_token_repository.get_by_jti_for_update(db, jti)
        if session is None:
            logger.warning("Token refresh failure: Session for jti '%s' not found", jti)
            raise UnauthorizedException(
                "Refresh token session not found or invalid."
            )

        if session.is_revoked:
            logger.warning("Token refresh failure: Refresh token jti '%s' is revoked", jti)
            raise UnauthorizedException(
                "Refresh token has been revoked."
            )

        token_hash = hashlib.sha256(data.refresh_token.encode("utf-8")).hexdigest()
        if session.token_hash and session.token_hash != token_hash:
            logger.warning("Token refresh failure: Token hash mismatch for jti '%s'", jti)
            raise UnauthorizedException(
                "Invalid refresh token."
            )

        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        if expires_at <= now:
            logger.warning("Token refresh failure: Refresh token jti '%s' has expired", jti)
            raise UnauthorizedException(
                "Refresh token has expired."
            )

        # -------------------------------------------
        # Retrieve and validate user & tenant
        # -------------------------------------------

        user_id = UUID(payload["sub"])
        school_id = UUID(payload["school_id"])

        if session.user_id != user_id or session.school_id != school_id:
            logger.warning("Token refresh failure: Session tenant/user mismatch for jti '%s'", jti)
            raise UnauthorizedException(
                "Invalid refresh token session ownership."
            )

        user = identity_user_repository.get_by_id(
            db,
            user_id,
        )

        if user is None or user.is_deleted:
            logger.warning("Token refresh failure: User ID '%s' not found", user_id)
            raise UnauthorizedException(
                "User not found."
            )

        if not user.is_active or getattr(user, "status", "ACTIVE") in ("SUSPENDED", "INACTIVE", "DELETED", "BLOCKED"):
            logger.warning("Token refresh failure: User ID '%s' is inactive", user_id)
            raise UnauthorizedException(
                "User account is inactive."
            )

        # -------------------------------------------
        # Atomic Rotation in single transaction
        # -------------------------------------------
        try:
            # 1. Revoke old refresh session (uncommitted in current transaction)
            identity_refresh_token_repository.revoke_session(
                db=db,
                session=session,
                reason="REFRESH_ROTATION",
                commit=False,
            )

            # 2. Issue new tokens
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

            new_refresh_payload = jwt_manager.decode_token(new_refresh_token)
            new_jti = new_refresh_payload["jti"]
            new_exp_ts = new_refresh_payload["exp"]
            new_expires_at = datetime.fromtimestamp(new_exp_ts, tz=timezone.utc)
            new_token_hash = hashlib.sha256(new_refresh_token.encode("utf-8")).hexdigest()

            # 3. Create new session record (uncommitted in current transaction)
            identity_refresh_token_repository.create_session(
                db=db,
                school_id=school_id,
                user_id=user_id,
                jti=new_jti,
                expires_at=new_expires_at,
                token_hash=new_token_hash,
                commit=False,
            )

            # 4. Commit atomic rotation transaction
            db.commit()
        except Exception:
            db.rollback()
            raise

        logger.info(
            "Token refreshed and rotated successfully for user %s",
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

    def logout(
        self,
        db: Session,
        user: IdentityUser,
        data: UserLogout | None = None,
    ) -> UserLogoutResponse:
        """
        Explicitly revoke the caller's refresh token session on logout.
        Idempotent: safe to call repeatedly even if already revoked or expired.
        Strict tenant/user validation: rejects attempts to revoke another user's session.
        """
        logger.info("Logout request received for user %s (school=%s)", user.id, user.school_id)

        if data and data.refresh_token:
            payload = jwt_manager.verify_token(data.refresh_token)
            if payload is not None:
                token_user_id = payload.get("sub")
                token_school_id = payload.get("school_id")

                # Strict cross-user and cross-tenant checks
                if token_user_id and str(token_user_id) != str(user.id):
                    logger.warning(
                        "Logout forbidden: User %s attempted to revoke token for user %s",
                        user.id,
                        token_user_id,
                    )
                    raise ForbiddenException("Cannot revoke a session belonging to another user.")

                if token_school_id and str(token_school_id) != str(user.school_id):
                    logger.warning(
                        "Logout forbidden: Cross-tenant revocation attempt from school %s for token school %s",
                        user.school_id,
                        token_school_id,
                    )
                    raise ForbiddenException("Cannot revoke a session belonging to another tenant.")

                jti = payload.get("jti")
                if jti:
                    session = identity_refresh_token_repository.get_by_jti(db, jti)
                    if session:
                        if session.user_id != user.id or session.school_id != user.school_id:
                            logger.warning("Logout forbidden: Session user/tenant mismatch")
                            raise ForbiddenException("Cannot revoke a session belonging to another user or tenant.")
                        if not session.is_revoked:
                            identity_refresh_token_repository.revoke_session(
                                db=db,
                                session=session,
                                reason="USER_LOGOUT",
                            )

        return UserLogoutResponse(message="Logged out successfully")

    def forgot_password(
        self,
        db: Session,
        data: ForgotPassword,
        client_ip: str | None = None,
    ) -> ForgotPasswordResponse:
        """
        Initiate password recovery / reset request.
        Strict anti-enumeration: Always returns identical generic response regardless of whether
        the user exists, is inactive, or whether the school code is valid.
        """
        logger.info(
            "Forgot password request for email '%s' (school_code=%s, client_ip=%s)",
            data.email,
            data.school_code,
            client_ip,
        )

        generic_response = ForgotPasswordResponse(
            success=True,
            message="If an account with that email exists, password reset instructions have been sent.",
        )

        user: IdentityUser | None = None
        school_id: UUID | None = None
        school_code: str | None = data.school_code

        if data.school_code:
            school = school_repository.get_by_code(db, data.school_code)
            if school is None:
                logger.info("Forgot password: School code '%s' not found", data.school_code)
                return generic_response

            school_id = school.id
            user = identity_user_repository.get_by_email(db, school_id, data.email)
        else:
            matching_users = identity_user_repository.get_all_by_email(db, data.email)
            if len(matching_users) == 1:
                user = matching_users[0]
                school_id = user.school_id
                school = school_repository.get_by_id(db, school_id)
                if school:
                    school_code = school.code
            elif len(matching_users) > 1:
                logger.info(
                    "Forgot password: Multiple accounts found for email '%s' without school_code",
                    data.email,
                )
                return generic_response

        if user is None:
            logger.info("Forgot password: User not found for email '%s'", data.email)
            return generic_response

        if not user.is_active or getattr(user, "status", "ACTIVE") in ("SUSPENDED", "INACTIVE", "DELETED", "BLOCKED"):
            logger.info("Forgot password: User ID '%s' is inactive", user.id)
            return generic_response

        # Generate cryptographically secure URL-safe raw token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )

        # Store only hashed token in database
        identity_password_reset_token_repository.create_token_record(
            db=db,
            school_id=user.school_id,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            requested_ip=client_ip,
            commit=True,
        )

        # Dispatch reset notification
        password_reset_delivery_service.send_password_reset_link(
            email=user.email,
            raw_token=raw_token,
            school_code=school_code,
        )

        logger.info("Forgot password reset token generated and dispatched for user ID %s", user.id)
        return generic_response

    def reset_password(
        self,
        db: Session,
        data: ResetPassword,
    ) -> ResetPasswordResponse:
        """
        Validate single-use reset token and update user's password.
        Atomically marks token as used, updates password hash (Argon2),
        and invalidates all existing refresh-token sessions for the user.
        """
        logger.info("Reset password request received")

        token_hash = hashlib.sha256(data.token.strip().encode("utf-8")).hexdigest()

        # Retrieve token record with row lock to prevent concurrent consumption
        token_record = identity_password_reset_token_repository.get_by_token_hash_for_update(
            db,
            token_hash,
        )

        if token_record is None:
            logger.warning("Reset password failure: Token record not found")
            raise BadRequestException("Invalid or expired password reset token.")

        if token_record.used_at is not None:
            logger.warning("Reset password failure: Token ID '%s' already used", token_record.id)
            raise BadRequestException("Password reset token has already been used.")

        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        if expires_at <= now:
            logger.warning("Reset password failure: Token ID '%s' has expired", token_record.id)
            raise BadRequestException("Password reset token has expired.")

        # Validate user
        user = identity_user_repository.get_by_id(db, token_record.user_id)
        if user is None or user.is_deleted:
            logger.warning("Reset password failure: User ID '%s' not found or deleted", token_record.user_id)
            raise BadRequestException("User account associated with this token is invalid.")

        if not user.is_active or getattr(user, "status", "ACTIVE") in ("SUSPENDED", "INACTIVE", "DELETED", "BLOCKED"):
            logger.warning("Reset password failure: User ID '%s' is inactive", user.id)
            raise BadRequestException("User account associated with this token is inactive.")

        if user.school_id != token_record.school_id:
            logger.warning("Reset password failure: Tenant mismatch for user ID '%s'", user.id)
            raise BadRequestException("Tenant mismatch for password reset token.")

        # Atomic transaction execution:
        # 1. Update password hash
        # 2. Mark token as used
        # 3. Revoke all active refresh sessions
        try:
            user.password_hash = hash_password(data.new_password)
            db.add(user)

            identity_password_reset_token_repository.mark_used(
                db=db,
                record=token_record,
                commit=False,
            )

            identity_refresh_token_repository.revoke_all_active_sessions_for_user(
                db=db,
                user_id=user.id,
                school_id=user.school_id,
                reason="PASSWORD_RESET",
                commit=False,
            )

            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Reset password failure: Database transaction error")
            raise

        logger.info(
            "Password successfully reset and all active sessions revoked for user ID %s",
            user.id,
        )

        return ResetPasswordResponse(
            success=True,
            message="Password has been successfully reset. Please log in with your new password.",
        )


authentication_service = AuthenticationService()