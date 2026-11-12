"""
Engine 4: Revenue & Product Performance Analysis
Calculates sales revenue across product categories, individual SKUs, and regions.
"""
from collections import defaultdict
from typing import List, Dict, Any
from models.transaction_record import TransactionRecord
from models.analytics_result import AnalyticsResult
from engines.analytics_engine_interface import IAnalyticsEngine


class RevenueProductEngine(IAnalyticsEngine):

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.category_revenue: Dict[str, float] = defaultdict(float)
        self.category_units: Dict[str, int] = defaultdict(int)
        
        # Product SKU performance: product_name -> {units, revenue, category}
        self.product_performance: Dict[str, dict] = defaultdict(lambda: {
            'units': 0,
            'revenue': 0.0,
            'category': 'Unknown'
        })

        self.payment_channel_revenue: Dict[str, float] = defaultdict(float)
        self.total_gross_sales: float = 0.0
        self.total_net_revenue: float = 0.0
        self.total_discounts_granted: float = 0.0
        self.total_returns_amount: float = 0.0

    def aggregate(self, chunk: List[TransactionRecord]) -> None:
        for r in chunk:
            if r.is_return:
                self.total_returns_amount += abs(r.total_amount)
                continue

            amt = r.total_amount
            units = r.quantity
            cat = r.product_category
            prod = r.product_name

            self.total_gross_sales += (r.unit_price * units)
            self.total_net_revenue += amt
            self.total_discounts_granted += r.discount_amount

            self.category_revenue[cat] += amt
            self.category_units[cat] += units

            sku = self.product_performance[prod]
            sku['units'] += units
            sku['revenue'] += amt
            sku['category'] = cat

            self.payment_channel_revenue[r.channel] += amt

    def generate_report(self) -> AnalyticsResult:
        # Sort top and bottom products
        sorted_skus = sorted(self.product_performance.items(), key=lambda x: x[1]['revenue'], reverse=True)
        top_products = [
            {'product_name': k, 'category': v['category'], 'units': v['units'], 'revenue': round(v['revenue'], 2)}
            for k, v in sorted_skus[:10]
        ]
        bottom_products = [
            {'product_name': k, 'category': v['category'], 'units': v['units'], 'revenue': round(v['revenue'], 2)}
            for k, v in sorted_skus[-10:] if v['revenue'] > 0
        ]

        metrics = {
            'total_gross_sales': round(self.total_gross_sales, 2),
            'total_net_revenue': round(self.total_net_revenue, 2),
            'total_discounts_granted': round(self.total_discounts_granted, 2),
            'total_returns_amount': round(self.total_returns_amount, 2),
            'discount_erosion_pct': round((self.total_discounts_granted / self.total_gross_sales * 100.0), 2) if self.total_gross_sales > 0 else 0.0,
            'category_revenue': {k: round(v, 2) for k, v in sorted(self.category_revenue.items(), key=lambda x: x[1], reverse=True)},
            'category_units': dict(sorted(self.category_units.items(), key=lambda x: x[1], reverse=True)),
            'channel_breakdown': {k: round(v, 2) for k, v in sorted(self.payment_channel_revenue.items())},
            'top_products': top_products,
            'bottom_products': bottom_products
        }

        top_cat = max(self.category_revenue, key=self.category_revenue.get) if self.category_revenue else "N/A"
        summary = (
            f"Revenue & Product Performance: Total Net Revenue is ${self.total_net_revenue:,.2f} "
            f"(with ${self.total_discounts_granted:,.2f} in promotional discounts granted). "
            f"Top product category: {top_cat} (${self.category_revenue.get(top_cat, 0.0):,.2f}). "
            f"Highest-grossing SKU: {top_products[0]['product_name'] if top_products else 'N/A'} "
            f"(${top_products[0]['revenue'] if top_products else 0.0:,.2f})."
        )

        return AnalyticsResult(
            engine_name="Revenue & Product Performance Engine",
            metrics=metrics,
            summary_text=summary
        )
