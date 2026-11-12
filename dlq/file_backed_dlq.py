"""
File-backed implementation of Dead-Letter Queue (DLQ).
Buffers records in memory for quick UI inspection and simultaneously writes to disk.
"""
import csv
import os
import threading
from typing import List
from models.faulty_record import FaultyRecord
from dlq.dlq_interface import IDeadLetterQueue


class FileBackedDLQ(IDeadLetterQueue):

    def __init__(self, audit_file_path: str = "dead_letter_audit.csv", max_buffer_size: int = 500):
        self.audit_file_path = audit_file_path
        self.max_buffer_size = max_buffer_size
        self._buffer: List[FaultyRecord] = []
        self._total_failure_count: int = 0
        self._lock = threading.Lock()
        self._file_handle = None
        self._csv_writer = None

        self._initialize_audit_file()

    def _initialize_audit_file(self):
        # Open file and write CSV header
        self._file_handle = open(self.audit_file_path, mode='w', newline='', encoding='utf-8')
        self._csv_writer = csv.writer(self._file_handle)
        self._csv_writer.writerow(['Line_Number', 'Timestamp', 'Failure_Reason', 'Raw_Payload'])
        self._file_handle.flush()

    def route(self, line_number: int, raw_payload: str, failure_reason: str) -> None:
        faulty = FaultyRecord(
            line_number=line_number,
            raw_payload=raw_payload,
            failure_reason=failure_reason
        )
        with self._lock:
            self._total_failure_count += 1
            if len(self._buffer) < self.max_buffer_size:
                self._buffer.append(faulty)
            
            if self._csv_writer:
                self._csv_writer.writerow(faulty.to_csv_row())
                if self._total_failure_count % 100 == 0:
                    self._file_handle.flush()

    def get_faulty_records(self, limit: int = 100) -> List[FaultyRecord]:
        with self._lock:
            return list(self._buffer[:limit])

    def export_audit_log(self, target_path: str) -> None:
        with self._lock:
            if self._file_handle:
                self._file_handle.flush()
        
        # If target path is different, copy over
        if os.path.abspath(target_path) != os.path.abspath(self.audit_file_path):
            import shutil
            shutil.copyfile(self.audit_file_path, target_path)

    def get_failure_count(self) -> int:
        with self._lock:
            return self._total_failure_count

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()
            self._total_failure_count = 0
            if self._file_handle and not self._file_handle.closed:
                self._file_handle.close()
            self._initialize_audit_file()

    def close(self) -> None:
        with self._lock:
            if self._file_handle and not self._file_handle.closed:
                self._file_handle.flush()
                self._file_handle.close()
