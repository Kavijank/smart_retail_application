"""
Facade Pattern orchestrating Data Ingestion, Chained Processing, DLQ, and Analytics.
Provides a single unified entry point for Desktop Controllers and automated test harnesses.
"""
import time
import threading
from typing import List, Dict, Optional
from models.analytics_result import AnalyticsResult
from ingestion.data_reader_interface import IDataReader
from ingestion.data_reader_factory import DataReaderFactory
from dlq.dlq_interface import IDeadLetterQueue
from dlq.file_backed_dlq import FileBackedDLQ
from pipeline.pipeline_stage_interface import IPipelineStage
from pipeline.validation_stage import ValidationStage
from pipeline.enrichment_stage import EnrichmentStage
from engines.analytics_engine_interface import IAnalyticsEngine
from engines.peak_sales_engine import PeakSalesEngine
from engines.customer_segmentation_engine import CustomerSegmentationEngine
from engines.seasonal_promotional_engine import SeasonalPromotionalEngine
from engines.revenue_product_engine import RevenueProductEngine
from engines.anomaly_detection_engine import AnomalyDetectionEngine
from engines.store_regional_engine import StoreRegionalEngine
from facade.pipeline_observer_interface import IPipelineObserver


class AnalyticsPipelineFacade:

    def __init__(self, dlq_path: str = "dead_letter_audit.csv"):
        self.dlq_path = dlq_path
        self.reader: Optional[IDataReader] = None
        self.pipeline_head: Optional[IPipelineStage] = None
        self.dlq: IDeadLetterQueue = FileBackedDLQ(audit_file_path=dlq_path)
        
        # Instantiate the 6 core analytics engines
        self.engines: Dict[str, IAnalyticsEngine] = {
            'peak_sales': PeakSalesEngine(),
            'customer_segmentation': CustomerSegmentationEngine(),
            'seasonal_promotional': SeasonalPromotionalEngine(),
            'revenue_product': RevenueProductEngine(),
            'anomaly_detection': AnomalyDetectionEngine(),
            'store_regional': StoreRegionalEngine()
        }

        self.observers: List[IPipelineObserver] = []
        self._is_cancelled = False
        self._is_running = False

    def register_observer(self, observer: IPipelineObserver) -> None:
        if observer not in self.observers:
            self.observers.append(observer)

    def remove_observer(self, observer: IPipelineObserver) -> None:
        if observer in self.observers:
            self.observers.remove(observer)

    def cancel(self) -> None:
        self._is_cancelled = True

    def configure_pipeline(self, source_path: str, chunk_size: int = 5000) -> None:
        self.chunk_size = chunk_size
        self.source_path = source_path
        self.reader = DataReaderFactory.create_reader(source_path)
        
        # Reset DLQ and Engines
        self.dlq.clear()
        for engine in self.engines.values():
            engine.reset()

        # Build Pipeline Chain: Validation -> Enrichment
        val_stage = ValidationStage(self.dlq)
        enrich_stage = EnrichmentStage()
        val_stage.set_next(enrich_stage)
        self.pipeline_head = val_stage

    def execute_pipeline(self) -> Dict[str, AnalyticsResult]:
        if not self.reader or not self.pipeline_head:
            raise RuntimeError("Pipeline must be configured before execution.")

        self._is_cancelled = False
        self._is_running = True

        processed_records = 0
        start_time = time.time()
        last_reported_dlq = 0

        try:
            self.reader.open(self.source_path)
            total_estimated = self.reader.get_total_lines_estimated()

            while self.reader.has_next() and not self._is_cancelled:
                # 1. Stream next chunk
                raw_chunk, parsing_faults = self.reader.read_next_chunk(self.chunk_size)

                # Route any low-level reader parsing faults to DLQ
                for line_num, raw_payload, reason in parsing_faults:
                    self.dlq.route(line_num, raw_payload, reason)

                if not raw_chunk and not self.reader.has_next():
                    break

                # 2. Process through transformation pipeline
                clean_chunk = self.pipeline_head.process_chunk(raw_chunk, line_offset=processed_records)
                processed_records += len(raw_chunk)

                # 3. Aggregate across all engines
                for engine in self.engines.values():
                    engine.aggregate(clean_chunk)

                # 4. Check for new DLQ items and notify observers
                current_dlq_count = self.dlq.get_failure_count()
                if current_dlq_count > last_reported_dlq:
                    faulty_samples = self.dlq.get_faulty_records(limit=1)
                    if faulty_samples:
                        for obs in self.observers:
                            obs.on_dlq_alert(faulty_samples[0], current_dlq_count)
                    last_reported_dlq = current_dlq_count

                # 5. Progress notification
                elapsed = max(0.001, time.time() - start_time)
                throughput = processed_records / elapsed
                for obs in self.observers:
                    obs.on_progress_update(processed_records, max(processed_records, total_estimated), throughput)

            # Generate final reports from all engines
            results: Dict[str, AnalyticsResult] = {}
            for name, engine in self.engines.items():
                results[name] = engine.generate_report()

            # Notify observers of completion
            for obs in self.observers:
                obs.on_pipeline_complete(results)

            return results

        except Exception as e:
            for obs in self.observers:
                obs.on_error(str(e))
            raise
        finally:
            self._is_running = False
            if self.reader:
                self.reader.close()

    def get_dlq(self) -> IDeadLetterQueue:
        return self.dlq
