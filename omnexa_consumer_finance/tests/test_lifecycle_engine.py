from decimal import Decimal

from frappe.tests.utils import FrappeTestCase

from omnexa_consumer_finance.engine import ConsumerCase, evaluate_lifecycle_case


class TestConsumerFinanceLifecycleEngine(FrappeTestCase):
	def test_evaluate_lifecycle_case(self):
		c = ConsumerCase(principal=Decimal("100000"), term_months=36, collection_stage="CURRENT", forbearance_flag=False)
		out = evaluate_lifecycle_case(c)
		self.assertIn(out.recommended_stage, ("ORIGINATION", "APPROVAL", "SERVICING", "WATCHLIST"))
		self.assertIn(out.ifrs9_stage, ("STAGE_1", "STAGE_2", "STAGE_3"))
		self.assertGreaterEqual(len(out.reason_codes), 1)
		self.assertGreaterEqual(len(out.required_controls), 1)
		self.assertGreaterEqual(out.risk_score, Decimal("0"))
		self.assertIn(out.customer_segment, ("PREMIUM", "HIGH_RISK", "DIGITAL_MASS", "STANDARD_MASS"))

	def test_high_risk_segment_and_strategy(self):
		c = ConsumerCase(
			principal=Decimal("50000"),
			term_months=48,
			collection_stage="90_DPD",
			forbearance_flag=True,
			application_channel="MOBILE",
			credit_score=580,
			dti_ratio=Decimal("0.55"),
			existing_exposure=Decimal("90000"),
			delinquency_days=120,
		)
		out = evaluate_lifecycle_case(c)
		self.assertEqual(out.recommended_stage, "WATCHLIST")
		self.assertEqual(out.ifrs9_stage, "STAGE_3")
		self.assertEqual(out.recommended_collections_strategy, "INTENSIVE_RECOVERY")
