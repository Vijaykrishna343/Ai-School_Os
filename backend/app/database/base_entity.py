from app.database.base import Base


class BaseEntity(Base):
    """
    Base entity for all database models.
    """

    __abstract__ = True