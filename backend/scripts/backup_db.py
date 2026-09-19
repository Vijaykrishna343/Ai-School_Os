"""
Automated Database Backup Tooling — Phase 30.8.

Supports timestamped PostgreSQL backups via pg_dump (-Fc), SQLite fallback,
SHA-256 checksum sidecars, credential sanitization, and retention cleanup.
"""

import argparse
import hashlib
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("backup_db")


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


def run_backup(
    storage_dir: str = "./storage/backups",
    retention_days: int = 30,
    database_url: str | None = None,
) -> str:
    """
    Perform database backup with SHA-256 checksum generation and retention cleanup.
    Returns path to created backup file.
    """
    db_url = database_url or os.getenv("DATABASE_URL")
    if not db_url:
        try:
            from app.core.config import settings
            db_url = str(settings.DATABASE_URL)
        except Exception:
            pass

    if not db_url:
        raise ValueError("DATABASE_URL must be provided or set in environment variables.")

    sanitized_url = sanitize_database_url(db_url)
    logger.info("Starting database backup for target: %s", sanitized_url)

    backup_path = Path(storage_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if "sqlite" in db_url:
        db_file = db_url.replace("sqlite:///", "").replace("./", "")
        db_src = Path(db_file)
        if not db_src.exists():
            db_src = Path("school.db")

        target_backup = backup_path / f"backup_AISchoolOS_{timestamp}.db"
        if db_src.exists():
            shutil.copy2(db_src, target_backup)
        else:
            raise FileNotFoundError(f"SQLite source database file '{db_src}' does not exist.")
    else:
        # Native PostgreSQL backup via pg_dump
        params = parse_postgres_url(db_url)
        target_backup = backup_path / f"backup_AISchoolOS_{timestamp}.dump"

        pg_dump_bin = find_pg_binary("pg_dump")
        env = os.environ.copy()
        if params["password"]:
            env["PGPASSWORD"] = params["password"]

        cmd = [
            pg_dump_bin,
            "-h", params["host"],
            "-p", params["port"],
            "-U", params["user"],
            "-d", params["dbname"],
            "-F", "c",  # Custom archive format (compressed, supports pg_restore)
            "-f", str(target_backup),
        ]

        logger.info("Executing pg_dump to generate custom archive: %s", target_backup.name)
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                logger.error("pg_dump failed with exit code %s: %s", result.returncode, result.stderr)
                raise RuntimeError(f"pg_dump execution failed: {result.stderr.strip()}")
        except FileNotFoundError:
            raise RuntimeError(
                f"PostgreSQL binary '{pg_dump_bin}' not found. Please ensure PostgreSQL client tools are installed."
            )

    # Validate generated backup exists and is not empty
    if not target_backup.exists() or target_backup.stat().st_size == 0:
        raise RuntimeError(f"Backup verification failed: '{target_backup}' is missing or 0 bytes.")

    logger.info("Backup archive generated successfully (Size: %s bytes)", target_backup.stat().st_size)

    # Generate SHA-256 Checksum Sidecar
    checksum = calculate_sha256(target_backup)
    checksum_file = backup_path / f"{target_backup.name}.sha256"
    with open(checksum_file, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {target_backup.name}\n")
    logger.info("SHA-256 checksum sidecar generated: %s (hash: %s)", checksum_file.name, checksum)

    # Retention Cleanup
    if retention_days > 0:
        cutoff_time = time.time() - (retention_days * 86400)
        for file in backup_path.glob("backup_AISchoolOS_*"):
            if file.is_file() and file.stat().st_mtime < cutoff_time:
                try:
                    file.unlink()
                    logger.info("Cleaned up expired backup file: %s", file.name)
                except Exception as exc:
                    logger.warning("Could not delete expired backup file %s: %s", file.name, exc)

    return str(target_backup)


def main():
    parser = argparse.ArgumentParser(description="AI School OS Automated Database Backup")
    parser.add_argument("--storage-dir", default="./storage/backups", help="Directory to store backup files")
    parser.add_argument("--retention-days", type=int, default=30, help="Backup retention period in days")
    parser.add_argument("--database-url", default=None, help="Target Database URL (overrides DATABASE_URL env)")
    args = parser.parse_args()

    try:
        backup_file = run_backup(
            storage_dir=args.storage_dir,
            retention_days=args.retention_days,
            database_url=args.database_url,
        )
        logger.info("Database backup completed successfully: %s", backup_file)
        sys.exit(0)
    except Exception as exc:
        logger.error("Database backup failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
