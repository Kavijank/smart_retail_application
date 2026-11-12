"""
Model capturing diagnostic details for records that fail validation.
Enables dead-letter queue auditing and forensic analysis.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class FaultyRecord:
    line_number: int
    raw_payload: str
    failure_reason: str
    timestamp: datetime = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()

    def to_csv_row(self) -> list:
        return [
            str(self.line_number),
            self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            self.failure_reason,
            self.raw_payload.replace('\n', ' ').replace('\r', '')
        ]
