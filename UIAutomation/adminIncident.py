import os
import unittest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


BASE_URL = os.getenv("FIREMEX_BASE_URL", "http://localhost:5173/FiremeX").rstrip("/")
INCIDENTS_URL = f"{BASE_URL}/admin/incidents"
LOGIN_URL = f"{BASE_URL}/login"
ADMIN_EMAIL = os.getenv("FIREMEX_ADMIN_EMAIL", "admin@firemex.com")
ADMIN_PASSWORD = os.getenv("FIREMEX_ADMIN_PASSWORD", "password123")


class FiremexIncidentTests(unittest.TestCase):
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
        self.driver.get(INCIDENTS_URL)

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

            self.driver.find_element(
                By.XPATH, "//button[normalize-space()='Sign in']"
            ).click()

            self.wait.until(
                lambda driver: "/admin/" in driver.current_url
                or "/operator/" in driver.current_url
            )

        # Login sends users to their home page; navigate to Incidents explicitly.
        self.driver.get(INCIDENTS_URL)
        self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h1[normalize-space()='Incidents']")
            )
        )
        self._wait_for_incidents_to_load()

    def _wait_for_incidents_to_load(self):
        self.wait.until(
            lambda driver: driver.find_elements(
                By.XPATH, "//section[@aria-label='Incident table']//tbody/tr"
            )
            or driver.find_elements(
                By.XPATH,
                "//*[normalize-space()='No incidents match this view']",
            )
            or driver.find_elements(By.XPATH, "//*[@role='alert']")
        )

    def _rows(self):
        return self.driver.find_elements(
            By.XPATH, "//section[@aria-label='Incident table']//tbody/tr"
        )

    def _hazard_filter(self):
        return self.driver.find_element(
            By.XPATH, "//select[@aria-label='Hazard class']"
        )

    def _response_filter(self):
        return self.driver.find_element(
            By.XPATH, "//select[@aria-label='Response status']"
        )

    def _open_first_incident(self):
        rows = self._rows()
        if not rows:
            self.skipTest("At least one incident is required for this test.")

        reference = rows[0].find_element(By.XPATH, "./td[1]").text.strip()
        rows[0].find_element(
            By.XPATH, ".//button[normalize-space()='View evidence ↗']"
        ).click()

        dialog = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, "//section[@role='dialog']"))
        )
        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.XPATH, "//section[@role='dialog']"), reference
            )
        )
        return dialog

    # TC_INC_001: Verify the Incidents sidebar link opens the incidents page.
    def test_TC_INC_001_incidents_sidebar_link_opens_page(self):
        incidents_link = self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//aside//button[.//span[normalize-space()='Incidents']]",
                )
            )
        )
        incidents_link.click()
        self.wait.until(EC.url_contains("/admin/incidents"))
        self.assertTrue(
            self.driver.find_element(
                By.XPATH, "//h1[normalize-space()='Incidents']"
            ).is_displayed()
        )

    # TC_INC_002: Verify the Hazard filter displays only the selected detection class.
    def test_TC_INC_002_hazard_filter_filters_incidents(self):
        hazard = self._hazard_filter()
        Select(hazard).select_by_value("fire")
        self.wait.until(lambda _driver: hazard.get_attribute("value") == "fire")
        self._wait_for_incidents_to_load()

        for row in self._rows():
            self.assertIn("Fire", row.find_element(By.XPATH, "./td[2]").text)

    # TC_INC_003: Verify camera or zone search filters the incident list.
    def test_TC_INC_003_camera_or_zone_search_filters_incidents(self):
        rows = self._rows()
        if not rows:
            self.skipTest("At least one incident is required to test search.")

        camera_zone = rows[0].find_element(By.XPATH, "./td[3]").text.splitlines()
        search_term = camera_zone[0].strip()
        self.assertTrue(search_term, "The first incident should have a camera name.")

        search = self.driver.find_element(
            By.XPATH, "//input[@aria-label='Search camera or zone']"
        )
        search.send_keys(search_term)

        self.wait.until(
            lambda _driver: all(
                search_term.lower()
                in row.find_element(By.XPATH, "./td[3]").text.lower()
                for row in self._rows()
            )
        )
        self.assertTrue(self._rows(), "Expected matching incidents for the camera.")

    # TC_INC_004: Verify the Response filter displays only the selected response state.
    def test_TC_INC_004_response_filter_filters_incidents(self):
        response = self._response_filter()
        Select(response).select_by_value("resolved")
        self.wait.until(lambda _driver: response.get_attribute("value") == "resolved")
        self._wait_for_incidents_to_load()

        for row in self._rows():
            self.assertIn(
                "resolved",
                row.find_element(By.XPATH, "./td[5]").text.lower(),
            )

    # TC_INC_005: Verify the default incident list includes all response states.
    def test_TC_INC_005_incident_list_defaults_to_all_response_states(self):
        self.assertEqual(self._hazard_filter().get_attribute("value"), "")
        self.assertEqual(self._response_filter().get_attribute("value"), "")

        for row in self._rows():
            self.assertTrue(row.find_element(By.XPATH, "./td[1]").text.strip())
            self.assertTrue(row.find_element(By.XPATH, "./td[2]").text.strip())
            self.assertTrue(row.find_element(By.XPATH, "./td[3]").text.strip())

    # TC_INC_006: Verify View evidence opens the selected incident's detail dialog.
    def test_TC_INC_006_view_evidence_opens_incident_details(self):
        dialog = self._open_first_incident()

        self.assertTrue(
            dialog.find_element(
                By.XPATH, ".//h2[contains(., 'detection')]"
            ).is_displayed()
        )
        self.assertTrue(
            dialog.find_element(
                By.XPATH, ".//*[normalize-space()='Detection details']"
            ).is_displayed()
        )
        self.assertTrue(
            dialog.find_element(
                By.XPATH, ".//*[normalize-space()='Captured evidence']"
            ).is_displayed()
        )

    # TC_INC_007: Verify each incident row shows its response status and confidence.
    def test_TC_INC_007_incident_status_and_confidence_are_displayed(self):
        for row in self._rows():
            with self.subTest(incident=row.find_element(By.XPATH, "./td[1]").text):
                status = row.find_element(By.XPATH, "./td[5]").text.strip().lower()
                confidence = row.find_element(By.XPATH, "./td[4]").text.strip()

                self.assertIn(status, {"unresolved", "in progress", "resolved"})
                self.assertRegex(confidence, r"^\d+(?:\.\d+)?%$")

    # TC_INC_008: Verify resolving an incident without a note is rejected for an eligible responder.
    def test_TC_INC_008_resolution_requires_a_note(self):
        dialog = self._open_first_incident()
        resolve_buttons = dialog.find_elements(
            By.XPATH, ".//button[normalize-space()='Mark resolved']"
        )
        if not resolve_buttons:
            self.skipTest(
                "The signed-in user must have response permission for this incident."
            )

        resolve_buttons[0].click()
        save_button = self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//section[@role='dialog']//button[normalize-space()='Save as resolved']",
                )
            )
        )
        save_button.click()

        self.assertIn(
            "Enter a resolution note",
            self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//section[@role='dialog']//*[@role='alert']")
                )
            ).text,
        )

    # TC_INC_009: Verify keeping an incident unresolved without a reason is rejected for an eligible responder.
    def test_TC_INC_009_unresolved_incident_requires_a_reason(self):
        dialog = self._open_first_incident()
        blocker_buttons = dialog.find_elements(
            By.XPATH, ".//button[normalize-space()='Keep unresolved']"
        )
        if not blocker_buttons:
            self.skipTest(
                "The signed-in user must have response permission and the incident "
                "must not already be resolved."
            )

        blocker_buttons[0].click()
        save_button = self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//section[@role='dialog']//button[normalize-space()='Save as unresolved']",
                )
            )
        )
        save_button.click()

        self.assertIn(
            "Enter a reason",
            self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//section[@role='dialog']//*[@role='alert']")
                )
            ).text,
        )

    # TC_INC_010: Verify incident rows display the required fields and evidence action.
    def test_TC_INC_010_incident_rows_show_required_data(self):
        headers = [
            header.text.strip()
            for header in self.driver.find_elements(
                By.XPATH, "//section[@aria-label='Incident table']//thead//th"
            )
        ]
        self.assertEqual(
            headers,
            [
                "Incident / observed",
                "Detection",
                "Camera / zone",
                "Confidence",
                "Response",
                "Evidence",
            ],
        )

        for row in self._rows():
            with self.subTest(incident=row.find_element(By.XPATH, "./td[1]").text):
                self.assertTrue(row.find_element(By.XPATH, "./td[1]").text.strip())
                self.assertTrue(row.find_element(By.XPATH, "./td[2]").text.strip())
                self.assertTrue(row.find_element(By.XPATH, "./td[3]").text.strip())
                self.assertTrue(row.find_element(By.XPATH, "./td[4]").text.strip())
                self.assertTrue(row.find_element(By.XPATH, "./td[5]").text.strip())
                self.assertTrue(
                    row.find_element(
                        By.XPATH,
                        ".//button[normalize-space()='View evidence ↗']",
                    ).is_displayed()
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
    