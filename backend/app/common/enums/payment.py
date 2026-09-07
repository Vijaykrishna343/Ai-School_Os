from enum import Enum


class PaymentProvider(str, Enum):
    RAZORPAY = "RAZORPAY"
    STRIPE = "STRIPE"
    OTHER = "OTHER"


class PaymentOrderStatus(str, Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class PaymentTransactionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    REFUNDED = "REFUNDED"
