from aupoll.stats import histogram, percentile, summarize


def test_summarize_values():
    summary = summarize([1, 2, 3, 4, 5])

    assert summary.count == 5
    assert summary.mean == 3
    assert summary.median == 3
    assert round(summary.standard_deviation, 3) == 1.581
    assert round(summary.fifth_percentile, 1) == 1.2
    assert summary.ninety_fifth_percentile == 4.8


def test_histogram_counts_scale_buckets():
    buckets = histogram([1, 1, 3, 5], minimum=1, maximum=5, step=1)

    assert buckets == [
        {"value": 1, "count": 2},
        {"value": 2, "count": 0},
        {"value": 3, "count": 1},
        {"value": 4, "count": 0},
        {"value": 5, "count": 1},
    ]


def test_percentile_clamps_to_edges():
    assert percentile([10, 20], 0) == 10
    assert percentile([10, 20], 100) == 20
