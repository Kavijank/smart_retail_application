"""
Engine 5: Anomaly Detection Engine
Automatically detects operational irregularities, sales drop outliers, discount spikes, and return surges.
"""
from collections import defaultdict
from typing import List, Dict, Any
from models.transaction_record import TransactionRecord
from models.analytics_result import AnalyticsResult
from engines.analytics_engine_interface import IAnalyticsEngine
from engines.strategies import IAnomalyStrategy, ZScoreAnomalyStrategy


class AnomalyDetectionEngine(IAnalyticsEngine):

    def __init__(self, strategy: IAnomalyStrategy = None):
        self.strategy = strategy or ZScoreAnomalyStrategy(threshold_sigma=2.5)
        self.reset()

    def set_strategy(self, strategy: IAnomalyStrategy) -> None:
        self.strategy = strategy

    def reset(self) -> None:
        # Daily sales tracking: YYYY-MM-DD -> total revenue
        self.daily_sales: Dict[str, float] = defaultdict(float)
        
        # High discount anomalies: records with discount >= 50%
        self.discount_spike_alerts: List[dict] = []

        # Store-level return tracking: store_id -> {sales_count, returns_count, return_amount}
        self.store_returns: Dict[str, dict] = defaultdict(lambda: {
            'sales_count': 0,
            'returns_count': 0,
            'returns_amount': 0.0,
            'sales_revenue': 0.0
        })

    def aggregate(self, chunk: List[TransactionRecord]) -> None:
        for r in chunk:
            date_key = r.transaction_datetime.strftime('%Y-%m-%d')
            store_stat = self.store_returns[r.store_id]

            if r.is_return:
                store_stat['returns_count'] += 1
                store_stat['returns_amount'] += abs(r.total_amount)
                continue

            amt = r.total_amount
            self.daily_sales[date_key] += amt
            store_stat['sales_count'] += 1
            store_stat['sales_revenue'] += amt

            # Check for excessive single-transaction discount spike
            if r.discount_percent >= 50.0 and len(self.discount_spike_alerts) < 200:
                self.discount_spike_alerts.append({
                    'transaction_id': r.transaction_id,
                    'datetime': r.transaction_datetime.strftime('%Y-%m-%d %H:%M'),
                    'store_id': r.store_id,
                    'product_name': r.product_name,
                    'discount_percent': r.discount_percent,
                    'total_amount': round(r.total_amount, 2),
                    'severity': 'HIGH' if r.discount_percent >= 70.0 else 'MEDIUM'
                })

    def generate_report(self) -> AnalyticsResult:
        # Run statistical anomaly detection on daily sales time series
        statistical_anomalies = self.strategy.detect_anomalies(self.daily_sales)

        # Evaluate abnormal return rates per store (> 8% of sales volume)
        abnormal_return_stores = []
        for s_id, data in self.store_returns.items():
            tot = data['sales_count'] + data['returns_count']
            if tot >= 50:
                ret_rate = (data['returns_count'] / tot) * 100.0
                if ret_rate >= 7.0:
                    abnormal_return_stores.append({
                        'store_id': s_id,
                        'sales_count': data['sales_count'],
                        'returns_count': data['returns_count'],
                        'return_rate_percent': round(ret_rate, 2),
                        'returns_amount': round(data['returns_amount'], 2),
                        'severity': 'CRITICAL' if ret_rate >= 10.0 else 'WARNING'
                    })
        abnormal_return_stores.sort(key=lambda x: x['return_rate_percent'], reverse=True)

        metrics = {
            'daily_sales_anomalies': statistical_anomalies,
            'discount_spike_count': len(self.discount_spike_alerts),
            'discount_spike_samples': self.discount_spike_alerts[:25],
            'abnormal_return_stores': abnormal_return_stores,
            'total_anomalies_detected': len(statistical_anomalies) + len(self.discount_spike_alerts) + len(abnormal_return_stores)
        }

        summary = (
            f"Anomaly Detection: Detected {len(statistical_anomalies)} statistical sales volume outliers, "
            f"{len(self.discount_spike_alerts):,} extreme discount spikes (>=50%), and "
            f"{len(abnormal_return_stores)} stores with elevated return rates (>=7%)."
        )

        return AnalyticsResult(
            engine_name="Anomaly Detection Engine",
            metrics=metrics,
            summary_text=summary
        )
