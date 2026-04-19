# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ConsumerCase:
	principal: Decimal
	term_months: int
	collection_stage: str = "CURRENT"
	forbearance_flag: bool = False
	application_channel: str = "BRANCH"
	credit_score: int = 700
	dti_ratio: Decimal = Decimal("0.30")
	existing_exposure: Decimal = Decimal("0")
	delinquency_days: int = 0


@dataclass(frozen=True)
class LifecycleResult:
	risk_score: Decimal
	pricing_spread: Decimal
	recommended_stage: str  # ORIGINATION | APPROVAL | SERVICING | WATCHLIST
	ifrs9_stage: str
	reason_codes: list[str]
	required_controls: list[str]
	customer_segment: str
	recommended_collections_strategy: str

	def to_dict(self) -> dict:
		return {
			"risk_score": str(self.risk_score),
			"pricing_spread": str(self.pricing_spread),
			"recommended_stage": self.recommended_stage,
			"ifrs9_stage": self.ifrs9_stage,
			"reason_codes": self.reason_codes,
			"required_controls": self.required_controls,
			"customer_segment": self.customer_segment,
			"recommended_collections_strategy": self.recommended_collections_strategy,
		}


def evaluate_lifecycle_case(c: ConsumerCase) -> LifecycleResult:
	risk = Decimal("0.05")
	reasons: list[str] = []
	controls = ["KYC_COMPLETE", "AFFORDABILITY_CHECK", "FAIR_LENDING_CHECK"]
	if c.application_channel in ("WEB", "MOBILE"):
		controls.append("DIGITAL_FRAUD_SCREENING")
	if c.application_channel == "BRANCH":
		controls.append("BRANCH_DOC_VERIFICATION")
	if c.credit_score < 620:
		risk += Decimal("0.10")
		reasons.append("LOW_CREDIT_SCORE")
	if c.dti_ratio > Decimal("0.45"):
		risk += Decimal("0.08")
		reasons.append("HIGH_DTI")
	if c.existing_exposure > (c.principal * Decimal("1.5")):
		risk += Decimal("0.05")
		reasons.append("HIGH_EXISTING_EXPOSURE")
	if c.delinquency_days >= 30:
		risk += Decimal("0.07")
		reasons.append("DELINQUENCY_HISTORY")
	if c.collection_stage in ("30_DPD", "60_DPD", "90_DPD"):
		risk += Decimal("0.10")
		reasons.append(f"COLLECTION_STAGE_{c.collection_stage}")
		controls.append("COLLECTIONS_STRATEGY_REVIEW")
	if c.forbearance_flag:
		risk += Decimal("0.05")
		reasons.append("FORBEARANCE_FLAG")
		controls.append("FORBEARANCE_POLICY_CHECK")
	if c.term_months > 84:
		reasons.append("LONG_TENOR")
	return _result(c, risk, reasons, controls)


def _result(c: ConsumerCase, risk: Decimal, reasons: list[str], controls: list[str]) -> LifecycleResult:
	spread = Decimal("0.02") + risk
	stage = "ORIGINATION"
	ifrs9_stage = "STAGE_1"
	collections_strategy = "LIGHT_TOUCH"
	if risk >= Decimal("0.18"):
		stage = "WATCHLIST"
		ifrs9_stage = "STAGE_3"
		controls.append("RECOVERY_REVIEW")
		collections_strategy = "INTENSIVE_RECOVERY"
	elif risk >= Decimal("0.10"):
		stage = "SERVICING"
		ifrs9_stage = "STAGE_2"
		controls.append("ENHANCED_MONITORING")
		collections_strategy = "STRUCTURED_COLLECTIONS"
	elif c.term_months > 84:
		stage = "APPROVAL"
		controls.append("SENIOR_APPROVAL")
		collections_strategy = "PREVENTIVE_OUTREACH"
	if not reasons:
		reasons.append("BASE_POLICY")
	segment = _segment(c, risk)
	return LifecycleResult(
		risk_score=risk,
		pricing_spread=spread,
		recommended_stage=stage,
		ifrs9_stage=ifrs9_stage,
		reason_codes=reasons,
		required_controls=sorted(set(controls)),
		customer_segment=segment,
		recommended_collections_strategy=collections_strategy,
	)


def _segment(c: ConsumerCase, risk: Decimal) -> str:
	if c.principal >= Decimal("250000"):
		return "PREMIUM"
	if risk >= Decimal("0.18"):
		return "HIGH_RISK"
	if c.application_channel in ("WEB", "MOBILE"):
		return "DIGITAL_MASS"
	return "STANDARD_MASS"
