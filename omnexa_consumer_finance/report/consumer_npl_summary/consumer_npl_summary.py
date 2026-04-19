import frappe


def execute(filters=None):
	columns = [
		{"label": "IFRS9 Stage", "fieldname": "ifrs9_stage", "fieldtype": "Data", "width": 120},
		{"label": "Cases", "fieldname": "cases", "fieldtype": "Int", "width": 100},
		{"label": "Principal", "fieldname": "principal", "fieldtype": "Currency", "width": 170},
	]
	rows = frappe.db.sql(
		"""
		select
			ifrs9_stage,
			count(*) as cases,
			sum(ifnull(principal, 0)) as principal
		from `tabConsumer Finance Case`
		group by ifrs9_stage
		order by cases desc
		""",
		as_dict=True,
	)
	return columns, rows

