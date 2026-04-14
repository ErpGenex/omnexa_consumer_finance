from frappe.tests.utils import FrappeTestCase

from omnexa_consumer_finance import hooks, license_gate


class TestConsumerFinanceLicenseSmoke(FrappeTestCase):
	def test_license_gate_is_wired(self):
		self.assertEqual(hooks.before_request, ["omnexa_consumer_finance.license_gate.before_request"])
		self.assertEqual(license_gate._APP, "omnexa_consumer_finance")
