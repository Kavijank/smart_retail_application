"""
Engine 2: Customer Segmentation Analysis
Segments customers by RFM characteristics and produces demographic/geographic cross-tabulations.
"""
from collections import defaultdict
from typing import List, Dict, Any
from models.transaction_record import TransactionRecord
from models.analytics_result import AnalyticsResult
from engines.analytics_engine_interface import IAnalyticsEngine
from engines.strategies import ISegmentationStrategy, RfmSegmentationStrategy


class CustomerSegmentationEngine(IAnalyticsEngine):

    def __init__(self, strategy: ISegmentationStrategy = None):
        self.strategy = strategy or RfmSegmentationStrategy()
        self.reset()

    def set_strategy(self, strategy: ISegmentationStrategy) -> None:
        self.strategy = strategy

    def reset(self) -> None:
        # Aggregated customer profiles: customer_id -> {count, total_spend, items, last_date, gender, age_group, city}
        self.customer_profiles: Dict[str, dict] = defaultdict(lambda: {
            'count': 0,
            'total_spend': 0.0,
            'total_items': 0,
            'last_date': None,
            'gender': 'Unknown',
            'age_group': 'Unknown',
            'city': 'Unknown'
        })

        # Demographic tallies
        self.age_group_spend: Dict[str, float] = defaultdict(float)
        self.gender_spend: Dict[str, float] = defaultdict(float)
        self.city_spend: Dict[str, float] = defaultdict(float)

    def aggregate(self, chunk: List[TransactionRecord]) -> None:
        for r in chunk:
            if r.is_return:
                continue

            cid = r.customer_id
            prof = self.customer_profiles[cid]
            prof['count'] += 1
            prof['total_spend'] += r.total_amount
            prof['total_items'] += r.quantity
            
            # Demographic attributes
            if r.customer_gender and r.customer_gender != 'Unknown':
                prof['gender'] = r.customer_gender
            
            age_label = self._classify_age_group(r.customer_age)
            prof['age_group'] = age_label

            if r.customer_city and r.customer_city != 'Unknown':
                prof['city'] = r.customer_city

            # Accumulators
            self.age_group_spend[age_label] += r.total_amount
            self.gender_spend[prof['gender']] += r.total_amount
            self.city_spend[prof['city']] += r.total_amount

    def _classify_age_group(self, age) -> str:
        if age is None or age <= 0:
            return "Unspecified"
        if age < 25:
            return "18-24"
        elif age < 35:
            return "25-34"
        elif age < 50:
            return "35-49"
        elif age < 65:
            return "50-64"
        else:
            return "65+"

    def generate_report(self) -> AnalyticsResult:
        segmented_clusters = self.strategy.segment(self.customer_profiles)

        cluster_summary = {}
        for cluster_name, c_ids in segmented_clusters.items():
            total_customers = len(c_ids)
            total_rev = sum(self.customer_profiles[cid]['total_spend'] for cid in c_ids)
            total_orders = sum(self.customer_profiles[cid]['count'] for cid in c_ids)
            total_items = sum(self.customer_profiles[cid]['total_items'] for cid in c_ids)
            avg_basket_val = (total_rev / total_orders) if total_orders > 0 else 0.0
            avg_basket_items = (total_items / total_orders) if total_orders > 0 else 0.0

            cluster_summary[cluster_name] = {
                'customer_count': total_customers,
                'total_revenue': round(total_rev, 2),
                'total_orders': total_orders,
                'avg_basket_value': round(avg_basket_val, 2),
                'avg_basket_size': round(avg_basket_items, 2)
            }

        metrics = {
            'cluster_summary': cluster_summary,
            'age_group_spend': {k: round(v, 2) for k, v in sorted(self.age_group_spend.items())},
            'gender_spend': {k: round(v, 2) for k, v in sorted(self.gender_spend.items())},
            'top_cities_spend': dict(sorted(self.city_spend.items(), key=lambda x: x[1], reverse=True)[:10]),
            'total_unique_customers': len(self.customer_profiles)
        }

        frequent_count = cluster_summary.get("Frequent / High-Value", {}).get('customer_count', 0)
        summary = (
            f"Customer Segmentation: Analyzed {len(self.customer_profiles):,} unique customer profiles. "
            f"Identified {frequent_count:,} Frequent shoppers contributing "
            f"${cluster_summary.get('Frequent / High-Value', {}).get('total_revenue', 0.0):,} in revenue. "
            f"Top spending age demographic: {max(self.age_group_spend, key=self.age_group_spend.get) if self.age_group_spend else 'N/A'}."
        )

        return AnalyticsResult(
            engine_name="Customer Segmentation Engine",
            metrics=metrics,
            summary_text=summary
        )
