import json

import click

from app.common.logger.logger import get_logger, setup_logging
from app.database.session import SessionLocal
from app.identity.seeders import seed_identity

logger = get_logger(__name__)


@click.group()
def cli() -> None:
    """School ERP CLI management tool."""
    setup_logging()


@cli.command(name="seed-identity")
def seed_identity_cmd() -> None:
    """
    Seed default permissions, system roles, and role-permission assignments.
    Idempotent and safe to run multiple times.
    """
    click.echo("Starting identity data seeding...")
    db = SessionLocal()
    try:
        summary = seed_identity(db)
        db.commit()
        click.echo("Seeding completed successfully:")
        click.echo(json.dumps(summary, indent=2))
    except Exception as e:
        db.rollback()
        click.echo(f"Error seeding identity data: {e}", err=True)
        raise click.ClickException(str(e))
    finally:
        db.close()


if __name__ == "__main__":
    cli()
