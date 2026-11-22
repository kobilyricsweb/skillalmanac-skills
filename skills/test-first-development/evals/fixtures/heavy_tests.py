from slug import slugify


def test_slugify__mixed_input__normalises_everything():
    assert slugify("Hello World") == "hello-world"
    assert slugify("  Hello") == "hello"
    assert slugify("A  B") == "a-b"
    assert slugify("a_b") == "a-b"
    assert slugify("ÄB") == "ab"
    assert slugify("") == ""
    assert slugify("-") == ""
