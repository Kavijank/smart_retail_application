"""
Engine 6: Store & Regional Performance Analysis
Compares performance across regional clusters and benchmarks retail outlets.
"""
from collections import defaultdict
from typing import List, Dict, Any
from models.transaction_record import TransactionRecord
from models.analytics_result import AnalyticsResult
from engines.analytics_engine_interface import IAnalyticsEngine


class StoreRegionalEngine(IAnalyticsEngine):

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        # Regional metrics: region -> {revenue, tx_count, units, stores}
        self.regional_data: Dict[str, dict] = defaultdict(lambda: {
            'revenue': 0.0,
            'tx_count': 0,
            'units': 0,
            'stores': set()
        })

        # Store-level metrics: store_id -> {city, region, revenue, tx_count, units, low_stock_alerts}
        self.store_metrics: Dict[str, dict] = defaultdict(lambda: {
            'city': 'Unknown',
            'region': 'Unknown',
            'revenue': 0.0,
            'tx_count': 0,
            'units': 0,
            'stock_critical_count': 0
        })

    def aggregate(self, chunk: List[TransactionRecord]) -> None:
        for r in chunk:
            if r.is_return:
                continue

            reg = r.region
            sid = r.store_id
            amt = r.total_amount
            qty = r.quantity

            # Region
            r_data = self.regional_data[reg]
            r_data['revenue'] += amt
            r_data['tx_count'] += 1
            r_data['units'] += qty
            r_data['stores'].add(sid)

            # Store
            s_data = self.store_metrics[sid]
            s_data['city'] = r.store_city
            s_data['region'] = reg
            s_data['revenue'] += amt
            s_data['tx_count'] += 1
            s_data['units'] += qty

            if r.stock_on_hand <= r.reorder_level:
                s_data['stock_critical_count'] += 1

    def generate_report(self) -> AnalyticsResult:
        # Regional summary
        total_chain_revenue = sum(v['revenue'] for v in self.regional_data.values())
        regional_summary = {}
        for reg, data in sorted(self.regional_data.items(), key=lambda x: x[1]['revenue'], reverse=True):
            rev_share = (data['revenue'] / total_chain_revenue * 100.0) if total_chain_revenue > 0 else 0.0
            avg_tx_val = (data['revenue'] / data['tx_count']) if data['tx_count'] > 0 else 0.0
            regional_summary[reg] = {
                'store_count': len(data['stores']),
                'total_revenue': round(data['revenue'], 2),
                'revenue_share_percent': round(rev_share, 2),
                'total_transactions': data['tx_count'],
                'average_transaction_value': round(avg_tx_val, 2)
            }

        # Store rankings
        store_rankings = []
        for sid, s in self.store_metrics.items():
            avg_ticket = (s['revenue'] / s['tx_count']) if s['tx_count'] > 0 else 0.0
            store_rankings.append({
                'store_id': sid,
                'city': s['city'],
                'region': s['region'],
                'revenue': round(s['revenue'], 2),
                'transactions': s['tx_count'],
                'avg_ticket': round(avg_ticket, 2),
                'stock_alerts': s['stock_critical_count']
            })
        store_rankings.sort(key=lambda x: x['revenue'], reverse=True)

        metrics = {
            'regional_summary': regional_summary,
            'top_5_stores': store_rankings[:5],
            'bottom_5_stores': store_rankings[-5:] if len(store_rankings) >= 5 else [],
            'all_store_rankings': store_rankings
        }

        top_store = store_rankings[0] if store_rankings else None
        summary = (
            f"Store & Regional Performance: Evaluated {len(self.regional_data)} geographic regions "
            f"and {len(store_rankings)} outlets. Highest-revenue region: "
            f"{max(regional_summary, key=lambda r: regional_summary[r]['total_revenue']) if regional_summary else 'N/A'}. "
            f"Top performing store: {top_store['store_id']} ({top_store['city']}) with ${top_store['revenue']:,.2f}."
        )

        return AnalyticsResult(
            engine_name="Store & Regional Performance Engine",
            metrics=metrics,
            summary_text=summary
        )
