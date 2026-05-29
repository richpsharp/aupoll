from aupoll.app import count_axis
from pytest import approx


def test_count_axis_uses_each_count_for_small_samples():
    axis_maximum, ticks = count_axis(3)

    assert axis_maximum == 3
    assert [tick["value"] for tick in ticks] == [0, 1, 2, 3]
    assert [tick["percent"] for tick in ticks] == approx([0, 100 / 3, 200 / 3, 100])


def test_count_axis_rounds_larger_samples_to_nice_top_tick():
    axis_maximum, ticks = count_axis(17)

    assert axis_maximum == 20
    assert [tick["value"] for tick in ticks] == [0, 5, 10, 15, 20]
