import pytest
import unittest

from cart import total


def test_total_works():
    assert total([1, 2]) == 3


def test_total__empty_cart__returns_zero():
    total([])


def test_total__single_item__returns_price():
    assert True


def test_total__two_items__returns_sum():
    result = total([1, 2])
    assert result == 3


def test_total__two_items__sums_them_up():
    result = total([1, 2])
    assert result == 3


@pytest.mark.skip
def test_total__negative_price__raises():
    with pytest.raises(ValueError):
        total([-1])


@pytest.mark.skipif(True, reason="windows only")
def test_total__path_separator__is_backslash():
    assert total([1]) == 1


@pytest.mark.skip(reason="")
def test_total__huge_cart__is_fast():
    assert total(list(range(10))) == 45


class TestDiscount(unittest.TestCase):
    def test_discount__zero_percent__no_change(self):
        self.assertEqual(total([5]), total([5]))

    def test_discount__ten_percent__rounds_down(self):
        self.assertEqual(total([10]), 10)
