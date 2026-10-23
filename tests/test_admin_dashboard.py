import os
import unittest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


APP_URL = os.getenv("FIREMEX_BASE_URL", "http://localhost:5173/FiremeX").rstrip("/")
DASHBOARD_URL = f"{APP_URL}/admin/dashboard"
ADMIN_EMAIL = os.getenv("FIREMEX_ADMIN_EMAIL", "admin@firemex.com")
ADMIN_PASSWORD = os.getenv("FIREMEX_ADMIN_PASSWORD", "password123")


class FiremexAdminDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        if os.getenv("FIREMEX_HEADLESS", "").lower() in {"1", "true", "yes"}:
            options.add_argument("--headless=new")
        cls.driver = webdriver.Chrome(options=options)
        cls.wait = WebDriverWait(cls.driver, 15)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "driver", None):
            cls.driver.quit()

    def setUp(self):
        self.driver.get(DASHBOARD_URL)
        try:
            self._dashboard_heading()
        except TimeoutException:
            self.driver.get(f"{APP_URL}/login")
            email = self.wait.until(
                EC.visibility_of_element_located((By.ID, "email"))
            )
            password = self.driver.find_element(By.ID, "password")
            email.clear()
            email.send_keys(ADMIN_EMAIL)
            password.clear()
            password.send_keys(ADMIN_PASSWORD)
            self.driver.find_element(
                By.XPATH, "//button[normalize-space()='Sign in']"
            ).click()
            self._dashboard_heading()

    def _dashboard_heading(self):
        return self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h1[normalize-space()='Safety at a glance']")
            )
        )

    def _sidebar_item(self, label):
        return self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f"//aside//nav//button[.//span[normalize-space()='{label}']]",
                )
            )
        )

    def _section(self, title):
        heading = self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    f"//h2[normalize-space()='{title}']",
                )
            )
        )
        return heading.find_element(By.XPATH, "ancestor::section[1]")

    # Updated these cases to match the current dashboard UI and API-driven data;
    # removed stale assumptions about fixed counts, a table, camera previews, and a live clock.
    # Verifies that the main dashboard heading ("Safety at a glance") and the
    # "Live overview" label are both rendered and visible, and that the browser
    # URL confirms we are on the /admin/dashboard route.
    def test_dashboard_header_and_live_status_are_visible(self):
        self._dashboard_heading()
        self.assertTrue(
            self.driver.find_element(
                By.XPATH, "//*[normalize-space()='Live overview']"
            ).is_displayed()
        )
        self.assertIn("/admin/dashboard", self.driver.current_url)

    # Checks each summary/metric card on the dashboard (Cameras, Total incidents,
    # Open responses, Active operators + admins). For every card it waits until
    # the API-backed counter is populated (i.e. no longer "—"), asserts the value
    # is a digit, clicks the card, and confirms the browser navigates to the
    # expected admin route before returning to the dashboard for the next iteration.
    def test_summary_cards_show_current_values_and_navigate(self):
        metrics = (
            ("Cameras", "/admin/livefeed"),
            ("Total incidents", "/admin/incidents"),
            ("Open responses", "/admin/incidents"),
            ("Active operators + admins", "/admin/users"),
        )
        for label, route in metrics:
            with self.subTest(metric=label):
                card = self.wait.until(
                    EC.visibility_of_element_located(
                        (
                            By.XPATH,
                            f"//button[.//span[normalize-space()='{label}']]",
                        )
                    )
                )
                self.wait.until(
                    lambda _driver: card.find_element(
                        By.XPATH, ".//strong"
                    ).text.strip()
                    != "—"
                )
                value = card.find_element(By.XPATH, ".//strong").text.strip()
                self.assertTrue(value.isdigit(), f"{label} should show a numeric value.")
                card.click()
                self.wait.until(EC.url_contains(route))
                self.driver.get(DASHBOARD_URL)
                self._dashboard_heading()

    # Iterates over all sidebar navigation items (Dashboard, Live Feed, Incidents,
    # Notifications, Users, Settings) and clicks each one in turn, asserting that
    # the browser URL updates to the corresponding /admin/* route after every click.
    def test_sidebar_options_navigate_to_their_pages(self):
        navigation = {
            "Dashboard": "/admin/dashboard",
            "Live Feed": "/admin/livefeed",
            "Incidents": "/admin/incidents",
            "Notifications": "/admin/alerts",
            "Users": "/admin/users",
            "Settings": "/admin/settings",
        }
        for label, route in navigation.items():
            with self.subTest(sidebar_item=label):
                if "/admin/dashboard" not in self.driver.current_url:
                    self.driver.get(DASHBOARD_URL)
                    self._dashboard_heading()
                self._sidebar_item(label).click()
                self.wait.until(EC.url_contains(route))

    # Asserts that the "Dashboard" sidebar button carries the active-state CSS
    # classes (border-l-4 and text-accent) while the dashboard page is open,
    # confirming that the UI correctly highlights the current section.
    def test_dashboard_sidebar_item_is_highlighted(self):
        dashboard_item = self._sidebar_item("Dashboard")
        classes = dashboard_item.get_attribute("class") or ""
        self.assertIn("border-l-4", classes)
        self.assertIn("text-accent", classes)

    # Validates the "Recent incidents" section. The "View all" button must always
    # be visible. If the API returned incident rows, each <li> must contain a
    # "Fire detected" or "Smoke detected" label and a confidence percentage
    # (e.g. "91.5%"). If no rows exist the section must display the
    # "No detections yet." placeholder instead.
    def test_recent_incidents_show_api_data_or_empty_state(self):
        section = self._section("Recent incidents")
        self.assertTrue(
            section.find_element(
                By.XPATH, ".//button[normalize-space()='View all ↗']"
            ).is_displayed()
        )
        rows = section.find_elements(By.XPATH, ".//ul/li")
        if rows:
            for row in rows:
                text = row.text
                self.assertTrue(
                    "Fire detected" in text or "Smoke detected" in text,
                    "Each recent incident should identify a fire or smoke detection.",
                )
                self.assertRegex(text, r"\d+(?:\.\d+)?%")
        else:
            self.assertIn("No detections yet.", section.text)

    # Clicks the "View all ↗" button inside the "Recent incidents" section and
    # asserts that the browser navigates to the /admin/incidents page.
    def test_recent_incidents_view_all_opens_incidents(self):
        section = self._section("Recent incidents")
        section.find_element(
            By.XPATH, ".//button[normalize-space()='View all ↗']"
        ).click()
        self.wait.until(EC.url_contains("/admin/incidents"))

    # Locates the visual-evidence section (heading contains the word "evidence").
    # If saved evidence images are present, verifies that the first image's alt
    # text begins with "Saved ". If no images are found, verifies that the section
    # shows one of the expected placeholder messages ("No saved evidence is
    # available yet.", "Loading saved evidence…", or
    # "This evidence image is unavailable.").
    def test_visual_evidence_panel_supports_available_and_empty_states(self):
        heading = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h2[contains(normalize-space(), 'evidence')]")
            )
        )
        section = heading.find_element(By.XPATH, "ancestor::section[1]")
        text = section.text
        images = section.find_elements(By.XPATH, ".//img")
        if images:
            self.assertTrue(images[0].get_attribute("alt").startswith("Saved "))
        else:
            self.assertTrue(
                "No saved evidence is available yet." in text
                or "Loading saved evidence…" in text
                or "This evidence image is unavailable." in text
            )

    # Validates the "Recent notifications" section. The "View all" button must
    # always be visible. If notification buttons exist inside the grid, at least
    # one must carry the text "Needs acknowledgement" or "Acknowledged". If no
    # buttons are found the section must display "No notifications yet.".
    def test_recent_notifications_show_items_or_empty_state(self):
        section = self._section("Recent notifications")
        self.assertTrue(
            section.find_element(
                By.XPATH, ".//button[normalize-space()='View all ↗']"
            ).is_displayed()
        )
        items = section.find_elements(By.XPATH, ".//div[contains(@class,'grid')]//button")
        if not items:
            self.assertIn("No notifications yet.", section.text)
        else:
            self.assertTrue(
                any(
                    "Needs acknowledgement" in item.text
                    or "Acknowledged" in item.text
                    for item in items
                )
            )

    # Clicks the "Notifications" button in the top header bar and verifies that
    # the browser navigates to the /admin/alerts route.
    def test_notifications_view_all_opens_alerts(self):
        button = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//header//button[contains(., 'Notifications')]")
            )
        )
        button.click()
        self.wait.until(EC.url_contains("/admin/alerts"))

    # Clicks the "Sign out" button and asserts that the browser is redirected to
    # the /login page and that the email input field becomes visible, confirming
    # the session has been cleared and the login form is ready.
    def test_sign_out_returns_to_login(self):
        self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Sign out']")
            )
        ).click()
        self.wait.until(EC.url_contains("/login"))
        self.wait.until(
            EC.visibility_of_element_located((By.ID, "email"))
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
