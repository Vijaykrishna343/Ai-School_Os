from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.academic_year.class_progression_rule import ClassProgressionRule
from app.repositories.academic_year.class_progression_rule_repository import (
    ClassProgressionRuleRepository,
    class_progression_rule_repository,
)
from app.repositories.school.school_repository import (
    SchoolRepository,
    school_repository,
)
from app.repositories.school_class.school_class_repository import (
    SchoolClassRepository,
    school_class_repository,
)
from app.schemas.academic_year.class_progression_rule_schema import (
    ClassProgressionRuleCreate,
    ClassProgressionRuleUpdate,
)

logger = get_logger(__name__)


class ClassProgressionRuleService:
    """
    Business logic for Class Progression Matrix operations.
    """

    def __init__(
        self,
        repository: ClassProgressionRuleRepository,
        school_repository: SchoolRepository,
        school_class_repository: SchoolClassRepository,
    ) -> None:
        self.repository = repository
        self.school_repository = school_repository
        self.school_class_repository = school_class_repository

    def create_rule(
        self,
        db: Session,
        rule_data: ClassProgressionRuleCreate,
        current_school_id: UUID,
    ) -> ClassProgressionRule:
        """
        Create a new class progression rule for a school.
        """
        logger.info(
            "Creating progression rule for source class ID '%s' in school ID: %s",
            rule_data.source_class_id,
            current_school_id,
        )

        # 1. Validate School
        school = self.school_repository.get(db, current_school_id)
        if school is None or school.is_deleted:
            raise NotFoundException("School", str(current_school_id))

        # 2. Validate Source Class belongs to School
        source_class = self.school_class_repository.get(db, rule_data.source_class_id)
        if source_class is None or source_class.is_deleted or source_class.school_id != current_school_id:
            raise ValidationException("Source class not found or belongs to another school.")

        # 3. Validate Terminal vs Target Class Consistency
        if rule_data.is_terminal:
            if rule_data.target_class_id is not None:
                raise ValidationException("Terminal progression rules must not specify a target class.")
        else:
            if rule_data.target_class_id is None:
                raise ValidationException("Non-terminal progression rules must specify a target class.")

        # 4. Validate Target Class (if provided)
        if rule_data.target_class_id is not None:
            if rule_data.target_class_id == rule_data.source_class_id:
                raise ValidationException("Source class and target class cannot be the same.")

            target_class = self.school_class_repository.get(db, rule_data.target_class_id)
            if target_class is None or target_class.is_deleted or target_class.school_id != current_school_id:
                raise ValidationException("Target class not found or belongs to another school.")

        # 5. Check Duplicate Active Rule for Source Class
        existing = self.repository.get_by_source_class(db, current_school_id, rule_data.source_class_id)
        if existing is not None:
            raise AlreadyExistsException("Class Progression Rule for source class", str(rule_data.source_class_id))

        # 6. Construct and Save
        rule = ClassProgressionRule(
            school_id=current_school_id,
            source_class_id=rule_data.source_class_id,
            target_class_id=rule_data.target_class_id,
            is_terminal=rule_data.is_terminal,
            description=rule_data.description,
        )
        created = self.repository.create(db, rule)
        logger.info("Class progression rule ID '%s' created successfully", created.id)
        return created

    def get_rule(
        self,
        db: Session,
        rule_id: UUID,
        current_school_id: UUID,
    ) -> ClassProgressionRule:
        """
        Get an active progression rule by ID. Enforces tenant isolation.
        """
        rule = self.repository.get_by_id_and_school(db, rule_id, current_school_id)
        if rule is None:
            raise NotFoundException("ClassProgressionRule", str(rule_id))
        return rule

    def get_paginated_rules(
        self,
        db: Session,
        current_school_id: UUID,
        source_class_id: UUID | None = None,
        target_class_id: UUID | None = None,
        is_terminal: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ClassProgressionRule], int, int]:
        """
        Get paginated active progression rules for a school.
        Returns (items, total, total_pages).
        """
        return self.repository.get_paginated_by_school(
            db,
            school_id=current_school_id,
            source_class_id=source_class_id,
            target_class_id=target_class_id,
            is_terminal=is_terminal,
            page=page,
            page_size=page_size,
        )

    def update_rule(
        self,
        db: Session,
        rule_id: UUID,
        rule_data: ClassProgressionRuleUpdate,
        current_school_id: UUID,
    ) -> ClassProgressionRule:
        """
        Update an existing class progression rule. Enforces tenant isolation and invariants.
        """
        rule = self.get_rule(db, rule_id, current_school_id)

        update_dict = rule_data.model_dump(exclude_unset=True)
        if not update_dict:
            return rule

        new_is_terminal = update_dict.get("is_terminal", rule.is_terminal)
        new_target_class_id = update_dict.get("target_class_id", rule.target_class_id) if "target_class_id" in update_dict else rule.target_class_id

        # If terminal state or target_class_id changed, re-validate invariants
        if new_is_terminal:
            if "target_class_id" in update_dict and update_dict["target_class_id"] is not None:
                raise ValidationException("Terminal progression rules must not specify a target class.")
            # If switching to terminal, force target_class_id to None
            new_target_class_id = None
        else:
            if new_target_class_id is None:
                raise ValidationException("Non-terminal progression rules must specify a target class.")

        if new_target_class_id is not None:
            if new_target_class_id == rule.source_class_id:
                raise ValidationException("Source class and target class cannot be the same.")

            target_class = self.school_class_repository.get(db, new_target_class_id)
            if target_class is None or target_class.is_deleted or target_class.school_id != current_school_id:
                raise ValidationException("Target class not found or belongs to another school.")

        rule.is_terminal = new_is_terminal
        rule.target_class_id = new_target_class_id
        if "description" in update_dict:
            rule.description = update_dict["description"]

        updated = self.repository.update(db, rule)
        logger.info("Class progression rule ID '%s' updated successfully", rule_id)
        return updated

    def delete_rule(
        self,
        db: Session,
        rule_id: UUID,
        current_school_id: UUID,
    ) -> None:
        """
        Soft delete a class progression rule entity.
        """
        rule = self.get_rule(db, rule_id, current_school_id)
        self.repository.delete(db, rule)
        logger.info("Class progression rule ID '%s' soft deleted successfully", rule_id)


class_progression_rule_service = ClassProgressionRuleService(
    repository=class_progression_rule_repository,
    school_repository=school_repository,
    school_class_repository=school_class_repository,
)
