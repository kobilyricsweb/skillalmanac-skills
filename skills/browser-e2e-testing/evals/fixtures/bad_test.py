import time

import pytest
from playwright.sync_api import expect
from selenium.webdriver.common.by import By

CREATED = []


@pytest.fixture(scope="session")
def shared_page(browser):
    page = browser.new_page()
    page.goto("/login")
    return page


def test_signup_and_record(page):
    page.goto("/signup")
    time.sleep(2)
    page.click("button.sc-bdfBwQ")
    CREATED.append("ada@example.com")
    expect(page.get_by_text("Welcome")).to_be_visible()


def test_uses_recorded_user(page):
    page.goto("/users")
    page.fill("#email", CREATED[0])
    page.wait_for_load_state("networkidle")
    page.click("text=Save", force=True)
    breakpoint()
    expect(page.get_by_text("Saved")).to_be_visible()


def test_navigates_only(driver):
    driver.get("/home")
    driver.find_element(By.CSS_SELECTOR, "div > div > div > span").click()
