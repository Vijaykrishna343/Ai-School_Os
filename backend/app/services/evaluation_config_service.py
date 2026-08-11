from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.grading.assessment_type_weightage import AssessmentTypeWeightage
from app.models.grading.evaluation_config import EvaluationConfig
from app.repositories.academic_year.academic_year_repository import (
    AcademicYearRepository,
    academic_year_repository,
)
from app.repositories.grading.evaluation_config_repository import (
    EvaluationConfigRepository,
    evaluation_config_repository,
)
from app.schemas.grading.evaluation_config import (
    EvaluationConfigCreate,
    EvaluationConfigListResponse,
    EvaluationConfigResponse,
    EvaluationConfigUpdate,
)

logger = get_logger(__name__)


class EvaluationConfigService:
    def __init__(
        self,
        repository: EvaluationConfigRepository = evaluation_config_repository,
        academic_year_repo: AcademicYearRepository = academic_year_repository,
    ) -> None:
        self.repository = repository
        self.academic_year_repository = academic_year_repo

    def create_evaluation_config(
        self,
        db: Session,
        config_data: EvaluationConfigCreate,
        current_school_id: UUID | None = None,
    ) -> EvaluationConfig:
        if current_school_id and config_data.school_id != current_school_id:
            raise ForbiddenException("Cannot create evaluation config for another school.")

        ay = self.academic_year_repository.get(db, config_data.academic_year_id)
        if not ay or ay.school_id != config_data.school_id or ay.is_deleted:
            raise NotFoundException("Academic Year", str(config_data.academic_year_id))

        if config_data.is_default:
            existing_default = self.repository.get_default_for_year(
                db, config_data.school_id, config_data.academic_year_id
            )
            if existing_default:
                existing_default.is_default = False
                self.repository.update(db, existing_default)

        config = EvaluationConfig(
            school_id=config_data.school_id,
            academic_year_id=config_data.academic_year_id,
            name=config_data.name.strip(),
            description=config_data.description,
            calculation_mode=config_data.calculation_mode,
            retest_policy=config_data.retest_policy,
            rounding_mode=config_data.rounding_mode,
            gpa_enabled=config_data.gpa_enabled,
            is_default=config_data.is_default,
        )

        for w in config_data.weightages:
            config.weightages.append(
                AssessmentTypeWeightage(
                    assessment_type=w.assessment_type,
                    weightage_percentage=w.weightage_percentage,
                )
            )

        created = self.repository.create(db, config)
        logger.info("EvaluationConfig '%s' created with ID: %s", created.name, created.id)
        return created

    def get_evaluation_config(
        self,
        db: Session,
        config_id: UUID,
        current_school_id: UUID | None = None,
    ) -> EvaluationConfig:
        if current_school_id:
            config = self.repository.get_by_id_and_school(db, config_id, current_school_id)
        else:
            config = self.repository.get(db, config_id)

        if not config or config.is_deleted:
            raise NotFoundException("EvaluationConfig", str(config_id))
        return config

    def list_evaluation_configs(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> EvaluationConfigListResponse:
        items, total = self.repository.list_by_school(
            db, school_id, academic_year_id=academic_year_id, page=page, page_size=page_size
        )
        total_pages = ceil(total / page_size) if total > 0 else 0

        return EvaluationConfigListResponse(
            items=[EvaluationConfigResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


evaluation_config_service = EvaluationConfigService()
