# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe

from .standards_profile import get_standards_profile as _get_standards_profile


@frappe.whitelist()
def get_standards_profile() -> dict:
	"""Expose standards profile for governance dashboards and audits."""
	return _get_standards_profile()


from decimal import Decimal
from datetime import date

from .engine import ConsumerCase, evaluate_lifecycle_case


@frappe.whitelist()
def evaluate_lifecycle(principal: str, term_months: int, collection_stage: str = "CURRENT", forbearance_flag: int = 0) -> dict:
	c = ConsumerCase(
		principal=Decimal(str(principal)),
		term_months=int(term_months),
		collection_stage=str(collection_stage),
		forbearance_flag=bool(int(forbearance_flag)),
	)
	return evaluate_lifecycle_case(c).to_dict()


@frappe.whitelist()
def onboard_customer(customer_name: str, country_code: str = "INTL", onboarding_channel: str = "BRANCH") -> dict:
	return {
		"customer_name": customer_name,
		"country_code": country_code,
		"onboarding_channel": onboarding_channel,
		"onboarding_status": "COMPLETED",
	}


@frappe.whitelist()
def create_loan_application(
	customer_name: str,
	principal: str,
	term_months: int,
	application_channel: str = "BRANCH",
	country_code: str = "INTL",
) -> dict:
	doc = frappe.get_doc(
		{
			"doctype": "Consumer Loan Application",
			"customer_name": customer_name,
			"principal": Decimal(str(principal)),
			"term_months": int(term_months),
			"application_channel": application_channel,
			"country_code": country_code,
			"application_status": "SUBMITTED",
		}
	)
	doc.insert(ignore_permissions=True)
	return {"application_id": doc.name, "application_status": doc.application_status}


@frappe.whitelist()
def integrate_credit_assessment(
	application_id: str,
	credit_score: int,
	dti_ratio: str,
	existing_exposure: str = "0",
) -> dict:
	app = frappe.get_doc("Consumer Loan Application", application_id)
	app.credit_score = int(credit_score)
	app.dti_ratio = Decimal(str(dti_ratio))
	app.existing_exposure = Decimal(str(existing_exposure))
	app.application_status = "ASSESSED"
	app.save(ignore_permissions=True)
	return {"application_id": app.name, "application_status": app.application_status}


@frappe.whitelist()
def upsert_consumer_finance_case(
	case_id: str | None = None,
	customer_name: str | None = None,
	principal: str = "0",
	term_months: int = 0,
	collection_stage: str = "CURRENT",
	forbearance_flag: int = 0,
	country_code: str = "INTL",
	application_channel: str = "BRANCH",
	credit_score: int = 700,
	dti_ratio: str = "0.30",
	existing_exposure: str = "0",
	delinquency_days: int = 0,
) -> dict:
	"""Create/update a consumer finance case with servicing/collections controls."""
	assessment = evaluate_lifecycle(
		principal=principal,
		term_months=term_months,
		collection_stage=collection_stage,
		forbearance_flag=forbearance_flag,
	)
	c = ConsumerCase(
		principal=Decimal(str(principal)),
		term_months=int(term_months),
		collection_stage=str(collection_stage),
		forbearance_flag=bool(int(forbearance_flag)),
		application_channel=str(application_channel),
		credit_score=int(credit_score),
		dti_ratio=Decimal(str(dti_ratio)),
		existing_exposure=Decimal(str(existing_exposure)),
		delinquency_days=int(delinquency_days),
	)
	assessment = evaluate_lifecycle_case(c).to_dict()
	doc = (
		frappe.get_doc("Consumer Finance Case", case_id)
		if case_id and frappe.db.exists("Consumer Finance Case", case_id)
		else frappe.new_doc("Consumer Finance Case")
	)
	doc.customer_name = customer_name or "Unknown Customer"
	doc.principal = Decimal(str(principal))
	doc.term_months = int(term_months)
	doc.collection_stage = collection_stage
	doc.forbearance_flag = int(forbearance_flag)
	doc.lifecycle_stage = assessment["recommended_stage"]
	doc.ifrs9_stage = assessment["ifrs9_stage"]
	doc.risk_score = float(assessment["risk_score"])
	doc.pricing_spread = float(assessment["pricing_spread"])
	doc.country_code = country_code
	doc.application_channel = application_channel
	doc.credit_score = int(credit_score)
	doc.dti_ratio = float(Decimal(str(dti_ratio)))
	doc.existing_exposure = Decimal(str(existing_exposure))
	doc.delinquency_days = int(delinquency_days)
	doc.customer_segment = assessment.get("customer_segment")
	doc.collections_strategy = assessment.get("recommended_collections_strategy")
	doc.decision_status = "APPROVED" if assessment["recommended_stage"] in ("ORIGINATION", "APPROVAL") else "WATCHLIST"
	doc.decision_reason_codes = ",".join(assessment.get("reason_codes", []))
	doc.required_controls = ",".join(assessment.get("required_controls", []))
	doc.save(ignore_permissions=True)
	return {"case_id": doc.name, "assessment": assessment}


