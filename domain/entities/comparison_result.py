from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ComparisonResult:
    metric_name: str
    timestamp: datetime

    simulated_value: float
    measured_value: float
    absolute_error: float
    relative_error_pct: float
