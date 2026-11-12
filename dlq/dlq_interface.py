"""
Contract for the Dead-Letter Queue (DLQ).
Enforces fault tolerance by capturing, auditing, and persisting faulty records.
"""
from abc import ABC, abstractmethod
from typing import List
from models.faulty_record import FaultyRecord


class IDeadLetterQueue(ABC):

    @abstractmethod
    def route(self, line_number: int, raw_payload: str, failure_reason: str) -> None:
        """Routes a corrupted/rejected record to the DLQ buffer and disk."""
        pass

    @abstractmethod
    def get_faulty_records(self, limit: int = 100) -> List[FaultyRecord]:
        """Returns recent faulty records for GUI inspection."""
        pass

    @abstractmethod
    def export_audit_log(self, target_path: str) -> None:
        """Exports the full audit log of all rejected records to CSV."""
        pass

    @abstractmethod
    def get_failure_count(self) -> int:
        """Returns the total number of quarantined records."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Resets the queue for a new run."""
        pass
