"""
Application Payment Exception Hierarchy — Phase 25.2
"""

class PaymentGatewayError(Exception):
    """Base exception for all payment gateway abstraction errors."""
    def __init__(self, message: str, provider: str | None = None):
        super().__init__(message)
        self.message = message
        self.provider = provider


class PaymentAuthenticationError(PaymentGatewayError):
    """Raised when payment gateway credentials/API keys fail authentication."""
    pass


class PaymentInvalidRequestError(PaymentGatewayError):
    """Raised when payment order parameters or amounts are invalid."""
    pass


class PaymentProviderUnavailableError(PaymentGatewayError):
    """Raised when gateway experiences connection timeouts or HTTP failures."""
    pass


class PaymentSignatureVerificationError(PaymentGatewayError):
    """Raised when client callback or webhook HMAC signature verification fails."""
    pass


class PaymentConfigurationError(PaymentGatewayError):
    """Raised when tenant or application payment configuration is missing."""
    pass


class PaymentUnsupportedProviderError(PaymentGatewayError):
    """Raised when an unsupported payment provider is requested."""
    pass
