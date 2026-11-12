"""
Concrete streaming CSV data reader implementing IDataReader.
Uses line-by-line streaming to prevent memory exhaustion on large datasets.
"""
import csv
import io
import os
from datetime import datetime
from typing import List, Tuple, Optional
from models.transaction_record import TransactionRecord
from ingestion.data_reader_interface import IDataReader


class CsvDataReader(IDataReader):

    DATE_FORMATS = (
        '%m/%d/%Y %H:%M',
        '%m/%d/%Y %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%d/%m/%Y %H:%M',
        '%d-%m-%Y %H:%M:%S'
    )

    def __init__(self, delimiter: str = ','):
        self.delimiter = delimiter
        self.file_handle: Optional[io.TextIOWrapper] = None
        self.csv_reader = None
        self.source_path: str = ""
        self.current_line_number: int = 0
        self.total_estimated_lines: int = 0
        self._is_eof: bool = False
        self.header_map: dict = {}

    def open(self, source_path: str) -> None:
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        self.source_path = source_path
        self.file_handle = open(source_path, mode='r', encoding='utf-8-sig', errors='replace')
        self.csv_reader = csv.reader(self.file_handle, delimiter=self.delimiter)
        self.current_line_number = 0
        self._is_eof = False

        # Read header row
        try:
            headers = next(self.csv_reader)
            self.current_line_number += 1
            self.header_map = {col.strip().lower(): idx for idx, col in enumerate(headers)}
        except StopIteration:
            self._is_eof = True

        # Quick line count estimation based on file size
        file_size = os.path.getsize(source_path)
        # Average line length is ~180 bytes
        self.total_estimated_lines = max(1, int(file_size / 180))

    def get_total_lines_estimated(self) -> int:
        return self.total_estimated_lines

    def has_next(self) -> bool:
        return not self._is_eof

    def read_next_chunk(self, chunk_size: int = 5000) -> Tuple[List[TransactionRecord], List[Tuple[int, str, str]]]:
        if self._is_eof or not self.csv_reader:
            return [], []

        valid_records: List[TransactionRecord] = []
        parsing_faults: List[Tuple[int, str, str]] = []

        count = 0
        while count < chunk_size:
            try:
                row = next(self.csv_reader)
                self.current_line_number += 1
                count += 1
            except StopIteration:
                self._is_eof = True
                break
            except Exception as e:
                self.current_line_number += 1
                parsing_faults.append((self.current_line_number, "<raw unreadable line>", f"IO_READ_ERROR: {str(e)}"))
                continue

            if not row or all(not cell.strip() for cell in row):
                continue  # Skip blank lines

            parsed_record, fault_reason = self._parse_row(row)
            if parsed_record:
                valid_records.append(parsed_record)
            else:
                raw_line = self.delimiter.join(row)
                parsing_faults.append((self.current_line_number, raw_line, fault_reason))

        return valid_records, parsing_faults

    def _parse_row(self, row: List[str]) -> Tuple[Optional[TransactionRecord], str]:
        def get_val(col_name: str, default: str = "") -> str:
            idx = self.header_map.get(col_name.lower())
            if idx is not None and idx < len(row):
                return row[idx].strip()
            return default

        tx_id = get_val('transaction_id')
        if not tx_id:
            return None, "MISSING_TRANSACTION_ID"

        dt_str = get_val('transaction_datetime')
        parsed_dt = None
        for fmt in self.DATE_FORMATS:
            try:
                parsed_dt = datetime.strptime(dt_str, fmt)
                break
            except ValueError:
                continue

        if not parsed_dt:
            return None, f"INVALID_DATETIME_FORMAT: '{dt_str}'"

        store_id = get_val('store_id')
        store_city = get_val('store_city')
        region = get_val('region')
        warehouse_id = get_val('warehouse_id')
        cust_id = get_val('customer_id') or "GUEST"
        
        age_str = get_val('customer_age')
        try:
            cust_age = int(float(age_str)) if age_str else None
        except ValueError:
            cust_age = None

        cust_gender = get_val('customer_gender') or "Unknown"
        cust_city = get_val('customer_city') or store_city
        prod_cat = get_val('product_category') or "Uncategorized"
        prod_name = get_val('product_name') or "Unknown Product"

        try:
            qty = int(float(get_val('quantity', '1')))
        except ValueError:
            return None, f"INVALID_QUANTITY_NUMERIC: '{get_val('quantity')}'"

        try:
            unit_price = float(get_val('unit_price', '0.0'))
        except ValueError:
            return None, f"INVALID_UNIT_PRICE_NUMERIC: '{get_val('unit_price')}'"

        try:
            disc_percent = float(get_val('discount_percent', '0.0'))
        except ValueError:
            disc_percent = 0.0

        promo_name = get_val('promotion_name') or "No Promotion"
        pay_method = get_val('payment_method') or "Cash"
        channel = get_val('channel') or "In-Store"

        try:
            total_amt = float(get_val('total_amount', '0.0'))
        except ValueError:
            total_amt = (unit_price * qty) * (1 - (disc_percent / 100.0))

        try:
            stock = int(float(get_val('stock_on_hand', '0')))
        except ValueError:
            stock = 0

        try:
            reorder = int(float(get_val('reorder_level', '0')))
        except ValueError:
            reorder = 0

        tx_type = get_val('transaction_type') or ('Return' if (qty < 0 or total_amt < 0) else 'Sale')

        record = TransactionRecord(
            transaction_id=tx_id,
            transaction_datetime=parsed_dt,
            store_id=store_id,
            store_city=store_city,
            region=region,
            warehouse_id=warehouse_id,
            customer_id=cust_id,
            customer_age=cust_age,
            customer_gender=cust_gender,
            customer_city=cust_city,
            product_category=prod_cat,
            product_name=prod_name,
            quantity=qty,
            unit_price=unit_price,
            discount_percent=disc_percent,
            promotion_name=promo_name,
            payment_method=pay_method,
            channel=channel,
            total_amount=total_amt,
            stock_on_hand=stock,
            reorder_level=reorder,
            transaction_type=tx_type
        )
        return record, ""

    def close(self) -> None:
        if self.file_handle and not self.file_handle.closed:
            self.file_handle.close()
