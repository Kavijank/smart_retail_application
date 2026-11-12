"""
Automated Unit Tests for ValidationStage and Dead-Letter Queue (DLQ).
Verifies that invalid prices, corrupt fields, and duplicates are quarantined properly.
"""
import os
import unittest
from datetime import datetime
from models.transaction_record import TransactionRecord
from dlq.file_backed_dlq import FileBackedDLQ
from pipeline.validation_stage import ValidationStage


class TestValidationAndDLQ(unittest.TestCase):

    def setUp(self):
        self.test_dlq_file = "test_dlq_audit.csv"
        self.dlq = FileBackedDLQ(audit_file_path=self.test_dlq_file)
        self.validator = ValidationStage(self.dlq)

    def tearDown(self):
        self.dlq.close()
        if os.path.exists(self.test_dlq_file):
            try:
                os.remove(self.test_dlq_file)
            except Exception:
                pass

    def test_valid_record_passes(self):
        rec = TransactionRecord(
            transaction_id="TX-VALID-1",
            transaction_datetime=datetime(2024, 5, 10, 14, 30),
            store_id="ST100",
            store_city="Jaffna",
            region="North",
            warehouse_id="WH-NORTH",
            customer_id="CUST01",
            customer_age=30,
            customer_gender="Male",
            customer_city="Jaffna",
            product_category="Groceries",
            product_name="Rice 5kg",
            quantity=2,
            unit_price=500.0,
            discount_percent=0.0,
            promotion_name="No Promotion",
            payment_method="Cash",
            channel="In-Store",
            total_amount=1000.0,
            stock_on_hand=50,
            reorder_level=20,
            transaction_type="Sale"
        )
        clean = self.validator.process_chunk([rec])
        self.assertEqual(len(clean), 1)
        self.assertEqual(self.dlq.get_failure_count(), 0)

    def test_negative_unit_price_routes_to_dlq(self):
        bad_rec = TransactionRecord(
            transaction_id="TX-BAD-PRICE",
            transaction_datetime=datetime(2024, 5, 10, 14, 30),
            store_id="ST100",
            store_city="Jaffna",
            region="North",
            warehouse_id="WH-NORTH",
            customer_id="CUST01",
            customer_age=30,
            customer_gender="Male",
            customer_city="Jaffna",
            product_category="Groceries",
            product_name="Rice 5kg",
            quantity=2,
            unit_price=-500.0,  # Negative price!
            discount_percent=0.0,
            promotion_name="No Promotion",
            payment_method="Cash",
            channel="In-Store",
            total_amount=-1000.0,
            stock_on_hand=50,
            reorder_level=20,
            transaction_type="Sale"
        )
        clean = self.validator.process_chunk([bad_rec])
        self.assertEqual(len(clean), 0)
        self.assertEqual(self.dlq.get_failure_count(), 1)
        faulty = self.dlq.get_faulty_records()
        self.assertIn("INVALID_UNIT_PRICE", faulty[0].failure_reason)

    def test_duplicate_transaction_id_routes_to_dlq(self):
        rec1 = TransactionRecord(
            transaction_id="TX-DUP-999",
            transaction_datetime=datetime(2024, 5, 10, 14, 30),
            store_id="ST100",
            store_city="Jaffna",
            region="North",
            warehouse_id="WH-NORTH",
            customer_id="CUST01",
            customer_age=30,
            customer_gender="Male",
            customer_city="Jaffna",
            product_category="Bakery",
            product_name="Bread",
            quantity=1,
            unit_price=200.0,
            discount_percent=0.0,
            promotion_name="No Promotion",
            payment_method="Cash",
            channel="In-Store",
            total_amount=200.0,
            stock_on_hand=50,
            reorder_level=20,
            transaction_type="Sale"
        )
        rec2 = TransactionRecord(
            transaction_id="TX-DUP-999",  # Duplicate ID
            transaction_datetime=datetime(2024, 5, 10, 14, 35),
            store_id="ST100",
            store_city="Jaffna",
            region="North",
            warehouse_id="WH-NORTH",
            customer_id="CUST02",
            customer_age=25,
            customer_gender="Female",
            customer_city="Jaffna",
            product_category="Bakery",
            product_name="Cake",
            quantity=1,
            unit_price=200.0,
            discount_percent=0.0,
            promotion_name="No Promotion",
            payment_method="Cash",
            channel="In-Store",
            total_amount=200.0,
            stock_on_hand=50,
            reorder_level=20,
            transaction_type="Sale"
        )
        clean = self.validator.process_chunk([rec1, rec2])
        self.assertEqual(len(clean), 1)
        self.assertEqual(self.dlq.get_failure_count(), 1)
        self.assertEqual(self.dlq.get_faulty_records()[0].failure_reason, "DUPLICATE_TRANSACTION_ID")


if __name__ == '__main__':
    unittest.main()