@frappe.whitelist()
def approve_and_disburse_loan(case_id: str, disbursement_date: str | None = None) -> dict:
	doc = frappe.get_doc("Consumer Finance Case", case_id)
	doc.lifecycle_stage = "SERVICING"
	doc.decision_status = "APPROVED"
	doc.disbursement_status = "DISBURSED"
	doc.disbursement_date = disbursement_date or str(date.today())
	doc.save(ignore_permissions=True)
	return {"case_id": doc.name, "disbursement_status": doc.disbursement_status}


@frappe.whitelist()
def generate_repayment_schedule(case_id: str, start_date: str, installments: int, periodic_payment: str) -> dict:
	amount = Decimal(str(periodic_payment))
	rows = []
	for i in range(1, int(installments) + 1):
		s = frappe.get_doc(
			{
				"doctype": "Consumer Repayment Schedule",
				"case_id": case_id,
				"installment_no": i,
				"due_date": start_date,
				"due_amount": str(amount),
				"paid_amount": "0",
				"status": "DUE",
			}
		)
		s.insert(ignore_permissions=True)
		rows.append(s.name)
	return {"case_id": case_id, "schedule_rows": rows}


@frappe.whitelist()
def restructure_loan_case(case_id: str, new_term_months: int, reason: str) -> dict:
	doc = frappe.get_doc("Consumer Finance Case", case_id)
	doc.term_months = int(new_term_months)
	doc.restructure_flag = 1
	doc.restructure_reason = reason
	doc.lifecycle_stage = "SERVICING"
	doc.save(ignore_permissions=True)
	return {"case_id": doc.name, "restructured": True, "new_term_months": doc.term_months}


