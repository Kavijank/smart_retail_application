"""
Factory Method implementation for creating source-agnostic data readers.
"""
import os
from ingestion.data_reader_interface import IDataReader
from ingestion.csv_data_reader import CsvDataReader


class DataReaderFactory:

    @staticmethod
    def create_reader(file_path: str) -> IDataReader:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ('.csv', '.txt'):
            return CsvDataReader(delimiter=',')
        elif ext == '.tsv':
            return CsvDataReader(delimiter='\t')
        elif ext == '.log':
            # Log files often formatted as tab or comma separated
            return CsvDataReader(delimiter=',')
        else:
            # Default to standard CSV reader
            return CsvDataReader(delimiter=',')
