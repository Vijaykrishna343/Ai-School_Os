from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums.visitor import ReceptionInquiryStatus, VisitorStatus
from app.common.exceptions import BadRequestException, ValidationException
from app.models.visitor.reception_inquiry import ReceptionInquiry
from app.models.visitor.visitor import Visitor
from app.schemas.visitor import (
    AnalyticsPeriod,
    AppointmentAnalyticsMetrics,
    DailyTrendItem,
    HostTypeCountItem,
    InquiryAnalyticsMetrics,
    OperationalAnalyticsMetrics,
    PurposeCountItem,
    ReceptionAnalyticsResponse,
    VisitorAnalyticsMetrics,
)


class ReceptionAnalyticsService:
    """
    Business logic and aggregation engine for Reception Analytics & Operational Reporting.
    Enforces strict multi-tenant isolation via school_id and soft-delete protection.
    """

    def get_analytics(
        self,
        db: Session,
        school_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> ReceptionAnalyticsResponse:
        """
        Calculates and returns operational analytics for visitors, inquiries, appointments,
        daily activity trends, and operational performance metrics.
        """
        today = date.today()

        # Date Range Validation & Normalization
        if start_date and end_date:
            if start_date > end_date:
                raise BadRequestException("start_date must be less than or equal to end_date.")
            if (end_date - start_date).days > 365:
                raise BadRequestException("Date range cannot exceed 365 days.")
        elif end_date and not start_date:
            start_date = end_date - timedelta(days=29)
        elif start_date and not end_date:
            end_date = start_date + timedelta(days=29)
        else:
            end_date = today
            start_date = today - timedelta(days=29)

        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)
        now_dt = datetime.now()

        # 1. Visitor Metrics
        period_visitors_q = (
            select(Visitor)
            .where(
                Visitor.school_id == school_id,
                Visitor.is_deleted == False,
                Visitor.check_in_time >= start_dt,
                Visitor.check_in_time <= end_dt,
            )
        )
        period_visitors = db.scalars(period_visitors_q).all()

        total_visitors_period = len(period_visitors)
        checked_in_period = sum(1 for v in period_visitors if v.status == VisitorStatus.CHECKED_IN)
        checked_out_period = sum(1 for v in period_visitors if v.status == VisitorStatus.CHECKED_OUT)

        # Currently Active Visitors right now (tenant-wide active check-ins)
        currently_active_count = db.scalar(
            select(func.count(Visitor.id)).where(
                Visitor.school_id == school_id,
                Visitor.is_deleted == False,
                Visitor.status == VisitorStatus.CHECKED_IN,
            )
        ) or 0

        visitor_metrics = VisitorAnalyticsMetrics(
            total=total_visitors_period,
            checked_in=checked_in_period,
            checked_out=checked_out_period,
            currently_active=currently_active_count,
        )

        # 2. Inquiry Metrics
        period_inquiries_q = (
            select(ReceptionInquiry)
            .where(
                ReceptionInquiry.school_id == school_id,
                ReceptionInquiry.is_deleted == False,
                ReceptionInquiry.created_at >= start_dt,
                ReceptionInquiry.created_at <= end_dt,
            )
        )
        period_inquiries = db.scalars(period_inquiries_q).all()

        total_inquiries_period = len(period_inquiries)
        pending_count = sum(1 for i in period_inquiries if i.status == ReceptionInquiryStatus.PENDING)
        in_progress_count = sum(1 for i in period_inquiries if i.status == ReceptionInquiryStatus.IN_PROGRESS)
        resolved_count = sum(1 for i in period_inquiries if i.status == ReceptionInquiryStatus.RESOLVED)
        cancelled_count = sum(1 for i in period_inquiries if i.status == ReceptionInquiryStatus.CANCELLED)

        inquiry_metrics = InquiryAnalyticsMetrics(
            total=total_inquiries_period,
            pending=pending_count,
            in_progress=in_progress_count,
            resolved=resolved_count,
            cancelled=cancelled_count,
        )

        # 3. Appointment Metrics
        appts_in_period = [i for i in period_inquiries if i.appointment_time is not None]
        total_appts = len(appts_in_period)

        # Upcoming appointments for the school that are not resolved or cancelled
        upcoming_appts_count = db.scalar(
            select(func.count(ReceptionInquiry.id)).where(
                ReceptionInquiry.school_id == school_id,
                ReceptionInquiry.is_deleted == False,
                ReceptionInquiry.appointment_time != None,
                ReceptionInquiry.appointment_time >= now_dt,
                ReceptionInquiry.status.notin_([ReceptionInquiryStatus.RESOLVED, ReceptionInquiryStatus.CANCELLED]),
            )
        ) or 0

        completed_appts = sum(
            1 for i in appts_in_period if i.status == ReceptionInquiryStatus.RESOLVED or (i.appointment_time and i.appointment_time < now_dt)
        )

        appointment_metrics = AppointmentAnalyticsMetrics(
            total=total_appts,
            upcoming=upcoming_appts_count,
            completed=completed_appts,
        )

        # 4. Operational Performance & Breakdown Metrics
        checkout_durations = [
            (v.check_out_time - v.check_in_time).total_seconds() / 60.0
            for v in period_visitors
            if v.check_out_time is not None and v.check_in_time is not None and v.check_out_time >= v.check_in_time
        ]

        avg_duration: float | None = None
        if checkout_durations:
            avg_duration = round(sum(checkout_durations) / len(checkout_durations), 1)

        checkin_hours = [v.check_in_time.hour for v in period_visitors if v.check_in_time is not None]
        peak_hour: int | None = None
        if checkin_hours:
            hour_counts: dict[int, int] = {}
            for h in checkin_hours:
                hour_counts[h] = hour_counts.get(h, 0) + 1
            peak_hour = max(hour_counts.keys(), key=lambda h: hour_counts[h])

        purpose_map: dict[str, int] = {}
        for v in period_visitors:
            p = (v.purpose or "General").strip()
            purpose_map[p] = purpose_map.get(p, 0) + 1
        sorted_purposes = sorted(purpose_map.items(), key=lambda item: item[1], reverse=True)[:5]
        purpose_items = [PurposeCountItem(purpose=p, count=c) for p, c in sorted_purposes]

        host_map: dict[str, int] = {}
        for v in period_visitors:
            ht = v.host_type.value if hasattr(v.host_type, "value") else (str(v.host_type) if v.host_type else "Unspecified")
            host_map[ht] = host_map.get(ht, 0) + 1
        sorted_hosts = sorted(host_map.items(), key=lambda item: item[1], reverse=True)
        host_items = [HostTypeCountItem(host_type=ht, count=c) for ht, c in sorted_hosts]

        operational_metrics = OperationalAnalyticsMetrics(
            avg_visitor_duration_minutes=avg_duration,
            peak_checkin_hour=peak_hour,
            visitors_by_purpose=purpose_items,
            visitors_by_host_type=host_items,
        )

        # 5. Daily Activity Trends
        visitor_daily_map: dict[date, int] = {}
        for v in period_visitors:
            if v.check_in_time:
                d = v.check_in_time.date()
                visitor_daily_map[d] = visitor_daily_map.get(d, 0) + 1

        inquiry_daily_map: dict[date, int] = {}
        for i in period_inquiries:
            if i.created_at:
                d = i.created_at.date()
                inquiry_daily_map[d] = inquiry_daily_map.get(d, 0) + 1

        visitor_trend_list: list[DailyTrendItem] = []
        inquiry_trend_list: list[DailyTrendItem] = []

        curr_d = start_date
        while curr_d <= end_date:
            visitor_trend_list.append(DailyTrendItem(date=curr_d, count=visitor_daily_map.get(curr_d, 0)))
            inquiry_trend_list.append(DailyTrendItem(date=curr_d, count=inquiry_daily_map.get(curr_d, 0)))
            curr_d += timedelta(days=1)

        return ReceptionAnalyticsResponse(
            period=AnalyticsPeriod(start_date=start_date, end_date=end_date),
            visitors=visitor_metrics,
            inquiries=inquiry_metrics,
            appointments=appointment_metrics,
            operational_metrics=operational_metrics,
            visitor_trend=visitor_trend_list,
            inquiry_trend=inquiry_trend_list,
        )


reception_analytics_service = ReceptionAnalyticsService()
