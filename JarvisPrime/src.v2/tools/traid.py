from typing import List
import statistics

def zscore(price_series: List[float]) -> float:
    if not price_series:
        return 0.0
    mean = statistics.mean(price_series)
    stdev = statistics.pstdev(price_series) or 1.0
    return (price_series[-1] - mean) / stdev
