"""
Engine 3: Seasonal & Promotional Demand Analysis
Evaluates monthly seasonal demand curves, promotional lift, and holiday impacts.
"""
from collections import defaultdict
from typing import List, Dict, Any
from models.transaction_record import TransactionRecord
from models.analytics_result import AnalyticsResult
from engines.analytics_engine_interface import IAnalyticsEngine


class SeasonalPromotionalEngine(IAnalyticsEngine):

    MONTHS = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        # Monthly trend (Revenue and Transactions)
        self.monthly_revenue: Dict[str, float] = {m: 0.0 for m in self.MONTHS}
        self.monthly_tx_count: Dict[str, int] = {m: 0 for m in self.MONTHS}

        # Promotional vs Baseline (No promotion)
        self.promo_revenue: float = 0.0
        self.promo_tx_count: int = 0
        self.baseline_revenue: float = 0.0
        self.baseline_tx_count: int = 0

        # Performance by Promotion Name
        self.campaign_revenue: Dict[str, float] = defaultdict(float)
        self.campaign_tx_count: Dict[str, int] = defaultdict(int)

    def aggregate(self, chunk: List[TransactionRecord]) -> None:
        for r in chunk:
            if r.is_return:
                continue

            m = r.month_name
            amt = r.total_amount

            if m in self.monthly_revenue:
                self.monthly_revenue[m] += amt
                self.monthly_tx_count[m] += 1

            if r.is_promotion:
                self.promo_revenue += amt
                self.promo_tx_count += 1
                promo_key = r.promotion_name.strip()
                self.campaign_revenue[promo_key] += amt
                self.campaign_tx_count[promo_key] += 1
            else:
                self.baseline_revenue += amt
                self.baseline_tx_count += 1

    def generate_report(self) -> AnalyticsResult:
        # Calculate promotional lift
        avg_promo_ticket = (self.promo_revenue / self.promo_tx_count) if self.promo_tx_count > 0 else 0.0
        avg_base_ticket = (self.baseline_revenue / self.baseline_tx_count) if self.baseline_tx_count > 0 else 0.0
        lift_percent = (((avg_promo_ticket - avg_base_ticket) / avg_base_ticket) * 100.0) if avg_base_ticket > 0 else 0.0

        # Sort campaign performance
        campaigns = []
        for c_name, c_rev in sorted(self.campaign_revenue.items(), key=lambda x: x[1], reverse=True):
            tx_c = self.campaign_tx_count[c_name]
            campaigns.append({
                'campaign_name': c_name,
                'revenue': round(c_rev, 2),
                'tx_count': tx_c,
                'avg_basket': round(c_rev / tx_c, 2) if tx_c > 0 else 0.0
            })

        # Find peak season month
        peak_month = max(self.monthly_revenue.keys(), key=lambda m: self.monthly_revenue[m]) if self.monthly_revenue else "December"

        metrics = {
            'monthly_revenue': {m: round(self.monthly_revenue[m], 2) for m in self.MONTHS},
            'monthly_tx_count': self.monthly_tx_count,
            'promo_revenue': round(self.promo_revenue, 2),
            'promo_tx_count': self.promo_tx_count,
            'baseline_revenue': round(self.baseline_revenue, 2),
            'baseline_tx_count': self.baseline_tx_count,
            'avg_promo_ticket': round(avg_promo_ticket, 2),
            'avg_baseline_ticket': round(avg_base_ticket, 2),
            'promotional_lift_percent': round(lift_percent, 2),
            'peak_month': peak_month,
            'campaign_breakdown': campaigns
        }

        summary = (
            f"Seasonal & Promotional Demand: Peak demand occurs in {peak_month} "
            f"(${self.monthly_revenue.get(peak_month, 0.0):,.2f} revenue). "
            f"Promotions generated a {lift_percent:+.2f}% lift in average ticket size "
            f"(${avg_promo_ticket:.2f} promo vs ${avg_base_ticket:.2f} baseline across {self.promo_tx_count:,} promotional orders)."
        )

        return AnalyticsResult(
            engine_name="Seasonal & Promotional Demand Engine",
            metrics=metrics,
            summary_text=summary
        )
