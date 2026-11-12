"""
Base abstract pipeline stage providing default successor chaining.
"""
from typing import Optional, List
from models.transaction_record import TransactionRecord
from pipeline.pipeline_stage_interface import IPipelineStage


class BasePipelineStage(IPipelineStage):

    def __init__(self):
        self._next_stage: Optional[IPipelineStage] = None

    def set_next(self, next_stage: IPipelineStage) -> IPipelineStage:
        self._next_stage = next_stage
        return next_stage

    def _pass_to_next(self, chunk: List[TransactionRecord], line_offset: int = 0) -> List[TransactionRecord]:
        if self._next_stage:
            return self._next_stage.process_chunk(chunk, line_offset)
        return chunk
