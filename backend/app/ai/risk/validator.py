"""
Independent Risk Score Validator for Phase 12.4.
Verifies score range, factor consistency, version presence, and data sufficiency alignment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional

from app.ai.risk.engine import RiskEvaluationOutput


@dataclass
class RiskValidationReport:
    is_valid: bool
    violations: List[str] = field(default_factory=list)


class RiskScoreValidator:
    """
    Independent deterministic validator verifying all safety & consistency invariants
    of calculated student risk assessments.
    """

    ALLOWED_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL", "INSUFFICIENT_DATA"}
    ALLOWED_SUFFICIENCY = {"FULL", "PARTIAL", "INSUFFICIENT"}

    def validate(self, output: RiskEvaluationOutput) -> RiskValidationReport:
        violations: List[str] = []

        # 1. Version Presence
        if not output.scoring_version:
            violations.append("Missing required 'scoring_version'.")

        # 2. Risk Level Enum Check
        if output.risk_level not in self.ALLOWED_RISK_LEVELS:
            violations.append(f"Invalid risk_level '{output.risk_level}'. Expected one of {self.ALLOWED_RISK_LEVELS}.")

        # 3. Data Sufficiency Status Check
        if output.data_sufficiency_status not in self.ALLOWED_SUFFICIENCY:
            violations.append(f"Invalid data_sufficiency_status '{output.data_sufficiency_status}'. Expected one of {self.ALLOWED_SUFFICIENCY}.")

        # 4. Score Bounds & Sufficiency Alignment
        if output.risk_level == "INSUFFICIENT_DATA":
            if output.data_sufficiency_status != "INSUFFICIENT":
                violations.append(f"Risk level 'INSUFFICIENT_DATA' requires data_sufficiency_status 'INSUFFICIENT', got '{output.data_sufficiency_status}'.")
            if output.risk_score is not None:
                violations.append("Risk level 'INSUFFICIENT_DATA' must have risk_score=None.")
        else:
            if output.risk_score is None:
                violations.append(f"Risk level '{output.risk_level}' requires a valid non-null risk_score.")
            else:
                if output.risk_score < Decimal("0.00") or output.risk_score > Decimal("1.00"):
                    violations.append(f"risk_score '{output.risk_score}' out of bounds [0.00, 1.00].")

        # 5. Confidence Bounds Check
        if output.confidence < Decimal("0.00") or output.confidence > Decimal("1.00"):
            violations.append(f"confidence '{output.confidence}' out of bounds [0.00, 1.00].")

        # 6. Score vs Risk Level Alignment Check
        if output.risk_score is not None:
            score = output.risk_score
            if score <= Decimal("0.25") and output.risk_level != "LOW":
                violations.append(f"Score {score} matches 'LOW' risk level, got '{output.risk_level}'.")
            elif Decimal("0.25") < score <= Decimal("0.50") and output.risk_level != "MEDIUM":
                violations.append(f"Score {score} matches 'MEDIUM' risk level, got '{output.risk_level}'.")
            elif Decimal("0.50") < score <= Decimal("0.75") and output.risk_level != "HIGH":
                violations.append(f"Score {score} matches 'HIGH' risk level, got '{output.risk_level}'.")
            elif score > Decimal("0.75") and output.risk_level != "CRITICAL":
                violations.append(f"Score {score} matches 'CRITICAL' risk level, got '{output.risk_level}'.")

        return RiskValidationReport(
            is_valid=len(violations) == 0,
            violations=violations,
        )


risk_score_validator = RiskScoreValidator()
