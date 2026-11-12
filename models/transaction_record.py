"""
Domain model representing an individual retail transaction record.
Follows clean encapsulation with immutability where applicable.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class TransactionRecord:
    transaction_id: str
    transaction_datetime: datetime
    store_id: str
    store_city: str
    region: str
    warehouse_id: str
    customer_id: str
    customer_age: Optional[int]
    customer_gender: str
    customer_city: str
    product_category: str
    product_name: str
    quantity: int
    unit_price: float
    discount_percent: float
    promotion_name: str
    payment_method: str
    channel: str
    total_amount: float
    stock_on_hand: int
    reorder_level: int
    transaction_type: str  # 'Sale' or 'Return'
    
    # Derived / Enriched attributes
    net_margin: float = 0.0
    discount_amount: float = 0.0
    hour: int = 0
    day_of_week: str = ""
    month_name: str = ""

    def __post_init__(self):
        if self.transaction_datetime:
            self.hour = self.transaction_datetime.hour
            self.day_of_week = self.transaction_datetime.strftime('%A')
            self.month_name = self.transaction_datetime.strftime('%B')
            
    @property
    def is_return(self) -> bool:
        return self.transaction_type.lower() == 'return' or self.quantity < 0 or self.total_amount < 0

    @property
    def is_promotion(self) -> bool:
        return bool(self.promotion_name and self.promotion_name.strip().lower() != 'no promotion')
