from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


DOMAIN = Path(__file__).with_name("domain.py")


def load_domain():
    if not DOMAIN.is_file():
        raise AssertionError("domain.py must own quantity validation")
    spec = importlib.util.spec_from_file_location("connected_product_domain", DOMAIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class QuantityRuleTests(unittest.TestCase):
    def test_negative_quantity_is_rejected_by_domain_rule(self):
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            load_domain().validate_quantity(-1)

    def test_zero_quantity_is_valid(self):
        self.assertEqual(load_domain().validate_quantity(0), 0)


if __name__ == "__main__":
    unittest.main()
