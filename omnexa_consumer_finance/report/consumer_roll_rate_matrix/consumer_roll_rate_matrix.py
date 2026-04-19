import frappe


def execute(filters=None):
	columns = [
		{"label": "Collection Stage", "fieldname": "collection_stage", "fieldtype": "Data", "width": 140},
		{"label": "IFRS9 Stage", "fieldname": "ifrs9_stage", "fieldtype": "Data", "width": 120},
		{"label": "Cases", "fieldname": "cases", "fieldtype": "Int", "width": 100},
	]
	rows = frappe.db.sql(
		"""
		select
			collection_stage,
			ifrs9_stage,
			count(*) as cases
		from `tabConsumer Finance Case`
		group by collection_stage, ifrs9_stage
		order by collection_stage, ifrs9_stage
		""",
		as_dict=True,
	)
	return columns, rows

