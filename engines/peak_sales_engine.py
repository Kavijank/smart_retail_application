"""
Engine 1: Peak Sales Analysis
Identifies peak sales hours, days, high-demand stores, and constructs a 24x7 workload matrix.
"""
from collections import defaultdict
from typing import List, Dict, Any
from models.transaction_record import TransactionRecord
from models.analytics_result import AnalyticsResult
from engines.analytics_engine_interface import IAnalyticsEngine


class PeakSalesEngine(IAnalyticsEngine):

    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        # Hourly traffic & revenue (0 - 23)
        self.hourly_tx_count: Dict[int, int] = defaultdict(int)
        self.hourly_revenue: Dict[int, float] = defaultdict(float)

        # Day of week traffic & revenue
        self.daily_tx_count: Dict[str, int] = defaultdict(int)
        self.daily_revenue: Dict[str, float] = defaultdict(float)

        # 24x7 Heatmap Matrix: [day_index][hour] -> transaction count
        self.heatmap_matrix: Dict[str, Dict[int, int]] = {
            day: {h: 0 for h in range(24)} for day in self.DAYS
        }

        # Store-level workload
        self.store_workload: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'tx_count': 0,
            'revenue': 0.0,
            'hourly_buckets': defaultdict(int)
        })

    def aggregate(self, chunk: List[TransactionRecord]) -> None:
        for r in chunk:
            if r.is_return:
                continue

            h = r.hour
            d = r.day_of_week
            amt = r.total_amount

            self.hourly_tx_count[h] += 1
            self.hourly_revenue[h] += amt

            if d in self.daily_tx_count or d in self.DAYS:
                self.daily_tx_count[d] += 1
                self.daily_revenue[d] += amt
                self.heatmap_matrix[d][h] += 1

            store = self.store_workload[r.store_id]
            store['tx_count'] += 1
            store['revenue'] += amt
            store['hourly_buckets'][h] += 1

    def generate_report(self) -> AnalyticsResult:
        # Find peak hour
        peak_hour = max(self.hourly_tx_count.keys(), key=lambda h: self.hourly_tx_count[h]) if self.hourly_tx_count else 0
        peak_day = max(self.daily_tx_count.keys(), key=lambda d: self.daily_tx_count[d]) if self.daily_tx_count else "Saturday"

        # Store workload summary
        store_summary = []
        for s_id, s_data in self.store_workload.items():
            top_h = max(s_data['hourly_buckets'].keys(), key=lambda h: s_data['hourly_buckets'][h]) if s_data['hourly_buckets'] else 0
            store_summary.append({
                'store_id': s_id,
                'total_tx': s_data['tx_count'],
                'total_revenue': round(s_data['revenue'], 2),
                'peak_hour': f"{top_h:02d}:00 - {top_h+1:02d}:00"
            })
        store_summary.sort(key=lambda x: x['total_tx'], reverse=True)

        metrics = {
            'hourly_tx_count': dict(sorted(self.hourly_tx_count.items())),
            'hourly_revenue': {k: round(v, 2) for k, v in sorted(self.hourly_revenue.items())},
            'daily_tx_count': {d: self.daily_tx_count.get(d, 0) for d in self.DAYS},
            'daily_revenue': {d: round(self.daily_revenue.get(d, 0.0), 2) for d in self.DAYS},
            'heatmap_matrix': self.heatmap_matrix,
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'store_workload_summary': store_summary
        }

        summary = (
            f"Peak Sales Analysis: Overall busiest hour across all stores is {peak_hour:02d}:00 - {peak_hour+1:02d}:00 "
            f"with {self.hourly_tx_count.get(peak_hour, 0):,} transactions. Busiest day of the week is {peak_day} "
            f"({self.daily_tx_count.get(peak_day, 0):,} transactions). Evaluated {len(store_summary)} store locations."
        )

        return AnalyticsResult(
            engine_name="Peak Sales Engine",
            metrics=metrics,
            summary_text=summary
        )
