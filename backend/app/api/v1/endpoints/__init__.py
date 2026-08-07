from .academic_year import router as academic_year_router
from .parent import router as parent_router
from .school import router as school_router
from .school_class import router as school_class_router
from .subject import router as subject_router

__all__ = [
    "academic_year_router",
    "parent_router",
    "school_router",
    "school_class_router",
    "subject_router",
]