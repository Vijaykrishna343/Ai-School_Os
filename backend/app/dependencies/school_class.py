from app.repositories.school_class import (
    SchoolClassRepository,
    school_class_repository,
)


def get_school_class_repository() -> SchoolClassRepository:
    """
    Dependency provider for SchoolClassRepository.
    Returns the module-level singleton.
    """
    return school_class_repository