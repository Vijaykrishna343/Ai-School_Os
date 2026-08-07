from app.dependencies.services import section_service
from app.services.section_service import SectionService


def get_section_service() -> SectionService:
    """
    FastAPI dependency that returns the SectionService singleton.
    """
    return section_service