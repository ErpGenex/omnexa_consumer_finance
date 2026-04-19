from frappe.tests.utils import FrappeTestCase

from omnexa_consumer_finance.api import (
	approve_and_disburse_loan,
	create_loan_application,
	evaluate_lifecycle,
	generate_repayment_schedule,
	get_consumer_kpi_dashboard,
	integrate_credit_assessment,
	run_collections_strategy,
	upsert_consumer_finance_case,
)


class TestConsumerFinanceLifecycleApi(FrappeTestCase):
	def test_evaluate_lifecycle_api(self):
		out = evaluate_lifecycle(principal="100000", term_months=36, collection_stage="CURRENT", forbearance_flag=0)
		self.assertIn("risk_score", out)
		self.assertIn("pricing_spread", out)
		self.assertIn("recommended_stage", out)
		self.assertIn("ifrs9_stage", out)
		self.assertIn("reason_codes", out)
		self.assertIn("required_controls", out)
		self.assertIn("customer_segment", out)
		self.assertIn("recommended_collections_strategy", out)

	def test_upsert_consumer_finance_case(self):
		out = upsert_consumer_finance_case(
			customer_name="Consumer Test Customer",
			principal="80000",
			term_months=36,
			collection_stage="CURRENT",
			forbearance_flag=0,
		)
		self.assertIn("case_id", out)
		self.assertTrue(out["case_id"])
		self.assertIn("assessment", out)

	def test_end_to_end_flow_and_kpis(self):
		app = create_loan_application(
			customer_name="Retail Customer One",
			principal="120000",
			term_months=48,
			application_channel="MOBILE",
		)
		integrate_credit_assessment(
			application_id=app["application_id"],
			credit_score=690,
			dti_ratio="0.38",
			existing_exposure="25000",
		)
		case = upsert_consumer_finance_case(
			customer_name="Retail Customer One",
			principal="120000",
			term_months=48,
			application_channel="MOBILE",
			credit_score=690,
			dti_ratio="0.38",
			existing_exposure="25000",
		)
		approve_and_disburse_loan(case_id=case["case_id"])
		schedule = generate_repayment_schedule(
			case_id=case["case_id"],
			start_date="2026-05-01",
			installments=3,
			periodic_payment="5000",
		)
		self.assertEqual(len(schedule["schedule_rows"]), 3)
		action = run_collections_strategy(
			case_id=case["case_id"],
			action_type="REMINDER_CALL",
			action_channel="CALL_CENTER",
			notes="Welcome call and payment reminder",
		)
		self.assertIn("action_id", action)
		kpis = get_consumer_kpi_dashboard()
		self.assertIn("par_ratio", kpis)
		self.assertIn("npl_ratio", kpis)
		self.assertIn("roll_rate_distribution", kpis)
