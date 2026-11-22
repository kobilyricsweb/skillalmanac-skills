import pytest

from cart import total


def test_total__empty_cart__returns_zero():
    assert total([]) == 0


def test_total__two_items__returns_sum():
    assert total([1, 2]) == 3


def test_total__negative_price__raises_value_error():
    with pytest.raises(ValueError):
        total([-1])


@pytest.mark.skip(reason="blocked until currency rounding spec is agreed")
def test_total__half_cent__rounds_to_even():
    assert total([0.005]) == 0.0


@pytest.mark.parametrize("prices", [[1], [2]])
def test_total__single_item__is_positive(prices):
    assert total(prices) > 0
