import uuid

import pytest
from playwright.sync_api import expect

# time.sleep is mentioned in this comment only.
CONFIG = {"base": "/shop"}


@pytest.fixture
def account(request):
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    request.getfixturevalue("api").create_user(email)
    yield email
    request.getfixturevalue("api").delete_user(email)


def test_login_shows_dashboard(page, account):
    page.goto(CONFIG["base"] + "/login")
    page.get_by_label("Email").fill(account)
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()


@pytest.mark.skip(reason="blocked by ticket 123")
def test_placeholder(page):
    page.goto("/later")


def test_cart_total(page):
    page.goto("/cart")
    assert page.get_by_test_id("total").inner_text() == "$0.00"
