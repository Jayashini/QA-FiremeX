import os
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


APP_BASE_URL = os.getenv(
    "FIREMEX_BASE_URL",
    "http://localhost:5173/FiremeX",
).rstrip("/")
PROFILE_URL = f"{APP_BASE_URL}/admin/profile"
LOGIN_URL = f"{APP_BASE_URL}/login"

ADMIN_EMAIL = os.getenv("FIREMEX_ADMIN_EMAIL", "admin@firemex.com")
ADMIN_PASSWORD = os.getenv("FIREMEX_ADMIN_PASSWORD", "password123")


class FiremexProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        if os.getenv("FIREMEX_HEADLESS", "").lower() in {"1", "true", "yes"}:
            options.add_argument("--headless=new")

        cls.driver = webdriver.Chrome(options=options)
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "driver", None):
            cls.driver.quit()

    def setUp(self):
        self.driver.get(PROFILE_URL)
        self._login_if_needed()
        self.driver.get(PROFILE_URL)
        self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h1[normalize-space()='Profile']")
            )
        )

    def _login_if_needed(self):
        self.wait.until(
            lambda driver: (
                "/login" in driver.current_url
                or driver.find_elements(
                    By.XPATH, "//h1[normalize-space()='Profile']"
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
            By.XPATH, "//button[@type='submit' and normalize-space()='Sign in']"
        ).click()

        self.wait.until(EC.url_contains("/admin"))

    def _section(self, title):
        return self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    f"//section[.//h2[normalize-space()='{title}']]",
                )
            )
        )

    def _text_field(self, label):
        return self.driver.find_element(
            By.XPATH,
            f"//label[span[normalize-space()='{label}']]/input",
        )

    def _button(self, label):
        return self.driver.find_element(
            By.XPATH,
            f"//button[normalize-space()='{label}']",
        )

    # TC_PROF_001: Verify the Profile page header and subtitle are displayed.
    def test_TC_PROF_001_profile_header_is_displayed(self):
        header = self.driver.find_element(
            By.XPATH, "//header[.//h1[normalize-space()='Profile']]"
        )
        self.assertIn("Your account and organisation", header.text)

    # TC_PROF_002: Verify the signed-in user's name, email, and avatar are displayed.
    def test_TC_PROF_002_user_identity_is_displayed(self):
        identity = self.driver.find_element(
            By.XPATH,
            "//header[.//h1[normalize-space()='Profile']]"
            "/following-sibling::div/section[1]",
        )
        display_name = self._text_field("Display name").get_attribute("value")
        initials = identity.find_element(
            By.XPATH, ".//div[contains(@class, 'rounded-full')]"
        ).text

        self.assertTrue(display_name.strip(), "Expected the user's name to be shown.")
        self.assertIn(display_name, identity.text)
        self.assertIn("@", identity.text, "Expected the user's email to be shown.")
        expected_initials = "".join(
            part[0] for part in display_name.split()[:2]
        ).upper()
        self.assertEqual(initials, expected_initials)

    # TC_PROF_003: Verify the role and account status badges are visible.
    def test_TC_PROF_003_role_and_status_are_displayed(self):
        identity = self.driver.find_element(
            By.XPATH,
            "//header[.//h1[normalize-space()='Profile']]"
            "/following-sibling::div/section[1]",
        )
        identity_text = identity.text.upper()

        self.assertIn("ADMINISTRATOR", identity_text)
        self.assertTrue(
            "ACTIVE" in identity_text or "PENDING" in identity_text,
            "Expected the user's account status to be displayed.",
        )

    # TC_PROF_004: Verify organisation details are displayed as read-only fields.
    def test_TC_PROF_004_organisation_details_are_read_only(self):
        organisation = self._section("Your organisation")
        organisation_text = organisation.text.upper()

        for label in ("NAME", "SECTOR", "CONTACT EMAIL", "PHONE", "COUNTRY"):
            with self.subTest(field=label):
                self.assertIn(label, organisation_text)

        editable_controls = organisation.find_elements(
            By.XPATH, ".//input | .//select | .//textarea"
        )
        self.assertEqual(
            editable_controls,
            [],
            "Organisation details should be read-only on the Profile page.",
        )

    # TC_PROF_005: Verify the account section shows member-since and display-name fields.
    def test_TC_PROF_005_account_fields_are_displayed(self):
        account = self._section("Account")
        account_text = account.text.upper()

        self.assertIn("MEMBER SINCE", account_text)
        self.assertTrue(self._text_field("Display name").is_displayed())

        member_since_row = account.find_element(
            By.XPATH, ".//div[span[normalize-space()='Member since']]"
        )
        values = member_since_row.find_elements(By.XPATH, "./span")
        self.assertEqual(len(values), 2)
        self.assertTrue(values[1].text.strip())

    # TC_PROF_006: Verify a display name shorter than two characters is rejected.
    def test_TC_PROF_006_short_display_name_is_rejected(self):
        name = self._text_field("Display name")
        name.clear()
        name.send_keys(" ")

        self._button("Save name").click()

        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "Please enter at least 2 characters.",
            )
        )
        self.assertEqual(name.get_attribute("value"), " ")

    # TC_PROF_007: Verify a valid display name can be saved and then restored.
    def test_TC_PROF_007_display_name_can_be_updated(self):
        name = self._text_field("Display name")
        original_name = name.get_attribute("value")
        updated_name = "Selenium Profile Test"

        self.assertNotEqual(original_name, updated_name)
        name.clear()
        name.send_keys(updated_name)
        self._button("Save name").click()

        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "Name updated.",
            )
        )
        self.assertIn(updated_name, self.driver.find_element(By.TAG_NAME, "body").text)

        # Restore the account name so this test does not leave a profile change behind.
        name = self._text_field("Display name")
        name.clear()
        name.send_keys(original_name)
        self._button("Save name").click()
        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "Name updated.",
            )
        )
        self.assertEqual(
            self._text_field("Display name").get_attribute("value"),
            original_name,
        )

    # TC_PROF_008: Verify password inputs are present and conceal typed characters.
    def test_TC_PROF_008_password_fields_are_secure(self):
        self._section("Change password")

        for label in ("Current password", "New password", "Confirm new password"):
            with self.subTest(field=label):
                password_field = self._text_field(label)
                self.assertTrue(password_field.is_displayed())
                self.assertEqual(password_field.get_attribute("type"), "password")

        self.assertTrue(self._button("Update password").is_displayed())

    # TC_PROF_009: Verify a new password shorter than six characters is rejected.
    def test_TC_PROF_009_short_new_password_is_rejected(self):
        self._text_field("Current password").send_keys("current-password")
        self._text_field("New password").send_keys("12345")
        self._text_field("Confirm new password").send_keys("12345")
        self._button("Update password").click()

        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "The new password must be at least 6 characters.",
            )
        )

    # TC_PROF_010: Verify mismatched new-password entries are rejected.
    def test_TC_PROF_010_password_mismatch_is_rejected(self):
        self._text_field("Current password").send_keys("current-password")
        self._text_field("New password").send_keys("NewPassword123")
        self._text_field("Confirm new password").send_keys("DifferentPassword123")
        self._button("Update password").click()

        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "The two new passwords do not match.",
            )
        )

    # TC_PROF_011: Verify a valid password can be changed and restored on a test account.
    def test_TC_PROF_011_password_can_be_changed_and_restored(self):
        current_password = os.getenv("FIREMEX_TEST_CURRENT_PASSWORD", "password123").strip()
        temporary_password = os.getenv("FIREMEX_TEST_NEW_PASSWORD", "password1234").strip()

        if not current_password or not temporary_password:
            self.skipTest(
                "Password-change test skipped. Set FIREMEX_TEST_CURRENT_PASSWORD "
                "and FIREMEX_TEST_NEW_PASSWORD to the current and temporary "
                "passwords for a dedicated test account."
            )

        if current_password == temporary_password:
            self.fail(
                "FIREMEX_TEST_NEW_PASSWORD must differ from "
                "FIREMEX_TEST_CURRENT_PASSWORD."
            )
        if len(temporary_password) < 6:
            self.fail(
                "FIREMEX_TEST_NEW_PASSWORD must be at least 6 characters long."
            )

        self._text_field("Current password").send_keys(current_password)
        self._text_field("New password").send_keys(temporary_password)
        self._text_field("Confirm new password").send_keys(temporary_password)
        self._button("Update password").click()

        self.wait.until(
            lambda _driver: all(
                not self._text_field(label).get_attribute("value")
                for label in (
                    "Current password",
                    "New password",
                    "Confirm new password",
                )
            )
        )

        self._text_field("Current password").send_keys(temporary_password)
        self._text_field("New password").send_keys(current_password)
        self._text_field("Confirm new password").send_keys(current_password)
        self._button("Update password").click()

        self.wait.until(
            lambda _driver: all(
                not self._text_field(label).get_attribute("value")
                for label in (
                    "Current password",
                    "New password",
                    "Confirm new password",
                )
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)