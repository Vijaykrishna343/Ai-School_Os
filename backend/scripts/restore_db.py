"""
Disaster Recovery Restore Tooling — Phase 30.8.

Provides safe database restore capabilities via pg_restore, SQLite fallback,
SHA-256 checksum validation, and destructive operation safeguards (--confirm).
"""

import argparse
import hashlib
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("restore_db")


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def sanitize_database_url(url: str) -> str:
    """Sanitize database URL to avoid printing credentials in logs."""
    try:
        parsed = urlparse(url)
        if parsed.password:
            netloc = f"{parsed.username or ''}:***@{parsed.hostname or ''}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return parsed._replace(netloc=netloc).geturl()
        return url
    except Exception:
        return "<sanitized_database_url>"


def find_pg_binary(binary_name: str) -> str:
    """Find PostgreSQL binary in system PATH or common installation directories."""
    found = shutil.which(binary_name)
    if found:
        return found

    if sys.platform == "win32":
        base_paths = [
            r"C:\Program Files\PostgreSQL\17\bin",
            r"C:\Program Files\PostgreSQL\16\bin",
            r"C:\Program Files\PostgreSQL\15\bin",
            r"C:\Program Files\PostgreSQL\14\bin",
        ]
        exe_name = f"{binary_name}.exe"
        for p in base_paths:
            candidate = Path(p) / exe_name
            if candidate.exists():
                return str(candidate)

    return binary_name


def parse_postgres_url(db_url: str) -> dict:
    """Extract connection parameters from PostgreSQL URL."""
    clean_url = db_url.replace("postgresql+psycopg2://", "postgresql://")
    parsed = urlparse(clean_url)
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "dbname": parsed.path.lstrip("/"),
    }


def run_restore(
    backup_file_path: str,
    target_database_url: str | None = None,
    verify_checksum: bool = True,
    confirmed: bool = True,
) -> bool:
    """
    Restore database from backup file after validating checksum integrity and confirmation safety.
    Returns True if restore succeeded.
    """
    if not confirmed:
        raise PermissionError(
            "Destructive restore operation aborted: --confirm flag is required to restore database."
        )

    backup_path = Path(backup_file_path)
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file '{backup_file_path}' not found.")

    if backup_path.stat().st_size == 0:
        raise ValueError(f"Backup file '{backup_file_path}' is empty (0 bytes). Cannot restore.")

    # 1. SHA-256 Checksum Validation
    if verify_checksum:
        checksum_path = backup_path.parent / f"{backup_path.name}.sha256"
        if not checksum_path.exists():
            raise ValueError(
                f"Checksum sidecar file missing for '{backup_file_path}'. Expected '{checksum_path.name}'."
            )
        with open(checksum_path, "r", encoding="utf-8") as f:
            expected_line = f.read().strip()
        expected_hash = expected_line.split()[0]
        actual_hash = calculate_sha256(backup_path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"Checksum validation failed for '{backup_file_path}'. Expected {expected_hash}, got {actual_hash}."
            )
        logger.info("SHA-256 checksum verified successfully: %s", actual_hash)

    # 2. Target Database Resolution
    db_url = target_database_url or os.getenv("DATABASE_URL")
    if not db_url:
        try:
            from app.core.config import settings
            db_url = str(settings.DATABASE_URL)
        except Exception:
            pass

    if not db_url:
        raise ValueError("Target database URL must be provided or set in environment variables.")

    sanitized_url = sanitize_database_url(db_url)
    logger.info("Executing database restore on target: %s", sanitized_url)

    if "sqlite" in db_url:
        db_file = db_url.replace("sqlite:///", "").replace("./", "")
        target_path = Path(db_file)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, target_path)
        logger.info("SQLite database restored successfully from %s to %s", backup_path.name, target_path)
        return True
    else:
        # Native PostgreSQL restore via pg_restore
        params = parse_postgres_url(db_url)
        pg_restore_bin = find_pg_binary("pg_restore")
        env = os.environ.copy()
        if params["password"]:
            env["PGPASSWORD"] = params["password"]

        cmd = [
            pg_restore_bin,
            "-h", params["host"],
            "-p", params["port"],
            "-U", params["user"],
            "-d", params["dbname"],
            "--clean",
            "--if-exists",
            "--no-owner",
            "-v",
            str(backup_path),
        ]

        logger.info("Executing pg_restore on target database: %s", params["dbname"])
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            # pg_restore returns non-zero if there are non-critical warnings or errors.
            # In pg_restore, exit code 0 is success, 1 is warning (often harmless object drops), >1 is failure.
            if result.returncode > 1:
                logger.error("pg_restore failed with exit code %s: %s", result.returncode, result.stderr)
                raise RuntimeError(f"pg_restore execution failed (code {result.returncode}): {result.stderr.strip()}")
            elif result.returncode == 1:
                logger.warning("pg_restore completed with warnings: %s", result.stderr.strip()[:200])
        except FileNotFoundError:
            raise RuntimeError(
                f"PostgreSQL binary '{pg_restore_bin}' not found. Please ensure PostgreSQL client tools are installed."
            )

        logger.info("PostgreSQL database restored successfully from archive %s", backup_path.name)
        return True


def main():
    parser = argparse.ArgumentParser(description="AI School OS Database Restore Tool")
    parser.add_argument("backup_file", help="Path to backup file (.dump or .db)")
    parser.add_argument("--database-url", default=None, help="Target Database URL (overrides DATABASE_URL env)")
    parser.add_argument("--no-verify-checksum", action="store_true", help="Skip SHA-256 sidecar checksum verification")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Explicit confirmation required to execute destructive database restore",
    )
    args = parser.parse_args()

    try:
        success = run_restore(
            backup_file_path=args.backup_file,
            target_database_url=args.database_url,
            verify_checksum=not args.no_verify_checksum,
            confirmed=args.confirm,
        )
        logger.info("Restore operation finished successfully: success=%s", success)
        sys.exit(0 if success else 1)
    except Exception as exc:
        logger.error("Database restore failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
