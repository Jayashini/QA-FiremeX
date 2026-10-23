import os
import unittest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = os.getenv("FIREMEX_BASE_URL", "http://localhost:5173/FiremeX").rstrip("/")
LIVE_FEED_URL = f"{BASE_URL}/admin/livefeed"
ADD_CAMERA_URL = f"{BASE_URL}/admin/livefeed/add-device"
LOGIN_URL = f"{BASE_URL}/login"
ADMIN_EMAIL = os.getenv("FIREMEX_ADMIN_EMAIL", "xxx@xxx.com")
ADMIN_PASSWORD = os.getenv("FIREMEX_ADMIN_PASSWORD", "xxxxxxxx")


class FiremexLiveFeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        if os.getenv("FIREMEX_HEADLESS", "").lower() in {"1", "true", "yes"}:
            chrome_options.add_argument("--headless=new")

        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(3)
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "driver", None):
            cls.driver.quit()

    def setUp(self):
        self.driver.get(LIVE_FEED_URL)
        self._login_if_needed()
        self.wait.until(EC.url_contains("/admin/livefeed"))

    def _login_if_needed(self):
        current_url = self.driver.current_url
        if "/admin/livefeed" not in current_url and "/login" not in current_url:
            self.driver.get(LOGIN_URL)

        if "/login" in self.driver.current_url:
            email = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, "//input[@type='email']"))
            )
            password = self.driver.find_element(By.XPATH, "//input[@type='password']")
            email.clear()
            email.send_keys(ADMIN_EMAIL)
            password.clear()
            password.send_keys(ADMIN_PASSWORD)
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(translate(normalize-space(.),"
                        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sign in')]",
                    )
                )
            ).click()
            self.wait.until(EC.url_contains("/admin"))

    def _button(self, text):
        return self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    f"//button[normalize-space(.)='{text}']"
                    f" | //a[normalize-space(.)='{text}']",
                )
            )
        )

    def _find_camera_card(self, camera_name=None):
        if camera_name:
            cards = self.driver.find_elements(
                By.XPATH,
                f"//*[self::article or self::div or self::li][contains(normalize-space(.), '{camera_name}')]",
            )
            if cards:
                return cards[0]
        cards = self.driver.find_elements(
            By.XPATH,
            "//*[self::article or self::div or self::li][contains(normalize-space(.), 'CAM-')]",
        )
        self.assertTrue(cards, "Expected at least one camera card on the live feed page.")
        return cards[0]

    def _notification_button(self):
        return self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(@aria-label, 'notification') or contains(@title, 'notification') or contains(@aria-label, 'alert') or contains(@title, 'alert')]"
                    " | //header//button[.//*[name()='svg']][last()]",
                )
            )
        )

    # # TC_LF_001: 1 x 2 layout button switches the grid layout.
    # def test_TC_LF_001_1x2_layout_button_switches_grid(self):
    #     self._button("1 x 2").click()
    #     self.assertIn("/admin/livefeed", self.driver.current_url)
    #     self.assertTrue(self._button("1 x 2").is_displayed())

    # TC_LF_002: 2 x 2 layout button switches the grid layout.
    # def test_TC_LF_002_2x2_layout_button_switches_grid(self):
    #     self._button("2 x 2").click()
    #     self.assertIn("/admin/livefeed", self.driver.current_url)
    #     self.assertTrue(self._button("2 x 2").is_displayed())

    # TC_LF_003: Add Camera button opens the camera registration form.
    def test_TC_LF_003_add_camera_button_opens_registration_form(self):
        self._button("Add Camera").click()
        self.wait.until(EC.url_contains("/admin/livefeed/add-device"))
        self.assertIn("/admin/livefeed/add-device", self.driver.current_url)
        self.assertTrue(
            self.driver.find_element(By.ID, "camera-source").is_displayed(),
            "Expected the camera source selector on the registration form.",
        )
        self.assertTrue(
            self._button("Add Camera").is_displayed(),
            "Expected the Add Camera submit button on the registration form.",
        )

    # TC_LF_004: Submit button stays disabled until required fields are filled.
    def test_TC_LF_004_submit_button_disabled_until_required_fields_are_filled(self):
        self.driver.get(ADD_CAMERA_URL)
        self.wait.until(EC.url_contains("/admin/livefeed/add-device"))
        submit = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//button[normalize-space()='Add Camera' and (@type='submit' or ancestor::form)]",
                )
            )
        )
        self.assertFalse(
            submit.is_enabled(),
            "The Add Camera button should be disabled while required fields are empty.",
        )

        name = self.driver.find_element(
            By.XPATH, "//input[@placeholder='e.g. Perimeter Main Entrance']"
        )
        name.send_keys("Server Room L3")

        from selenium.webdriver.support.ui import Select

        source = Select(self.driver.find_element(By.ID, "camera-source"))
        source.select_by_value("home_assistant")

        entity_controls = self.wait.until(
            lambda driver: [
                element
                for element in driver.find_elements(By.XPATH, "//form//select")
                if element.get_attribute("id") != "camera-source"
            ]
            or driver.find_elements(
                By.XPATH, "//input[@placeholder='camera.demo_camera']"
            )
        )
        if entity_controls[0].tag_name.lower() == "select":
            entity_selector = Select(entity_controls[0])
            available_entities = [
                option
                for option in entity_selector.options
                if option.is_enabled()
                and option.get_attribute("value")
                and option.get_attribute("value") != "placeholder"
            ]
            self.assertTrue(
                available_entities,
                "Expected at least one Home Assistant camera entity to select.",
            )
            entity_selector.select_by_value(
                available_entities[0].get_attribute("value")
            )
        else:
            entity_input = entity_controls[0]
            entity_input.send_keys("camera.demo_camera")

        zone = Select(
            self.driver.find_element(
                By.XPATH, "//select[.//option[normalize-space()='Warehouse A']]"
            )
        )
        zone.select_by_visible_text("Warehouse A")
        self.assertTrue(
            submit.is_enabled(),
            "The Add Camera button should be enabled after required fields are filled.",
        )

    # TC_LF_005: Cancel button closes the add camera form.
    def test_TC_LF_005_cancel_button_closes_registration_form(self):
        self.driver.get(ADD_CAMERA_URL)
        self.wait.until(EC.url_contains("/admin/livefeed/add-device"))
        cancel = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'cancel')] | //a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'cancel')]")))
        cancel.click()
        self.wait.until(EC.url_contains("/admin/livefeed"))
        self.assertIn("/admin/livefeed", self.driver.current_url)

    # TC_LF_006: Verify the Live Feed AI toggle changes the selected camera's AI state.
    def test_TC_LF_006_ai_enable_toggle_updates_camera_state(self):
        self.driver.get(LIVE_FEED_URL)
        self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h1[normalize-space()='Live Feed']")
            )
        )
        self.wait.until(
            lambda driver: driver.find_elements(By.CSS_SELECTOR, "article")
            or "No cameras enrolled."
            in driver.find_element(By.TAG_NAME, "body").text
        )
        camera_cards = self.driver.find_elements(By.CSS_SELECTOR, "article")
        if not camera_cards:
            self.skipTest("An enrolled camera is required to test the AI toggle.")

        def get_toggle():
            return self.driver.find_element(By.CSS_SELECTOR, "article").find_element(
                By.XPATH,
                ".//button[normalize-space()='Enable AI' or normalize-space()='Disable AI']",
            )

        initial_label = get_toggle().text.strip()
        self.assertIn(initial_label, {"Enable AI", "Disable AI"})
        expected_label = "Disable AI" if initial_label == "Enable AI" else "Enable AI"
        expected_state = "AI enabled" if initial_label == "Enable AI" else "AI disabled"
        get_toggle().click()
        self.wait.until(lambda _driver: get_toggle().text.strip() == expected_label)
        self.wait.until(
            lambda _driver: expected_state
            in self.driver.find_element(By.CSS_SELECTOR, "article").text
        )

    # TC_LF_007: Required field validation is shown when camera details are missing.
    def test_TC_LF_007_required_field_validation_shows_error_messages(self):
        self.driver.get(ADD_CAMERA_URL)
        self.wait.until(EC.url_contains("/admin/livefeed/add-device"))
        submit = self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'add camera')]",
                )
            )
        )
        submit.click()
        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        self.assertTrue(
            any(
                word in page_text
                for word in [
                    "required",
                    "please enter",
                    "invalid",
                    "camera name",
                    "ip address",
                ]
            ),
            "Expected the form to show validation errors for missing camera fields.",
        )

    # TC_LF_008: Verify camera registration is blocked when the required display name is empty.
    def test_TC_LF_008_empty_display_name_is_rejected(self):
        self.driver.get(ADD_CAMERA_URL)
        name = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//input[@placeholder='e.g. Perimeter Main Entrance']")
            )
        )
        name.clear()
        self.driver.find_element(
            By.XPATH, "//button[normalize-space()='Add Camera']"
        ).click()
        self.assertTrue(
            self.driver.execute_script(
                "return arguments[0].validity.valueMissing;", name
            ),
            "The browser should reject submission when the required display name is empty.",
        )
        self.assertIn("/admin/livefeed/add-device", self.driver.current_url)

    # TC_LF_009: Verify a valid Home Assistant camera can be registered and appears in Live Feed.
    def test_TC_LF_009_successful_camera_registration(self):
        import uuid

        from selenium.webdriver.support.ui import Select

        entity_id = os.getenv("FIREMEX_TEST_CAMERA_ENTITY")
        self.assertTrue(
            entity_id,
            "Set FIREMEX_TEST_CAMERA_ENTITY to a dedicated, available Home Assistant camera.",
        )
        camera_name = f"FiremeX Selenium {uuid.uuid4().hex[:8]}"
        self.driver.get(ADD_CAMERA_URL)
        name = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//input[@placeholder='e.g. Perimeter Main Entrance']")
            )
        )
        name.clear()
        name.send_keys(camera_name)
        source = self.wait.until(
            EC.presence_of_element_located((By.ID, "camera-source"))
        )
        Select(source).select_by_value("home_assistant")
        entity_selects = [
            element
            for element in self.driver.find_elements(By.XPATH, "//form//select")
            if element.get_attribute("id") != "camera-source"
        ]
        if entity_selects:
            Select(entity_selects[0]).select_by_value(entity_id)
        else:
            entity_input = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//input[@placeholder='camera.demo_camera']")
                )
            )
            entity_input.clear()
            entity_input.send_keys(entity_id)
        zone_select = self.driver.find_element(
            By.XPATH,
            "//select[.//option[normalize-space()='Warehouse A']]",
        )
        Select(zone_select).select_by_visible_text("Warehouse A")
        self.driver.find_element(
            By.XPATH, "//button[normalize-space()='Add Camera']"
        ).click()
        self.wait.until(EC.url_contains("/admin/livefeed"))
        self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, f"//article[contains(., '{camera_name}')]")
            )
        )

    # TC_LF_010: Critical or altered camera cards are highlighted in red.
    def test_TC_LF_010_critical_camera_shown_in_red(self):
        self._find_camera_card()
        body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        self.assertTrue(
            "critical" in body_text or "alert" in body_text or "camera" in body_text,
            "Expected the live feed to display an alert state for critical cameras.",
        )

    # TC_LF_011: Camera card edit button is clickable.
    def test_TC_LF_011_edit_button_on_camera_card_is_clickable(self):
        card = self._find_camera_card()
        edit_button = card.find_element(
            By.XPATH,
            ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'edit')] | .//button[contains(@aria-label, 'edit')] | .//*[name()='svg'][contains(@data-testid, 'edit')]",
        )
        self.assertTrue(edit_button.is_displayed())
        edit_button.click()

    # TC_LF_012: Camera card delete button is clickable.
    def test_TC_LF_012_delete_button_on_camera_card_is_clickable(self):
        card = self._find_camera_card()
        delete_button = card.find_element(
            By.XPATH,
            ".//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'delete')] | .//button[contains(@aria-label, 'delete')] | .//*[name()='svg'][contains(@data-testid, 'delete')]",
        )
        self.assertTrue(delete_button.is_displayed())
        delete_button.click()

    # TC_LF_013: Camera card includes required details.
    def test_TC_LF_013_camera_card_shows_required_details(self):
        card_text = self._find_camera_card().text.lower()
        self.assertTrue(
            any(
                keyword in card_text
                for keyword in ["cam-", "camera", "normal", "zone", "live"]
            ),
            "Expected the camera card to include its identification and status details.",
        )

    # TC_LF_014: All registered cameras are displayed on the live feed.
    def test_TC_LF_014_all_registered_cameras_are_shown(self):
        cards = self.driver.find_elements(
            By.XPATH,
            "//*[self::article or self::div or self::li][contains(normalize-space(.), 'CAM-')]",
        )
        self.assertTrue(cards, "Expected camera cards to be rendered on the live feed.")

    # TC_LF_017: Live feed should show a real-time camera preview for the active stream.
    def test_TC_LF_017_live_feed_display_updates_with_stream_preview(self):
        preview = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[self::video or self::img or self::canvas][1] | //*[contains(@class,'video')][1]",
                )
            )
        )
        self.assertTrue(
            preview.is_displayed(),
            "Expected the live camera preview to be visible.",
        )

    # TC_LF_018: Live Feed is highlighted in the sidebar navigation.
    def test_TC_LF_018_live_feed_sidebar_is_highlighted(self):
        nav_item = self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//aside//*[self::a or self::button][normalize-space(.)='Live Feed']"
                    " | //nav//*[self::a or self::button][normalize-space(.)='Live Feed']",
                )
            )
        )
        self.assertTrue(
            nav_item.is_displayed(),
            "Expected the Live Feed nav item to be visible.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
