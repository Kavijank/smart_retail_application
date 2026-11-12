"""
Validation pipeline stage.
Enforces data quality rules and routes corrupted rows to the Dead-Letter Queue (DLQ).
"""
from typing import List, Set
from models.transaction_record import TransactionRecord
from dlq.dlq_interface import IDeadLetterQueue
from pipeline.base_pipeline_stage import BasePipelineStage


class ValidationStage(BasePipelineStage):

    def __init__(self, dlq: IDeadLetterQueue, max_seen_ids: int = 500000):
        super().__init__()
        self.dlq = dlq
        self._seen_transaction_ids: Set[str] = set()
        self.max_seen_ids = max_seen_ids

    def process_chunk(self, chunk: List[TransactionRecord], line_offset: int = 0) -> List[TransactionRecord]:
        clean_chunk: List[TransactionRecord] = []

        for idx, record in enumerate(chunk):
            current_line = line_offset + idx + 1
            is_valid, reason = self._validate_record(record)

            if is_valid:
                clean_chunk.append(record)
            else:
                raw_summary = (
                    f"id={record.transaction_id}|store={record.store_id}|prod={record.product_name}|"
                    f"qty={record.quantity}|price={record.unit_price}|disc={record.discount_percent}|total={record.total_amount}"
                )
                self.dlq.route(current_line, raw_summary, reason)

        return self._pass_to_next(clean_chunk, line_offset)

    def _validate_record(self, r: TransactionRecord) -> tuple[bool, str]:
        # 1. Duplicate Check
        if r.transaction_id in self._seen_transaction_ids:
            return False, "DUPLICATE_TRANSACTION_ID"
        
        # 2. Required identifier checks
        if not r.store_id or not r.store_id.strip():
            return False, "MISSING_STORE_ID"
        if not r.region or not r.region.strip():
            return False, "MISSING_REGION"

        # 3. Unit Price sanity
        if r.unit_price <= 0:
            return False, f"INVALID_UNIT_PRICE: {r.unit_price}"

        # 4. Discount % sanity
        if r.discount_percent < 0 or r.discount_percent > 100:
            return False, f"INVALID_DISCOUNT_PERCENT: {r.discount_percent}%"

        # 5. Quantity and Transaction Type sanity
        if not r.is_return and r.quantity <= 0:
            return False, f"NON_POSITIVE_SALE_QUANTITY: {r.quantity}"

        # 6. Mathematical Total Amount verification (tolerance for floating point)
        expected_total = (r.quantity * r.unit_price) * (1.0 - (r.discount_percent / 100.0))
        # Returns have negative expected totals
        if abs(r.total_amount - expected_total) > 2.0:
            # Significant calculation mismatch
            return False, f"TOTAL_AMOUNT_MISMATCH: expected {expected_total:.2f}, got {r.total_amount:.2f}"

        # Register ID
        if len(self._seen_transaction_ids) < self.max_seen_ids:
            self._seen_transaction_ids.add(r.transaction_id)

        return True, ""
