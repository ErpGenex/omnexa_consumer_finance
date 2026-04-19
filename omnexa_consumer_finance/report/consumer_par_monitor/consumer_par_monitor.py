import frappe


def execute(filters=None):
	columns = [
		{"label": "Collection Stage", "fieldname": "collection_stage", "fieldtype": "Data", "width": 150},
		{"label": "Cases", "fieldname": "cases", "fieldtype": "Int", "width": 100},
		{"label": "Outstanding Principal", "fieldname": "outstanding", "fieldtype": "Currency", "width": 180},
	]
	rows = frappe.db.sql(
		"""
		select
			collection_stage,
			count(*) as cases,
			sum(ifnull(principal, 0)) as outstanding
		from `tabConsumer Finance Case`
		group by collection_stage
		order by cases desc
		""",
		as_dict=True,
	)
	return columns, rows

