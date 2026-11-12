"""
Chain of Responsibility interface for modular pipeline stages.
"""
from abc import ABC, abstractmethod
from typing import List
from models.transaction_record import TransactionRecord


class IPipelineStage(ABC):

    @abstractmethod
    def set_next(self, next_stage: 'IPipelineStage') -> 'IPipelineStage':
        """Sets the successor in the chain and returns it for fluent chaining."""
        pass

    @abstractmethod
    def process_chunk(self, chunk: List[TransactionRecord], line_offset: int = 0) -> List[TransactionRecord]:
        """Processes the chunk of records and passes them down the chain."""
        pass
