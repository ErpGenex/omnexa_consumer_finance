import frappe


def execute(filters=None):
	columns = [
		{"label": "Action Channel", "fieldname": "action_channel", "fieldtype": "Data", "width": 140},
		{"label": "Action Type", "fieldname": "action_type", "fieldtype": "Data", "width": 160},
		{"label": "Actions", "fieldname": "actions", "fieldtype": "Int", "width": 100},
		{"label": "Completed", "fieldname": "completed", "fieldtype": "Int", "width": 110},
	]
	rows = frappe.db.sql(
		"""
		select
			action_channel,
			action_type,
			count(*) as actions,
			sum(case when action_status='DONE' then 1 else 0 end) as completed
		from `tabConsumer Collections Action`
		group by action_channel, action_type
		order by actions desc
		""",
		as_dict=True,
	)
	return columns, rows