@frappe.whitelist()
def run_collections_strategy(case_id: str, action_type: str, action_channel: str, notes: str = "") -> dict:
	doc = frappe.get_doc(
		{
			"doctype": "Consumer Collections Action",
			"case_id": case_id,
			"action_type": action_type,
			"action_channel": action_channel,
			"action_status": "DONE",
			"notes": notes,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"action_id": doc.name, "case_id": case_id}


@frappe.whitelist()
def get_consumer_kpi_dashboard() -> dict:
	par = frappe.db.sql(
		"""
		select
			round(sum(case when collection_stage in ('30_DPD','60_DPD','90_DPD') then ifnull(principal,0) else 0 end) /
				nullif(sum(ifnull(principal,0)),0), 6) as par_ratio
		from `tabConsumer Finance Case`
		""",
		as_dict=True,
	)
	npl = frappe.db.sql(
		"""
		select
			round(sum(case when ifrs9_stage='STAGE_3' then ifnull(principal,0) else 0 end) /
				nullif(sum(ifnull(principal,0)),0), 6) as npl_ratio
		from `tabConsumer Finance Case`
		""",
		as_dict=True,
	)
	roll = frappe.db.sql(
		"""
		select collection_stage, count(*) as cases
		from `tabConsumer Finance Case`
		group by collection_stage
		order by cases desc
		""",
		as_dict=True,
	)
	return {
		"par_ratio": str((par[0].par_ratio if par else 0) or 0),
		"npl_ratio": str((npl[0].npl_ratio if npl else 0) or 0),
		"roll_rate_distribution": roll,
	}


@frappe.whitelist()
def submit_policy_version(policy_name: str, version: str, payload: str, effective_from: str | None = None) -> dict:
	import json
	from .governance import submit_policy_version as _submit
	obj = json.loads(payload) if isinstance(payload, str) else payload
	if not isinstance(obj, dict):
		frappe.throw(frappe._("payload must be a JSON object"))
	return _submit("omnexa_consumer_finance", policy_name=policy_name, version=version, payload=obj, effective_from=effective_from)


@frappe.whitelist()
def approve_policy_version(policy_name: str, version: str) -> dict:
	from .governance import approve_policy_version as _approve
	return _approve("omnexa_consumer_finance", policy_name=policy_name, version=version)


@frappe.whitelist()
def create_audit_snapshot(process_name: str, inputs: str, outputs: str, policy_ref: str | None = None) -> dict:
	import json
	from .governance import create_audit_snapshot as _snap
	in_obj = json.loads(inputs) if isinstance(inputs, str) else inputs
	out_obj = json.loads(outputs) if isinstance(outputs, str) else outputs
	if not isinstance(in_obj, dict) or not isinstance(out_obj, dict):
		frappe.throw(frappe._("inputs/outputs must be JSON objects"))
	return _snap("omnexa_consumer_finance", process_name=process_name, inputs=in_obj, outputs=out_obj, policy_ref=policy_ref)


@frappe.whitelist()
def get_governance_overview() -> dict:
	from .governance import governance_overview as _overview
	return _overview("omnexa_consumer_finance")


@frappe.whitelist()
def reject_policy_version(policy_name: str, version: str, reason: str = "") -> dict:
	from .governance import reject_policy_version as _reject
	return _reject("omnexa_consumer_finance", policy_name=policy_name, version=version, reason=reason)


@frappe.whitelist()
def list_policy_versions(policy_name: str | None = None) -> list[dict]:
	from .governance import list_policy_versions as _list
	return _list("omnexa_consumer_finance", policy_name=policy_name)


@frappe.whitelist()
def list_audit_snapshots(process_name: str | None = None, limit: int = 100) -> list[dict]:
	from .governance import list_audit_snapshots as _list
	return _list("omnexa_consumer_finance", process_name=process_name, limit=int(limit))


@frappe.whitelist()
def get_regulatory_dashboard() -> dict:
	"""Unified compliance dashboard payload for this app."""
	from .governance import governance_overview
	from .standards_profile import get_standards_profile
	std = get_standards_profile()
	gov = governance_overview("omnexa_consumer_finance")
	return {
		"app": "omnexa_consumer_finance",
		"standards": std.get("standards", []),
		"activity_controls": std.get("activity_controls", []),
		"governance": gov,
		"compliance_score": _compute_compliance_score(std=std, gov=gov),
	}


def _compute_compliance_score(std: dict, gov: dict) -> int:
	"""Simple normalized readiness score (0..100) for executive monitoring."""
	base = min(50, 5 * len(std.get("standards", [])))
	controls = min(30, 3 * len(std.get("activity_controls", [])))
	approved = int(gov.get("policies_approved", 0) or 0)
	pending = int(gov.get("policies_pending", 0) or 0)
	governance = min(20, approved * 2)
	if pending > 0:
		governance = max(0, governance - min(10, pending))
	return int(base + controls + governance)
