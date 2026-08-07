from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.core.config import settings
from app.database.base import Base 
from app.database import models

# Import all models here so Alembic can detect them
from app.models import *  # noqa: F401,F403

config = context.config

# Use the database URL from our application settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
print("=" * 80)
print("DATABASE URL:", config.get_main_option("sqlalchemy.url"))
print("=" * 80)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

print("=" * 80)
print("TABLES IN METADATA:")
print(list(target_metadata.tables.keys()))
print("=" * 80)


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

    target_metadata = Base.metadata