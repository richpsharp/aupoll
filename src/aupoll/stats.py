"""Statistical helpers for poll result summaries."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, sqrt


@dataclass(frozen=True)
class Summary:
    """Descriptive statistics for a set of poll answers.

    Attributes:
        count: Number of submitted values.
        mean: Arithmetic mean, or ``None`` when there are no values.
        median: Median value, or ``None`` when there are no values.
        stdev: Sample standard deviation, or ``None`` when there are no values.
        p05: Fifth percentile, or ``None`` when there are no values.
        p95: Ninety-fifth percentile, or ``None`` when there are no values.
    """

    count: int
    mean: float | None
    median: float | None
    stdev: float | None
    p05: float | None
    p95: float | None


def summarize(values: list[float]) -> Summary:
    """Compute summary statistics for poll answers.

    Args:
        values: Numeric answer values for one question.

    Returns:
        Summary statistics. Empty input returns a zero-count summary with
        optional statistics set to ``None``.
    """
    if not values:
        return Summary(count=0, mean=None, median=None, stdev=None, p05=None, p95=None)

    ordered = sorted(values)
    count = len(ordered)
    mean = sum(ordered) / count
    variance = sum((value - mean) ** 2 for value in ordered) / (count - 1) if count > 1 else 0.0

    return Summary(
        count=count,
        mean=mean,
        median=percentile(ordered, 50),
        stdev=sqrt(variance),
        p05=percentile(ordered, 5),
        p95=percentile(ordered, 95),
    )


def percentile(sorted_values: list[float], percentile_value: float) -> float:
    """Interpolate a percentile from pre-sorted values.

    Args:
        sorted_values: Values sorted in ascending order.
        percentile_value: Percentile in the inclusive range from 0 to 100.

    Returns:
        Interpolated percentile value, clamped to the data edges for values
        outside the inclusive percentile range.
    """
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
    """Count answer values into configured scale buckets.

    Args:
        values: Numeric answer values to count.
        minimum: Lowest scale value and first bucket.
        maximum: Highest scale value and last bucket.
        step: Distance between adjacent buckets.

    Returns:
        Bucket dictionaries containing the scale value and answer count.
    """
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

