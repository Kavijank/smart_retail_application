"""
Strategy Pattern implementations for Customer Segmentation and Anomaly Detection.
Enables runtime swappability of mathematical models.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import math


# ==========================================================
# 1. CUSTOMER SEGMENTATION STRATEGY
# ==========================================================

class ISegmentationStrategy(ABC):
    @abstractmethod
    def segment(self, customer_profiles: Dict[str, dict]) -> Dict[str, List[str]]:
        """
        Segments customers into clusters based on purchase history.
        Returns: Dict mapping 'Segment Name' -> list of customer_ids
        """
        pass


class RfmSegmentationStrategy(ISegmentationStrategy):
    """
    Classifies customers into Frequent, Occasional, and One-Time Shoppers
    based on transaction count and monetary spend.
    """
    def __init__(self, frequent_min_orders: int = 5, occasional_min_orders: int = 2):
        self.frequent_min_orders = frequent_min_orders
        self.occasional_min_orders = occasional_min_orders

    def segment(self, customer_profiles: Dict[str, dict]) -> Dict[str, List[str]]:
        segments = {
            "Frequent / High-Value": [],
            "Occasional Shoppers": [],
            "One-Time / Inactive": []
        }

        for cid, data in customer_profiles.items():
            tx_count = data.get('count', 0)
            if tx_count >= self.frequent_min_orders:
                segments["Frequent / High-Value"].append(cid)
            elif tx_count >= self.occasional_min_orders:
                segments["Occasional Shoppers"].append(cid)
            else:
                segments["One-Time / Inactive"].append(cid)

        return segments


# ==========================================================
# 2. ANOMALY DETECTION STRATEGY
# ==========================================================

class IAnomalyStrategy(ABC):
    @abstractmethod
    def detect_anomalies(self, daily_series: Dict[str, float]) -> List[dict]:
        """
        Evaluates a time series and returns detected anomaly events.
        """
        pass


class ZScoreAnomalyStrategy(IAnomalyStrategy):
    """
    Detects outliers where metric deviates by more than threshold * standard deviations.
    """
    def __init__(self, threshold_sigma: float = 2.5):
        self.threshold_sigma = threshold_sigma

    def detect_anomalies(self, daily_series: Dict[str, float]) -> List[dict]:
        if not daily_series or len(daily_series) < 5:
            return []

        values = list(daily_series.values())
        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return []

        anomalies = []
        for date_str, val in daily_series.items():
            z_score = (val - mean_val) / std_dev
            if abs(z_score) >= self.threshold_sigma:
                severity = "HIGH" if abs(z_score) >= 3.0 else "MEDIUM"
                anomalies.append({
                    'date': date_str,
                    'value': round(val, 2),
                    'mean': round(mean_val, 2),
                    'z_score': round(z_score, 2),
                    'severity': severity,
                    'direction': "SPIKE" if z_score > 0 else "DROP"
                })

        return anomalies
