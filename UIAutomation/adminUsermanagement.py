import os
import re
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = os.getenv("FIREMEX_BASE_URL", "http://localhost:5173/FiremeX").rstrip("/")
USER_MANAGEMENT_URL = f"{BASE_URL}/admin/users"
LOGIN_URL = f"{BASE_URL}/login"
ADMIN_EMAIL = os.getenv("FIREMEX_ADMIN_EMAIL", "admin@firemex.com")
ADMIN_PASSWORD = os.getenv("FIREMEX_ADMIN_PASSWORD", "password123")


class FiremexUserManagementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        if os.getenv("FIREMEX_HEADLESS", "").lower() in {"1", "true", "yes"}:
            chrome_options.add_argument("--headless=new")

        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "driver", None):
            cls.driver.quit()

    def setUp(self):
        self.driver.get(USER_MANAGEMENT_URL)
        self._login_if_needed()
        self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h1[normalize-space()='User Management']")
            )
        )
        self._wait_for_users_to_load()

    def _login_if_needed(self):
        self.wait.until(
            lambda driver: "/admin/users" in driver.current_url
            or "/login" in driver.current_url
        )

        if "/login" in self.driver.current_url:
            email = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, "//input[@type='email']"))
            )
            password = self.driver.find_element(
                By.XPATH, "//input[@type='password']"
            )
            email.clear()
            email.send_keys(ADMIN_EMAIL)
            password.clear()
            password.send_keys(ADMIN_PASSWORD)

            self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[normalize-space()='Sign in']")
                )
            ).click()

            self.wait.until(
                lambda driver: "/admin/dashboard" in driver.current_url
                or "/admin/users" in driver.current_url
            )

        if "/admin/users" not in self.driver.current_url:
            self.driver.get(USER_MANAGEMENT_URL)

            self.wait.until(EC.url_contains("/admin/users"))

    def _wait_for_users_to_load(self):
        self.wait.until(
            EC.invisibility_of_element_located(
                (By.XPATH, "//*[normalize-space()='Loading users from server...']")
            )
        )

    def _tab(self, label):
        return self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f"//button[contains(normalize-space(.), '{label}')]",
                )
            )
        )

    def _active_operator_cards(self):
        revoke_buttons = self.driver.find_elements(
            By.XPATH, "//button[normalize-space()='Revoke Access']"
        )
        return [
            button.find_element(
                By.XPATH, "ancestor::div[contains(@class, 'rounded-3xl')][1]"
            )
            for button in revoke_buttons
        ]

    def _pending_request_cards(self):
        approve_buttons = self.driver.find_elements(
            By.XPATH, "//button[normalize-space()='Approve Access']"
        )
        return [
            button.find_element(
                By.XPATH, "ancestor::div[contains(@class, 'rounded-3xl')][1]"
            )
            for button in approve_buttons
        ]

    def _assert_tab_selected(self, tab):
        self.wait.until(
            lambda _driver: "border-b-2" in (tab.get_attribute("class") or "")
            and "border-accent" in (tab.get_attribute("class") or "")
        )

    @staticmethod
    def _tab_count(tab):
        match = re.search(r"\((\d+)\)\s*$", tab.text)
        if not match:
            raise AssertionError(f"Tab count is missing from: {tab.text!r}")
        return int(match.group(1))

    # TC_UM_001: Verify the Pending Requests tab is clickable and selected.
    def test_TC_UM_001_Pending_Requests_tab_is_clickable(self):
        pending_tab = self._tab("Pending Requests")
        pending_tab.click()
        self._assert_tab_selected(pending_tab)

    # TC_UM_002: Verify pending operator cards show names, emails, roles, and status.
    def test_TC_UM_002_operator_details_are_visible_in_active_tab(self):
        self._tab("Active Operators").click()
        cards = self._active_operator_cards()

        if not cards:
            self.assertIn(
                "No Active Operators",
                self.driver.find_element(By.TAG_NAME, "body").text,
            )
            return

        for card in cards:
            with self.subTest(operator=card.text.splitlines()[0]):
                self.assertTrue(card.find_elements(By.XPATH, ".//*[normalize-space()]"))
                self.assertIn("System Role", card.text)
                self.assertIn("Status", card.text)
                self.assertIn("Joined Date", card.text)
                self.assertIn("Revoke Access", card.text)

    # TC_UM_003: Verify Revoke Access opens a confirmation and cancel preserves the operator.
    def test_TC_UM_003_revoke_access_button_is_clickable(self):
        self._tab("Active Operators").click()
        cards = self._active_operator_cards()
        if not cards:
            self.skipTest("An active operator is required to test the revoke control.")

        card = cards[0]
        revoke = card.find_element(
            By.XPATH, ".//button[normalize-space()='Revoke Access']"
        )
        self.wait.until(lambda _driver: revoke.is_enabled())
        revoke.click()

        self.wait.until(EC.alert_is_present()).dismiss()
        self.assertTrue(card.is_displayed(), "Cancelling revoke should preserve the operator.")

    # TC_UM_004: Verify the active-operator count matches the displayed operator cards.
    def test_TC_UM_004_all_active_operators_are_visible_in_tab(self):
        active_tab = self._tab("Active Operators")
        active_tab.click()
        self._assert_tab_selected(active_tab)

        self.assertEqual(
            self._tab_count(active_tab),
            len(self._active_operator_cards()),
            "The tab count should match the number of visible active operator cards.",
        )

    # TC_UM_005: Verify the Pending Requests tab is clickable and selected.
    def test_TC_UM_005_pending_operator_tab_is_clickable(self):
        pending_tab = self._tab("Pending Requests")
        pending_tab.click()
        self._assert_tab_selected(pending_tab)

    # TC_UM_006: Verify Approve Access is enabled for a pending request.
    def test_TC_UM_006_approve_access_button_is_clickable(self):
        self._tab("Pending Requests").click()
        cards = self._pending_request_cards()
        if not cards:
            self.skipTest("A pending request is required to test the approve control.")

        approve = cards[0].find_element(
            By.XPATH, ".//button[normalize-space()='Approve Access']"
        )
        self.wait.until(EC.element_to_be_clickable(approve))
        self.assertTrue(approve.is_enabled())

    # TC_UM_007: Verify Deny Request is enabled for a pending request.
    def test_TC_UM_007_deny_request_button_is_clickable(self):
        self._tab("Pending Requests").click()
        cards = self._pending_request_cards()
        if not cards:
            self.skipTest("A pending request is required to test the deny control.")

        deny = cards[0].find_element(
            By.XPATH, ".//button[normalize-space()='Deny Request']"
        )
        self.wait.until(EC.element_to_be_clickable(deny))
        self.assertTrue(deny.is_enabled())

    # TC_UM_008: Verify pending request cards show the requested user details.
    def test_TC_UM_008_requested_operator_details_are_visible_in_pending_tab(self):
        self._tab("Pending Requests").click()
        cards = self._pending_request_cards()

        if not cards:
            self.assertIn(
                "No Pending Requests",
                self.driver.find_element(By.TAG_NAME, "body").text,
            )
            return

        for card in cards:
            with self.subTest(request=card.text.splitlines()[0]):
                self.assertIn("Requested Role", card.text)
                self.assertIn("Requested Date", card.text)
                self.assertIn("Approve Access", card.text)
                self.assertIn("Deny Request", card.text)

    # TC_UM_009: Verify the pending-request count matches the displayed request cards.
    def test_TC_UM_009_all_pending_requests_are_visible_in_tab(self):
        pending_tab = self._tab("Pending Requests")
        pending_tab.click()
        self._assert_tab_selected(pending_tab)

        self.assertEqual(
            self._tab_count(pending_tab),
            len(self._pending_request_cards()),
            "The tab count should match the number of visible pending request cards.",
        )

    # TC_UM_010: Verify the selected tab receives the page's active styling.
    def test_TC_UM_010_selected_tab_is_highlighted(self):
        for tab_name in ("Active Operators", "Pending Requests"):
            with self.subTest(tab=tab_name):
                tab = self._tab(tab_name)
                tab.click()
                self._assert_tab_selected(tab)


if __name__ == "__main__":
    unittest.main(verbosity=2)