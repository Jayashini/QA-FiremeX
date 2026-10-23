import os
import re
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait


APP_BASE_URL = os.getenv(
    "FIREMEX_BASE_URL",
    "http://localhost:5173/FiremeX",
).rstrip("/")
ALERTS_URL = f"{APP_BASE_URL}/admin/alerts"
LOGIN_URL = f"{APP_BASE_URL}/login"

ADMIN_EMAIL = os.getenv("FIREMEX_ADMIN_EMAIL", "admin@firemex.com")
ADMIN_PASSWORD = os.getenv("FIREMEX_ADMIN_PASSWORD", "password123")


class FiremexAdminAlertsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = Options()
        options.add_argument("--start-maximized")
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
        self.driver.get(ALERTS_URL)
        self._login_if_needed()
        self.driver.get(ALERTS_URL)

        self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h1[normalize-space()='Notifications']")
            )
        )
        self._wait_for_initial_refresh()

    def _login_if_needed(self):
        self.wait.until(
            lambda driver: (
                "/login" in driver.current_url
                or driver.find_elements(
                    By.XPATH, "//h1[normalize-space()='Notifications']"
                )
            )
        )

        if "/login" not in self.driver.current_url:
            return

        email = self.wait.until(
            EC.visibility_of_element_located((By.ID, "email"))
        )
        password = self.driver.find_element(By.ID, "password")

        email.clear()
        email.send_keys(ADMIN_EMAIL)
        password.clear()
        password.send_keys(ADMIN_PASSWORD)

        self.driver.find_element(
            By.XPATH,
            "//button[@type='submit' and normalize-space()='Sign in']",
        ).click()

        self.wait.until(EC.url_contains("/admin"))

    def _wait_for_initial_refresh(self):
        self.wait.until(
            lambda driver: (
                "Updated" in driver.find_element(By.TAG_NAME, "body").text
                or driver.find_elements(By.XPATH, "//*[@role='alert']")
            )
        )

    def _alert_rows(self):
        return self.driver.find_elements(
            By.XPATH, "//section[@aria-label='Notification table']//tbody/tr"
        )

    def _notification_filter(self):
        return self.driver.find_element(
            By.XPATH, "//label[starts-with(normalize-space(.), 'Show notifications')]/select"
        )

    def _wait_for_filter_refresh(self):
        self.wait.until(
            lambda driver: "Refreshing" not in driver.find_element(
                By.TAG_NAME, "body"
            ).text
        )

    # TC_ALERT_001: Verify the Notifications page heading and response guidance appear.
    def test_TC_ALERT_001_notifications_header_is_displayed(self):
        header = self.driver.find_element(
            By.XPATH, "//header[.//h1[normalize-space()='Notifications']]"
        )
        header_text = header.text.upper()

        self.assertIn("RESPONSE QUEUE", header_text)
        self.assertIn("ACKNOWLEDGE A DETECTION", header_text)

    # TC_ALERT_002: Verify total and unacknowledged counters show numeric values.
    def test_TC_ALERT_002_notification_counters_are_displayed(self):
        total = self.driver.find_element(
            By.XPATH,
            "//header//span[normalize-space()='Total']/following-sibling::strong",
        ).text
        unacknowledged = self.driver.find_element(
            By.XPATH,
            "//header//span[normalize-space()='Unacknowledged']/following-sibling::strong",
        ).text

        self.assertRegex(total, r"^\d+$")
        self.assertRegex(unacknowledged, r"^\d+$")
        self.assertLessEqual(int(unacknowledged), int(total))

    # TC_ALERT_003: Verify the table displays the expected notification columns.
    def test_TC_ALERT_003_notification_table_headers_are_displayed(self):
        table = self.driver.find_element(
            By.XPATH, "//section[@aria-label='Notification table']//table"
        )
        table_text = " ".join(table.find_elements(By.XPATH, ".//thead//th")[i].text
                              for i in range(len(table.find_elements(By.XPATH, ".//thead//th"))))

        for heading in (
            "Notification / detected",
            "Detection",
            "Camera / zone",
            "Confidence",
            "Acknowledgement",
            "Action",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading.lower(), table_text.lower())

    # TC_ALERT_004: Verify each notification row shows detection, camera, zone, and confidence.
    def test_TC_ALERT_004_notification_row_details_are_displayed(self):
        rows = self._alert_rows()
        if not rows:
            self.skipTest("There are no notifications in the current test account.")

        row_text = rows[0].text
        self.assertRegex(row_text, r"\b(Fire|Smoke)\b")
        self.assertRegex(row_text, r"\d+\.\d%")
        self.assertTrue(
            "Not acknowledged" in row_text or "Acknowledged by" in row_text,
            "Expected the row to show its acknowledgement state.",
        )

    # TC_ALERT_005: Verify notifications without a zone display the fallback label.
    def test_TC_ALERT_005_missing_zone_uses_fallback_label(self):
        rows_without_zone = self.driver.find_elements(
            By.XPATH,
            "//section[@aria-label='Notification table']//tbody/tr"
            "[.//*[normalize-space()='Zone not set']]",
        )
        rows = self._alert_rows()

        if not rows:
            self.skipTest("There are no notifications in the current test account.")
        if not rows_without_zone:
            self.skipTest("No current notification has a missing zone.")

        self.assertTrue(
            rows_without_zone[0].find_element(
                By.XPATH, ".//*[normalize-space()='Zone not set']"
            ).is_displayed()
        )

    # TC_ALERT_006: Verify the acknowledgement filter offers all supported states.
    def test_TC_ALERT_006_acknowledgement_filter_options_are_available(self):
        options = [
            option.text
            for option in self._notification_filter().find_elements(By.TAG_NAME, "option")
        ]
        self.assertEqual(
            options,
            ["All notifications", "Needs acknowledgement", "Acknowledged"],
        )

    # TC_ALERT_007: Verify selecting a notification filter returns to page one.
    def test_TC_ALERT_007_filter_selection_is_applied_from_first_page(self):
        filter_select = Select(self._notification_filter())

        for value in ("false", "true", ""):
            with self.subTest(filter_value=value):
                filter_select.select_by_value(value)
                self._wait_for_filter_refresh()

                self.assertEqual(
                    self._notification_filter().get_attribute("value"),
                    value,
                )
                self.assertRegex(
                    self.driver.find_element(
                        By.XPATH,
                        "//div[contains(@class,'border-t')]//p[contains(., 'Page')]",
                    ).text,
                    r"Page 1 of \d+",
                )

    # TC_ALERT_008: Verify acknowledgement status is represented in each notification row.
    def test_TC_ALERT_008_acknowledgement_state_is_visible(self):
        rows = self._alert_rows()
        if not rows:
            self.skipTest("There are no notifications in the current test account.")

        for index, row in enumerate(rows):
            with self.subTest(row=index):
                text = row.text
                self.assertTrue(
                    "Not acknowledged" in text or "Acknowledged by" in text,
                    f"Notification row {index + 1} has no visible acknowledgement status.",
                )

    # TC_ALERT_009: Verify acknowledged notifications do not show an Acknowledge button.
    def test_TC_ALERT_009_acknowledged_rows_hide_acknowledge_action(self):
        filter_select = Select(self._notification_filter())
        filter_select.select_by_value("true")
        self._wait_for_filter_refresh()

        rows = self._alert_rows()
        if not rows:
            self.skipTest("There are no acknowledged notifications in the current account.")

        for index, row in enumerate(rows):
            with self.subTest(row=index):
                self.assertFalse(
                    row.find_elements(
                        By.XPATH,
                        ".//button[normalize-space()='Acknowledge']",
                    ),
                    "An acknowledged notification should not offer Acknowledge.",
                )
                self.assertTrue(
                    row.find_elements(
                        By.XPATH,
                        ".//button[contains(normalize-space(.), 'View incident')]",
                    ),
                    "Expected an acknowledged notification to offer View incident.",
                )

    # TC_ALERT_010: Verify View incident opens the corresponding incident page.
    def test_TC_ALERT_010_view_incident_opens_incident(self):
        rows = self._alert_rows()
        if not rows:
            self.skipTest("There are no notifications in the current test account.")

        row = rows[0]
        incident_reference = row.find_element(
            By.XPATH, ".//td[1]//span"
        ).text
        row.find_element(
            By.XPATH,
            ".//button[contains(normalize-space(.), 'View incident')]",
        ).click()

        self.wait.until(EC.url_contains("/admin/incidents"))
        self.assertIn("/admin/incidents", self.driver.current_url)
        self.assertIn("incident=", self.driver.current_url)
        self.assertTrue(incident_reference.strip())

    # TC_ALERT_011: Verify pagination controls reflect the current result count.
    def test_TC_ALERT_011_pagination_controls_match_result_count(self):
        page_text = self.driver.find_element(
            By.XPATH, "//p[contains(., 'Page')]"
        ).text
        match = re.search(r"Page (\d+) of (\d+)", page_text)
        self.assertIsNotNone(match, "Expected the current page and page count.")
        self.assertEqual(match.group(1), "1")

        previous = self.driver.find_element(
            By.XPATH, "//button[normalize-space()='Previous']"
        )
        next_button = self.driver.find_element(
            By.XPATH, "//button[normalize-space()='Next']"
        )
        self.assertTrue(previous.get_property("disabled"))

        total_pages = int(match.group(2))
        if total_pages == 1:
            self.assertTrue(next_button.get_property("disabled"))
        else:
            next_button.click()
            self.wait.until(
                EC.text_to_be_present_in_element(
                    (By.XPATH, "//p[contains(., 'Page')]"),
                    "Page 2 of",
                )
            )
            self.assertFalse(
                self.driver.find_element(
                    By.XPATH, "//button[normalize-space()='Previous']"
                ).get_property("disabled")
            )

    # TC_ALERT_012: Verify the empty-state message appears when no notifications match.
    def test_TC_ALERT_012_empty_filter_results_show_empty_state(self):
        filter_select = Select(self._notification_filter())
        filter_select.select_by_value("true")
        self._wait_for_filter_refresh()

        rows = self._alert_rows()
        if rows:
            self.skipTest(
                "The selected filter has notifications, so the empty state is not applicable."
            )

        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("No notifications match this view", body_text)
        self.assertIn("New detections will appear here as they arrive.", body_text)

    # TC_ALERT_013: Verify acknowledging an alert opens its incident response page.
    def test_TC_ALERT_013_acknowledge_opens_incident(self):
        if os.getenv("FIREMEX_RUN_MUTATING_TESTS", "").lower() not in {
            "1", "true", "yes"
        }:
            self.skipTest(
                "This test changes server-side acknowledgement data. "
                "Set FIREMEX_RUN_MUTATING_TESTS=1 to enable it."
            )

        filter_select = Select(self._notification_filter())
        filter_select.select_by_value("false")
        self._wait_for_filter_refresh()

        rows = self._alert_rows()
        if not rows:
            self.skipTest("There are no unacknowledged notifications to acknowledge.")

        row = rows[0]
        row.find_element(
            By.XPATH, ".//button[normalize-space()='Acknowledge']"
        ).click()

        self.wait.until(EC.url_contains("/admin/incidents"))
        self.assertIn("/admin/incidents", self.driver.current_url)
        self.assertIn("incident=", self.driver.current_url)


if __name__ == "__main__":
    unittest.main(verbosity=2)