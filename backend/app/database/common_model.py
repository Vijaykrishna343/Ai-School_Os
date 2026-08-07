from app.common.mixins.database.soft_delete_mixin import SoftDeleteMixin
from app.common.mixins.database.timestamp_mixin import TimestampMixin
from app.common.mixins.database.uuid_mixin import UUIDMixin
from app.database.base_entity import BaseEntity


class CommonModel(
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    BaseEntity,
):
    """
    Abstract base model shared by all business entities.
    """

    __abstract__ = True