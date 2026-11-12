"""
Observer pattern interface for reactive UI callbacks.
Decouples background thread pipeline processing from GUI rendering.
"""
from abc import ABC, abstractmethod
from typing import Dict
from models.faulty_record import FaultyRecord
from models.analytics_result import AnalyticsResult


class IPipelineObserver(ABC):

    @abstractmethod
    def on_progress_update(self, processed_count: int, estimated_total: int, throughput_rps: float) -> None:
        """Invoked periodically as chunks are processed."""
        pass

    @abstractmethod
    def on_dlq_alert(self, faulty_record: FaultyRecord, current_failure_count: int) -> None:
        """Invoked when a record is quarantined in the DLQ."""
        pass

    @abstractmethod
    def on_pipeline_complete(self, results: Dict[str, AnalyticsResult]) -> None:
        """Invoked when pipeline finishes processing."""
        pass

    @abstractmethod
    def on_error(self, error_message: str) -> None:
        """Invoked if an unrecoverable exception occurs."""
        pass
