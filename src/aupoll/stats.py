from __future__ import annotations

from dataclasses import dataclass
from math import floor, sqrt


@dataclass(frozen=True)
class Summary:
    count: int
    mean: float | None
    median: float | None
    standard_deviation: float | None
    fifth_percentile: float | None
    ninety_fifth_percentile: float | None


def summarize(values: list[float]) -> Summary:
    if not values:
        return Summary(
            count=0,
            mean=None,
            median=None,
            standard_deviation=None,
            fifth_percentile=None,
            ninety_fifth_percentile=None,
        )

    ordered = sorted(values)
    count = len(ordered)
    mean = sum(ordered) / count
    variance = sum((value - mean) ** 2 for value in ordered) / (count - 1) if count > 1 else 0.0

    return Summary(
        count=count,
        mean=mean,
        median=percentile(ordered, 50),
        standard_deviation=sqrt(variance),
        fifth_percentile=percentile(ordered, 5),
        ninety_fifth_percentile=percentile(ordered, 95),
    )


def percentile(sorted_values: list[float], percentile_value: float) -> float:
    if not sorted_values:
        raise ValueError("percentile requires at least one value")
    if percentile_value <= 0:
        return sorted_values[0]
    if percentile_value >= 100:
        return sorted_values[-1]

    rank = (len(sorted_values) - 1) * (percentile_value / 100)
    lower = floor(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = rank - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def histogram(values: list[float], minimum: float, maximum: float, step: float) -> list[dict[str, float | int]]:
    buckets = []
    current = minimum
    while current <= maximum + (step / 1000):
        rounded = round(current, 10)
        buckets.append({"value": rounded, "count": 0})
        current += step

    if not buckets:
        return []

    for value in values:
        index = round((value - minimum) / step)
        if 0 <= index < len(buckets):
            buckets[index]["count"] = int(buckets[index]["count"]) + 1
    return buckets

