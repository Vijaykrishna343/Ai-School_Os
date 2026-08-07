from app.identity.services import (
    AuthenticationService,
    authentication_service,
)


def get_authentication_service() -> AuthenticationService:
    return authentication_service