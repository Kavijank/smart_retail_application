"""
Abstract interface contract for source-agnostic data readers.
Supports chunk-based streaming to ensure memory efficiency.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
from models.transaction_record import TransactionRecord


class IDataReader(ABC):

    @abstractmethod
    def open(self, source_path: str) -> None:
        """Opens the data source stream."""
        pass

    @abstractmethod
    def read_next_chunk(self, chunk_size: int = 5000) -> Tuple[List[TransactionRecord], List[Tuple[int, str, str]]]:
        """
        Reads next batch of records.
        Returns:
            Tuple of:
             - List of parsed TransactionRecord instances
             - List of unparseable raw tuples (line_number, raw_text, reason)
        """
        pass

    @abstractmethod
    def has_next(self) -> bool:
        """Returns True if more data remains to be read."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Closes stream and releases resources."""
        pass

    @abstractmethod
    def get_total_lines_estimated(self) -> int:
        """Returns total line count or best estimate for progress bars."""
        pass
