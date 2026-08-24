"""
AsyncJobRunner Service — Processes background tasks and manages retries/backoff.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.logger.logger import get_logger
from app.database.session import SessionLocal
from app.models.background_job import BackgroundJob, JobStatus, JobType
from app.repositories.job_repository import job_repository

logger = get_logger(__name__)


class AsyncJobRunner:
    def process_job(self, school_id: UUID, job_id: UUID, db: Session | None = None) -> None:
        """
        Main worker entry point executed in background task thread.
        Uses provided session or creates its own DB session for isolation.
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            try:
                BackgroundJob.__table__.create(db.get_bind(), checkfirst=True)
            except Exception:
                pass

            job = job_repository.get_by_id(db, school_id, job_id)
            if not job or job.status in (JobStatus.COMPLETED, JobStatus.CANCELLED):
                return

            logger.info(
                "JOB_STARTED [school_id:%s] [job_id:%s] [type:%s]",
                school_id,
                job_id,
                job.job_type,
            )
            job_repository.mark_started(db, job)
            db.commit()

            if job.job_type == JobType.BATCH_REPORT_CARD_GEN:
                self._execute_batch_report_card_gen(db, job)
            elif job.job_type == JobType.BULK_NOTIFICATION_DISPATCH:
                self._execute_bulk_notification_dispatch(db, job)
            else:
                err_msg = f"Unsupported job type: {job.job_type}"
                logger.error(
                    "JOB_FAILED [school_id:%s] [job_id:%s]: %s",
                    school_id,
                    job_id,
                    err_msg,
                )
                job_repository.mark_failed(db, job, err_msg)
                db.commit()

        except Exception as exc:
            logger.exception(
                "JOB_FAILED [school_id:%s] [job_id:%s] Unhandled exception: %s",
                school_id,
                job_id,
                exc,
            )
            db.rollback()
            try:
                job = job_repository.get_by_id(db, school_id, job_id)
                if job:
                    job_repository.mark_failed(db, job, f"Worker execution error: {type(exc).__name__}")
                    db.commit()
            except Exception:
                pass
        finally:

            if should_close:
                db.close()

    def _execute_batch_report_card_gen(self, db: Session, job: BackgroundJob) -> None:
        from app.schemas.grading.report_card import BatchReportCardBatchGenerateRequest
        from app.services.report_card_service import report_card_service

        payload = job.payload
        school_id = job.school_id
        section_id_str = payload.get("section_id")
        academic_year_id_str = payload.get("academic_year_id")
        school_class_id_str = payload.get("school_class_id")

        if not all([section_id_str, academic_year_id_str, school_class_id_str]):
            job_repository.mark_failed(db, job, "Missing required batch parameters in job payload.")
            db.commit()
            return

        req = BatchReportCardBatchGenerateRequest.model_validate(payload)
        resp = report_card_service.batch_generate_report_cards(db, req, current_school_id=school_id)

        job_repository.mark_completed(
            db,
            job,
            result={
                "generated_count": resp.generated_count,
                "updated_count": resp.updated_count,
                "total_processed": resp.total_processed,
                "missing_data_count": resp.missing_data_count,
            },
        )
        db.commit()

    def _execute_bulk_notification_dispatch(self, db: Session, job: BackgroundJob) -> None:
        from app.models.notification import NotificationChannel, NotificationRecipientType
        from app.services.notification_service import notification_service

        payload = job.payload
        recipients = payload.get("recipients", [])
        template_key = payload.get("template_key", "general_announcement")
        template_variables = payload.get("template_variables", {})
        channel_str = payload.get("channel", "IN_APP")
        channel = NotificationChannel(channel_str.upper()) if channel_str else NotificationChannel.IN_APP

        total = len(recipients)
        job_repository.update_progress(db, job, processed_items=0, total_items=total)
        db.commit()

        sent_ids = []
        for idx, rec in enumerate(recipients, start=1):
            r_type_str = rec.get("recipient_type", "STAFF")
            r_type = NotificationRecipientType(r_type_str.upper()) if r_type_str else NotificationRecipientType.STAFF
            r_name = rec.get("recipient_name", "Recipient")
            r_contact = rec.get("recipient_contact", "")

            notif = notification_service.create_and_send(
                db=db,
                school_id=job.school_id,
                recipient_type=r_type,
                recipient_name=r_name,
                recipient_contact=r_contact,
                channel=channel,
                template_key=template_key,
                template_variables=template_variables,
            )
            db.commit()

            sent_ids.append(str(notif.id))
            job_repository.update_progress(db, job, processed_items=idx, total_items=total)
            db.commit()

        job_repository.mark_completed(
            db,
            job,
            result={
                "dispatched_count": len(sent_ids),
                "total_recipients": total,
                "notification_ids": sent_ids,
            },
        )
        db.commit()


async_job_runner = AsyncJobRunner()
