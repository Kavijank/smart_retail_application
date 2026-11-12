"""
Enrichment pipeline stage.
Computes derived financial and operational metrics on sanitized records.
"""
from typing import List, Dict
from models.transaction_record import TransactionRecord
from pipeline.base_pipeline_stage import BasePipelineStage


class EnrichmentStage(BasePipelineStage):

    # Benchmark gross margin estimates by category
    CATEGORY_MARGINS: Dict[str, float] = {
        'groceries': 0.18,
        'bakery': 0.35,
        'beverages': 0.28,
        'dairy': 0.22,
        'clothing': 0.45,
        'electronics': 0.20,
        'frozen foods': 0.25,
        'personal care': 0.38,
        'household': 0.30
    }

    def process_chunk(self, chunk: List[TransactionRecord], line_offset: int = 0) -> List[TransactionRecord]:
        for r in chunk:
            # 1. Discount amount
            gross_val = r.unit_price * r.quantity
            r.discount_amount = gross_val * (r.discount_percent / 100.0)

            # 2. Net margin calculation
            cat_key = r.product_category.strip().lower()
            margin_rate = self.CATEGORY_MARGINS.get(cat_key, 0.25)
            r.net_margin = r.total_amount * margin_rate

        return self._pass_to_next(chunk, line_offset)
