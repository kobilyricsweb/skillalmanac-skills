from geo.loader import load_point


def test_order():
    assert load_point(34.78, 32.08) == (34.78, 32.08)
