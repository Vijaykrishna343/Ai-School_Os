from __future__ import annotations

from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.endpoints.audit_logs import write_audit_log
from app.common.enums import (
    AcademicYearStatus,
    SchoolClassStatus,
    SectionStatus,
)
from app.common.enums.school import SchoolStatus
from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.repositories import (
    identity_user_repository,
    permission_repository,
    role_permission_repository,
    role_repository,
    user_role_repository,
)
from app.identity.seeders.role_permission_seeder import (
    ROLE_PERMISSIONS_MATRIX,
    RolePermissionSeeder,
)
from app.identity.seeders.role_seeder import DEFAULT_ROLES
from app.identity.security.password import hash_password
from app.models.academic_year import AcademicYear
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.repositories.academic_year import academic_year_repository
from app.repositories.school import school_repository
from app.schemas.school_onboarding import (
    SchoolOnboardingRequest,
    SchoolOnboardingResponse,
)

logger = get_logger(__name__)


class SchoolOnboardingService:
    """
    Transactional tenant provisioning service for new schools.
    Ensures complete, atomic bootstrap of School, Roles, Admin User,
    Primary Academic Year, and Optional Class Templates.
    """

    def __init__(self) -> None:
        self.role_seeder_helper = RolePermissionSeeder()

    def bootstrap_school_tenant(
        self,
        db: Session,
        request: SchoolOnboardingRequest,
        current_user: IdentityUser | None = None,
    ) -> SchoolOnboardingResponse:
        """
        Bootstrap a new school tenant in a single fail-closed database transaction.
        """
        if current_user is not None and not current_user.is_super_admin:
            logger.warning(
                "Unauthorized tenant onboarding attempt by user: %s",
                getattr(current_user, "email", "unknown"),
            )
            raise ForbiddenException(
                "School tenant onboarding is restricted to Platform Super Administrators."
            )

        # 1. Validation & Duplicate Checking
        if request.academic_year.start_date >= request.academic_year.end_date:
            logger.warning("Tenant onboarding validation error: Academic start date >= end date")
            raise ValidationException("Academic year start date must be before end date.")

        if school_repository.exists_by_code(db, request.code):
            logger.warning("Tenant onboarding conflict: School code '%s' already exists", request.code)
            raise AlreadyExistsException("School code", request.code)

        existing_user_stmt = select(IdentityUser).where(
            func.lower(IdentityUser.email) == request.admin.email.lower(),
            IdentityUser.is_deleted.is_(False),
        )
        if db.scalar(existing_user_stmt) is not None:
            logger.warning("Tenant onboarding conflict: Admin email '%s' already exists", request.admin.email)
            raise AlreadyExistsException("Admin email", request.admin.email)

        try:
            logger.info("Starting atomic onboarding for school '%s' (%s)", request.name, request.code)

            # Step 1: Create School Entity
            school = School(
                name=request.name,
                code=request.code.strip().upper(),
                email=request.email,
                phone=request.phone,
                website=request.website,
                logo_url=request.logo_url,
                address_line1=request.address_line1,
                address_line2=request.address_line2,
                city=request.city,
                district=request.district,
                state=request.state,
                country=request.country,
                postal_code=request.postal_code,
                status=SchoolStatus.ACTIVE,
                subscription_tier=request.subscription_tier,
                max_students=request.max_students,
                max_teachers=request.max_teachers,
            )
            db.add(school)
            db.flush()
            logger.info("School record created with ID: %s", school.id)

            # Step 2: Provision Tenant-Scoped Roles & Permissions
            all_permissions = permission_repository.get_all(db)
            roles_created_count = 0
            school_admin_role: IdentityRole | None = None

            for role_data in DEFAULT_ROLES:
                role_name = role_data["name"]
                # Create tenant-scoped role
                role = IdentityRole(
                    school_id=school.id,
                    name=role_name,
                    description=role_data.get("description"),
                    is_system=False,
                )
                db.add(role)
                db.flush()
                roles_created_count += 1

                if role_name == "School Admin":
                    school_admin_role = role

                # Attach matching permissions from canonical matrix
                patterns = ROLE_PERMISSIONS_MATRIX.get(role_name, [])
                target_permissions = self.role_seeder_helper._resolve_permissions_for_patterns(
                    patterns,
                    all_permissions,
                )
                for perm in target_permissions:
                    role_permission_repository.assign_permission(
                        db=db,
                        role_id=role.id,
                        permission_id=perm.id,
                    )

            db.flush()
            logger.info("Provisioned %d tenant roles for school ID: %s", roles_created_count, school.id)

            # Step 3: Create Initial Administrator Account
            admin_username = request.admin.username or request.admin.email.split("@")[0]
            admin_user = IdentityUser(
                school_id=school.id,
                email=request.admin.email,
                username=admin_username,
                password_hash=hash_password(request.admin.password),
                first_name=request.admin.first_name,
                last_name=request.admin.last_name,
                phone=request.admin.phone,
                is_active=True,
            )
            db.add(admin_user)
            db.flush()

            # Assign School Admin role to the initial administrator
            if school_admin_role is not None:
                user_role_repository.assign_role(
                    db=db,
                    user_id=admin_user.id,
                    role_id=school_admin_role.id,
                )
            logger.info("Provisioned initial admin '%s' with ID: %s", admin_user.email, admin_user.id)

            # Step 4: Provision Primary Academic Year
            academic_year = AcademicYear(
                school_id=school.id,
                name=request.academic_year.name,
                start_date=request.academic_year.start_date,
                end_date=request.academic_year.end_date,
                status=AcademicYearStatus.ACTIVE,
                is_current=request.academic_year.is_current,
            )
            db.add(academic_year)
            db.flush()
            logger.info("Provisioned academic year '%s' with ID: %s", academic_year.name, academic_year.id)

            # Step 5: Optional Class & Section Templates
            classes_created_count = 0
            if request.class_templates:
                for item in request.class_templates:
                    s_class = SchoolClass(
                        school_id=school.id,
                        name=item.name,
                        display_order=item.display_order,
                        status=SchoolClassStatus.ACTIVE,
                    )
                    db.add(s_class)
                    db.flush()
                    classes_created_count += 1

                    if item.create_default_section:
                        section = Section(
                            school_class_id=s_class.id,
                            name=item.default_section_name,
                            capacity=item.capacity,
                            status=SectionStatus.ACTIVE,
                        )
                        db.add(section)
                        db.flush()

                logger.info("Provisioned %d classes with default sections for school ID: %s", classes_created_count, school.id)

            # Step 6: Safe Audit Log Entry
            actor_user_id = current_user.id if current_user else None
            actor_email = current_user.email if current_user else "platform_super_admin"
            write_audit_log(
                db=db,
                school_id=school.id,
                user_id=actor_user_id,
                user_email=actor_email,
                action="TENANT_PROVISIONED",
                module="SCHOOL_ONBOARDING",
                entity_type="School",
                entity_id=str(school.id),
                status_code=201,
                details=f"Provisioned tenant '{school.name}' ({school.code}) with admin '{admin_user.email}', academic year '{academic_year.name}', and {classes_created_count} initial classes.",
            )

            # Commit the atomic transaction
            db.commit()
            db.refresh(school)
            db.refresh(admin_user)
            db.refresh(academic_year)

            logger.info("School tenant onboarding successfully committed for '%s'", school.name)

            return SchoolOnboardingResponse(
                school_id=school.id,
                name=school.name,
                code=school.code,
                status=str(school.status.value if hasattr(school.status, "value") else school.status),
                subscription_tier=school.subscription_tier,
                admin_user_id=admin_user.id,
                admin_email=admin_user.email,
                admin_name=f"{admin_user.first_name} {admin_user.last_name}".strip(),
                academic_year_id=academic_year.id,
                academic_year_name=academic_year.name,
                roles_provisioned_count=roles_created_count,
                classes_provisioned_count=classes_created_count,
                message="School tenant provisioned successfully with initial admin, roles, and academic calendar.",
            )

        except Exception as e:
            db.rollback()
            logger.error("Failed to provision school tenant '%s', transaction rolled back: %s", request.code, str(e), exc_info=True)
            raise


school_onboarding_service = SchoolOnboardingService()
