# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import json

import frappe

APP = "omnexa_consumer_finance"
WORKSPACE = "Consumer Finance Governance"
POLICY_DTYPE = "Consumer Finance Policy Version"
SNAP_DTYPE = "Consumer Finance Audit Snapshot"
CHART_POL = "Consumer Finance Governance - Policies by Status"
CHART_SNP = "Consumer Finance Governance - Snapshots (Last Month)"
CHART_PAR = "Consumer Finance - PAR by Stage"
CHART_NPL = "Consumer Finance - NPL by IFRS9"
CHART_ROLL = "Consumer Finance - Roll Rate Distribution"
MODULE = "Omnexa Consumer Finance"
ICON = "retail"


def after_migrate():
	ensure_workspace_assets()


def ensure_workspace_assets():
	if not frappe.db.exists("DocType", POLICY_DTYPE):
		return
	_ensure_chart(CHART_POL, chart_type="Group By", document_type=POLICY_DTYPE, group_by_based_on="status", chart_render_type="Donut", timeseries=0)
	_ensure_chart(CHART_SNP, chart_type="Count", document_type=SNAP_DTYPE, based_on="created_at", chart_render_type="Line", timeseries=1)
	if frappe.db.exists("DocType", "Consumer Finance Case"):
		_ensure_chart(CHART_PAR, chart_type="Group By", document_type="Consumer Finance Case", group_by_based_on="collection_stage", chart_render_type="Donut", timeseries=0)
		_ensure_chart(CHART_NPL, chart_type="Group By", document_type="Consumer Finance Case", group_by_based_on="ifrs9_stage", chart_render_type="Donut", timeseries=0)
	if frappe.db.exists("DocType", "Consumer Collections Action"):
		_ensure_chart(CHART_ROLL, chart_type="Group By", document_type="Consumer Collections Action", group_by_based_on="action_channel", chart_render_type="Donut", timeseries=0)
	_ensure_workspace()


def _ensure_chart(name: str, chart_type: str, document_type: str, chart_render_type: str, timeseries: int, based_on: str | None = None, group_by_based_on: str | None = None):
	if frappe.db.exists("Dashboard Chart", name):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Dashboard Chart",
			"chart_name": name,
			"is_standard": "No",
			"module": MODULE,
			"is_public": 1,
			"chart_type": chart_type,
			"document_type": document_type,
			"group_by_type": "Count",
			"group_by_based_on": group_by_based_on,
			"based_on": based_on,
			"timeseries": timeseries,
			"timespan": "Last Month",
			"time_interval": "Daily",
			"filters_json": "[]",
			"type": chart_render_type,
		}
	)
	doc.insert(ignore_permissions=True)


def _ensure_workspace():
	ws = None
	if frappe.db.exists("Workspace", WORKSPACE):
		try:
			ws = frappe.get_doc("Workspace", WORKSPACE)
		except Exception:
			ws = None
	if not ws:
		ws = frappe.new_doc("Workspace")
		ws.update({"label": WORKSPACE, "title": WORKSPACE, "name": WORKSPACE, "module": MODULE, "public": 1, "icon": ICON})
		ws.insert(ignore_permissions=True)

	ws.icon = ICON
	ws.module = MODULE
	ws.public = 1
	ws.content = json.dumps([
		{"id": "omnexa_consumer_finance-h", "type": "header", "data": {"text": "<span class=\"h4\"><b>Consumer Finance Governance</b></span>", "col": 12}},
		{"id": "omnexa_consumer_finance-c1", "type": "card", "data": {"card_name": "Governance", "col": 4}},
		{"id": "omnexa_consumer_finance-ch1", "type": "chart", "data": {"chart_name": CHART_POL, "col": 4}},
		{"id": "omnexa_consumer_finance-ch2", "type": "chart", "data": {"chart_name": CHART_SNP, "col": 4}},
	])

	if not ws.get("links"):
		ws.set("links", [])
	if not any((l.get("type") == "Card Break" and l.get("label") == "Governance") for l in ws.links):
		ws.append("links", {"type": "Card Break", "label": "Governance", "hidden": 0})
	for lb, lt in (("Policy Versions", POLICY_DTYPE), ("Audit Snapshots", SNAP_DTYPE)):
		if not any((l.get("type") == "Link" and l.get("link_to") == lt) for l in ws.links):
			ws.append("links", {"type": "Link", "label": lb, "link_type": "DocType", "link_to": lt, "hidden": 0})

	if not ws.get("charts"):
		ws.set("charts", [])
	if not any(c.get("chart_name") == CHART_POL for c in ws.charts):
		ws.append("charts", {"chart_name": CHART_POL, "label": "Policies by Status"})
	if not any(c.get("chart_name") == CHART_SNP for c in ws.charts):
		ws.append("charts", {"chart_name": CHART_SNP, "label": "Snapshots (Last Month)"})

	ws.save(ignore_permissions=True)
