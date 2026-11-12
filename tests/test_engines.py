"""
Automated Unit Tests for Analytics Engines and Strategies.
"""
import unittest
from datetime import datetime
from models.transaction_record import TransactionRecord
from engines.peak_sales_engine import PeakSalesEngine
from engines.customer_segmentation_engine import CustomerSegmentationEngine
from engines.strategies import RfmSegmentationStrategy, ZScoreAnomalyStrategy
from engines.anomaly_detection_engine import AnomalyDetectionEngine


class TestAnalyticsEngines(unittest.TestCase):

    def _create_sample_record(self, tx_id="TX-1", hour=14, day="Monday", amount=150.0, cust_id="CUST-01"):
        dt = datetime(2024, 6, 3, hour, 15)  # 2024-06-03 was a Monday
        return TransactionRecord(
            transaction_id=tx_id,
            transaction_datetime=dt,
            store_id="ST101",
            store_city="Colombo",
            region="Western",
            warehouse_id="WH-WEST",
            customer_id=cust_id,
            customer_age=32,
            customer_gender="Female",
            customer_city="Colombo",
            product_category="Beverages",
            product_name="Coffee",
            quantity=1,
            unit_price=amount,
            discount_percent=0.0,
            promotion_name="No Promotion",
            payment_method="Credit Card",
            channel="In-Store",
            total_amount=amount,
            stock_on_hand=100,
            reorder_level=20,
            transaction_type="Sale"
        )

    def test_peak_sales_engine(self):
        engine = PeakSalesEngine()
        # Feed 3 records at 14:00 and 1 record at 09:00
        recs = [
            self._create_sample_record("TX-1", hour=14, amount=100.0),
            self._create_sample_record("TX-2", hour=14, amount=200.0),
            self._create_sample_record("TX-3", hour=14, amount=300.0),
            self._create_sample_record("TX-4", hour=9, amount=50.0)
        ]
        engine.aggregate(recs)
        result = engine.generate_report()

        self.assertEqual(result.metrics['peak_hour'], 14)
        self.assertEqual(result.metrics['hourly_tx_count'][14], 3)
        self.assertEqual(result.metrics['hourly_tx_count'][9], 1)

    def test_customer_segmentation_rfm(self):
        engine = CustomerSegmentationEngine(strategy=RfmSegmentationStrategy(frequent_min_orders=3, occasional_min_orders=2))
        recs = [
            self._create_sample_record(f"TX-{i}", cust_id="CUST-FREQUENT") for i in range(5)
        ] + [
            self._create_sample_record(f"TX-OCC-{i}", cust_id="CUST-OCCASIONAL") for i in range(2)
        ] + [
            self._create_sample_record("TX-ONE", cust_id="CUST-ONE-TIME")
        ]
        engine.aggregate(recs)
        result = engine.generate_report()

        clusters = result.metrics['cluster_summary']
        self.assertEqual(clusters["Frequent / High-Value"]['customer_count'], 1)
        self.assertEqual(clusters["Occasional Shoppers"]['customer_count'], 1)
        self.assertEqual(clusters["One-Time / Inactive"]['customer_count'], 1)

    def test_zscore_anomaly_strategy(self):
        strategy = ZScoreAnomalyStrategy(threshold_sigma=2.0)
        daily_series = {
            f"2024-01-{i:02d}": 1000.0 for i in range(1, 20)
        }
        # Inject extreme sales drop outlier on 20th
        daily_series["2024-01-20"] = 100.0

        anomalies = strategy.detect_anomalies(daily_series)
        self.assertTrue(len(anomalies) >= 1)
        self.assertEqual(anomalies[0]['date'], "2024-01-20")
        self.assertEqual(anomalies[0]['direction'], "DROP")


if __name__ == '__main__':
    unittest.main()
