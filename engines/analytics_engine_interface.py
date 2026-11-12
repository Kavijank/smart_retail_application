"""
Abstract contract for all analytical engines.
Maintains running aggregations across chunks without storing full datasets in memory.
"""
from abc import ABC, abstractmethod
from typing import List
from models.transaction_record import TransactionRecord
from models.analytics_result import AnalyticsResult


class IAnalyticsEngine(ABC):

    @abstractmethod
    def reset(self) -> None:
        """Resets all internal accumulators."""
        pass

    @abstractmethod
    def aggregate(self, chunk: List[TransactionRecord]) -> None:
        """Processes an incoming chunk and updates running statistical aggregates."""
        pass

    @abstractmethod
    def generate_report(self) -> AnalyticsResult:
        """Produces the finalized analytical result and summary metrics."""
        pass
