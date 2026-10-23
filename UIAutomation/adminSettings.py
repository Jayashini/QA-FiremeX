import os
import unittest
from urllib.parse import urlsplit

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = os.getenv("FIREMEX_BASE_URL", "http://localhost:5173/FiremeX").rstrip("/")
SETTINGS_URL = f"{BASE_URL}/admin/settings"
LOGIN_URL = f"{BASE_URL}/login"
ADMIN_EMAIL = os.getenv("FIREMEX_ADMIN_EMAIL", "admin@firemex.com")
ADMIN_PASSWORD = os.getenv("FIREMEX_ADMIN_PASSWORD", "password123")


class FiremexSettingsTests(unittest.TestCase):
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
        self.driver.get(SETTINGS_URL)

        if "/login" in self.driver.current_url:
            email = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//input[@type='email']")
                )
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

            # Successful login may redirect to the dashboard, so navigate to Settings directly.
            self.wait.until(
                lambda driver: "/admin/" in driver.current_url
                or "/operator/" in driver.current_url
            )
            self.driver.get(SETTINGS_URL)

        self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h1[normalize-space()='Settings']")
            )
        )

    def _card(self, title):
        return self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    f"//section[.//h2[normalize-space()='{title}']]",
                )
            )
        )

    def _field_input(self, label):
        return self._card("Organisation").find_element(
            By.XPATH,
            f".//label[.//span[normalize-space()='{label}']]//input",
        )

    # TC_SET_001: Verify organization details are loaded into the Settings form.
    def test_TC_SET_001_organization_details_are_displayed(self):
        organization = self._card("Organisation")

        for label in ("Name", "Sector", "Contact email"):
            field = organization.find_element(
                By.XPATH,
                f".//label[.//span[normalize-space()='{label}']]//input",
            )
            self.assertTrue(field.get_attribute("value").strip(), f"{label} should be populated.")

        self.assertTrue(
            organization.find_element(
                By.XPATH,
                ".//label[.//span[normalize-space()='Country']]//select",
            ).is_displayed()
        )

    # TC_SET_002: Verify organization changes save successfully and restore the original name.
    def test_TC_SET_002_organization_changes_can_be_saved(self):
        organization = self._card("Organisation")
        name_field = self._field_input("Name")
        original_name = name_field.get_attribute("value").strip()
        self.assertTrue(original_name, "A saved organization name is required for this test.")

        try:
            name_field.clear()
            name_field.send_keys(f"{original_name} Test")
            organization.find_element(
                By.XPATH, ".//button[normalize-space()='Save changes']"
            ).click()

            self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//*[normalize-space()='Organisation updated.']")
                )
            )
        finally:
            # Restore the original organization name to avoid leaving test data behind.
            name_field = self._field_input("Name")
            name_field.clear()
            name_field.send_keys(original_name)
            self._card("Organisation").find_element(
                By.XPATH, ".//button[normalize-space()='Save changes']"
            ).click()
            self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//*[normalize-space()='Organisation updated.']")
                )
            )

    # TC_SET_003: Verify the Save changes button is visible and enabled.
    def test_TC_SET_003_save_changes_button_is_visible_and_enabled(self):
        save_button = self._card("Organisation").find_element(
            By.XPATH, ".//button[normalize-space()='Save changes']"
        )
        self.assertTrue(save_button.is_displayed())
        self.assertTrue(save_button.is_enabled())

    # TC_SET_004: Verify the organization join code is displayed.
    def test_TC_SET_004_operator_join_code_is_displayed(self):
        join_code_card = self._card("Operator join code")
        code = join_code_card.find_element(
            By.XPATH, ".//button[normalize-space()='Copy']/preceding-sibling::span"
        ).text.strip()

        self.assertTrue(code, "An organization join code should be displayed.")
        self.assertNotEqual(code, "...", "The join code should finish loading.")

    # TC_SET_005: Verify team summary shows loaded active and pending counts.
    def test_TC_SET_005_team_counts_are_displayed(self):
        team_card = self._card("Your team")
        self.wait.until(
            lambda _driver: all(
                count.text.strip().isdigit()
                for count in team_card.find_elements(
                    By.XPATH, ".//span[contains(@class,'text-3xl')]"
                )
            )
        )

        counts = team_card.find_elements(
            By.XPATH, ".//span[contains(@class,'text-3xl')]"
        )
        self.assertEqual(len(counts), 2)
        for count in counts:
            self.assertRegex(count.text.strip(), r"^\d+$")

        card_text = " ".join(team_card.text.split()).upper()
        self.assertIn("ACTIVE", card_text)
        self.assertIn("AWAITING APPROVAL", card_text)

    # TC_SET_006: Verify camera summary shows total and AI-enabled camera counts.
    def test_TC_SET_006_camera_counts_are_displayed(self):
        camera_card = self._card("Monitored cameras")
        self.wait.until(
            lambda _driver: all(
                count.text.strip().isdigit()
                for count in camera_card.find_elements(
                    By.XPATH, ".//span[contains(@class,'text-3xl')]"
                )
            )
        )

        counts = camera_card.find_elements(
            By.XPATH, ".//span[contains(@class,'text-3xl')]"
        )
        self.assertEqual(len(counts), 2)
        total_cameras, ai_enabled = [int(count.text.strip()) for count in counts]
        self.assertGreaterEqual(total_cameras, ai_enabled)

        card_text = " ".join(camera_card.text.split()).upper()
        self.assertIn("CAMERAS", card_text)
        self.assertIn("AI ENABLED", card_text)

    # # TC_SET_007: Verify all system dependency statuses finish loading with a status detail.
    # def test_TC_SET_007_system_status_details_are_displayed(self):
    #     status_card = self._card("System status")
    #     expected_services = ("Home Assistant", "Database", "Detection service")

    #     for service in expected_services:
    #         self.assertIn(service, status_card.text)

    #     self.wait.until(
    #         lambda _driver: "Checking..." not in status_card.text
    #     )
    #     self.assertTrue(status_card.text.strip())

    # TC_SET_008: Verify the Settings sidebar item is highlighted as the active page.
    def test_TC_SET_008_settings_sidebar_item_is_highlighted(self):
        settings_button = self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//aside//nav//button[.//span[normalize-space()='Settings']]",
                )
            )
        )
        classes = settings_button.get_attribute("class") or ""
        self.assertIn("border-l-4", classes)
        self.assertIn("text-accent", classes)

    # TC_SET_009: Verify Copy writes the displayed organization code to the clipboard.
    def test_TC_SET_009_operator_join_code_can_be_copied(self):
        origin = urlsplit(BASE_URL)
        self.driver.execute_cdp_cmd(
            "Browser.grantPermissions",
            {
                "origin": f"{origin.scheme}://{origin.netloc}",
                "permissions": ["clipboardReadWrite", "clipboardSanitizedWrite"],
            },
        )

        join_code_card = self._card("Operator join code")
        code = join_code_card.find_element(
            By.XPATH, ".//button[normalize-space()='Copy']/preceding-sibling::span"
        ).text.strip()
        self.assertTrue(code and code != "...", "A loaded join code is required.")

        join_code_card.find_element(
            By.XPATH, ".//button[normalize-space()='Copy']"
        ).click()

        self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//section[.//h2[normalize-space()='Operator join code']]"
                    "//button[normalize-space()='Copied']",
                )
            )
        )

        clipboard_text = self.driver.execute_async_script(
            """
            const done = arguments[0];
            navigator.clipboard.readText().then(done).catch(error => done(`ERROR: ${error}`));
            """
        )
        self.assertEqual(clipboard_text, code, "Clipboard should contain the displayed join code.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
