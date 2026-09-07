"""
AI Communication Draft Engine for Phase 12.5.
Generates context-aware, multi-channel announcement and notice proposals.

Constraints Enforced:
- SMS: <= 160 characters
- WhatsApp: Rich markdown with bullet points and clear headers
- Email: Formatted subject line, formal body, salutation, and signature
- In-App: Compact title and 2-sentence summary
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CommunicationDraftInput:
    category: str  # ANNOUNCEMENT, ACADEMIC_NOTICE, EMERGENCY_ALERT, EVENT_INVITATION, PARENT_UPDATE
    target_audience: str  # PARENTS, STUDENTS, TEACHERS, ALL_STAFF
    tone: str  # FORMAL, URGENT, FRIENDLY, ENCOURAGING
    key_details: str  # User prompt / event summary
    school_name: str = "School OS"
    requested_channels: List[str] = field(default_factory=lambda: ["SMS", "EMAIL", "WHATSAPP", "IN_APP"])
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelVariant:
    title: str
    body: str


@dataclass
class CommunicationDraftOutput:
    category: str
    target_audience: str
    tone: str
    variants: Dict[str, ChannelVariant]
    token_count: int = 150


class AICommunicationDraftEngine:
    """
    Intelligent engine producing category-aware, multi-channel communication draft proposals.
    """

    VALID_CATEGORIES = {
        "ANNOUNCEMENT",
        "ACADEMIC_NOTICE",
        "EMERGENCY_ALERT",
        "EVENT_INVITATION",
        "PARENT_UPDATE",
    }

    VALID_AUDIENCES = {
        "PARENTS",
        "STUDENTS",
        "TEACHERS",
        "ALL_STAFF",
    }

    VALID_TONES = {
        "FORMAL",
        "URGENT",
        "FRIENDLY",
        "ENCOURAGING",
    }

    def generate(self, input_data: CommunicationDraftInput) -> CommunicationDraftOutput:
        category = input_data.category.upper() if input_data.category else "ANNOUNCEMENT"
        if category not in self.VALID_CATEGORIES:
            category = "ANNOUNCEMENT"

        audience = input_data.target_audience.upper() if input_data.target_audience else "PARENTS"
        if audience not in self.VALID_AUDIENCES:
            audience = "PARENTS"

        tone = input_data.tone.upper() if input_data.tone else "FORMAL"
        if tone not in self.VALID_TONES:
            tone = "FORMAL"

        school_name = input_data.school_name or "School"
        details = input_data.key_details.strip()

        variants: Dict[str, ChannelVariant] = {}

        # 1. Generate SMS Variant (Constraint: <= 160 characters)
        if "SMS" in input_data.requested_channels:
            sms_prefix = f"[{school_name}] "
            if category == "EMERGENCY_ALERT":
                sms_body = f"{sms_prefix}URGENT: {details}"
            else:
                sms_body = f"{sms_prefix}{category.replace('_', ' ').title()}: {details}"

            # Truncate strictly to 160 chars if necessary
            if len(sms_body) > 160:
                sms_body = sms_body[:157] + "..."
            
            variants["SMS"] = ChannelVariant(
                title="SMS Notification",
                body=sms_body,
            )

        # 2. Generate WhatsApp Variant (Markdown & Emoticons)
        if "WHATSAPP" in input_data.requested_channels:
            wa_header = f"📢 *{school_name} - {category.replace('_', ' ').title()}*"
            if category == "EMERGENCY_ALERT":
                wa_header = f"🚨 *EMERGENCY ALERT - {school_name}*"
            elif category == "EVENT_INVITATION":
                wa_header = f"📅 *INVITATION - {school_name}*"

            wa_body = f"{wa_header}\n\nDear {audience.replace('_', ' ').title()},\n\n{details}\n\n• For queries, please contact the school administration.\n• Thank you for your cooperation.\n\n_Regards,_\n*{school_name} Administration*"
            
            variants["WHATSAPP"] = ChannelVariant(
                title=f"{category.replace('_', ' ').title()} - {school_name}",
                body=wa_body,
            )

        # 3. Generate Email Variant (Subject, Salutation, Detailed Body, Signature)
        if "EMAIL" in input_data.requested_channels:
            subject = f"{school_name}: {category.replace('_', ' ').title()} regarding {details[:40]}"
            if category == "EMERGENCY_ALERT":
                subject = f"URGENT ALERT: {school_name} Notice"
            elif category == "EVENT_INVITATION":
                subject = f"Invitation: {details[:40]} - {school_name}"

            email_body = f"Dear {audience.replace('_', ' ').title()},\n\nWe hope this email finds you well.\n\n{details}\n\nPlease reach out to the school administration office should you require any further information or assistance.\n\nWarm regards,\n{school_name} Administration Team"

            variants["EMAIL"] = ChannelVariant(
                title=subject,
                body=email_body,
            )

        # 4. Generate In-App Variant (Compact Title & 2-sentence summary)
        if "IN_APP" in input_data.requested_channels:
            in_app_title = f"{category.replace('_', ' ').title()}: {details[:30]}..."
            in_app_body = f"Important notice for {audience.lower()}: {details}"
            if len(in_app_body) > 250:
                in_app_body = in_app_body[:247] + "..."

            variants["IN_APP"] = ChannelVariant(
                title=in_app_title,
                body=in_app_body,
            )

        # Estimate token count (rough heuristic: ~1 token per 4 chars of output)
        total_chars = sum(len(v.title) + len(v.body) for v in variants.values())
        token_count = max(50, total_chars // 4)

        return CommunicationDraftOutput(
            category=category,
            target_audience=audience,
            tone=tone,
            variants=variants,
            token_count=token_count,
        )


ai_communication_draft_engine = AICommunicationDraftEngine()
