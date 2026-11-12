"""
Generates multi-format executive summary reports (HTML / Markdown / Text).
"""
import os
from datetime import datetime
from typing import Dict
from models.analytics_result import AnalyticsResult


class ReportExporter:

    @staticmethod
    def export_html_report(results: Dict[str, AnalyticsResult], output_path: str = "smartmart_executive_report.html") -> str:
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SmartMart Retail Group - Operational Analytics Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; margin: 30px; background: #f8fafc; color: #1e293b; }}
        .header {{ background: #1e3a8a; color: white; padding: 25px; border-radius: 8px; margin-bottom: 25px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.06); }}
        h1, h2, h3 {{ margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 10px 12px; border-bottom: 1px solid #e2e8f0; text-align: left; }}
        th {{ background: #f1f5f9; font-weight: 600; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }}
        .badge-success {{ background: #dcfce7; color: #166534; }}
        .badge-warning {{ background: #fef9c3; color: #854d0e; }}
        .badge-danger {{ background: #fee2e2; color: #991b1b; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SmartMart Retail Group (Pvt) Ltd</h1>
        <p>Operational Data Processing & Analytics Executive Report | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""
        for engine_key, res in results.items():
            html += f"""
    <div class="card">
        <h2>{res.engine_name}</h2>
        <p><strong>Summary:</strong> {res.summary_text}</p>
        <div>
"""
            # Add specific tables if present
            if 'store_workload_summary' in res.metrics:
                html += "<h3>Store-Level Workload Top 10</h3><table><tr><th>Store ID</th><th>Total Orders</th><th>Revenue ($)</th><th>Peak Hours</th></tr>"
                for s in res.metrics['store_workload_summary'][:10]:
                    html += f"<tr><td>{s['store_id']}</td><td>{s['total_tx']:,}</td><td>${s['total_revenue']:,.2f}</td><td>{s['peak_hour']}</td></tr>"
                html += "</table>"

            elif 'cluster_summary' in res.metrics:
                html += "<h3>Customer Segmentation Clusters</h3><table><tr><th>Segment</th><th>Customers</th><th>Total Orders</th><th>Total Spend</th><th>Avg Basket</th></tr>"
                for c_name, c in res.metrics['cluster_summary'].items():
                    html += f"<tr><td><strong>{c_name}</strong></td><td>{c['customer_count']:,}</td><td>{c['total_orders']:,}</td><td>${c['total_revenue']:,.2f}</td><td>${c['avg_basket_value']:.2f}</td></tr>"
                html += "</table>"

            elif 'top_products' in res.metrics:
                html += "<h3>Top Grossing Products</h3><table><tr><th>Product Name</th><th>Category</th><th>Units Sold</th><th>Revenue ($)</th></tr>"
                for p in res.metrics['top_products']:
                    html += f"<tr><td>{p['product_name']}</td><td>{p['category']}</td><td>{p['units']:,}</td><td>${p['revenue']:,.2f}</td></tr>"
                html += "</table>"

            elif 'regional_summary' in res.metrics:
                html += "<h3>Regional Performance Overview</h3><table><tr><th>Region</th><th>Stores</th><th>Revenue ($)</th><th>Share %</th><th>Orders</th></tr>"
                for r_name, r in res.metrics['regional_summary'].items():
                    html += f"<tr><td>{r_name}</td><td>{r['store_count']}</td><td>${r['total_revenue']:,.2f}</td><td>{r['revenue_share_percent']}%</td><td>{r['total_transactions']:,}</td></tr>"
                html += "</table>"

            elif 'daily_sales_anomalies' in res.metrics:
                html += "<h3>Detected Anomalies</h3><table><tr><th>Date</th><th>Revenue ($)</th><th>Mean ($)</th><th>Z-Score</th><th>Severity</th></tr>"
                for a in res.metrics['daily_sales_anomalies'][:15]:
                    b_class = "badge-danger" if a['severity'] == 'HIGH' else "badge-warning"
                    html += f"<tr><td>{a['date']}</td><td>${a['value']:,.2f}</td><td>${a['mean']:,.2f}</td><td>{a['z_score']}</td><td><span class='badge {b_class}'>{a['severity']}</span></td></tr>"
                html += "</table>"

            html += "</div></div>"

        html += "</body></html>"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path
