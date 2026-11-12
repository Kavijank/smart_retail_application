"""
Exports tabular analytical summaries to CSV format.
"""
import csv
from typing import List, Dict, Any


class CsvExporter:

    @staticmethod
    def export_table(rows: List[Dict[str, Any]], fieldnames: List[str], target_path: str) -> str:
        with open(target_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)
        return target_path
